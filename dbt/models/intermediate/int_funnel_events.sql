/*
  int_funnel_events
  ─────────────────
  Event-grain view filtered to the five core purchase funnel stages.
  Adds funnel_stage (label) and funnel_stage_order (integer) for
  aggregation and ordering in mart_daily_funnel and ad-hoc funnel queries.

  Stages (in order):
    1  session_start   — browser opened a new session
    2  view_item       — user viewed a product detail page
    3  add_to_cart     — user added an item to their cart
    4  begin_checkout  — user initiated the checkout flow
    5  purchase        — transaction completed
*/

{{ config(materialized='view') }}

with events as (

    select * from {{ ref('stg_ga4__events') }}

),

funnel as (

    select
        event_key,
        event_date,
        event_ts,
        user_pseudo_id,
        session_key,

        -- Funnel stage label and sort order
        event_name                                                      as funnel_stage,
        case event_name
            when 'session_start'  then 1
            when 'view_item'      then 2
            when 'add_to_cart'    then 3
            when 'begin_checkout' then 4
            when 'purchase'       then 5
        end                                                             as funnel_stage_order,

        -- Ecommerce context (non-null on relevant stages only)
        transaction_id,
        purchase_revenue_usd,
        first_item_id,
        first_item_name,
        first_item_category,
        first_item_price_usd,

        -- Attribution context
        traffic_medium,
        traffic_source,
        device_category,
        geo_country

    from events
    where event_name in (
        'session_start',
        'view_item',
        'add_to_cart',
        'begin_checkout',
        'purchase'
    )

)

select * from funnel
