/*
  mart_geo_performance
  ────────────────────
  Session-level performance metrics aggregated by geography.
  One row per (session_date, geo_continent, geo_country, geo_region).

  Key questions answered:
  - Which countries drive the most revenue?
  - Where are session conversion rates lowest (targeting opportunities)?
  - How does engagement vary by continent?
*/

{{ config(materialized='table') }}

with sessions as (

    select * from {{ ref('fct_sessions') }}

),

final as (

    select
        session_date,
        geo_continent,
        geo_country,
        geo_region,

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
        geo_continent,
        geo_country,
        geo_region

)

select * from final
