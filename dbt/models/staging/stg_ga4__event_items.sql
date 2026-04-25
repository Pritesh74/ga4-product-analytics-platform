/*
  stg_ga4__event_items
  ────────────────────
  One row per item per event — UNNESTs the items ARRAY from the raw source.
  Reads directly from source (not from stg_ga4__events) to keep the two
  views independent and avoid compounding BigQuery scan costs.

  Filtered to ecommerce event types only: events without items are excluded
  upfront to minimize bytes scanned.

  Downstream use: fct_product_views, fct_add_to_cart, fct_purchases,
                  mart_ltv_by_channel (item-level revenue).
*/

{{ config(materialized='view') }}

with source as (

    select
        event_date,
        event_timestamp,
        timestamp_micros(event_timestamp)                   as event_ts,
        event_name,
        user_pseudo_id,

        (select value.int_value
         from unnest(event_params) where key = 'ga_session_id')
                                                            as ga_session_id,

        ecommerce.transaction_id                            as transaction_id,

        item

    from {{ source('ga4_raw', 'events') }},
    unnest(items) as item

    where _table_suffix between
        replace('{{ var("start_date") }}', '-', '')
        and
        replace('{{ var("end_date") }}', '-', '')

      -- Only events that can have items — filters upfront to save scan cost
      and event_name in (
          'view_item',
          'view_item_list',
          'select_item',
          'add_to_cart',
          'remove_from_cart',
          'view_cart',
          'begin_checkout',
          'add_shipping_info',
          'add_payment_info',
          'purchase',
          'refund'
      )

),

final as (

    select
        -- ── Event identity ────────────────────────────────────────────────
        parse_date('%Y%m%d', event_date)                    as event_date,
        event_ts,
        event_name,
        user_pseudo_id,
        ga_session_id,

        concat(
            user_pseudo_id, '_',
            coalesce(cast(ga_session_id as string), 'unknown')
        )                                                   as session_key,

        transaction_id,

        -- Surrogate key: one row = one item within one event for one user.
        {{ dbt_utils.generate_surrogate_key([
            'user_pseudo_id',
            'event_timestamp',
            'event_name',
            'item.item_id'
        ]) }}                                               as item_event_key,

        -- ── Item fields ───────────────────────────────────────────────────
        item.item_id,
        item.item_name,
        item.item_brand,
        item.item_variant,
        item.item_category,
        item.item_category2,
        item.item_category3,
        item.price_in_usd                                   as item_price_usd,
        item.quantity,
        item.item_revenue_in_usd                            as item_revenue_usd,
        item.coupon                                         as item_coupon,
        item.affiliation,
        item.item_list_id,
        item.item_list_name,
        item.item_list_index,
        item.promotion_id,
        item.promotion_name,
        item.creative_name,
        item.creative_slot

    from source

)

select * from final
