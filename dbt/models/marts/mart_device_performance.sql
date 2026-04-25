/*
  mart_device_performance
  ───────────────────────
  Session-level performance metrics aggregated by device.
  One row per (session_date, device_category, device_os, device_browser).

  Key questions answered:
  - Do mobile users convert at the same rate as desktop?
  - Which browsers drive the highest revenue per session?
  - Is engagement rate consistent across device types?
*/

{{ config(materialized='table') }}

with sessions as (

    select * from {{ ref('fct_sessions') }}

),

final as (

    select
        session_date,
        device_category,
        device_os,
        device_browser,

        count(distinct session_key)                                     as total_sessions,
        count(distinct user_pseudo_id)                                  as unique_users,

        -- Engagement
        countif(is_engaged)                                             as engaged_sessions,
        safe_divide(
            countif(is_engaged),
            count(distinct session_key)
        )                                                               as engagement_rate,

        -- Funnel depth
        sum(page_view_count)                                            as total_page_views,
        sum(view_item_count)                                            as total_view_items,
        sum(add_to_cart_count)                                          as total_add_to_cart,
        sum(begin_checkout_count)                                       as total_begin_checkout,

        -- Conversion
        countif(has_purchase)                                           as converting_sessions,
        safe_divide(
            countif(has_purchase),
            count(distinct session_key)
        )                                                               as session_conversion_rate,

        -- Revenue
        sum(session_revenue_usd)                                        as total_revenue_usd,
        safe_divide(
            sum(session_revenue_usd),
            count(distinct session_key)
        )                                                               as revenue_per_session

    from sessions
    group by
        session_date,
        device_category,
        device_os,
        device_browser

)

select * from final
