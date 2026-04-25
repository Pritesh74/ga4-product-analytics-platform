"""
Geography Performance
─────────────────────
Session volume, conversion rate, and revenue by country and continent.
Source: mart_geo_performance.
"""

import streamlit as st
import plotly.express as px
import pandas as pd

st.set_page_config(page_title="Geography", page_icon="🌍", layout="wide")

from utils.queries import load_country_performance

def fmt_pct(v):
    return f"{v*100:.1f}%" if pd.notna(v) and v > 0 else "—"

def fmt_currency(v):
    return f"${v:,.2f}" if pd.notna(v) else "—"

# ── Header ────────────────────────────────────────────────────────────────────
st.title("Geography Performance")
st.caption(
    "Session volume, engagement, conversion, and revenue by country.  \n"
    "Source: ga4_marts.mart_geo_performance"
)

# ── Load data ─────────────────────────────────────────────────────────────────
try:
    with st.spinner("Loading…"):
        df = load_country_performance()
except Exception as e:
    st.error(f"Could not load data from BigQuery: {e}")
    st.stop()

if df.empty:
    st.warning("No geography data available.")
    st.stop()

# ── Continent filter ──────────────────────────────────────────────────────────
continents = sorted(df["geo_continent"].dropna().unique().tolist())
selected = st.multiselect(
    "Filter by continent",
    options=continents,
    default=continents,
    label_visibility="collapsed",
)
df_f = df[df["geo_continent"].isin(selected)] if selected else df

# ── KPI Cards ─────────────────────────────────────────────────────────────────
top_country = df_f.iloc[0]["geo_country"] if not df_f.empty else "—"
top_conv = df_f.sort_values("conversion_rate", ascending=False)
top_conv_country = top_conv.iloc[0]["geo_country"] if not top_conv.empty else "—"
total_rev = float(df_f["revenue_usd"].sum())
total_sess = int(df_f["sessions"].sum())
n_countries = df_f["geo_country"].nunique()

k1, k2, k3, k4 = st.columns(4)
k1.metric("Countries represented", f"{n_countries:,}")
k2.metric("Total sessions", f"{total_sess:,}")
k3.metric("Top country by revenue", top_country)
k4.metric("Top country by conv. rate", top_conv_country, help="Min. 100 sessions")

st.divider()

# ── World map ─────────────────────────────────────────────────────────────────
st.subheader("Revenue by Country")
metric_map = st.radio(
    "Map metric",
    options=["revenue_usd", "sessions", "conversion_rate"],
    format_func=lambda x: {
        "revenue_usd": "Total Revenue",
        "sessions": "Sessions",
        "conversion_rate": "Conversion Rate",
    }[x],
    horizontal=True,
)

color_scales = {
    "revenue_usd": "Greens",
    "sessions": "Blues",
    "conversion_rate": "Oranges",
}
hover_formats = {
    "revenue_usd": "$,.0f",
    "sessions": ",",
    "conversion_rate": ".2%",
}

fig_map = px.choropleth(
    df_f,
    locations="geo_country",
    locationmode="country names",
    color=metric_map,
    color_continuous_scale=color_scales[metric_map],
    hover_name="geo_country",
    hover_data={
        "sessions": True,
        "conversion_rate": ":.1%",
        "revenue_usd": ":$,.0f",
    },
    labels={
        "revenue_usd": "Revenue (USD)",
        "sessions": "Sessions",
        "conversion_rate": "Conv. Rate",
    },
    template="plotly_white",
)
fig_map.update_layout(
    margin=dict(l=0, r=0, t=16, b=0),
    height=420,
    coloraxis_colorbar=dict(
        title={
            "revenue_usd": "Revenue",
            "sessions": "Sessions",
            "conversion_rate": "Conv. Rate",
        }[metric_map],
        tickformat=hover_formats[metric_map],
    ),
    geo=dict(showframe=False, showcoastlines=True, coastlinecolor="lightgray"),
)
st.plotly_chart(fig_map, use_container_width=True)

st.divider()

# ── Top countries charts ──────────────────────────────────────────────────────
col1, col2 = st.columns(2)

top_n = 15
df_top = df_f.sort_values("revenue_usd", ascending=False).head(top_n)

with col1:
    st.subheader(f"Top {top_n} Countries by Revenue")
    df_top_rev = df_top.sort_values("revenue_usd")
    fig_rev = px.bar(
        df_top_rev,
        y="geo_country",
        x="revenue_usd",
        orientation="h",
        color="revenue_usd",
        color_continuous_scale=[[0, "#e5f5e0"], [1, "#006d2c"]],
        text=df_top_rev["revenue_usd"].apply(lambda v: f"${v:,.0f}"),
        labels={"geo_country": "", "revenue_usd": "Revenue (USD)"},
        template="plotly_white",
    )
    fig_rev.update_layout(
        margin=dict(l=0, r=0, t=8, b=0),
        coloraxis_showscale=False,
        xaxis_tickprefix="$", xaxis_tickformat=",.0f",
        height=420,
    )
    fig_rev.update_traces(textposition="outside")
    st.plotly_chart(fig_rev, use_container_width=True)

with col2:
    st.subheader(f"Conversion Rate – Top {top_n} by Revenue")
    st.caption("Sorted by conversion rate. Min 100 sessions applied.")
    df_top_cr = (
        df_f[df_f["sessions"] >= 100]
        .sort_values("conversion_rate", ascending=True)
        .tail(top_n)
    )
    fig_cr = px.bar(
        df_top_cr,
        y="geo_country",
        x="conversion_rate",
        orientation="h",
        color="conversion_rate",
        color_continuous_scale=[[0, "#fff7bc"], [1, "#d95f0e"]],
        text=df_top_cr["conversion_rate"].apply(fmt_pct),
        labels={"geo_country": "", "conversion_rate": "Conv. Rate"},
        template="plotly_white",
    )
    fig_cr.update_layout(
        margin=dict(l=0, r=0, t=8, b=0),
        coloraxis_showscale=False,
        xaxis_tickformat=".1%",
        height=420,
    )
    fig_cr.update_traces(textposition="outside")
    st.plotly_chart(fig_cr, use_container_width=True)

st.divider()

# ── Full data table ────────────────────────────────────────────────────────────
with st.expander("Full country data table"):
    display = df_f[["geo_country", "geo_continent", "sessions", "unique_users",
                    "engagement_rate", "conversion_rate", "revenue_usd",
                    "revenue_per_session"]].copy()
    display["engagement_rate"] = display["engagement_rate"].apply(fmt_pct)
    display["conversion_rate"] = display["conversion_rate"].apply(fmt_pct)
    display["revenue_usd"] = display["revenue_usd"].apply(lambda x: f"${x:,.0f}")
    display["revenue_per_session"] = display["revenue_per_session"].apply(fmt_currency)
    display.columns = [
        "Country", "Continent", "Sessions", "Users",
        "Engagement Rate", "Conv. Rate", "Revenue", "Rev/Session"
    ]
    st.dataframe(display, hide_index=True, use_container_width=True, height=400)
