"""
LTV by Acquisition Channel
──────────────────────────
Customer lifetime value metrics broken down by the channel that acquired
each user. Answers: which channels bring users who spend the most?
Source: mart_ltv_by_channel.
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

st.set_page_config(page_title="LTV by Channel", page_icon="💰", layout="wide")

from utils.queries import load_ltv_by_channel

CHANNEL_LABELS = {
    "organic_search": "Organic Search",
    "paid_search": "Paid Search",
    "direct": "Direct",
    "referral": "Referral",
    "email": "Email",
    "social": "Social",
    "affiliate": "Affiliate",
    "other": "Other",
}

def fmt_currency(v):
    return f"${v:,.2f}"

def fmt_pct(v):
    return f"{v*100:.1f}%"

# ── Header ───────────────────────────────────────────────────────────────────
st.title("Customer LTV by Acquisition Channel")
st.caption(
    "Which channels bring the highest-value users? "
    "Source: ga4_marts.mart_ltv_by_channel"
)

# ── Load data ─────────────────────────────────────────────────────────────────
try:
    with st.spinner("Loading…"):
        df = load_ltv_by_channel()
except Exception as e:
    st.error(f"Could not load data from BigQuery: {e}")
    st.stop()

if df.empty:
    st.warning("No LTV data available.")
    st.stop()

# Aggregate to channel level (collapse traffic_medium within channel_group)
ch = (
    df.groupby("channel_group")
    .agg(
        total_users=("total_users", "sum"),
        purchasing_users=("purchasing_users", "sum"),
        total_revenue_usd=("total_revenue_usd", "sum"),
        total_orders=("avg_orders_per_purchaser", lambda x: (x * df.loc[x.index, "purchasing_users"]).sum()),
    )
    .reset_index()
)
ch["purchase_rate"] = ch["purchasing_users"] / ch["total_users"].replace(0, float("nan"))
ch["avg_revenue_per_user"] = ch["total_revenue_usd"] / ch["total_users"].replace(0, float("nan"))
ch["avg_revenue_per_purchaser"] = ch["total_revenue_usd"] / ch["purchasing_users"].replace(0, float("nan"))
ch["channel_label"] = ch["channel_group"].map(CHANNEL_LABELS).fillna(ch["channel_group"])
ch = ch.sort_values("total_revenue_usd", ascending=False)

# ── KPI Summary row ───────────────────────────────────────────────────────────
total_users = int(ch["total_users"].sum())
total_purchasing = int(ch["purchasing_users"].sum())
total_revenue = float(ch["total_revenue_usd"].sum())
overall_purchase_rate = total_purchasing / total_users if total_users > 0 else 0
overall_ltv = total_revenue / total_users if total_users > 0 else 0
overall_purchaser_ltv = total_revenue / total_purchasing if total_purchasing > 0 else 0

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Total Users", f"{total_users:,}")
k2.metric("Purchasing Users", f"{total_purchasing:,}")
k3.metric("Overall Purchase Rate", fmt_pct(overall_purchase_rate))
k4.metric("Avg Rev / User", fmt_currency(overall_ltv), help="Includes non-purchasers")
k5.metric("Avg Rev / Purchaser", fmt_currency(overall_purchaser_ltv), help="Purchasers only")

st.divider()

# ── LTV comparison chart ──────────────────────────────────────────────────────
st.subheader("Revenue per User vs Revenue per Purchaser")
st.caption("Revenue per user includes everyone acquired through that channel (the true LTV signal)")

ltv_melt = pd.melt(
    ch,
    id_vars=["channel_label"],
    value_vars=["avg_revenue_per_user", "avg_revenue_per_purchaser"],
    var_name="metric",
    value_name="value",
)
ltv_melt["metric"] = ltv_melt["metric"].map({
    "avg_revenue_per_user": "Avg Revenue / User",
    "avg_revenue_per_purchaser": "Avg Revenue / Purchaser",
})

fig_ltv = px.bar(
    ltv_melt.dropna(),
    x="channel_label",
    y="value",
    color="metric",
    barmode="group",
    color_discrete_map={
        "Avg Revenue / User": "#636EFA",
        "Avg Revenue / Purchaser": "#00CC96",
    },
    labels={"channel_label": "", "value": "Revenue (USD)", "metric": ""},
    template="plotly_white",
    text_auto="$.2f",
)
fig_ltv.update_layout(
    margin=dict(l=0, r=0, t=8, b=0),
    yaxis_tickprefix="$",
    yaxis_tickformat=",.2f",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
)
fig_ltv.update_traces(texttemplate="$%{y:.2f}", textposition="outside")
st.plotly_chart(fig_ltv, use_container_width=True)

st.divider()

# ── Purchase rate + Revenue volume ───────────────────────────────────────────
col_pr, col_rev = st.columns(2)

with col_pr:
    st.subheader("Purchase Rate by Channel")
    st.caption("% of all acquired users who made at least one purchase")
    ch_pr = ch.sort_values("purchase_rate", ascending=True)
    fig_pr = px.bar(
        ch_pr,
        y="channel_label",
        x="purchase_rate",
        orientation="h",
        color="purchase_rate",
        color_continuous_scale=[[0, "#fff7bc"], [1, "#d95f0e"]],
        labels={"channel_label": "", "purchase_rate": "Purchase Rate"},
        text=ch_pr["purchase_rate"].apply(fmt_pct),
        template="plotly_white",
    )
    fig_pr.update_layout(
        margin=dict(l=0, r=0, t=8, b=0),
        coloraxis_showscale=False,
        xaxis_tickformat=".0%",
    )
    fig_pr.update_traces(textposition="outside")
    st.plotly_chart(fig_pr, use_container_width=True)

with col_rev:
    st.subheader("Total Revenue by Channel")
    ch_rev = ch.sort_values("total_revenue_usd")
    fig_rev = px.bar(
        ch_rev,
        y="channel_label",
        x="total_revenue_usd",
        orientation="h",
        color="total_revenue_usd",
        color_continuous_scale=[[0, "#e5f5e0"], [1, "#006d2c"]],
        labels={"channel_label": "", "total_revenue_usd": "Revenue (USD)"},
        text=ch_rev["total_revenue_usd"].apply(lambda v: f"${v:,.0f}"),
        template="plotly_white",
    )
    fig_rev.update_layout(
        margin=dict(l=0, r=0, t=8, b=0),
        coloraxis_showscale=False,
        xaxis_tickprefix="$",
        xaxis_tickformat=",.0f",
    )
    fig_rev.update_traces(textposition="outside")
    st.plotly_chart(fig_rev, use_container_width=True)

st.divider()

# ── Data table ────────────────────────────────────────────────────────────────
with st.expander("Full data table"):
    display = ch[["channel_label", "total_users", "purchasing_users",
                  "purchase_rate", "total_revenue_usd",
                  "avg_revenue_per_user", "avg_revenue_per_purchaser"]].copy()
    display["purchase_rate"] = display["purchase_rate"].apply(
        lambda x: f"{x*100:.1f}%" if pd.notna(x) else "—"
    )
    for col in ["total_revenue_usd", "avg_revenue_per_user", "avg_revenue_per_purchaser"]:
        display[col] = display[col].apply(
            lambda x: f"${x:,.2f}" if pd.notna(x) else "—"
        )
    display.columns = [
        "Channel", "Total Users", "Purchasing Users",
        "Purchase Rate", "Total Revenue", "Avg Rev/User", "Avg Rev/Purchaser"
    ]
    st.dataframe(display, hide_index=True, use_container_width=True)

with st.expander("How this is built"):
    st.markdown(
        """
**Source:** `mart_ltv_by_channel`
```
dim_users (channel_group per user) + fct_purchases (revenue per user)
  → aggregated to channel_group × cohort_month
  → this page collapses cohort_month to show full-period channel LTV
```

**Key distinction:**
- **Avg Revenue per User** = revenue ÷ ALL users from that channel (including non-purchasers).
  This is the true LTV signal for comparing channel quality.
- **Avg Revenue per Purchaser** = revenue ÷ users who bought at least once.
  Higher this is, the deeper the purchase behavior.
- **Purchase Rate** = the channel's e-commerce conversion efficiency.
        """
    )
