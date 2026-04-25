/*
  int_sessions
  ────────────
  Session-grain view. One row per (user_pseudo_id, ga_session_id).
  Aggregates all events in a session into engagement metrics,
  funnel-stage counts, and conversion outcome.

  Key design choices:
  - session_date  = date of the first event (sessions can span midnight)
  - device/geo    = first observed value in the session (stable in practice)
  - is_engaged    = true if GA4 recorded session_engaged=1 on any event
  - landing_page  = first page_location ordered by event_ts
*/

{{ config(materialized='view') }}

with events as (

    select * from {{ ref('stg_ga4__events') }}

),

session_agg as (

    select
        session_key,
        user_pseudo_id,

        max(ga_session_id)                                              as ga_session_id,
        max(ga_session_number)                                          as ga_session_number,

        -- Session time bounds
        min(event_date)                                                 as session_date,
        min(event_ts)                                                   as session_start_ts,
        max(event_ts)                                                   as session_end_ts,

        -- Channel (user-level attribute in GA4 — same across all events for a user)
        max(traffic_medium)                                             as traffic_medium,
        max(traffic_source)                                             as traffic_source,
        max(traffic_campaign)                                           as traffic_campaign,

        -- Device: take first observed value in the session
        (array_agg(device_category ignore nulls order by event_ts limit 1))[safe_offset(0)]
                                                                        as device_category,
        (array_agg(device_os       ignore nulls order by event_ts limit 1))[safe_offset(0)]
                                                                        as device_os,
        (array_agg(device_browser  ignore nulls order by event_ts limit 1))[safe_offset(0)]
                                                                        as device_browser,

        -- Geography: take first observed value in the session
        (array_agg(geo_country   ignore nulls order by event_ts limit 1))[safe_offset(0)]
                                                                        as geo_country,
        (array_agg(geo_region    ignore nulls order by event_ts limit 1))[safe_offset(0)]
                                                                        as geo_region,
        (array_agg(geo_city      ignore nulls order by event_ts limit 1))[safe_offset(0)]
                                                                        as geo_city,
        (array_agg(geo_continent ignore nulls order by event_ts limit 1))[safe_offset(0)]
                                                                        as geo_continent,

        -- Engagement
        coalesce(max(session_engaged), 0) = 1                          as is_engaged,
        sum(coalesce(engagement_time_msec, 0))                         as total_engagement_msec,

        -- Funnel event counts within the session
        countif(is_page_view)                                          as page_view_count,
        countif(is_view_item)                                          as view_item_count,
        countif(is_add_to_cart)                                        as add_to_cart_count,
        countif(is_begin_checkout)                                     as begin_checkout_count,
        countif(is_purchase)                                           as purchase_count,

        -- Conversion outcome
        countif(is_purchase) > 0                                       as has_purchase,
        max(if(is_purchase, transaction_id, null))                     as transaction_id,
        coalesce(sum(if(is_purchase, purchase_revenue_usd, null)), 0)  as session_revenue_usd,

        -- Landing page: first page_location in the session
        (array_agg(page_location ignore nulls order by event_ts limit 1))[safe_offset(0)]
                                                                        as landing_page

    from events
    group by session_key, user_pseudo_id

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
        timestamp_diff(session_end_ts, session_start_ts, second)       as session_duration_seconds,

        -- Channel
        traffic_medium,
        traffic_source,
        traffic_campaign,

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

        -- Funnel activity
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

    from session_agg

)

select * from final
