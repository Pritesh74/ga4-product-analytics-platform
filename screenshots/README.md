# Screenshots

This folder contains dashboard screenshots for portfolio and GitHub use.

---

## Folder Structure

```
screenshots/
  dashboard/
    raw/        Full-browser captures from the live Streamlit app (local only, not committed)
    edited/     Cropped, consistent-size versions ready for docs and GitHub
  github/       Images embedded directly in README.md (1200px wide recommended)
  portfolio/
    raw/        Pre-crop captures for portfolio PDF (local only, not committed)
    final/      Finished portfolio images — committed, ready to share
```

> `dashboard/raw/` and `portfolio/raw/` are excluded from git (see `.gitignore`).
> Only `dashboard/edited/`, `github/`, and `portfolio/final/` are committed.

---

## Naming Convention

```
01_experiment_demo.png
02_executive_overview.png
03_funnel.png
04_ltv_channel.png
05_data_quality.png
06_geography_backup.png
```

Use the same names in all folders so it's clear which capture corresponds to which page.

---

## What Goes Where

| Filename | Dashboard Page | URL path |
|---|---|---|
| `01_experiment_demo.png` | Experiment Demo | `http://localhost:8501/experiment_demo` |
| `02_executive_overview.png` | Executive Overview | `http://localhost:8501/executive_overview` |
| `03_funnel.png` | Funnel | `http://localhost:8501/funnel` |
| `04_ltv_channel.png` | LTV | `http://localhost:8501/ltv` |
| `05_data_quality.png` | Data Quality | `http://localhost:8501/data_quality` |
| `06_geography_backup.png` | Geography | `http://localhost:8501/geography` |

---

## Recommended Capture Order

1. **Start the app** — `./scripts/run_app.sh` → open `http://localhost:8501`
2. Let each page fully load before capturing (BigQuery queries take 2–4 seconds per tab)
3. Use a **1440 × 900px** browser window minimum for consistent sizing
4. Capture in this order to match the portfolio narrative flow:

| Order | Page | Folder target | Notes |
|---|---|---|---|
| 1st | Experiment Demo | `dashboard/raw/` | Scroll down to show power curve AND z-test curve in one capture, or take two crops |
| 2nd | Executive Overview | `dashboard/raw/` | Capture the full KPI row + revenue chart |
| 3rd | Funnel | `dashboard/raw/` | Make sure the Funnel chart + drop-off table are both visible |
| 4th | LTV / Channel | `dashboard/raw/` | Revenue per user grouped bar is the key visual |
| 5th | Data Quality | `dashboard/raw/` | Row count chart + test results bar side by side |
| 6th | Geography (backup) | `dashboard/raw/` | Choropleth map is the visual anchor |

---

## Best 5 Screenshots for Portfolio PDF

| # | File | Caption |
|---|---|---|
| **1 (cover)** | `01_experiment_demo.png` | "End-to-end A/B testing framework — simulated on real GA4-modeled data. Includes power analysis, SRM check, and two-proportion z-test." |
| **2** | `02_executive_overview.png` | "Executive dashboard: $360K revenue, 360K sessions, 270K users — real GA4 data, Nov–Jan 2021." |
| **3** | `03_funnel.png` | "Purchase funnel analysis: 79.5% drop at View→Add to Cart is the primary optimization opportunity." |
| **4** | `04_ltv_channel.png` | "LTV by acquisition channel: referral drives $3.84 revenue/user — 4× higher than organic search." |
| **5** | `05_data_quality.png` | "Data quality dashboard: 128 dbt tests, 0 errors, 2 expected warnings across 4 model layers." |

**Backup:** `06_geography_backup.png` — "Country-level conversion and revenue choropleth across 59 markets."

---

## Portfolio PDF Layout Guidance

- **Cover image:** `01_experiment_demo.png` — leads with the most technically differentiated section
- **Page size:** Use full-bleed images at 1200×700px for a clean slide-deck look
- **Theme:** Streamlit's default light theme is clean and professional for screenshots
- **Caption rule:** always include one of:
  - "Source: real GA4 public e-commerce data (Google Merchandise Store, Nov–Jan 2021)"
  - "SIMULATED experiment — deterministic hash assignment on real GA4-modeled data"

---

## Note on the Experiment Page

The **Experiment Demo** page is labeled as simulated throughout:
- A yellow warning banner is displayed at the top of the page
- Each section explicitly states results are from a synthetic user split
- The underlying GA4 event data (purchases, sessions) is real
- Only the treatment group assignment is synthetic (FARM_FINGERPRINT hash)

This is the correct way to represent a portfolio A/B testing demonstration.
