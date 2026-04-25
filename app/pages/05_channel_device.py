"""
Channel & Device Performance
────────────────────────────
Conversion rate, engagement, and revenue broken down by acquisition channel
and device type. Side-by-side comparison surfaces UX gaps (e.g. mobile vs desktop).
Source: fct_sessions, mart_device_performance.
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

st.set_page_config(page_title="Channel & Device", page_icon="📱", layout="wide")

from utils.queries import load_channel_performance, load_device_performance, load_browser_performance

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

def fmt_pct(v):
    return f"{v*100:.1f}%" if pd.notna(v) else "—"

def fmt_currency(v):
    return f"${v:.2f}" if pd.notna(v) else "—"

# ── Header ────────────────────────────────────────────────────────────────────
st.title("Channel & Device Performance")
st.caption(
    "Conversion rate, engagement, and revenue per session by channel and device.  \n"
    "Source: ga4_marts.fct_sessions (channel), mart_device_performance (device/browser)"
)

# ── Load data ─────────────────────────────────────────────────────────────────
try:
    with st.spinner("Loading…"):
        ch = load_channel_performance()
        dev = load_device_performance()
        browser = load_browser_performance()
except Exception as e:
    st.error(f"Could not load data from BigQuery: {e}")
    st.stop()

ch["channel_label"] = ch["channel_group"].map(CHANNEL_LABELS).fillna(ch["channel_group"])

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab_ch, tab_dev = st.tabs(["📣 Channel Performance", "📱 Device Performance"])

# ══════════════════════════════════════════════════════════════════════════════
# Channel Performance
# ══════════════════════════════════════════════════════════════════════════════
with tab_ch:
    col1, col2, col3 = st.columns(3)

    with col1:
        st.subheader("Sessions by Channel")
        ch_sess = ch.sort_values("sessions")
        fig_s = px.bar(
            ch_sess,
            y="channel_label",
            x="sessions",
            orientation="h",
            color="sessions",
            color_continuous_scale=[[0, "#c6dbef"], [1, "#08519c"]],
            labels={"channel_label": "", "sessions": "Sessions"},
            text=ch_sess["sessions"].apply(lambda x: f"{x:,}"),
            template="plotly_white",
        )
        fig_s.update_layout(margin=dict(l=0, r=0, t=8, b=0), coloraxis_showscale=False,
                            xaxis_tickformat=",")
        fig_s.update_traces(textposition="outside")
        st.plotly_chart(fig_s, use_container_width=True)

    with col2:
        st.subheader("Conversion Rate by Channel")
        ch_cr = ch.sort_values("conversion_rate")
        fig_cr = px.bar(
            ch_cr,
            y="channel_label",
            x="conversion_rate",
            orientation="h",
            color="conversion_rate",
            color_continuous_scale=[[0, "#fff7bc"], [1, "#d95f0e"]],
            labels={"channel_label": "", "conversion_rate": "Conv. Rate"},
            text=ch_cr["conversion_rate"].apply(fmt_pct),
            template="plotly_white",
        )
        fig_cr.update_layout(margin=dict(l=0, r=0, t=8, b=0), coloraxis_showscale=False,
                             xaxis_tickformat=".1%")
        fig_cr.update_traces(textposition="outside")
        st.plotly_chart(fig_cr, use_container_width=True)

    with col3:
        st.subheader("Revenue per Session")
        ch_rps = ch.sort_values("revenue_per_session")
        fig_rps = px.bar(
            ch_rps,
            y="channel_label",
            x="revenue_per_session",
            orientation="h",
            color="revenue_per_session",
            color_continuous_scale=[[0, "#e5f5e0"], [1, "#006d2c"]],
            labels={"channel_label": "", "revenue_per_session": "Rev / Session"},
            text=ch_rps["revenue_per_session"].apply(fmt_currency),
            template="plotly_white",
        )
        fig_rps.update_layout(margin=dict(l=0, r=0, t=8, b=0), coloraxis_showscale=False,
                              xaxis_tickprefix="$", xaxis_tickformat=".2f")
        fig_rps.update_traces(textposition="outside")
        st.plotly_chart(fig_rps, use_container_width=True)

    st.divider()

    # Channel engagement rate
    st.subheader("Engagement Rate by Channel")
    st.caption("GA4 engaged session = 10s+ duration, 2+ page views, or a conversion")
    ch_eng = ch.sort_values("engagement_rate", ascending=False)
    fig_eng = px.bar(
        ch_eng,
        x="channel_label",
        y="engagement_rate",
        color="channel_label",
        color_discrete_sequence=px.colors.qualitative.Set2,
        labels={"channel_label": "", "engagement_rate": "Engagement Rate"},
        text=ch_eng["engagement_rate"].apply(fmt_pct),
        template="plotly_white",
    )
    fig_eng.update_layout(margin=dict(l=0, r=0, t=8, b=0), showlegend=False,
                          yaxis_tickformat=".0%")
    fig_eng.update_traces(textposition="outside")
    st.plotly_chart(fig_eng, use_container_width=True)

    with st.expander("Channel data table"):
        display_ch = ch[["channel_label", "sessions", "unique_users",
                          "engagement_rate", "conversion_rate",
                          "total_revenue_usd", "revenue_per_session"]].copy()
        display_ch["engagement_rate"] = display_ch["engagement_rate"].apply(fmt_pct)
        display_ch["conversion_rate"] = display_ch["conversion_rate"].apply(fmt_pct)
        display_ch["total_revenue_usd"] = display_ch["total_revenue_usd"].apply(
            lambda x: f"${x:,.0f}"
        )
        display_ch["revenue_per_session"] = display_ch["revenue_per_session"].apply(fmt_currency)
        display_ch.columns = ["Channel", "Sessions", "Users", "Engagement Rate",
                               "Conv. Rate", "Revenue", "Rev/Session"]
        st.dataframe(display_ch, hide_index=True, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# Device Performance
# ══════════════════════════════════════════════════════════════════════════════
with tab_dev:
    # KPI cards per device
    st.subheader("Device Category Comparison")

    device_order = ["desktop", "mobile", "tablet"]
    dev_display = dev[dev["device_category"].isin(device_order)].copy()
    dev_display = dev_display.set_index("device_category")

    card_cols = st.columns(len(dev_display))
    for i, cat in enumerate(device_order):
        if cat not in dev_display.index:
            continue
        row = dev_display.loc[cat]
        with card_cols[i]:
            st.metric(f"**{cat.capitalize()}**", "")
            st.metric("Sessions", f"{int(row['sessions']):,}")
            st.metric("Conv. Rate", fmt_pct(float(row["conversion_rate"])))
            st.metric("Engagement Rate", fmt_pct(float(row["engagement_rate"])))
            st.metric("Rev / Session", fmt_currency(float(row["revenue_per_session"])))

    st.divider()

    col_dv1, col_dv2 = st.columns(2)

    with col_dv1:
        st.subheader("Conversion Rate by Device")
        fig_dv = px.bar(
            dev.sort_values("conversion_rate", ascending=False),
            x="device_category",
            y="conversion_rate",
            color="device_category",
            color_discrete_sequence=["#636EFA", "#EF553B", "#00CC96"],
            text=dev.sort_values("conversion_rate", ascending=False)["conversion_rate"].apply(fmt_pct),
            labels={"device_category": "", "conversion_rate": "Session Conv. Rate"},
            template="plotly_white",
        )
        fig_dv.update_layout(margin=dict(l=0, r=0, t=8, b=0), showlegend=False,
                             yaxis_tickformat=".1%")
        fig_dv.update_traces(textposition="outside")
        st.plotly_chart(fig_dv, use_container_width=True)

    with col_dv2:
        st.subheader("Revenue per Session by Device")
        fig_drps = px.bar(
            dev.sort_values("revenue_per_session", ascending=False),
            x="device_category",
            y="revenue_per_session",
            color="device_category",
            color_discrete_sequence=["#636EFA", "#EF553B", "#00CC96"],
            text=dev.sort_values("revenue_per_session", ascending=False)[
                "revenue_per_session"
            ].apply(fmt_currency),
            labels={"device_category": "", "revenue_per_session": "Revenue / Session (USD)"},
            template="plotly_white",
        )
        fig_drps.update_layout(margin=dict(l=0, r=0, t=8, b=0), showlegend=False,
                               yaxis_tickprefix="$", yaxis_tickformat=".2f")
        fig_drps.update_traces(textposition="outside")
        st.plotly_chart(fig_drps, use_container_width=True)

    st.divider()
    st.subheader("Top Browsers by Session Volume")
    fig_br = px.bar(
        browser.sort_values("sessions", ascending=True).tail(12),
        y="device_browser",
        x="sessions",
        orientation="h",
        color="conversion_rate",
        color_continuous_scale=[[0, "#fff7bc"], [1, "#d95f0e"]],
        labels={
            "device_browser": "",
            "sessions": "Sessions",
            "conversion_rate": "Conv. Rate",
        },
        text=browser.sort_values("sessions", ascending=True).tail(12)["sessions"].apply(
            lambda x: f"{x:,}"
        ),
        template="plotly_white",
        hover_data={"conversion_rate": ":.1%", "revenue_per_session": ":.2f"},
    )
    fig_br.update_layout(
        margin=dict(l=0, r=0, t=8, b=0),
        xaxis_tickformat=",",
        coloraxis_colorbar=dict(title="Conv.<br>Rate", tickformat=".1%"),
    )
    fig_br.update_traces(textposition="outside")
    st.plotly_chart(fig_br, use_container_width=True)
