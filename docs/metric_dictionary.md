# Metric Dictionary

> All metrics are derived from `bigquery-public-data.ga4_obfuscated_sample_ecommerce`
> (Nov 1, 2020 – Jan 31, 2021) unless otherwise noted.
>
> Computed values reflect the full 92-day dataset period.
>
> ⚠️ Metrics in the **Experiment** section are based on a **simulated** assignment —
> no real A/B test was conducted.

---

## Session & Traffic Metrics

| Metric | Definition | Source Model | Computed Value |
|---|---|---|---|
| **Sessions** | COUNT DISTINCT (user_pseudo_id, ga_session_id) | `fct_sessions` | 360,129 |
| **Unique Users** | COUNT DISTINCT user_pseudo_id | `fct_sessions` | 270,154 |
| **Engaged Sessions** | Sessions where `is_engaged = true` | `fct_sessions` | — |
| **Engagement Rate** | Engaged Sessions / Sessions | `fct_sessions` | ~81.7% (desktop) |
| **Session CVR** | Purchasing sessions / Total sessions | `fct_sessions` | 1.35% |
| **Avg Session Duration** | Mean (session_end_ts − session_start_ts) in seconds | `fct_sessions` | — |

---

## Funnel Metrics

Funnel is computed at user level (distinct users per stage) for the full period.

| Stage | Unique Users | Drop-off to Next Stage |
|---|---|---|
| Session Start | 270,154 | — |
| View Item | 61,252 | −77.3% |
| Add to Cart | 12,545 | −79.5% ← steepest |
| Begin Checkout | 9,715 | −22.6% |
| Purchase | 4,419 | −54.5% |

| Metric | Definition | Source Model |
|---|---|---|
| **Product Views** | COUNT of `view_item` events | `fct_product_views` |
| **View → Cart Rate** | Users with add_to_cart / Users with view_item | Computed from `fct_*` tables |
| **Cart → Checkout Rate** | Users with begin_checkout / Users with add_to_cart | Computed from `fct_*` tables |
| **Checkout → Purchase Rate** | Users with purchase / Users with begin_checkout | Computed from `fct_*` tables |
| **Overall Funnel CVR** | Purchasing users / Session start users | Computed from `fct_*` tables |
| **Step Drop-off %** | 1 − (next_stage_users / current_stage_users) | `mart_daily_funnel` |

---

## Revenue Metrics

| Metric | Definition | Source Model | Computed Value |
|---|---|---|---|
| **Gross Revenue** | SUM(purchase_revenue_usd) where transaction_id IS NOT NULL | `fct_purchases` | $360,837 |
| **Total Orders** | COUNT DISTINCT transaction_id | `fct_purchases` | 4,452 |
| **Average Order Value (AOV)** | Gross Revenue / Total Orders | `fct_purchases` | $81.05 |
| **Revenue per User (RPU)** | Total Revenue / Unique Users | `mart_ltv_by_channel` | Varies by channel |
| **Revenue per Session** | Total Revenue / Sessions | `fct_sessions` | ~$1.00 |
| **LTV (observed)** | Cumulative revenue per user_pseudo_id over dataset period | `mart_ltv_by_channel` | $3.84 referral · $0.94 organic |

> **Note:** 23 purchase events have a null `transaction_id` (known GA4 sample data gap).
> These are included in session revenue totals but excluded from order-count and AOV calculations.

---

## Retention Metrics

Retention is measured as the % of cohort members who made a purchase in month N
after their acquisition month. Dataset spans only 3 calendar months, so retention
data is sparse by design.

| Cohort Month | Cohort Size (all users) | Month 0 Purchasers | Month 0 Rate | Month 1 Rate | Month 2 Rate |
|---|---|---|---|---|---|
| Nov 2020 | 79,421 | 1,532 | 1.93% | 0.58% | 0.12% |
| Dec 2020 | 99,664 | 1,518 | 1.52% | 0.15% | — |
| Jan 2021 | 91,069 | 821 | 0.90% | — | — |

| Metric | Definition | Source Model |
|---|---|---|
| **Cohort Month** | `DATE_TRUNC(first_seen_date, MONTH)` for each user | `dim_users` |
| **Month N Retention Rate** | Purchasing users in cohort_month + N / cohort_size | `mart_retention_cohorts` |
| **Repeat Purchase Rate** | Users with ≥2 lifetime orders / All purchasers | `dim_users` | **11.4%** (502 / 4,400) |

---

## Channel & LTV Metrics

Channel is assigned at first touch using `traffic_source.medium` from the first GA4 event.

| Channel | Users | Revenue | Revenue per User | Share of Revenue |
|---|---|---|---|---|
| referral | 55,495 | $213,179 | $3.84 | 59.1% |
| organic_search | 100,518 | $94,158 | $0.94 | 26.1% |
| direct | 56,531 | $24,387 | $0.43 | 6.8% |
| other | 44,579 | $24,022 | $0.54 | 6.7% |
| paid_search | 13,031 | $6,419 | $0.49 | 1.8% |

| Metric | Definition | Source Model |
|---|---|---|
| **Channel Group** | Medium-based classification (organic_search, paid_search, email, referral, social, direct, other) | `dim_users`, `fct_sessions` |
| **Channel CVR** | Purchasers from channel / Users from channel | `mart_ltv_by_channel` |
| **Channel LTV** | Total revenue from channel / Users from channel | `mart_ltv_by_channel` |
| **Revenue per Converter** | Total revenue / Purchasing users | `mart_ltv_by_channel` |

---

## Device Metrics

| Device | Sessions | Session CVR | Revenue per Session |
|---|---|---|---|
| desktop | 208,942 | 1.32% | $1.00 |
| mobile | 143,185 | 1.39% | $1.03 |
| tablet | 8,002 | 1.30% | $0.82 |

---

## Geography Metrics (Top 8 by Revenue)

| Country | Sessions | Revenue | Session CVR |
|---|---|---|---|
| United States | 158,155 | $160,573 | 1.34% |
| India | 33,769 | $34,986 | 1.33% |
| Canada | 26,824 | $32,799 | 1.45% |
| United Kingdom | 11,327 | $11,458 | 1.33% |
| Spain | 6,667 | $7,681 | 1.48% |
| France | 7,162 | $6,650 | 1.42% |
| China | 6,258 | $6,623 | 1.28% |
| Japan | 4,732 | $5,752 | **1.61%** ← highest CVR |

---

## Experiment Metrics

> ⚠️ All values below are from a **simulated** demonstration experiment.
> No real A/B test was conducted. The assignment mechanism and statistical tests
> are real and production-ready; only the treatment condition is synthetic.

**Experiment:** `exp_checkout_v2_001` — "Checkout UX v2"
**Window:** Dec 1, 2020 – Jan 31, 2021
**Eligibility:** Users with ≥1 `begin_checkout` event in window

| Metric | Control | Treatment | Δ |
|---|---|---|---|
| Eligible users | 2,817 | 2,878 | +61 (SRM p = 0.42 ✅) |
| Conversions | 1,468 | 1,528 | +60 |
| **Conversion rate** | **52.1%** | **53.1%** | **+1.0 pp** |
| Revenue per user | $37.32 | $39.17 | +$1.85 |
| Engagement rate | 81.7% | 81.5% | −0.2 pp (guardrail ✅) |

| Metric | Definition | Source Model |
|---|---|---|
| **Assignment** | `MOD(ABS(FARM_FINGERPRINT(user_pseudo_id \|\| salt)), 2)` | `exp_simulated_assignment` |
| **Conversion Rate per Variant** | Purchasing users / Assigned users, by variant | `exp_simulated_results` |
| **Relative Lift** | (treatment CVR − control CVR) / control CVR | Computed in `07_experiment_demo.py` |
| **Absolute Lift** | treatment CVR − control CVR | Computed in `07_experiment_demo.py` |
| **Z-statistic** | (p̂_t − p̂_c) / SE_pooled | Computed in `07_experiment_demo.py` |
| **P-value** | Two-proportion z-test, two-sided, α = 0.05 | **0.46** (inconclusive) |
| **Statistical Power** | Prospective power at assumed MDE, computed via interactive slider | `07_experiment_demo.py` |
| **SRM p-value** | Chi-square test of 50/50 balance | **0.42** (no imbalance) |
| **Pre-experiment baseline CVR** | Nov 2020 checkout users who purchased | **36.3%** |

---

## Data Quality Metrics

| Metric | Definition | Source |
|---|---|---|
| **Model row count** | `COUNT(*)` per mart table | `08_data_quality.py` → live BQ query |
| **Date range** | MIN/MAX event_date per mart table | `08_data_quality.py` → live BQ query |
| **dbt test pass rate** | Tests passed / total tests per layer | `08_data_quality.py` → hardcoded from last run |
| **Null rate** | % NULL values in key columns | dbt `not_null` tests |

---

## Column Naming Conventions

| Suffix | Meaning |
|---|---|
| `_key` | Surrogate key (hashed, stable across rebuilds) |
| `_ts` | Timestamp (UTC) |
| `_date` | DATE type (no time component) |
| `_usd` | Monetary value in US dollars |
| `is_*` | Boolean flag |
| `has_*` | Boolean flag (event-level: did this session contain X?) |
| `total_*` | Aggregated count or sum |
| `n_*` | Count (experiment metrics) |
