"""
Funnel Analysis
───────────────
Purchase funnel drop-off from session start → purchase.
Period totals from fact tables; daily trends from mart_daily_funnel.
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

st.set_page_config(page_title="Funnel Analysis", page_icon="🔽", layout="wide")

from utils.queries import load_period_funnel, load_daily_funnel

# ── Header ───────────────────────────────────────────────────────────────────
st.title("Purchase Funnel")
st.caption(
    "Stage-by-stage drop-off analysis across the full Nov 2020 – Jan 2021 period.  \n"
    "Source: ga4_marts.fct_sessions, fct_product_views, fct_add_to_cart, "
    "fct_begin_checkout, fct_purchases, mart_daily_funnel"
)

# ── Load data ─────────────────────────────────────────────────────────────────
try:
    with st.spinner("Loading…"):
        period = load_period_funnel()
        daily = load_daily_funnel()
except Exception as e:
    st.error(f"Could not load data from BigQuery: {e}")
    st.stop()

# ── Period funnel ─────────────────────────────────────────────────────────────
st.subheader("Overall Funnel  ·  Nov 2020 – Jan 2021")

STAGE_COLORS = ["#636EFA", "#EF553B", "#00CC96", "#AB63FA", "#FFA15A"]

col_funnel, col_dropoff = st.columns([3, 2])

with col_funnel:
    fig_funnel = go.Figure(go.Funnel(
        y=period["stage"].tolist(),
        x=period["users"].tolist(),
        textposition="inside",
        textinfo="value+percent previous",
        marker=dict(color=STAGE_COLORS),
        connector=dict(line=dict(color="rgba(100,100,100,0.2)", width=1)),
    ))
    fig_funnel.update_layout(
        template="plotly_white",
        margin=dict(l=0, r=0, t=8, b=0),
        height=360,
        font=dict(size=13),
    )
    st.plotly_chart(fig_funnel, use_container_width=True)

with col_dropoff:
    st.subheader("Stage Drop-off")

    # Build drop-off table
    period_sorted = period.sort_values("stage_order")
    rows = []
    for i, row in period_sorted.iterrows():
        prev_users = period_sorted.loc[
            period_sorted["stage_order"] == row["stage_order"] - 1, "users"
        ]
        if not prev_users.empty and int(prev_users.iloc[0]) > 0:
            kept = row["users"] / prev_users.iloc[0]
            lost = 1 - kept
        else:
            kept = 1.0
            lost = 0.0
        rows.append({
            "Stage": row["stage"],
            "Users": f"{int(row['users']):,}",
            "From prev.": "—" if row["stage_order"] == 1 else f"{kept*100:.1f}%",
            "Drop-off": "—" if row["stage_order"] == 1 else f"{lost*100:.1f}%",
        })

    df_dropoff = pd.DataFrame(rows)
    st.dataframe(
        df_dropoff,
        use_container_width=True,
        hide_index=True,
        height=220,
    )

    # Overall funnel conversion
    top_users = int(period_sorted["users"].iloc[0])
    bottom_users = int(period_sorted["users"].iloc[-1])
    overall_cr = bottom_users / top_users if top_users > 0 else 0
    st.metric(
        "End-to-end conversion",
        f"{overall_cr*100:.2f}%",
        help="Purchase users ÷ Session Start users",
    )

st.divider()

# ── Daily funnel trend ────────────────────────────────────────────────────────
st.subheader("Daily Unique Users by Funnel Stage")

stage_order = {
    "session_start": 1,
    "view_item": 2,
    "add_to_cart": 3,
    "begin_checkout": 4,
    "purchase": 5,
}
stage_labels = {
    "session_start": "Session Start",
    "view_item": "View Item",
    "add_to_cart": "Add to Cart",
    "begin_checkout": "Begin Checkout",
    "purchase": "Purchase",
}

daily["stage_label"] = daily["funnel_stage"].map(stage_labels)

# Stage filter
all_stages = ["Session Start", "View Item", "Add to Cart", "Begin Checkout", "Purchase"]
selected_stages = st.multiselect(
    "Select stages to display",
    options=all_stages,
    default=all_stages,
    label_visibility="collapsed",
)

daily_filtered = daily[daily["stage_label"].isin(selected_stages)]

fig_trend = px.line(
    daily_filtered,
    x="event_date",
    y="unique_users",
    color="stage_label",
    color_discrete_sequence=STAGE_COLORS,
    labels={"event_date": "", "unique_users": "Unique Users", "stage_label": "Stage"},
    template="plotly_white",
    markers=False,
)
fig_trend.update_layout(
    margin=dict(l=0, r=0, t=8, b=0),
    hovermode="x unified",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    yaxis_tickformat=",",
)
fig_trend.update_traces(line_width=2)
st.plotly_chart(fig_trend, use_container_width=True)

st.divider()

with st.expander("How to read this"):
    st.markdown(
        """
**Funnel definition:** A user is counted at a stage if they triggered that event type
at least once during the full dataset period. This is a *loose funnel* (not same-session).

**Stage sources:**
| Stage | Source table |
|---|---|
| Session Start | `fct_sessions` — COUNT DISTINCT user_pseudo_id |
| View Item | `fct_product_views` |
| Add to Cart | `fct_add_to_cart` |
| Begin Checkout | `fct_begin_checkout` |
| Purchase | `fct_purchases` |

**Daily trend:** Uses `mart_daily_funnel` which counts unique users PER DAY per stage.
The same user is counted on each day they appear — appropriate for trend analysis.
        """
    )
