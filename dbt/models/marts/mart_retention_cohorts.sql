/*
  mart_retention_cohorts
  ──────────────────────
  Monthly purchase retention cohort matrix.
  One row per (cohort_month, months_since_acquisition).

  Definition:
  - cohort_month = DATE_TRUNC(first_seen_date, MONTH) from dim_users
    (acquisition cohort: the month the user first appeared in GA4)
  - months_since_acquisition = how many months after acquisition the user
    made at least one purchase
  - retention_rate = retained_users / cohort_size

  Dataset note: GA4 sample covers only 2020-11 through 2021-01 (3 months),
  so the matrix has a natural triangular shape with max 2 months of follow-up.
*/

{{ config(materialized='table') }}

with users as (

    select
        user_pseudo_id,
        cohort_month

    from {{ ref('dim_users') }}
    where cohort_month is not null

),

purchases as (

    select
        user_pseudo_id,
        event_date

    from {{ ref('fct_purchases') }}

),

-- One row per user × purchase month (deduplicated — we only care if they bought, not how many times)
user_active_months as (

    select distinct
        p.user_pseudo_id,
        u.cohort_month,
        date_trunc(p.event_date, month)                                 as active_month,
        date_diff(
            date_trunc(p.event_date, month),
            u.cohort_month,
            month
        )                                                               as months_since_acquisition

    from purchases p
    inner join users u using (user_pseudo_id)
    where date_trunc(p.event_date, month) >= u.cohort_month

),

cohort_sizes as (

    select
        cohort_month,
        count(distinct user_pseudo_id)                                  as cohort_size

    from users
    group by cohort_month

),

retention as (

    select
        cohort_month,
        months_since_acquisition,
        count(distinct user_pseudo_id)                                  as retained_users

    from user_active_months
    group by cohort_month, months_since_acquisition

),

final as (

    select
        r.cohort_month,
        r.months_since_acquisition,
        cs.cohort_size,
        r.retained_users,
        safe_divide(r.retained_users, cs.cohort_size)                   as retention_rate

    from retention r
    inner join cohort_sizes cs using (cohort_month)

)

select * from final
