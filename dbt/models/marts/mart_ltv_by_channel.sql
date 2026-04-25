/*
  mart_ltv_by_channel
  ───────────────────
  Customer lifetime value summary by acquisition channel.
  One row per (channel_group, traffic_medium, traffic_source, cohort_month).

  Key metrics:
  - avg_revenue_per_user       (includes non-purchasers — true channel LTV)
  - avg_revenue_per_purchaser  (purchasers only — measures order value depth)
  - purchase_rate              (channel conversion efficiency)

  Consumers: Streamlit LTV dashboard, channel ROI comparisons.
*/

{{ config(materialized='table') }}

with users as (

    select
        user_pseudo_id,
        channel_group,
        traffic_medium,
        traffic_source,
        cohort_month

    from {{ ref('dim_users') }}

),

purchases as (

    select
        user_pseudo_id,
        transaction_id,
        purchase_revenue_usd

    from {{ ref('fct_purchases') }}

),

-- User-level LTV: one row per user with their lifetime order count and revenue
user_ltv as (

    select
        u.user_pseudo_id,
        u.channel_group,
        u.traffic_medium,
        u.traffic_source,
        u.cohort_month,
        count(distinct p.transaction_id)                                as total_orders,
        coalesce(sum(p.purchase_revenue_usd), 0)                       as total_revenue_usd

    from users u
    left join purchases p using (user_pseudo_id)
    group by
        u.user_pseudo_id,
        u.channel_group,
        u.traffic_medium,
        u.traffic_source,
        u.cohort_month

),

final as (

    select
        channel_group,
        traffic_medium,
        traffic_source,
        cohort_month,

        count(distinct user_pseudo_id)                                  as total_users,
        countif(total_orders > 0)                                       as purchasing_users,
        safe_divide(
            countif(total_orders > 0),
            count(distinct user_pseudo_id)
        )                                                               as purchase_rate,

        sum(total_revenue_usd)                                          as total_revenue_usd,
        safe_divide(
            sum(total_revenue_usd),
            count(distinct user_pseudo_id)
        )                                                               as avg_revenue_per_user,
        safe_divide(
            sum(total_revenue_usd),
            nullif(countif(total_orders > 0), 0)
        )                                                               as avg_revenue_per_purchaser,

        sum(total_orders)                                               as total_orders,
        safe_divide(
            sum(total_orders),
            nullif(countif(total_orders > 0), 0)
        )                                                               as avg_orders_per_purchaser

    from user_ltv
    group by
        channel_group,
        traffic_medium,
        traffic_source,
        cohort_month

)

select * from final
