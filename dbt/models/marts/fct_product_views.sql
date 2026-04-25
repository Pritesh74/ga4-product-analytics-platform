/*
  fct_product_views
  ─────────────────
  Product view fact. One row per view_item event.
  Item details sourced from items[SAFE_OFFSET(0)] in stg_ga4__events
  (view_item events carry exactly one item in the GA4 data model).
*/

{{ config(materialized='table') }}

with events as (

    select
        event_key,
        event_date,
        event_ts,
        user_pseudo_id,
        session_key,
        traffic_medium,
        traffic_source,
        traffic_campaign,
        device_category,
        geo_country,
        geo_continent,
        first_item_id                                                   as item_id,
        first_item_name                                                 as item_name,
        first_item_category                                             as item_category,
        first_item_price_usd                                            as item_price_usd,
        page_location,
        page_title

    from {{ ref('stg_ga4__events') }}
    where is_view_item = true

)

select * from events
