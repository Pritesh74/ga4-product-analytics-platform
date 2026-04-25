"""
Product Analytics & Experimentation Platform
Landing page / navigation hub.

Run: streamlit run app/main.py
"""

import streamlit as st

st.set_page_config(
    page_title="GA4 Product Analytics Platform",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Sidebar ──────────────────────────────────────────────────────────────────
st.sidebar.title("📊 Analytics Platform")
st.sidebar.markdown("---")
st.sidebar.caption(
    "**Source:** Google Merchandise Store  \n"
    "**Dataset:** BigQuery public GA4 sample  \n"
    "**Period:** Nov 2020 – Jan 2021  \n"
    "**Stack:** BigQuery · dbt · Streamlit"
)

# ── Hero ─────────────────────────────────────────────────────────────────────
st.title("Product Analytics & Experimentation Platform")
st.markdown(
    "A portfolio-grade analytics stack built on Google's public GA4 e-commerce "
    "sample dataset. Raw event data flows through a dbt-powered transformation "
    "layer into mart tables, which feed this Streamlit dashboard."
)

st.divider()

# ── Tab index ─────────────────────────────────────────────────────────────────
col1, col2 = st.columns(2)

with col1:
    st.subheader("Dashboard tabs")
    st.markdown(
        """
| Tab | What you'll find |
|---|---|
| **Executive Overview** | Revenue trend, session volume, conversion rate, AOV, top channels |
| **Funnel** | Stage-by-stage drop-off from session start → purchase |
| **Retention** | Monthly cohort retention matrix — who comes back to buy? |
| **LTV** | Lifetime value and purchase rate by acquisition channel |
| **Channel & Device** | Conversion and revenue by medium, device, and browser |
| **Geography** | Country and continent performance breakdown |
| **Data Quality** | Mart row counts, test pass rates, data freshness |
        """
    )

with col2:
    st.subheader("Architecture")
    st.markdown(
        """
| Layer | Technology | What it does |
|---|---|---|
| Source | BigQuery public dataset | Raw GA4 event tables |
| Staging | dbt views | Flatten, type-cast, add keys |
| Intermediate | dbt views | Session & user aggregations |
| Marts | dbt tables | Business-ready fact & dim tables |
| Dashboard | Streamlit + Plotly | This app |
        """
    )
    st.markdown(
        """
**dbt test coverage:** 82 tests, 0 errors
**Mart tables:** 11 models across `ga4_marts`
**Source data:** 2.5M+ raw events, Nov 2020 – Jan 2021
        """
    )

st.divider()
st.caption(
    "Built by Pritesh Viramgama · "
    "Stack: BigQuery · dbt Core 1.8 · Python · Streamlit · Plotly"
)
