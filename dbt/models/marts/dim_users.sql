/*
  dim_users
  ─────────
  User dimension table. One row per user_pseudo_id.
  Source: int_user_spine.

  Adds:
  - cohort_month  (DATE_TRUNC of first_seen_date) for retention analysis
  - channel_group (simplified grouping of traffic_medium)
*/

{{ config(materialized='table') }}

with user_spine as (

    select * from {{ ref('int_user_spine') }}

),

final as (

    select
        user_pseudo_id,
        first_seen_date,
        last_seen_date,
        user_first_touch_ts,
        user_lifespan_days,

        -- Acquisition cohort (month of first event — used in retention matrix)
        date_trunc(first_seen_date, month)                              as cohort_month,

        -- Raw channel attributes from GA4 first-touch user property
        traffic_medium,
        traffic_source,
        traffic_campaign,

        -- Channel grouping aligned with GA4 default channel grouping conventions
        case
            when lower(traffic_medium) = 'organic'                      then 'organic_search'
            when lower(traffic_medium) in ('cpc', 'ppc', 'paid search') then 'paid_search'
            when lower(traffic_medium) = 'email'                        then 'email'
            when lower(traffic_medium) = 'referral'                     then 'referral'
            when lower(traffic_medium) in ('social', 'social media')    then 'social'
            when lower(traffic_medium) = 'affiliate'                    then 'affiliate'
            when traffic_medium is null
              or lower(traffic_medium) = '(none)'                       then 'direct'
            else 'other'
        end                                                             as channel_group,

        -- First-touch device and geography
        first_device_category,
        first_geo_country,

        -- Lifetime activity summary
        total_sessions,
        total_page_views,
        total_view_items,
        total_add_to_cart,
        total_begin_checkout,
        total_purchase_events,
        total_orders,
        total_revenue_usd,
        first_purchase_date,
        last_purchase_date,
        is_purchaser

    from user_spine

)

select * from final
