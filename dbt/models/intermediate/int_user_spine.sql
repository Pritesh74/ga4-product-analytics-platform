/*
  int_user_spine
  ──────────────
  User-grain view. One row per user_pseudo_id.
  Aggregates lifetime activity: first/last seen dates, first-touch channel,
  session counts, funnel activity totals, and purchase history.

  Channel note: traffic_source.medium in GA4 is a user-level property set at
  first touch. It does not change across events, so MAX() is a safe aggregation.
*/

{{ config(materialized='view') }}

with events as (

    select * from {{ ref('stg_ga4__events') }}

),

user_agg as (

    select
        user_pseudo_id,

        -- Activity window
        min(event_date)                                                 as first_seen_date,
        max(event_date)                                                 as last_seen_date,
        min(user_first_touch_ts)                                        as user_first_touch_ts,

        -- First-touch channel (user-level GA4 attribute, consistent per user)
        max(traffic_medium)                                             as traffic_medium,
        max(traffic_source)                                             as traffic_source,
        max(traffic_campaign)                                           as traffic_campaign,

        -- Device and geo at first event
        (array_agg(device_category ignore nulls order by event_ts limit 1))[safe_offset(0)]
                                                                        as first_device_category,
        (array_agg(geo_country     ignore nulls order by event_ts limit 1))[safe_offset(0)]
                                                                        as first_geo_country,

        -- Lifetime activity counts
        count(distinct session_key)                                     as total_sessions,
        countif(is_page_view)                                           as total_page_views,
        countif(is_view_item)                                           as total_view_items,
        countif(is_add_to_cart)                                         as total_add_to_cart,
        countif(is_begin_checkout)                                      as total_begin_checkout,
        countif(is_purchase)                                            as total_purchase_events,

        -- Purchase outcomes
        -- total_orders excludes the ~23 GA4 sample events with null transaction_id
        count(distinct if(is_purchase and transaction_id is not null,
                          transaction_id, null))                        as total_orders,
        sum(if(is_purchase, coalesce(purchase_revenue_usd, 0), 0))     as total_revenue_usd,
        min(if(is_purchase, event_date, null))                          as first_purchase_date,
        max(if(is_purchase, event_date, null))                          as last_purchase_date

    from events
    group by user_pseudo_id

),

final as (

    select
        user_pseudo_id,
        first_seen_date,
        last_seen_date,
        user_first_touch_ts,
        date_diff(last_seen_date, first_seen_date, day)                 as user_lifespan_days,

        -- Acquisition channel
        traffic_medium,
        traffic_source,
        traffic_campaign,

        -- Device and geography at first touch
        first_device_category,
        first_geo_country,

        -- Lifetime activity
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

        -- Purchaser flag
        total_orders > 0                                                as is_purchaser

    from user_agg

)

select * from final
