"""
Executive Overview
──────────────────
Top-line KPIs, daily revenue trend, and channel mix for the Google
Merchandise Store. All data from ga4_marts fact tables.
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

st.set_page_config(page_title="Executive Overview", page_icon="📊", layout="wide")

from utils.queries import (
    load_session_kpis,
    load_purchase_kpis,
    load_daily_revenue,
    load_daily_sessions,
    load_channel_ltv_summary,
    load_top_categories,
)

# ── Helpers ──────────────────────────────────────────────────────────────────

COLORS = {
    "revenue": "#00CC96",
    "sessions": "#636EFA",
    "conversion": "#EF553B",
    "orders": "#AB63FA",
    "neutral": "#FECB52",
}

def fmt_currency(v):
    if v >= 1_000_000:
        return f"${v/1_000_000:.2f}M"
    if v >= 1_000:
        return f"${v/1_000:.1f}K"
    return f"${v:.2f}"

def fmt_pct(v):
    return f"{v*100:.1f}%"

def fmt_int(v):
    return f"{int(v):,}"

# ── Header ───────────────────────────────────────────────────────────────────
st.title("Executive Overview")
st.caption(
    "Google Merchandise Store · Nov 2020 – Jan 2021 · "
    "Source: ga4_marts.fct_sessions, fct_purchases, mart_ltv_by_channel"
)

# ── Load data ────────────────────────────────────────────────────────────────
try:
    with st.spinner("Loading…"):
        s_kpis = load_session_kpis().iloc[0]
        p_kpis = load_purchase_kpis().iloc[0]
        daily_rev = load_daily_revenue()
        daily_sess = load_daily_sessions()
        channel_ltv = load_channel_ltv_summary()
        top_cats = load_top_categories()
except Exception as e:
    st.error(f"Could not load data from BigQuery: {e}")
    st.stop()

# ── KPI Cards ────────────────────────────────────────────────────────────────
st.subheader("Period totals  ·  Nov 2020 – Jan 2021")
k1, k2, k3, k4, k5 = st.columns(5)

k1.metric(
    "Total Revenue",
    fmt_currency(float(p_kpis["gross_revenue_usd"])),
    help="Sum of purchase_revenue_usd for orders with a transaction_id",
)
k2.metric(
    "Total Sessions",
    fmt_int(s_kpis["total_sessions"]),
    help="Distinct (user_pseudo_id, ga_session_id) pairs",
)
k3.metric(
    "Unique Users",
    fmt_int(s_kpis["unique_users"]),
    help="Distinct user_pseudo_id values across all sessions",
)
k4.metric(
    "Session Conv. Rate",
    fmt_pct(float(s_kpis["session_conversion_rate"])),
    help="Sessions that contained at least one purchase event",
)
k5.metric(
    "Avg Order Value",
    fmt_currency(float(p_kpis["aov_usd"])),
    help="Gross revenue ÷ distinct orders (excluding null transaction_ids)",
)

st.divider()

# ── Revenue & Sessions trends ────────────────────────────────────────────────
col_rev, col_sess = st.columns(2)

with col_rev:
    st.subheader("Daily Revenue")
    fig_rev = px.area(
        daily_rev,
        x="event_date",
        y="revenue_usd",
        title=None,
        labels={"event_date": "", "revenue_usd": "Revenue (USD)"},
        color_discrete_sequence=[COLORS["revenue"]],
        template="plotly_white",
    )
    fig_rev.update_layout(
        margin=dict(l=0, r=0, t=8, b=0),
        yaxis_tickprefix="$",
        yaxis_tickformat=",.0f",
        hovermode="x unified",
    )
    fig_rev.update_traces(
        hovertemplate="$%{y:,.0f}",
        line_width=2,
        fillcolor="rgba(0,204,150,0.15)",
    )
    st.plotly_chart(fig_rev, use_container_width=True, config={"responsive": True})

with col_sess:
    st.subheader("Daily Sessions vs Conversions")
    fig_sess = go.Figure()
    fig_sess.add_trace(go.Scatter(
        x=daily_sess["event_date"],
        y=daily_sess["sessions"],
        name="Sessions",
        line=dict(color=COLORS["sessions"], width=2),
        mode="lines",
    ))
    fig_sess.add_trace(go.Bar(
        x=daily_sess["event_date"],
        y=daily_sess["converting_sessions"],
        name="Conversions",
        marker_color=COLORS["conversion"],
        opacity=0.7,
        yaxis="y2",
    ))
    fig_sess.update_layout(
        template="plotly_white",
        margin=dict(l=0, r=0, t=8, b=0),
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        yaxis=dict(title="Sessions", showgrid=True),
        yaxis2=dict(title="Conversions", overlaying="y", side="right", showgrid=False),
    )
    st.plotly_chart(fig_sess, use_container_width=True, config={"responsive": True})

st.divider()

# ── Channel & Category breakdown ─────────────────────────────────────────────
col_ch, col_cat = st.columns(2)

with col_ch:
    st.subheader("Revenue by Acquisition Channel")
    # Clean channel labels
    label_map = {
        "organic_search": "Organic Search",
        "paid_search": "Paid Search",
        "direct": "Direct",
        "referral": "Referral",
        "email": "Email",
        "social": "Social",
        "affiliate": "Affiliate",
        "other": "Other",
    }
    ch = channel_ltv.copy()
    ch["channel_label"] = ch["channel_group"].map(label_map).fillna(ch["channel_group"])
    ch = ch.sort_values("total_revenue_usd")

    fig_ch = px.bar(
        ch,
        y="channel_label",
        x="total_revenue_usd",
        orientation="h",
        text=ch["total_revenue_usd"].apply(fmt_currency),
        color="total_revenue_usd",
        color_continuous_scale=[[0, "#c7e9c0"], [1, "#005a32"]],
        labels={"channel_label": "", "total_revenue_usd": "Revenue (USD)"},
        template="plotly_white",
    )
    fig_ch.update_layout(
        margin=dict(l=0, r=0, t=8, b=0),
        coloraxis_showscale=False,
        xaxis_tickprefix="$",
        xaxis_tickformat=",.0f",
    )
    fig_ch.update_traces(textposition="outside")
    st.plotly_chart(fig_ch, use_container_width=True, config={"responsive": True})

    # Purchase rate footnote
    if not ch.empty:
        top_ch = ch.sort_values("total_revenue_usd", ascending=False).iloc[0]
        st.caption(
            f"Highest purchase rate: **{label_map.get(ch.sort_values('purchase_rate', ascending=False).iloc[0]['channel_group'], '—')}** "
            f"({fmt_pct(float(ch.sort_values('purchase_rate', ascending=False).iloc[0]['purchase_rate']))})"
        )

with col_cat:
    st.subheader("Top Product Categories by Views")
    top_cats_plot = top_cats.head(8).copy()
    top_cats_plot = top_cats_plot.sort_values("view_count")

    fig_cat = px.bar(
        top_cats_plot,
        y="item_category",
        x="view_count",
        orientation="h",
        text="view_count",
        color="view_count",
        color_continuous_scale=[[0, "#c6dbef"], [1, "#08519c"]],
        labels={"item_category": "", "view_count": "Product Views"},
        template="plotly_white",
    )
    fig_cat.update_layout(
        margin=dict(l=0, r=0, t=8, b=0),
        coloraxis_showscale=False,
        xaxis_tickformat=",",
    )
    fig_cat.update_traces(texttemplate="%{text:,}", textposition="outside")
    st.plotly_chart(fig_cat, use_container_width=True, config={"responsive": True})

st.divider()

# ── Methodology expander ──────────────────────────────────────────────────────
with st.expander("How this is built"):
    st.markdown(
        """
**Data lineage:**
```
bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*
  → stg_ga4__events          (dbt staging view, flatten + type-cast)
  → int_sessions             (dbt intermediate view, session-grain aggregation)
  → fct_sessions             (dbt mart table, 360k rows)
  → fct_purchases            (dbt mart table, 5.7k rows)
  → mart_ltv_by_channel      (dbt mart table, 35 rows)
```

**Metric definitions:**
- **Revenue** = `SUM(purchase_revenue_usd)` on purchase events with a non-null transaction_id
- **Session Conversion Rate** = sessions with ≥1 purchase ÷ total sessions
- **AOV** = gross revenue ÷ distinct orders (null transaction_ids excluded)
- **Acquisition Channel** = first-touch traffic medium mapped to 8 channel groups
        """
    )
