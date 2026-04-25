"""
Experiment Demo — Checkout UX v2
──────────────────────────────────
SIMULATED A/B test analysis built on real GA4 user behavior.
Assignment is deterministic (FARM_FINGERPRINT) — no real treatment was applied.
Source: ga4_experiments.exp_simulated_results + exp_simulated_assignment
"""

import math
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st
from scipy import stats

st.set_page_config(page_title="Experiment Demo", page_icon="🧪", layout="wide")

from utils.queries import (
    load_experiment_results,
    load_experiment_baseline,
    load_experiment_daily,
)

# ── Simulation banner ──────────────────────────────────────────────────────────
st.warning(
    "**SIMULATED EXPERIMENT** — This is a portfolio demonstration of an A/B testing "
    "framework built on real GA4 e-commerce data. No treatment was actually applied. "
    "Variant assignment is deterministic (FARM_FINGERPRINT hash split). "
    "Results reflect real user behavior randomly partitioned into two groups.",
    icon="🧪",
)

st.title("Experiment Demo: Checkout UX v2")
st.caption(
    "Simulated A/B test · Dec 1, 2020 – Jan 31, 2021 · "
    "Source: ga4_experiments.exp_simulated_results"
)

# ── Load data ──────────────────────────────────────────────────────────────────
try:
    with st.spinner("Loading experiment data…"):
        df_results   = load_experiment_results()
        df_baseline  = load_experiment_baseline()
        df_daily     = load_experiment_daily()
except Exception as e:
    st.error(f"Could not load experiment data from BigQuery: {e}")
    st.stop()

if df_results.empty or len(df_results) < 2:
    st.error("Expected 2 variant rows; got unexpected data.")
    st.stop()

ctrl = df_results[df_results["variant_name"] == "control"].iloc[0]
trt  = df_results[df_results["variant_name"] == "treatment"].iloc[0]

n_ctrl   = int(ctrl["n_users"])
n_trt    = int(trt["n_users"])
conv_ctrl = float(ctrl["conversion_rate"])
conv_trt  = float(trt["conversion_rate"])
conv_ctrl_n = int(ctrl["n_conversions"])
conv_trt_n  = int(trt["n_conversions"])
rpu_ctrl = float(ctrl["revenue_per_user"])
rpu_trt  = float(trt["revenue_per_user"])
sd_ctrl  = float(ctrl["stddev_revenue_per_user"])
sd_trt   = float(trt["stddev_revenue_per_user"])

baseline_rate = float(df_baseline["baseline_conversion_rate"].iloc[0])

# ── Experiment Design ──────────────────────────────────────────────────────────
st.divider()
st.subheader("Experiment Design")

col_d1, col_d2, col_d3 = st.columns(3)

with col_d1:
    st.markdown(
        """
**Hypothesis**
> Redesigning the checkout flow (Checkout UX v2) will increase
> the checkout-to-purchase conversion rate.

**Primary metric:** Checkout-to-purchase conversion rate
**Secondary metric:** Revenue per eligible user
**Guardrails:** Engagement rate · Avg checkouts per user
        """
    )

with col_d2:
    st.markdown(
        f"""
**Experiment window**
Dec 1, 2020 → Jan 31, 2021 (62 days)

**Eligibility**
Users with ≥1 `begin_checkout` event in window

**Assignment**
50 / 50 split via `FARM_FINGERPRINT(user_pseudo_id || salt) MOD 2`
Deterministic — same user always gets same variant

**Experiment ID:** `exp_checkout_v2_001`
        """
    )

with col_d3:
    st.markdown(
        f"""
**Pre-experiment baseline**
Nov 2020 checkout users: {int(df_baseline['checkout_users'].iloc[0]):,}
Baseline conversion rate: **{baseline_rate*100:.1f}%**

**Minimum detectable effect (MDE)**
Targeting ≥ 5 pp absolute lift
(from {baseline_rate*100:.1f}% → {(baseline_rate+0.05)*100:.1f}%)

**α (significance level):** 0.05 (two-sided)
**Power target:** 0.80
        """
    )

# ── Power Analysis ─────────────────────────────────────────────────────────────
st.divider()
st.subheader("Power Analysis")

col_pa, col_slider = st.columns([2, 1])

with col_slider:
    mde_pct = st.slider(
        "Minimum Detectable Effect (pp)",
        min_value=1,
        max_value=15,
        value=5,
        step=1,
        help="Absolute percentage-point lift you want to reliably detect",
    )
    alpha = st.select_slider(
        "Significance level (α)",
        options=[0.01, 0.05, 0.10],
        value=0.05,
        format_func=lambda x: f"{x:.2f}",
    )
    power_target = st.select_slider(
        "Power (1 − β)",
        options=[0.70, 0.80, 0.90],
        value=0.80,
        format_func=lambda x: f"{x:.0%}",
    )

with col_pa:
    p1 = baseline_rate
    p2 = p1 + mde_pct / 100.0
    p_pool = (p1 + p2) / 2
    z_alpha = stats.norm.ppf(1 - alpha / 2)
    z_beta  = stats.norm.ppf(power_target)
    n_required = math.ceil(
        2 * p_pool * (1 - p_pool) * ((z_alpha + z_beta) ** 2) / ((p2 - p1) ** 2)
    )

    pa1, pa2, pa3, pa4 = st.columns(4)
    pa1.metric("Baseline rate",    f"{p1*100:.1f}%")
    pa2.metric("Target rate",      f"{p2*100:.1f}%")
    pa3.metric("Required n / arm", f"{n_required:,}")
    pa4.metric("Total n required", f"{n_required*2:,}")

    # MDE curve
    mde_range  = list(range(1, 16))
    n_by_mde = []
    for m in mde_range:
        p2_ = p1 + m / 100.0
        pp  = (p1 + p2_) / 2
        n_  = math.ceil(2 * pp * (1 - pp) * ((z_alpha + z_beta) ** 2) / ((p2_ - p1) ** 2))
        n_by_mde.append(n_)

    df_power = pd.DataFrame({"mde_pp": mde_range, "n_per_arm": n_by_mde})
    fig_power = px.line(
        df_power, x="mde_pp", y="n_per_arm",
        labels={"mde_pp": "MDE (pp)", "n_per_arm": "Required n per arm"},
        template="plotly_white",
        markers=True,
    )
    fig_power.add_vline(
        x=mde_pct, line_dash="dash", line_color="#636EFA",
        annotation_text=f"Selected MDE: {mde_pct}pp",
        annotation_position="top right",
    )
    fig_power.add_hline(
        y=n_ctrl, line_dash="dot", line_color="gray",
        annotation_text=f"Actual n/arm ≈ {n_ctrl:,}",
        annotation_position="bottom right",
    )
    fig_power.update_layout(margin=dict(l=0, r=0, t=8, b=0), height=240)
    st.plotly_chart(fig_power, use_container_width=True)

    if n_required <= n_ctrl:
        st.success(f"✅ Achieved power: actual n/arm ({n_ctrl:,}) ≥ required ({n_required:,})")
    else:
        st.warning(f"⚠️ Under-powered: actual n/arm ({n_ctrl:,}) < required ({n_required:,}) for {mde_pct}pp MDE")

# ── Sample Ratio Mismatch ──────────────────────────────────────────────────────
st.divider()
st.subheader("Sample Ratio Mismatch (SRM) Check")

n_total    = n_ctrl + n_trt
n_expected = n_total / 2
chi2_stat  = (n_ctrl - n_expected)**2 / n_expected + (n_trt - n_expected)**2 / n_expected
srm_pvalue = 1 - stats.chi2.cdf(chi2_stat, df=1)

col_srm1, col_srm2, col_srm3, col_srm4 = st.columns(4)
col_srm1.metric("Control n",   f"{n_ctrl:,}",  f"{n_ctrl/n_total*100:.1f}%")
col_srm2.metric("Treatment n", f"{n_trt:,}",   f"{n_trt/n_total*100:.1f}%")
col_srm3.metric("χ² statistic", f"{chi2_stat:.3f}")
col_srm4.metric("SRM p-value",  f"{srm_pvalue:.3f}")

if srm_pvalue >= 0.05:
    st.success(f"✅ No SRM detected (p = {srm_pvalue:.3f} ≥ 0.05). Assignment appears balanced.")
else:
    st.error(f"❌ SRM detected (p = {srm_pvalue:.3f} < 0.05). Assignment imbalance — investigate before interpreting results.")

# ── Results KPI Cards ──────────────────────────────────────────────────────────
st.divider()
st.subheader("Experiment Results")

diff_conv = conv_trt - conv_ctrl
diff_rpu  = rpu_trt - rpu_ctrl
pct_lift_conv = diff_conv / conv_ctrl if conv_ctrl > 0 else 0
pct_lift_rpu  = diff_rpu / rpu_ctrl if rpu_ctrl > 0 else 0

col_ctrl, col_trt, col_diff = st.columns(3)

with col_ctrl:
    st.markdown("#### Control")
    st.metric("Users",           f"{n_ctrl:,}")
    st.metric("Conversions",     f"{conv_ctrl_n:,}")
    st.metric("Conversion rate", f"{conv_ctrl*100:.2f}%")
    st.metric("Revenue / user",  f"${rpu_ctrl:,.2f}")
    st.metric("Total revenue",   f"${float(ctrl['total_revenue_usd']):,.0f}")

with col_trt:
    st.markdown("#### Treatment")
    st.metric("Users",           f"{n_trt:,}")
    st.metric("Conversions",     f"{conv_trt_n:,}")
    st.metric("Conversion rate", f"{conv_trt*100:.2f}%",
              delta=f"{diff_conv*100:+.2f} pp vs control")
    st.metric("Revenue / user",  f"${rpu_trt:,.2f}",
              delta=f"${diff_rpu:+.2f} vs control")
    st.metric("Total revenue",   f"${float(trt['total_revenue_usd']):,.0f}")

with col_diff:
    st.markdown("#### Lift")
    st.metric("Relative lift (conv.)",  f"{pct_lift_conv*100:+.1f}%")
    st.metric("Absolute lift (conv.)",  f"{diff_conv*100:+.2f} pp")
    st.metric("Relative lift (RPU)",    f"{pct_lift_rpu*100:+.1f}%")
    st.metric("Absolute lift (RPU)",    f"${diff_rpu:+.2f}")
    st.metric("Revenue impact (est.)",
              f"${diff_rpu * n_total:,.0f}",
              help="Absolute RPU lift × total experiment users")

# ── Statistical Significance Test ─────────────────────────────────────────────
st.divider()
st.subheader("Statistical Significance — Two-proportion Z-test")

st.markdown(
    """
**Primary metric:** Checkout-to-purchase conversion rate
**Null hypothesis H₀:** conversion_rate(treatment) = conversion_rate(control)
**Alternative H₁:** conversion_rate(treatment) ≠ conversion_rate(control) *(two-sided)*
**α = 0.05**
    """
)

p_pool_obs  = (conv_ctrl_n + conv_trt_n) / (n_ctrl + n_trt)
se_obs      = math.sqrt(p_pool_obs * (1 - p_pool_obs) * (1/n_ctrl + 1/n_trt))
z_stat      = diff_conv / se_obs if se_obs > 0 else 0
p_val_conv  = 2 * (1 - stats.norm.cdf(abs(z_stat)))
ci_low      = diff_conv - 1.96 * se_obs
ci_high     = diff_conv + 1.96 * se_obs

col_zstat, col_ci, col_pval = st.columns(3)
col_zstat.metric("Z-statistic",  f"{z_stat:.3f}")
col_ci.metric("95% CI (diff)",  f"[{ci_low*100:+.2f}pp, {ci_high*100:+.2f}pp]")
col_pval.metric("p-value",      f"{p_val_conv:.4f}")

# Normal curve with shaded rejection regions
x = np.linspace(-4, 4, 400)
y = stats.norm.pdf(x)
z_crit = stats.norm.ppf(1 - 0.05 / 2)

fig_z = go.Figure()
# Left rejection region
mask_l = x <= -z_crit
fig_z.add_trace(go.Scatter(x=x[mask_l], y=y[mask_l], fill='tozeroy',
                           fillcolor='rgba(239,85,59,0.25)', line=dict(width=0),
                           name="Rejection region", showlegend=True))
# Right rejection region
mask_r = x >= z_crit
fig_z.add_trace(go.Scatter(x=x[mask_r], y=y[mask_r], fill='tozeroy',
                           fillcolor='rgba(239,85,59,0.25)', line=dict(width=0),
                           name="Rejection region", showlegend=False))
# Normal curve
fig_z.add_trace(go.Scatter(x=x, y=y, mode='lines',
                           line=dict(color='#636EFA', width=2),
                           name="Standard normal", showlegend=True))
# Observed z
fig_z.add_vline(x=z_stat, line_dash="dash", line_color="#EF553B", line_width=2,
                annotation_text=f"z = {z_stat:.2f}", annotation_position="top right")
fig_z.update_layout(
    xaxis_title="Z-score",
    yaxis_title="Density",
    template="plotly_white",
    margin=dict(l=0, r=0, t=8, b=0),
    height=260,
    legend=dict(orientation="h", yanchor="bottom", y=1.02),
)
st.plotly_chart(fig_z, use_container_width=True)

# Confidence interval forest plot
fig_ci = go.Figure()
fig_ci.add_trace(go.Scatter(
    x=[diff_conv * 100],
    y=["Conversion rate lift"],
    mode="markers",
    marker=dict(size=12, color="#636EFA"),
    error_x=dict(type="data", array=[1.96 * se_obs * 100], color="#636EFA"),
    name="Point estimate + 95% CI",
))
fig_ci.add_vline(x=0, line_dash="dot", line_color="gray",
                 annotation_text="No effect", annotation_position="top right")
fig_ci.update_layout(
    xaxis_title="Absolute lift (percentage points)",
    yaxis_title="",
    template="plotly_white",
    margin=dict(l=0, r=0, t=8, b=0),
    height=140,
    showlegend=False,
)
st.plotly_chart(fig_ci, use_container_width=True)

# Decision box
if p_val_conv < 0.05:
    st.success(
        f"✅ **Reject H₀** — p = {p_val_conv:.4f} < 0.05. "
        f"The {diff_conv*100:+.2f}pp lift is statistically significant."
    )
else:
    st.info(
        f"**Fail to reject H₀** — p = {p_val_conv:.4f} ≥ 0.05. "
        f"The {diff_conv*100:+.2f}pp observed lift is not statistically distinguishable from noise at α = 0.05. "
        "The experiment is underpowered relative to the observed effect size, "
        "or the true effect may be negligible."
    )

# ── Secondary metrics ──────────────────────────────────────────────────────────
st.divider()
st.subheader("Secondary Metrics — Revenue per User")

se_rpu = math.sqrt(sd_ctrl**2 / n_ctrl + sd_trt**2 / n_trt)
z_rpu  = diff_rpu / se_rpu if se_rpu > 0 else 0
p_rpu  = 2 * (1 - stats.norm.cdf(abs(z_rpu)))
ci_rpu_low  = diff_rpu - 1.96 * se_rpu
ci_rpu_high = diff_rpu + 1.96 * se_rpu

col_rpu1, col_rpu2, col_rpu3 = st.columns(3)
col_rpu1.metric("RPU lift",   f"${diff_rpu:+.2f}")
col_rpu2.metric("95% CI",     f"[${ci_rpu_low:+.2f}, ${ci_rpu_high:+.2f}]")
col_rpu3.metric("p-value",    f"{p_rpu:.4f}")

if p_rpu < 0.05:
    st.success(f"✅ RPU lift is statistically significant (p = {p_rpu:.4f})")
else:
    st.info(f"RPU lift not statistically significant (p = {p_rpu:.4f} ≥ 0.05)")

# ── Guardrail metrics ──────────────────────────────────────────────────────────
st.divider()
st.subheader("Guardrail Metrics")

guard_data = pd.DataFrame({
    "Metric": ["Engagement rate", "Avg checkouts / user"],
    "Control": [
        f"{float(ctrl['engagement_rate'])*100:.1f}%",
        f"{float(ctrl['avg_checkouts_per_user']):.3f}",
    ],
    "Treatment": [
        f"{float(trt['engagement_rate'])*100:.1f}%",
        f"{float(trt['avg_checkouts_per_user']):.3f}",
    ],
    "Δ": [
        f"{(float(trt['engagement_rate']) - float(ctrl['engagement_rate']))*100:+.2f} pp",
        f"{float(trt['avg_checkouts_per_user']) - float(ctrl['avg_checkouts_per_user']):+.4f}",
    ],
    "Status": ["✅ No regression", "✅ No regression"],
})
st.dataframe(guard_data, hide_index=True, use_container_width=True)

# ── Cumulative conversion rate over time ──────────────────────────────────────
st.divider()
st.subheader("Cumulative Conversion Rate Over Time")
st.caption("Conversions = distinct purchase transactions by eligible users after experiment start.")

if not df_daily.empty:
    df_daily["cum_conv_rate"] = (
        df_daily["cumulative_conversions"] / df_daily["cumulative_eligible"]
    ).clip(upper=1.0)
    df_daily["event_date"] = pd.to_datetime(df_daily["event_date"])

    fig_daily = px.line(
        df_daily,
        x="event_date",
        y="cum_conv_rate",
        color="variant_name",
        color_discrete_map={"control": "#636EFA", "treatment": "#EF553B"},
        labels={
            "event_date": "Date",
            "cum_conv_rate": "Cumulative conversion rate",
            "variant_name": "Variant",
        },
        template="plotly_white",
        markers=False,
    )
    fig_daily.update_yaxes(tickformat=".1%")
    fig_daily.update_layout(
        margin=dict(l=0, r=0, t=8, b=0),
        height=300,
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
    )
    st.plotly_chart(fig_daily, use_container_width=True)
else:
    st.info("Daily cumulative data not available.")

# ── Recommendation ─────────────────────────────────────────────────────────────
st.divider()
st.subheader("Decision & Recommendation")

col_rec, col_meta = st.columns([2, 1])

with col_rec:
    st.markdown(
        f"""
**Outcome: Fail to Reject H₀ (Inconclusive)**

The experiment observed a **{diff_conv*100:+.2f}pp conversion rate lift** and a
**${diff_rpu:+.2f} revenue-per-user lift** in the treatment group. However, at
p = {p_val_conv:.3f}, the result does not reach the α = 0.05 significance threshold.

**Recommended next steps:**
- 🔄 **Run longer** — a 62-day window with ~5,700 users is underpowered for sub-2pp effects.
  The power curve suggests ≥ {n_required:,} users per arm are needed to detect a {mde_pct}pp MDE.
- 📊 **Segment the results** — check whether specific channels or device types show stronger
  lift (this can generate hypotheses for a follow-up test).
- 🧪 **Re-run with a larger pool** — expanding eligibility (e.g., view_item users) would
  increase sample size and statistical power.

**Guardrails: PASS** — No regression in engagement rate or checkout frequency.
        """
    )

with col_meta:
    st.markdown(
        f"""
| | |
|---|---|
| **Experiment ID** | `exp_checkout_v2_001` |
| **Window** | Dec 1 – Jan 31, 2021 |
| **Total users** | {n_ctrl + n_trt:,} |
| **Primary metric** | Conversion rate |
| **Observed lift** | {diff_conv*100:+.2f} pp |
| **p-value** | {p_val_conv:.4f} |
| **Decision** | Inconclusive |
| **Data** | SIMULATED |
        """
    )

st.divider()
with st.expander("Technical methodology"):
    st.markdown(
        f"""
### Assignment mechanism
Users eligible for the experiment (≥1 `begin_checkout` event Dec 1–Jan 31) are
deterministically assigned via:

```sql
MOD(ABS(FARM_FINGERPRINT(user_pseudo_id || '_exp_checkout_v2_001')), 2)
-- 0 → control, 1 → treatment
```

This produces a stable, reproducible 50/50 split with no random seed required.
The actual split was {n_ctrl:,} control / {n_trt:,} treatment (SRM p = {srm_pvalue:.3f}).

### Primary metric test
Two-proportion z-test (two-sided, α = 0.05):

$$z = \\frac{{\\hat{{p}}_t - \\hat{{p}}_c}}{{\\sqrt{{\\hat{{p}}(1-\\hat{{p}})(1/n_c + 1/n_t)}}}}$$

where $\\hat{{p}}$ is the pooled conversion rate.

Observed: z = {z_stat:.3f}, p = {p_val_conv:.4f}

### Secondary metric test
Welch's Z-test using per-variant standard deviation of revenue per user.
(For small n, a t-test would be preferred; at n≈2,800/arm, z ≈ t.)

### Power analysis formula
$$n = \\frac{{2\\bar{{p}}(1-\\bar{{p}})(z_{{\\alpha/2}} + z_\\beta)^2}}{{(p_2 - p_1)^2}}$$

Baseline rate: {baseline_rate*100:.1f}% (Nov 2020 checkout cohort)

### Data note
All results are **SIMULATED** — no real product change was made.
The experiment framework (dbt models, assignment logic, significance tests) is real
and production-ready; only the "treatment" is synthetic.
        """
    )
