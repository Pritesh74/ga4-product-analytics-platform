# Executive Summary — GA4 E-commerce Analytics

**Period:** November 1, 2020 – January 31, 2021 (92 days)
**Data source:** Google Merchandise Store · `bigquery-public-data.ga4_obfuscated_sample_ecommerce`
**Prepared:** April 2026
**Model version:** dbt build with 18 models, 128 tests, 0 errors

> **Note:** This document is a completed example showing how this analytics
> platform's outputs would be packaged for a business audience.
> All findings below are real computed values from the GA4 dataset.
> The experiment section is clearly labeled as simulated.

---

## Business Snapshot

| KPI | Value | Context |
|---|---|---|
| Gross Revenue | $360,837 | 92-day period, 4,452 orders |
| Average Order Value | $81.05 | Per distinct transaction |
| Sessions | 360,129 | Unique user-session pairs |
| Unique Users | 270,154 | Distinct `user_pseudo_id` values |
| Session Conversion Rate | 1.35% | Purchasing sessions / total sessions |
| Overall Funnel CVR | 1.63% | Purchasing users / unique users |
| Repeat Purchase Rate | 11.4% | 502 of 4,400 buyers returned |

---

## Key Findings

### 1. Funnel — Largest Drop-off is at Product Discovery

The steepest funnel drop-off occurs between **View Item and Add to Cart: −79.5%**.
Only 12,545 of 61,252 users who viewed a product added one to their cart.

| Stage | Users | Drop-off |
|---|---|---|
| Session Start | 270,154 | — |
| View Item | 61,252 | −77.3% |
| **Add to Cart** | **12,545** | **−79.5% ← opportunity** |
| Begin Checkout | 9,715 | −22.6% |
| Purchase | 4,419 | −54.5% |

**Recommendation:** The 79.5% view-to-cart drop is the primary conversion lever.
Improving product page experience, social proof, or price presentation could
meaningfully move the overall funnel CVR. Checkout abandonment (54.5%) is the
secondary opportunity.

---

### 2. Channel Performance — Referral Drives Disproportionate Revenue

Referral traffic represents 20% of users but generates **59% of total revenue**
at $3.84 revenue per user — 4× higher than organic search ($0.94 RPU).

| Channel | Users | Revenue | RPU |
|---|---|---|---|
| **Referral** | 55,495 | $213,179 | **$3.84** |
| Organic Search | 100,518 | $94,158 | $0.94 |
| Direct | 56,531 | $24,387 | $0.43 |
| Other | 44,579 | $24,022 | $0.54 |
| Paid Search | 13,031 | $6,419 | $0.49 |

**Recommendation:** Investigate which specific referral sources drive high-LTV users.
Invest in expanding those referral partnerships. Paid search ($0.49 RPU) is acquiring
users at below-organic LTV and warrants creative or targeting review.

---

### 3. Retention — Dataset Window Limits Cohort Depth

With only 92 days of data, the cohort matrix has at most 2 follow-up months.
The November cohort shows:
- Month 0 (Nov): 1.93% of users purchased — 1,532 of 79,421
- Month 1 (Dec): 0.58% returned — 457 of 79,421
- Month 2 (Jan): 0.12% returned — 95 of 79,421

Overall, **11.4% of purchasers made a second purchase** within the dataset window
(502 of 4,400 buyers). This is the repeat purchase rate, not the traditional
month-N cohort retention (which would be tracked over a longer window in production).

**Recommendation:** A longer dataset window (6–12 months) would give more actionable
cohort retention curves. Focus near-term retention efforts on the first 30 days
post-purchase, where the re-engagement rate appears highest.

---

### 4. Device & Geography — Mobile is Not a Problem; Japan Stands Out

**Device:**
Mobile CVR (1.39%) is slightly above desktop (1.32%) — there is no mobile experience
deficit. Tablet has the lowest CVR (1.30%) but represents only 2% of sessions.

**Geography:**
- United States: 44% of sessions, 44.5% of revenue ($160,573) — revenue share matches traffic share
- Japan: highest CVR at 1.61% on 4,732 sessions — $5,752 revenue (small but efficient)
- Canada and Spain both outperform US conversion rate (1.45% and 1.48% respectively)
- China: 1.28% CVR — slightly below average; potential UX or payment friction

**Recommendation:** Japan's high CVR suggests strong purchase intent; consider whether
additional marketing investment there would be ROI-positive. Canada's 1.45% CVR on
26,824 sessions is an efficient market worth scaling.

---

## Experiment Results

> ⚠️ The following section describes a **simulated** A/B experiment built on top of
> the GA4 data as a portfolio methodology demonstration. No real product change was made.
> The statistical framework and significance test are real; the treatment is synthetic.

**Experiment:** "Checkout UX v2" (`exp_checkout_v2_001`)
**Window:** December 1, 2020 – January 31, 2021
**Eligibility:** 5,695 users with ≥1 begin_checkout event
**Assignment:** Deterministic 50/50 FARM_FINGERPRINT hash split

| | Control | Treatment |
|---|---|---|
| Users | 2,817 | 2,878 |
| Conversions | 1,468 | 1,528 |
| Conversion Rate | 52.1% | 53.1% |
| Revenue per User | $37.32 | $39.17 |
| Z-statistic | — | 0.74 |
| P-value | — | 0.46 |
| Decision | — | **Fail to reject H₀** |

**Interpretation (simulated):** The experiment observed a +1.0pp conversion rate lift and
+$1.85 revenue per user in the treatment group. However, with p = 0.46 (>> 0.05),
the result is not statistically significant. The experiment is underpowered: detecting a
~1pp effect at the observed baseline (~52%) would require roughly 40,000+ users per arm
at α = 0.05 and 80% power. With only ~2,800 per arm, the test cannot distinguish signal
from noise at this effect size.

**Recommended action:** Extend the experiment window or expand the eligible user pool
before drawing conclusions. No product decision should be made on this result.

---

## Limitations & Assumptions

- `user_pseudo_id` is a device-level identifier; one person using multiple devices may appear as multiple users.
- Traffic source attribution is **first-touch only** (`traffic_source` RECORD on user, set at first event).
- Revenue figures are in USD as reported by the GA4 `purchase` event parameter.
- Dataset period is Nov 2020 – Jan 2021 (holiday season bias; not representative of year-round behavior).
- 23 purchase events have null `transaction_id` — these are excluded from order count and AOV but included in session revenue totals.
- Experiment assignment is simulated via deterministic hashing — not a historical live test.

---

## Appendix — Data Pipeline

Full technical details in [`docs/architecture.md`](architecture.md).

The pipeline uses:
- **BigQuery** for all storage and compute
- **dbt Core 1.8** for transformation (18 models, 128 tests)
- **Streamlit + Plotly** for interactive visualization
- **scipy** for statistical testing

Authentication uses Application Default Credentials (ADC/oauth) — no service account
key files stored anywhere in the codebase.
