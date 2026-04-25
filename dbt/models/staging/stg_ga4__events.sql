/*
  stg_ga4__events
  ───────────────
  Flattens GA4 date-sharded wildcard tables into a clean, typed staging view.
  One row per event. No business logic — extraction, casting, and renaming only.

  CTE structure:
    source    → raw read + _TABLE_SUFFIX date filter (cost control)
    extracted → unnest event_params, flatten RECORDs, cast types
    final     → add surrogate key, session_key, and funnel boolean flags
*/

{{ config(materialized='view') }}

with source as (

    select *
    from {{ source('ga4_raw', 'events') }}
    where _table_suffix between
        replace('{{ var("start_date") }}', '-', '')
        and
        replace('{{ var("end_date") }}', '-', '')

),

extracted as (

    select
        -- ── Timestamps & identity ─────────────────────────────────────────
        parse_date('%Y%m%d', event_date)                    as event_date,
        event_date                                          as event_date_str,
        event_timestamp,
        timestamp_micros(event_timestamp)                   as event_ts,
        event_name,
        user_pseudo_id,
        user_id,

        -- ── Session params ────────────────────────────────────────────────
        (select value.int_value
         from unnest(event_params) where key = 'ga_session_id')
                                                            as ga_session_id,

        (select value.int_value
         from unnest(event_params) where key = 'ga_session_number')
                                                            as ga_session_number,

        (select value.int_value
         from unnest(event_params) where key = 'session_engaged')
                                                            as session_engaged,

        (select value.int_value
         from unnest(event_params) where key = 'entrances')
                                                            as is_entrance,

        (select value.int_value
         from unnest(event_params) where key = 'engagement_time_msec')
                                                            as engagement_time_msec,

        -- ── Page params ───────────────────────────────────────────────────
        (select value.string_value
         from unnest(event_params) where key = 'page_location')
                                                            as page_location,

        (select value.string_value
         from unnest(event_params) where key = 'page_title')
                                                            as page_title,

        (select value.string_value
         from unnest(event_params) where key = 'page_referrer')
                                                            as page_referrer,

        -- ── Search ────────────────────────────────────────────────────────
        (select value.string_value
         from unnest(event_params) where key = 'search_term')
                                                            as search_term,

        -- ── Scroll ────────────────────────────────────────────────────────
        (select value.int_value
         from unnest(event_params) where key = 'percent_scrolled')
                                                            as percent_scrolled,

        -- ── Device ───────────────────────────────────────────────────────
        device.category                                     as device_category,
        device.operating_system                             as device_os,
        device.operating_system_version                     as device_os_version,
        device.web_info.browser                             as device_browser,
        device.web_info.browser_version                     as device_browser_version,
        device.language                                     as device_language,
        device.mobile_brand_name                            as device_mobile_brand,
        device.mobile_model_name                            as device_mobile_model,

        -- ── Geography ─────────────────────────────────────────────────────
        geo.country                                         as geo_country,
        geo.region                                          as geo_region,
        geo.city                                            as geo_city,
        geo.continent                                       as geo_continent,
        geo.sub_continent                                   as geo_sub_continent,

        -- ── Traffic source (first-touch, user-level) ─────────────────────
        -- Note: this is a user property set at first touch, not event-level.
        -- It does NOT change across events for the same user.
        traffic_source.medium                               as traffic_medium,
        traffic_source.source                               as traffic_source,
        traffic_source.name                                 as traffic_campaign,

        -- ── User lifetime value (accumulated by GA4) ─────────────────────
        user_ltv.revenue                                    as user_ltv_revenue,
        user_ltv.currency                                   as user_ltv_currency,
        timestamp_micros(
            coalesce(user_first_touch_timestamp, 0)
        )                                                   as user_first_touch_ts,

        -- ── Ecommerce — order level (non-null on purchase events only) ────
        ecommerce.transaction_id                            as transaction_id,
        ecommerce.purchase_revenue                          as purchase_revenue,
        ecommerce.purchase_revenue_in_usd                   as purchase_revenue_usd,
        ecommerce.refund_value                              as refund_value,
        ecommerce.shipping_value                            as shipping_value,
        ecommerce.tax_value                                 as tax_value,
        ecommerce.unique_items                              as ecommerce_unique_items,

        -- ── First item — quick lookups without UNNEST ─────────────────────
        items[safe_offset(0)].item_id                       as first_item_id,
        items[safe_offset(0)].item_name                     as first_item_name,
        items[safe_offset(0)].item_category                 as first_item_category,
        items[safe_offset(0)].price_in_usd                  as first_item_price_usd,
        items[safe_offset(0)].quantity                      as first_item_quantity,

        -- ── Pass-through for downstream unnesting in stg_ga4__event_items ─
        items,
        platform,
        stream_id

    from source

),

final as (

    select
        -- Surrogate key — uniquely identifies each event row.
        -- Note: GA4 can fire duplicate events; deduplication happens in int_sessions.
        {{ dbt_utils.generate_surrogate_key([
            'user_pseudo_id',
            'event_timestamp',
            'event_name'
        ]) }}                                               as event_key,

        -- Session key used for joins across all staging and intermediate models.
        concat(
            user_pseudo_id, '_',
            coalesce(cast(ga_session_id as string), 'unknown')
        )                                                   as session_key,

        -- All extracted columns
        event_date,
        event_date_str,
        event_timestamp,
        event_ts,
        event_name,
        user_pseudo_id,
        user_id,
        ga_session_id,
        ga_session_number,
        session_engaged,
        is_entrance,
        engagement_time_msec,
        page_location,
        page_title,
        page_referrer,
        search_term,
        percent_scrolled,
        device_category,
        device_os,
        device_os_version,
        device_browser,
        device_browser_version,
        device_language,
        device_mobile_brand,
        device_mobile_model,
        geo_country,
        geo_region,
        geo_city,
        geo_continent,
        geo_sub_continent,
        traffic_medium,
        traffic_source,
        traffic_campaign,
        user_ltv_revenue,
        user_ltv_currency,
        user_first_touch_ts,
        transaction_id,
        purchase_revenue,
        purchase_revenue_usd,
        refund_value,
        shipping_value,
        tax_value,
        ecommerce_unique_items,
        first_item_id,
        first_item_name,
        first_item_category,
        first_item_price_usd,
        first_item_quantity,
        items,
        platform,
        stream_id,

        -- ── Funnel stage boolean flags ─────────────────────────────────────
        -- Used extensively in intermediate + mart models for readability.
        (event_name = 'session_start')                      as is_session_start,
        (event_name = 'page_view')                          as is_page_view,
        (event_name = 'view_item')                          as is_view_item,
        (event_name = 'add_to_cart')                        as is_add_to_cart,
        (event_name = 'begin_checkout')                     as is_begin_checkout,
        (event_name = 'purchase')                           as is_purchase,
        (event_name = 'search')                             as is_search

    from extracted

)

select * from final
