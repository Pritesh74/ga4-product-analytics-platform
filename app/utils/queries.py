"""
All BigQuery query functions for the Streamlit app.
Each function is cached for 1 hour via @st.cache_data.
All queries read exclusively from ga4_marts tables — no raw event logic here.
"""

import streamlit as st
import pandas as pd
from utils.bq_client import run_query, marts_table, experiments_table


# ── Executive Overview ─────────────────────────────────────────────────────

@st.cache_data(ttl=3600, show_spinner=False)
def load_session_kpis() -> pd.DataFrame:
    sql = f"""
    SELECT
        COUNT(DISTINCT session_key)                             AS total_sessions,
        COUNT(DISTINCT user_pseudo_id)                         AS unique_users,
        COUNTIF(has_purchase)                                  AS converting_sessions,
        SAFE_DIVIDE(COUNTIF(has_purchase),
                    COUNT(DISTINCT session_key))                AS session_conversion_rate,
        SUM(session_revenue_usd)                               AS total_revenue_usd
    FROM {marts_table('fct_sessions')}
    """
    return run_query(sql)


@st.cache_data(ttl=3600, show_spinner=False)
def load_purchase_kpis() -> pd.DataFrame:
    sql = f"""
    SELECT
        COUNT(*)                                               AS total_purchase_events,
        COUNT(DISTINCT transaction_id)                         AS total_orders,
        SUM(purchase_revenue_usd)                              AS gross_revenue_usd,
        SAFE_DIVIDE(SUM(purchase_revenue_usd),
                    COUNT(DISTINCT transaction_id))             AS aov_usd
    FROM {marts_table('fct_purchases')}
    WHERE transaction_id IS NOT NULL
    """
    return run_query(sql)


@st.cache_data(ttl=3600, show_spinner=False)
def load_daily_revenue() -> pd.DataFrame:
    sql = f"""
    SELECT
        event_date,
        SUM(purchase_revenue_usd)   AS revenue_usd,
        COUNT(DISTINCT transaction_id) AS orders
    FROM {marts_table('fct_purchases')}
    WHERE transaction_id IS NOT NULL
    GROUP BY event_date
    ORDER BY event_date
    """
    return run_query(sql)


@st.cache_data(ttl=3600, show_spinner=False)
def load_daily_sessions() -> pd.DataFrame:
    sql = f"""
    SELECT
        session_date                                    AS event_date,
        COUNT(DISTINCT session_key)                     AS sessions,
        COUNT(DISTINCT user_pseudo_id)                  AS unique_users,
        COUNTIF(has_purchase)                           AS converting_sessions,
        SAFE_DIVIDE(COUNTIF(has_purchase),
                    COUNT(DISTINCT session_key))         AS conversion_rate
    FROM {marts_table('fct_sessions')}
    GROUP BY session_date
    ORDER BY session_date
    """
    return run_query(sql)


@st.cache_data(ttl=3600, show_spinner=False)
def load_channel_ltv_summary() -> pd.DataFrame:
    sql = f"""
    SELECT
        channel_group,
        SUM(total_users)                                                AS total_users,
        SUM(purchasing_users)                                           AS purchasing_users,
        SAFE_DIVIDE(SUM(purchasing_users), NULLIF(SUM(total_users), 0)) AS purchase_rate,
        SUM(total_revenue_usd)                                          AS total_revenue_usd,
        SAFE_DIVIDE(SUM(total_revenue_usd), NULLIF(SUM(total_users), 0))
                                                                        AS avg_revenue_per_user
    FROM {marts_table('mart_ltv_by_channel')}
    WHERE channel_group IS NOT NULL
    GROUP BY channel_group
    ORDER BY total_revenue_usd DESC
    """
    return run_query(sql)


@st.cache_data(ttl=3600, show_spinner=False)
def load_top_categories() -> pd.DataFrame:
    sql = f"""
    SELECT
        COALESCE(item_category, '(not set)') AS item_category,
        COUNT(*)                             AS view_count,
        COUNT(DISTINCT user_pseudo_id)       AS unique_viewers
    FROM {marts_table('fct_product_views')}
    GROUP BY item_category
    ORDER BY view_count DESC
    LIMIT 10
    """
    return run_query(sql)


# ── Funnel ─────────────────────────────────────────────────────────────────

@st.cache_data(ttl=3600, show_spinner=False)
def load_period_funnel() -> pd.DataFrame:
    """Period-level unique users at each funnel stage (not summed daily)."""
    sql = f"""
    SELECT 1 AS stage_order, 'Session Start'   AS stage, COUNT(DISTINCT user_pseudo_id) AS users FROM {marts_table('fct_sessions')}
    UNION ALL
    SELECT 2, 'View Item',      COUNT(DISTINCT user_pseudo_id) FROM {marts_table('fct_product_views')}
    UNION ALL
    SELECT 3, 'Add to Cart',    COUNT(DISTINCT user_pseudo_id) FROM {marts_table('fct_add_to_cart')}
    UNION ALL
    SELECT 4, 'Begin Checkout', COUNT(DISTINCT user_pseudo_id) FROM {marts_table('fct_begin_checkout')}
    UNION ALL
    SELECT 5, 'Purchase',       COUNT(DISTINCT user_pseudo_id) FROM {marts_table('fct_purchases')}
    ORDER BY stage_order
    """
    return run_query(sql)


@st.cache_data(ttl=3600, show_spinner=False)
def load_daily_funnel() -> pd.DataFrame:
    sql = f"""
    SELECT
        event_date,
        funnel_stage,
        funnel_stage_order,
        unique_users,
        unique_sessions
    FROM {marts_table('mart_daily_funnel')}
    ORDER BY event_date, funnel_stage_order
    """
    return run_query(sql)


# ── Retention ─────────────────────────────────────────────────────────────

@st.cache_data(ttl=3600, show_spinner=False)
def load_retention_cohorts() -> pd.DataFrame:
    sql = f"""
    SELECT
        cohort_month,
        months_since_acquisition,
        cohort_size,
        retained_users,
        retention_rate
    FROM {marts_table('mart_retention_cohorts')}
    ORDER BY cohort_month, months_since_acquisition
    """
    return run_query(sql)


# ── LTV ───────────────────────────────────────────────────────────────────

@st.cache_data(ttl=3600, show_spinner=False)
def load_ltv_by_channel() -> pd.DataFrame:
    sql = f"""
    SELECT
        channel_group,
        traffic_medium,
        SUM(total_users)                                                         AS total_users,
        SUM(purchasing_users)                                                    AS purchasing_users,
        SAFE_DIVIDE(SUM(purchasing_users), NULLIF(SUM(total_users), 0))          AS purchase_rate,
        SUM(total_revenue_usd)                                                   AS total_revenue_usd,
        SAFE_DIVIDE(SUM(total_revenue_usd), NULLIF(SUM(total_users), 0))         AS avg_revenue_per_user,
        SAFE_DIVIDE(SUM(total_revenue_usd), NULLIF(SUM(purchasing_users), 0))    AS avg_revenue_per_purchaser,
        SAFE_DIVIDE(SUM(total_orders), NULLIF(SUM(purchasing_users), 0))         AS avg_orders_per_purchaser
    FROM {marts_table('mart_ltv_by_channel')}
    WHERE channel_group IS NOT NULL
    GROUP BY channel_group, traffic_medium
    ORDER BY total_revenue_usd DESC
    """
    return run_query(sql)


# ── Channel & Device ──────────────────────────────────────────────────────

@st.cache_data(ttl=3600, show_spinner=False)
def load_channel_performance() -> pd.DataFrame:
    sql = f"""
    SELECT
        channel_group,
        COUNT(DISTINCT session_key)                                      AS sessions,
        COUNT(DISTINCT user_pseudo_id)                                   AS unique_users,
        COUNTIF(is_engaged)                                              AS engaged_sessions,
        SAFE_DIVIDE(COUNTIF(is_engaged), COUNT(DISTINCT session_key))    AS engagement_rate,
        COUNTIF(has_purchase)                                            AS converting_sessions,
        SAFE_DIVIDE(COUNTIF(has_purchase), COUNT(DISTINCT session_key))  AS conversion_rate,
        SUM(session_revenue_usd)                                         AS total_revenue_usd,
        SAFE_DIVIDE(SUM(session_revenue_usd),
                    COUNT(DISTINCT session_key))                          AS revenue_per_session
    FROM {marts_table('fct_sessions')}
    WHERE channel_group IS NOT NULL
    GROUP BY channel_group
    ORDER BY sessions DESC
    """
    return run_query(sql)


@st.cache_data(ttl=3600, show_spinner=False)
def load_device_performance() -> pd.DataFrame:
    sql = f"""
    SELECT
        device_category,
        SUM(total_sessions)                                                        AS sessions,
        SUM(unique_users)                                                          AS unique_users,
        SAFE_DIVIDE(SUM(engaged_sessions), NULLIF(SUM(total_sessions), 0))         AS engagement_rate,
        SUM(total_add_to_cart)                                                     AS add_to_cart,
        SUM(total_begin_checkout)                                                  AS begin_checkout,
        SUM(converting_sessions)                                                   AS converting_sessions,
        SAFE_DIVIDE(SUM(converting_sessions), NULLIF(SUM(total_sessions), 0))      AS conversion_rate,
        SUM(total_revenue_usd)                                                     AS total_revenue_usd,
        SAFE_DIVIDE(SUM(total_revenue_usd), NULLIF(SUM(total_sessions), 0))        AS revenue_per_session
    FROM {marts_table('mart_device_performance')}
    WHERE device_category IS NOT NULL
    GROUP BY device_category
    ORDER BY sessions DESC
    """
    return run_query(sql)


@st.cache_data(ttl=3600, show_spinner=False)
def load_browser_performance() -> pd.DataFrame:
    sql = f"""
    SELECT
        device_browser,
        SUM(total_sessions)                                                        AS sessions,
        SAFE_DIVIDE(SUM(converting_sessions), NULLIF(SUM(total_sessions), 0))      AS conversion_rate,
        SUM(total_revenue_usd)                                                     AS total_revenue_usd,
        SAFE_DIVIDE(SUM(total_revenue_usd), NULLIF(SUM(total_sessions), 0))        AS revenue_per_session
    FROM {marts_table('mart_device_performance')}
    WHERE device_browser IS NOT NULL
    GROUP BY device_browser
    ORDER BY sessions DESC
    LIMIT 15
    """
    return run_query(sql)


# ── Geography ─────────────────────────────────────────────────────────────

@st.cache_data(ttl=3600, show_spinner=False)
def load_country_performance() -> pd.DataFrame:
    sql = f"""
    SELECT
        geo_country,
        geo_continent,
        SUM(total_sessions)                                                        AS sessions,
        SUM(unique_users)                                                          AS unique_users,
        SAFE_DIVIDE(SUM(engaged_sessions), NULLIF(SUM(total_sessions), 0))         AS engagement_rate,
        SUM(converting_sessions)                                                   AS converting_sessions,
        SAFE_DIVIDE(SUM(converting_sessions), NULLIF(SUM(total_sessions), 0))      AS conversion_rate,
        SUM(total_revenue_usd)                                                     AS revenue_usd,
        SAFE_DIVIDE(SUM(total_revenue_usd), NULLIF(SUM(total_sessions), 0))        AS revenue_per_session
    FROM {marts_table('mart_geo_performance')}
    WHERE geo_country IS NOT NULL
      AND geo_country != '(not set)'
    GROUP BY geo_country, geo_continent
    ORDER BY revenue_usd DESC
    """
    return run_query(sql)


# ── Data Quality ──────────────────────────────────────────────────────────

@st.cache_data(ttl=3600, show_spinner=False)
def load_model_inventory() -> pd.DataFrame:
    """Row counts and date ranges for all mart tables."""
    # CAST(NULL AS STRING) required — untyped NULL in UNION ALL is rejected by BigQuery
    sql = f"""
    SELECT 'dim_users'               AS model, COUNT(*) AS row_count, CAST(NULL AS STRING) AS min_date, CAST(NULL AS STRING) AS max_date FROM {marts_table('dim_users')}
    UNION ALL SELECT 'fct_sessions',           COUNT(*), CAST(MIN(session_date) AS STRING),  CAST(MAX(session_date) AS STRING)  FROM {marts_table('fct_sessions')}
    UNION ALL SELECT 'fct_purchases',          COUNT(*), CAST(MIN(event_date) AS STRING),    CAST(MAX(event_date) AS STRING)    FROM {marts_table('fct_purchases')}
    UNION ALL SELECT 'fct_product_views',      COUNT(*), CAST(MIN(event_date) AS STRING),    CAST(MAX(event_date) AS STRING)    FROM {marts_table('fct_product_views')}
    UNION ALL SELECT 'fct_add_to_cart',        COUNT(*), CAST(MIN(event_date) AS STRING),    CAST(MAX(event_date) AS STRING)    FROM {marts_table('fct_add_to_cart')}
    UNION ALL SELECT 'fct_begin_checkout',     COUNT(*), CAST(MIN(event_date) AS STRING),    CAST(MAX(event_date) AS STRING)    FROM {marts_table('fct_begin_checkout')}
    UNION ALL SELECT 'mart_daily_funnel',      COUNT(*), CAST(MIN(event_date) AS STRING),    CAST(MAX(event_date) AS STRING)    FROM {marts_table('mart_daily_funnel')}
    UNION ALL SELECT 'mart_retention_cohorts', COUNT(*), CAST(NULL AS STRING),               CAST(NULL AS STRING)               FROM {marts_table('mart_retention_cohorts')}
    UNION ALL SELECT 'mart_ltv_by_channel',    COUNT(*), CAST(NULL AS STRING),               CAST(NULL AS STRING)               FROM {marts_table('mart_ltv_by_channel')}
    UNION ALL SELECT 'mart_device_performance',COUNT(*), CAST(MIN(session_date) AS STRING),  CAST(MAX(session_date) AS STRING)  FROM {marts_table('mart_device_performance')}
    UNION ALL SELECT 'mart_geo_performance',   COUNT(*), CAST(MIN(session_date) AS STRING),  CAST(MAX(session_date) AS STRING)  FROM {marts_table('mart_geo_performance')}
    ORDER BY model
    """
    return run_query(sql)


# ── Experimentation ───────────────────────────────────────────────────────

@st.cache_data(ttl=3600, show_spinner=False)
def load_experiment_results() -> pd.DataFrame:
    """Per-variant summary from exp_simulated_results."""
    sql = f"""
    SELECT
        experiment_id,
        experiment_name,
        variant_id,
        variant_name,
        experiment_start_date,
        experiment_end_date,
        is_simulated,
        n_users,
        n_conversions,
        conversion_rate,
        total_revenue_usd,
        revenue_per_user,
        revenue_per_converter,
        stddev_revenue_per_user,
        total_orders,
        avg_orders_per_converter,
        avg_checkouts_per_user,
        engagement_rate
    FROM {experiments_table('exp_simulated_results')}
    ORDER BY variant_id
    """
    return run_query(sql)


@st.cache_data(ttl=3600, show_spinner=False)
def load_experiment_baseline() -> pd.DataFrame:
    """Pre-experiment (November 2020) checkout→purchase conversion rate."""
    sql = f"""
    SELECT
        COUNT(DISTINCT s.user_pseudo_id)                                          AS checkout_users,
        COUNT(DISTINCT IF(s.has_purchase, s.user_pseudo_id, NULL))                AS converting_users,
        SAFE_DIVIDE(
            COUNT(DISTINCT IF(s.has_purchase, s.user_pseudo_id, NULL)),
            COUNT(DISTINCT s.user_pseudo_id)
        )                                                                         AS baseline_conversion_rate
    FROM {marts_table('fct_sessions')} s
    WHERE s.session_date BETWEEN DATE '2020-11-01' AND DATE '2020-11-30'
      AND s.begin_checkout_count > 0
    """
    return run_query(sql)


@st.cache_data(ttl=3600, show_spinner=False)
def load_experiment_daily() -> pd.DataFrame:
    """Daily cumulative conversion rate per variant for a running-rate chart."""
    sql = f"""
    WITH daily_outcomes AS (
        SELECT
            a.variant_name,
            p.event_date,
            COUNT(DISTINCT a.user_pseudo_id)                AS daily_eligible,
            COUNT(DISTINCT p.transaction_id)                AS daily_conversions
        FROM {experiments_table('exp_simulated_assignment')} a
        LEFT JOIN {marts_table('fct_purchases')} p
            ON  a.user_pseudo_id = p.user_pseudo_id
            AND p.event_date BETWEEN a.experiment_start_date AND a.experiment_end_date
            AND p.transaction_id IS NOT NULL
        GROUP BY a.variant_name, p.event_date
    )
    SELECT
        variant_name,
        event_date,
        SUM(daily_conversions) OVER (PARTITION BY variant_name ORDER BY event_date) AS cumulative_conversions,
        SUM(daily_eligible)    OVER (PARTITION BY variant_name ORDER BY event_date) AS cumulative_eligible
    FROM daily_outcomes
    WHERE event_date IS NOT NULL
    ORDER BY variant_name, event_date
    """
    return run_query(sql)
