# Dashboard Specification

> Documents what each Streamlit page actually contains (as built).
> Source file for each page is `app/pages/<name>.py`.

---

## Page 1 — Executive Overview (`01_executive_overview.py`)

**Purpose:** Give a hiring manager or executive a 30-second read on business health.

| Component | Type | Data Source | Notes |
|---|---|---|---|
| Total Revenue | KPI card | `fct_purchases` | $360,837 |
| Total Sessions | KPI card | `fct_sessions` | 360,129 |
| Unique Users | KPI card | `fct_sessions` | 270,154 |
| Session CVR | KPI card | `fct_sessions` | 1.35% |
| AOV | KPI card | `fct_purchases` | $81.05 |
| Daily revenue area chart | Area chart with dual y-axis | `fct_purchases` | Revenue + orders |
| Daily sessions + CVR | Line chart | `fct_sessions` | Sessions + conversion rate |
| Revenue by channel | Horizontal bar | `mart_ltv_by_channel` | Sorted by revenue |
| Top product categories | Horizontal bar | `fct_product_views` | Top 10 by views |

---

## Page 2 — Funnel (`02_funnel.py`)

**Purpose:** Show exactly where users drop out of the purchase funnel.

| Component | Type | Data Source | Notes |
|---|---|---|---|
| Funnel visualization | `go.Funnel` | `fct_*` (5 tables) | Period-level, unique users per stage |
| Drop-off rate table | Table | Computed from funnel | % and absolute drop per step |
| Daily funnel trend | Area chart | `mart_daily_funnel` | All 5 stages stacked |
| Biggest drop-off callout | Metric | Computed | View Item → Add to Cart: −79.5% |

**Key insight:** Add-to-cart is the steepest drop at 79.5%; checkout abandonment is 54.5%.

---

## Page 3 — Retention (`03_retention.py`)

**Purpose:** Show cohort purchase return rate as a heatmap matrix.

| Component | Type | Data Source | Notes |
|---|---|---|---|
| Cohort retention heatmap | `go.Heatmap` | `mart_retention_cohorts` | Months 0–2, color = retention % |
| Cohort size and rates table | Table | `mart_retention_cohorts` | Raw numbers |
| Data sparsity note | Info box | Static | Explains 3-month dataset window |

**Note on sparsity:** The dataset spans only Nov 2020 – Jan 2021 (3 months), so the
cohort matrix has at most 2 follow-up periods. This is documented on the page.
Month-0 rates (1–2%) represent the % of cohort members who purchased in their first month,
not a session-level conversion rate.

---

## Page 4 — LTV (`04_ltv.py`)

**Purpose:** Show lifetime value and revenue distribution by acquisition channel.

| Component | Type | Data Source | Notes |
|---|---|---|---|
| Revenue per user vs per purchaser | Grouped bar | `mart_ltv_by_channel` | Side-by-side comparison |
| Purchase rate by channel | Horizontal bar | `mart_ltv_by_channel` | % of channel users who purchased |
| Total revenue by channel | Horizontal bar | `mart_ltv_by_channel` | Absolute revenue |
| Avg orders per purchaser | Table | `mart_ltv_by_channel` | Repeat purchase intensity |

**Key insight:** Referral drives $3.84 revenue/user vs $0.94 for organic — 4× LTV gap.

---

## Page 5 — Channel & Device (`05_channel_device.py`)

**Purpose:** Compare conversion and revenue across traffic sources and device types.

| Component | Type | Data Source | Notes |
|---|---|---|---|
| Channel sessions, CVR, revenue | 3-panel metric grid | `fct_sessions` | Engagement + conversion + revenue |
| Device KPI cards | 3 metric cards | `mart_device_performance` | Desktop / Mobile / Tablet |
| Browser conversion chart | Horizontal bar | `mart_device_performance` | Top 15 browsers |
| Channel table | `st.dataframe` | `fct_sessions` | Full channel breakdown |

Layout: `st.tabs(["Channel", "Device"])` — channel tab is default.

**Key insight:** Mobile CVR (1.39%) slightly exceeds desktop (1.32%) — no mobile deficit.

---

## Page 6 — Geography (`06_geography.py`)

**Purpose:** Identify over- and under-performing markets.

| Component | Type | Data Source | Notes |
|---|---|---|---|
| Continent filter | `st.multiselect` | `mart_geo_performance` | Filters all charts |
| KPI cards | 4 metric cards | Computed | Countries, sessions, top-revenue country, top-CVR country |
| Choropleth world map | `px.choropleth` | `mart_geo_performance` | Toggle: Revenue / Sessions / CVR |
| Top 15 countries by revenue | Horizontal bar | `mart_geo_performance` | Color gradient |
| Top 15 countries by CVR | Horizontal bar | `mart_geo_performance` | Min 100 sessions filter |
| Full country data table | Collapsible | `mart_geo_performance` | All columns |

**Key insight:** Japan leads CVR at 1.61%; Canada (1.45%) and Spain (1.48%) also outperform US (1.34%).

---

## Page 7 — Experiment Demo (`07_experiment_demo.py`)

> ⚠️ **SIMULATED EXPERIMENT** — clearly labeled throughout.
> No real product change was made. Results demonstrate A/B testing methodology on a synthetic split.

| Component | Type | Data Source | Notes |
|---|---|---|---|
| Simulation warning banner | `st.warning` | Static | Prominent top-of-page disclosure |
| Experiment design | 3-column layout | Static + `exp_simulated_results` | Hypothesis, window, eligibility, assignment |
| Pre-experiment baseline | Static metric | `load_experiment_baseline()` | Nov 2020: 36.3% baseline CVR |
| Power analysis curve | Interactive line chart | Computed (scipy) | MDE slider 1–15pp, α selector, power selector |
| SRM chi-square check | Metric cards | Computed | χ² = 0.65, p = 0.42 → no imbalance |
| Results KPI cards | 3-column layout | `exp_simulated_results` | Per-variant + absolute/relative lift |
| Z-test normal curve | `go.Figure` | Computed (scipy) | Rejection regions shaded, observed z marked |
| CI forest plot | `go.Figure` | Computed (scipy) | Point estimate + 95% error bar |
| Decision box | `st.info` / `st.success` | Computed | Fail to reject H₀ at α = 0.05 |
| Revenue per user Z-test | Metric cards | `exp_simulated_results` | Welch's Z |
| Guardrail metrics table | `st.dataframe` | `exp_simulated_results` | Engagement rate, avg checkouts |
| Cumulative conversion chart | `px.line` | `load_experiment_daily()` | Running rate by variant |
| Recommendation | 2-column layout | Computed | Inconclusive decision + next steps |
| Technical methodology | Collapsible | Static | Full formula derivation with LaTeX |

**Experiment results:**
- Control: 2,817 users · 52.1% CVR · $37.32 RPU
- Treatment: 2,878 users · 53.1% CVR · $39.17 RPU
- Z = 0.74 · p = 0.46 → Inconclusive (underpowered for this effect size)

---

## Page 8 — Data Quality (`08_data_quality.py`)

**Purpose:** Show pipeline health and build trust in the data.

| Component | Type | Data Source | Notes |
|---|---|---|---|
| Total mart tables | KPI card | `load_model_inventory()` | 11 |
| Total rows across marts | KPI card | `load_model_inventory()` | ~1.1M |
| Earliest / Latest data date | KPI cards | `load_model_inventory()` | Nov 1, 2020 – Jan 31, 2021 |
| dbt test summary | Table + stacked bar | Embedded (from last build) | Per-layer breakdowns |
| Model inventory bar chart | Horizontal bar | `load_model_inventory()` | Color-coded by layer |
| Full model inventory table | `st.dataframe` | `load_model_inventory()` | Model, layer, rows, dates, description |
| Known data quality notes | 2-column markdown | Static | 2 warnings explained + 3 passing checks |
| Pipeline architecture diagram | Collapsible | Static | Full ASCII diagram |

---

## Real vs Simulated — Page-by-Page

| Page | Data | Label |
|---|---|---|
| Executive Overview | Real GA4 events | None needed — all real |
| Funnel | Real GA4 events | None needed |
| Retention | Real GA4 events | Note about 3-month window sparsity |
| LTV | Real GA4 events | None needed |
| Channel & Device | Real GA4 events | None needed |
| Geography | Real GA4 events | None needed |
| Experiment Demo | Simulated assignment / real outcomes | **Prominent warning banner + inline labels** |
| Data Quality | Real mart data + hardcoded test results | Note that experiment section is simulated |
