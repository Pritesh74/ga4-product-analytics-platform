/*
  fct_sessions
  ────────────
  Session fact table. One row per (user_pseudo_id, ga_session_id).
  Source: int_sessions (view) materialized here as a queryable table.

  Adds channel_group on top of int_sessions for convenient slicing
  without requiring a join to dim_users.
*/

{{ config(materialized='table') }}

with sessions as (

    select * from {{ ref('int_sessions') }}

),

final as (

    select
        session_key,
        user_pseudo_id,
        ga_session_id,
        ga_session_number,
        session_date,
        session_start_ts,
        session_end_ts,
        session_duration_seconds,

        -- Raw channel attributes
        traffic_medium,
        traffic_source,
        traffic_campaign,

        -- Channel grouping (same logic as dim_users for consistent slicing)
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

        -- Device
        device_category,
        device_os,
        device_browser,

        -- Geography
        geo_country,
        geo_region,
        geo_city,
        geo_continent,

        -- Engagement
        is_engaged,
        total_engagement_msec,

        -- Funnel activity counts
        page_view_count,
        view_item_count,
        add_to_cart_count,
        begin_checkout_count,
        purchase_count,

        -- Conversion
        has_purchase,
        transaction_id,
        session_revenue_usd,

        landing_page

    from sessions

)

select * from final
