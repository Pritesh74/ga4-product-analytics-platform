/*
  mart_daily_funnel
  ─────────────────
  Daily funnel aggregation. One row per (event_date, funnel_stage).

  Shows unique users and sessions at each of the five funnel stages per day.
  Drop-off rate between stages is computed in the consuming layer (e.g. Streamlit)
  as: 1 - (stage_n_users / stage_n-1_users).

  Grain: event_date × funnel_stage (5 rows per day)
*/

{{ config(materialized='table') }}

with funnel_events as (

    select * from {{ ref('int_funnel_events') }}

),

final as (

    select
        event_date,
        funnel_stage,
        funnel_stage_order,
        count(distinct user_pseudo_id)                                  as unique_users,
        count(distinct session_key)                                     as unique_sessions,
        count(*)                                                        as total_events

    from funnel_events
    group by
        event_date,
        funnel_stage,
        funnel_stage_order

)

select * from final
