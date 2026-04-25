/*
  fct_purchases
  ─────────────
  Purchase fact table. One row per purchase event.
  Filtered from stg_ga4__events where is_purchase = true.

  Note: ~23 rows have null transaction_id — a known GA4 sample data quality gap
  (documented and warn-tested in assert_purchase_has_transaction_id).
  These rows are included here; downstream models that join on transaction_id
  will naturally exclude them.
*/

{{ config(materialized='table') }}

with events as (

    select
        event_key,
        event_date,
        event_ts,
        user_pseudo_id,
        session_key,
        transaction_id,
        coalesce(purchase_revenue_usd, 0)                               as purchase_revenue_usd,
        ecommerce_unique_items,
        coalesce(shipping_value, 0)                                     as shipping_value,
        coalesce(tax_value, 0)                                          as tax_value,
        traffic_medium,
        traffic_source,
        traffic_campaign,
        device_category,
        geo_country,
        geo_continent

    from {{ ref('stg_ga4__events') }}
    where is_purchase = true

)

select * from events
