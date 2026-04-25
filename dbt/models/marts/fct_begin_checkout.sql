/*
  fct_begin_checkout
  ──────────────────
  Begin-checkout fact. One row per begin_checkout event.
  Marks the entry point into the checkout flow.
  Used to measure checkout initiation rate and cart-to-checkout drop-off.
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
        geo_continent

    from {{ ref('stg_ga4__events') }}
    where is_begin_checkout = true

)

select * from events
