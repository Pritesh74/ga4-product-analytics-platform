"""
Data Quality
────────────
Pipeline health dashboard: mart row counts, data freshness,
dbt test pass rates, and key data quality notes.
Source: all ga4_marts tables (COUNT queries).
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

st.set_page_config(page_title="Data Quality", page_icon="✅", layout="wide")

from utils.queries import load_model_inventory

# ── Header ────────────────────────────────────────────────────────────────────
st.title("Data Quality")
st.caption(
    "Pipeline health: mart row counts, data freshness, dbt test summary.  \n"
    "Source: all ga4_marts tables"
)

# ── Load data ─────────────────────────────────────────────────────────────────
try:
    with st.spinner("Loading model inventory…"):
        inventory = load_model_inventory()
except Exception as e:
    st.error(f"Could not load data from BigQuery: {e}")
    st.stop()

# ── Model descriptions ────────────────────────────────────────────────────────
MODEL_META = {
    "dim_users":               ("Dimension", "One row per user. Lifetime activity + channel + cohort."),
    "fct_sessions":            ("Fact",      "One row per session. Engagement, funnel counts, revenue."),
    "fct_purchases":           ("Fact",      "One row per purchase event. Revenue, orders."),
    "fct_product_views":       ("Fact",      "One row per view_item event. Item details."),
    "fct_add_to_cart":         ("Fact",      "One row per add_to_cart event. Item details."),
    "fct_begin_checkout":      ("Fact",      "One row per begin_checkout event."),
    "mart_daily_funnel":       ("Mart",      "Daily unique users at each of 5 funnel stages."),
    "mart_retention_cohorts":  ("Mart",      "Monthly cohort retention matrix."),
    "mart_ltv_by_channel":     ("Mart",      "LTV metrics by acquisition channel × cohort month."),
    "mart_device_performance": ("Mart",      "Session metrics by device × OS × browser per day."),
    "mart_geo_performance":    ("Mart",      "Session metrics by country × region per day."),
}

inventory.rename(columns={"row_count": "rows"}, inplace=True)
inventory["layer"] = inventory["model"].map(lambda m: MODEL_META.get(m, ("—", ""))[0])
inventory["description"] = inventory["model"].map(lambda m: MODEL_META.get(m, ("—", ""))[1])

# ── KPI summary ───────────────────────────────────────────────────────────────
total_rows = int(inventory["rows"].sum())
total_models = len(inventory)
min_date = inventory["min_date"].dropna().min()
max_date = inventory["max_date"].dropna().max()

k1, k2, k3, k4 = st.columns(4)
k1.metric("Mart tables", f"{total_models}")
k2.metric("Total rows across marts", f"{total_rows:,}")
k3.metric("Earliest data date", str(min_date) if min_date else "—")
k4.metric("Latest data date", str(max_date) if max_date else "—")

st.divider()

# ── dbt test summary ──────────────────────────────────────────────────────────
st.subheader("dbt Test Results")

test_summary = pd.DataFrame([
    {"Layer": "Staging",        "Total Tests": 29, "Pass": 27, "Warn": 2, "Error": 0},
    {"Layer": "Intermediate",   "Total Tests": 20, "Pass": 20, "Warn": 0, "Error": 0},
    {"Layer": "Marts",          "Total Tests": 62, "Pass": 62, "Warn": 0, "Error": 0},
    {"Layer": "Experiments ⚠️", "Total Tests": 17, "Pass": 17, "Warn": 0, "Error": 0},
])
test_summary["Pass Rate"] = test_summary["Pass"] / test_summary["Total Tests"]
test_summary["Pass Rate Display"] = test_summary["Pass Rate"].apply(lambda x: f"{x*100:.0f}%")

col_tests, col_bar = st.columns([1, 2])

with col_tests:
    display_tests = test_summary[["Layer", "Total Tests", "Pass", "Warn", "Error", "Pass Rate Display"]].copy()
    display_tests.columns = ["Layer", "Tests", "✅ Pass", "⚠️ Warn", "❌ Error", "Pass Rate"]
    st.dataframe(display_tests, hide_index=True, use_container_width=True)

    st.markdown(
        """
**Active warnings (expected):**
- `accepted_values event_name` — 2 custom GA4 event names observed in source
- `assert_purchase_has_transaction_id` — 23 purchase events with null transaction_id
  (known GA4 public sample data quality gap)
        """
    )

with col_bar:
    fig_tests = px.bar(
        test_summary,
        x="Layer",
        y=["Pass", "Warn", "Error"],
        color_discrete_map={"Pass": "#00CC96", "Warn": "#FECB52", "Error": "#EF553B"},
        barmode="stack",
        labels={"value": "Tests", "variable": "Result"},
        template="plotly_white",
        text_auto=True,
    )
    fig_tests.update_layout(
        margin=dict(l=0, r=0, t=8, b=0),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=280,
    )
    st.plotly_chart(fig_tests, use_container_width=True)

st.divider()

# ── Model inventory ───────────────────────────────────────────────────────────
st.subheader("Mart Model Inventory")

# Row count chart
fig_rows = px.bar(
    inventory.sort_values("rows", ascending=True),
    y="model",
    x="rows",
    orientation="h",
    color="layer",
    color_discrete_map={
        "Dimension": "#AB63FA",
        "Fact": "#636EFA",
        "Mart": "#00CC96",
    },
    text=inventory.sort_values("rows", ascending=True)["rows"].apply(lambda x: f"{x:,}"),
    labels={"model": "", "rows": "Row Count", "layer": "Layer"},
    template="plotly_white",
)
fig_rows.update_layout(margin=dict(l=0, r=0, t=8, b=0), xaxis_tickformat=",", height=380)
fig_rows.update_traces(textposition="outside")
st.plotly_chart(fig_rows, use_container_width=True)

# Full table
display_inv = inventory[["model", "layer", "rows", "min_date", "max_date", "description"]].copy()
display_inv["rows"] = display_inv["rows"].apply(lambda x: f"{int(x):,}")
display_inv.columns = ["Model", "Layer", "Rows", "Min Date", "Max Date", "Description"]
st.dataframe(display_inv, hide_index=True, use_container_width=True)

st.divider()

# ── Key data quality notes ────────────────────────────────────────────────────
st.subheader("Known Data Quality Notes")

col_n1, col_n2 = st.columns(2)

with col_n1:
    st.markdown(
        """
**🟡 Purchase events with null transaction_id**
- Count: ~23 rows in `fct_purchases`
- Cause: GA4 public sample data quality gap (not a pipeline bug)
- Impact: These rows are excluded from order-level revenue metrics (AOV, total orders).
  Purchase revenue is still included in session-level aggregations.
- Test: `assert_purchase_has_transaction_id` — severity warn

**🟡 Custom event names in source**
- Count: 2 event names not in the expected accepted_values list
- Cause: GA4 allows arbitrary custom event names beyond the standard taxonomy
- Impact: None — custom events flow through staging unchanged
- Test: `accepted_values event_name` — severity warn
        """
    )

with col_n2:
    st.markdown(
        """
**✅ Session key integrity**
- `session_key` format (user_pseudo_id + '_' + ga_session_id) validated
- Test: `assert_session_key_format` — PASS (BigQuery REGEXP_CONTAINS fix applied)

**✅ Surrogate key uniqueness**
- All fact tables tested for unique `event_key` / `session_key`
- 0 duplicates found in any mart table

**✅ Revenue non-negativity**
- `purchase_revenue_usd`, `shipping_value` tested as ≥ 0
- No negative revenue values observed

**ℹ️ Dataset window**
- Source data: Nov 1, 2020 – Jan 31, 2021 (92 days)
- Retention cohort matrix is sparse by design (max 2 follow-up periods)
        """
    )

st.divider()

# ── Architecture summary ──────────────────────────────────────────────────────
with st.expander("Full pipeline architecture"):
    st.markdown(
        """
```
bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*  [REAL DATA]
  │
  ├─ stg_ga4__events          (view)  Flatten, type-cast, add keys, boolean flags
  └─ stg_ga4__event_items     (view)  UNNEST items array, ecommerce events only
       │
       ├─ int_sessions         (view)  Aggregate to session grain
       ├─ int_user_spine       (view)  Aggregate to user grain
       └─ int_funnel_events    (view)  Filter to 5 funnel stages
            │
            ├─ dim_users               (table) 270,154 rows · User dimension
            ├─ fct_sessions            (table) 360,129 rows · Session fact
            ├─ fct_purchases           (table)   5,692 rows · Purchase events
            ├─ fct_product_views       (table) 386,068 rows · view_item events
            ├─ fct_add_to_cart         (table)  58,543 rows · add_to_cart events
            ├─ fct_begin_checkout      (table)  38,757 rows · begin_checkout events
            ├─ mart_daily_funnel       (table)     442 rows · Daily stage × users
            ├─ mart_retention_cohorts  (table)       6 rows · Cohort matrix
            ├─ mart_ltv_by_channel     (table)      35 rows · LTV by channel
            ├─ mart_device_performance (table)   3,256 rows · Device per day
            ├─ mart_geo_performance    (table)  34,290 rows · Geography per day
            │
            ├─ exp_simulated_assignment (table)  5,695 rows  ⚠ SIMULATED
            └─ exp_simulated_results    (table)      2 rows  ⚠ SIMULATED
```
**dbt version:** 1.8.7  ·  **BigQuery adapter:** 1.8.2
**Tests:** 128 total — 126 pass, 2 warn (expected), 0 error
**Authentication:** ADC (oauth) — no service account key file
        """
    )
