"""
Retention Cohorts
─────────────────
Monthly acquisition cohort matrix. Shows what fraction of users acquired
in each month returned to make a purchase in subsequent months.
Source: mart_retention_cohorts, dim_users.
"""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np

st.set_page_config(page_title="Retention Cohorts", page_icon="🔁", layout="wide")

from utils.queries import load_retention_cohorts

# ── Header ───────────────────────────────────────────────────────────────────
st.title("Retention Cohorts")
st.caption(
    "Acquisition cohort × purchase activity. "
    "Source: ga4_marts.mart_retention_cohorts"
)

st.info(
    "**Dataset note:** The GA4 public sample covers only 3 months (Nov 2020 – Jan 2021), "
    "so this matrix has a maximum of 2 follow-up periods. In a production dataset with "
    "12+ months of history this chart reveals long-term customer retention patterns.",
    icon="ℹ️",
)

# ── Load data ─────────────────────────────────────────────────────────────────
try:
    with st.spinner("Loading…"):
        df = load_retention_cohorts()
except Exception as e:
    st.error(f"Could not load data from BigQuery: {e}")
    st.stop()

if df.empty:
    st.warning("No retention data available.")
    st.stop()

# ── Format cohort labels ──────────────────────────────────────────────────────
df["cohort_label"] = pd.to_datetime(df["cohort_month"]).dt.strftime("%b %Y")
df["period_label"] = df["months_since_acquisition"].apply(
    lambda m: f"Month {m}" if m > 0 else "Month 0\n(acquisition)"
)

# ── Pivot for heatmap ─────────────────────────────────────────────────────────
pivot = df.pivot(
    index="cohort_label",
    columns="months_since_acquisition",
    values="retention_rate",
).fillna(np.nan)

pivot_users = df.pivot(
    index="cohort_label",
    columns="months_since_acquisition",
    values="retained_users",
).fillna(0).astype(int)

pivot_size = df.groupby("cohort_label")["cohort_size"].first()

# Column labels
col_labels = [f"Month +{c}" if c > 0 else "Month 0" for c in pivot.columns]

# Text annotations: "X% (N users)"
text_matrix = []
for cohort in pivot.index:
    row_texts = []
    for m in pivot.columns:
        rate = pivot.loc[cohort, m]
        users = pivot_users.loc[cohort, m] if cohort in pivot_users.index and m in pivot_users.columns else 0
        if pd.isna(rate):
            row_texts.append("")
        else:
            row_texts.append(f"{rate*100:.1f}%<br>{users:,} users")
    text_matrix.append(row_texts)

# ── Heatmap ───────────────────────────────────────────────────────────────────
col_heat, col_info = st.columns([3, 1])

with col_heat:
    st.subheader("Purchase Retention Rate by Cohort")
    fig = go.Figure(go.Heatmap(
        z=pivot.values.tolist(),
        x=col_labels,
        y=pivot.index.tolist(),
        text=text_matrix,
        texttemplate="%{text}",
        colorscale=[
            [0.0, "#f7fbff"],
            [0.3, "#6baed6"],
            [0.6, "#2171b5"],
            [1.0, "#08306b"],
        ],
        zmin=0,
        zmax=0.15,
        colorbar=dict(
            title="Retention<br>Rate",
            tickformat=".0%",
        ),
        hoverongaps=False,
        xgap=3,
        ygap=3,
    ))
    fig.update_layout(
        template="plotly_white",
        margin=dict(l=0, r=0, t=16, b=0),
        height=280,
        font=dict(size=11),
        xaxis=dict(side="top"),
    )
    st.plotly_chart(fig, use_container_width=True, config={"responsive": True})

with col_info:
    st.subheader("Cohort Sizes")
    st.markdown("Users acquired per month:")

    size_df = (
        df.groupby("cohort_label")
        .agg(cohort_size=("cohort_size", "first"))
        .reset_index()
        .rename(columns={"cohort_label": "Cohort", "cohort_size": "Users"})
    )
    size_df["Users"] = size_df["Users"].apply(lambda x: f"{int(x):,}")
    st.dataframe(size_df, hide_index=True, use_container_width=True)

    st.markdown("---")
    # Month 0 retention rates
    if 0 in df["months_since_acquisition"].values:
        m0 = df[df["months_since_acquisition"] == 0][["cohort_label", "retention_rate"]]
        st.markdown("**Month 0 purchase rate:**")
        for _, row in m0.iterrows():
            st.write(f"{row['cohort_label']}: **{row['retention_rate']*100:.1f}%**")

st.divider()

# ── Raw data table ────────────────────────────────────────────────────────────
with st.expander("Raw cohort data"):
    display = df[["cohort_label", "months_since_acquisition", "cohort_size",
                  "retained_users", "retention_rate"]].copy()
    display["retention_rate"] = display["retention_rate"].apply(
        lambda x: f"{x*100:.1f}%" if pd.notna(x) else "—"
    )
    display.columns = ["Cohort", "Months Since Acq.", "Cohort Size", "Retained Users", "Retention Rate"]
    st.dataframe(display, hide_index=True, use_container_width=True)

st.divider()

with st.expander("How this is built"):
    st.markdown(
        """
**Cohort definition:**
- `cohort_month` = DATE_TRUNC(first_seen_date, MONTH) from `dim_users`
- A user is "retained" in month N if they made at least one purchase
  N months after their acquisition month.

**Source:** `mart_retention_cohorts`
```
dim_users (cohort_month per user)
  + fct_purchases (purchase dates)
  → one row per (cohort_month × months_since_acquisition)
```

**Why the matrix is sparse:** The GA4 sample only covers Nov 2020 – Jan 2021 (3 months).
A Jan 2021 cohort can only have Month 0 data; a Nov 2020 cohort has Month 0, 1, and 2.
        """
    )
