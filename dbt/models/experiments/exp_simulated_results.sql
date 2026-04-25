-- SIMULATED experiment results — not real A/B test data.
-- Joins deterministic assignments to observed outcomes within the experiment window.
-- Treatment effect is emergent from the hash split — no artificial uplift injected.
{{ config(materialized='table') }}

with assignments as (
    select * from {{ ref('exp_simulated_assignment') }}
),

-- All purchases made by assigned users during the experiment window
user_purchases as (
    select
        p.user_pseudo_id,
        count(distinct p.transaction_id)            as total_orders,
        sum(p.purchase_revenue_usd)                 as total_revenue_usd
    from {{ ref('fct_purchases') }} p
    inner join assignments a
        on p.user_pseudo_id = a.user_pseudo_id
       and p.event_date between a.experiment_start_date and a.experiment_end_date
    where p.transaction_id is not null
    group by p.user_pseudo_id
),

-- All checkout events by assigned users during the experiment window
user_checkouts as (
    select
        s.user_pseudo_id,
        count(*) as checkout_sessions
    from {{ ref('fct_sessions') }} s
    inner join assignments a
        on s.user_pseudo_id = a.user_pseudo_id
       and s.session_date between a.experiment_start_date and a.experiment_end_date
    where s.begin_checkout_count > 0
    group by s.user_pseudo_id
),

-- All session engagement for guardrail metrics
user_engagement as (
    select
        s.user_pseudo_id,
        count(*)                                    as total_sessions,
        countif(s.is_engaged)                       as engaged_sessions,
        safe_divide(
            countif(s.is_engaged), count(*)
        )                                           as engagement_rate
    from {{ ref('fct_sessions') }} s
    inner join assignments a
        on s.user_pseudo_id = a.user_pseudo_id
       and s.session_date between a.experiment_start_date and a.experiment_end_date
    group by s.user_pseudo_id
),

user_outcomes as (
    select
        a.user_pseudo_id,
        a.experiment_id,
        a.experiment_name,
        a.variant_id,
        a.variant_name,
        a.experiment_start_date,
        a.experiment_end_date,
        a.is_simulated,
        -- Primary metric: did user purchase at all during window?
        coalesce(p.total_orders, 0) > 0             as did_convert,
        coalesce(p.total_orders, 0)                 as total_orders,
        coalesce(p.total_revenue_usd, 0)            as total_revenue_usd,
        -- Guardrail: checkout sessions
        coalesce(c.checkout_sessions, 0)            as checkout_sessions,
        -- Guardrail: engagement
        coalesce(e.total_sessions, 0)               as total_sessions,
        coalesce(e.engaged_sessions, 0)             as engaged_sessions,
        coalesce(e.engagement_rate, 0)              as user_engagement_rate
    from assignments a
    left join user_purchases p   using (user_pseudo_id)
    left join user_checkouts c   using (user_pseudo_id)
    left join user_engagement e  using (user_pseudo_id)
),

variant_summary as (
    select
        experiment_id,
        experiment_name,
        variant_id,
        variant_name,
        experiment_start_date,
        experiment_end_date,
        is_simulated,

        -- Sample size
        count(*)                                                                as n_users,

        -- Primary metric: conversion rate (checkout → purchase)
        countif(did_convert)                                                    as n_conversions,
        safe_divide(countif(did_convert), count(*))                             as conversion_rate,

        -- Revenue per user (including non-purchasers)
        sum(total_revenue_usd)                                                  as total_revenue_usd,
        safe_divide(sum(total_revenue_usd), count(*))                           as revenue_per_user,
        safe_divide(sum(total_revenue_usd), nullif(countif(did_convert), 0))    as revenue_per_converter,

        -- Standard deviation for revenue per user (for z-test SE computation)
        stddev_pop(total_revenue_usd)                                           as stddev_revenue_per_user,

        -- Orders
        sum(total_orders)                                                       as total_orders,
        safe_divide(sum(total_orders), nullif(countif(did_convert), 0))         as avg_orders_per_converter,

        -- Guardrail: avg checkout sessions per user
        safe_divide(sum(checkout_sessions), count(*))                           as avg_checkouts_per_user,

        -- Guardrail: engagement rate
        safe_divide(sum(engaged_sessions), nullif(sum(total_sessions), 0))      as engagement_rate

    from user_outcomes
    group by
        experiment_id, experiment_name,
        variant_id, variant_name,
        experiment_start_date, experiment_end_date,
        is_simulated
)

select * from variant_summary
order by variant_id
