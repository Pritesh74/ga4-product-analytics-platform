# Portfolio Screenshot Guide

Screenshots are stored in `screenshots/portfolio/final/` and are ready to use
in a portfolio PDF, case study slide deck, or GitHub README.

All screenshots were captured from the live Streamlit app at 1440×900px using
a headless Chromium browser with BigQuery cache warmed before capture.

---

## Best 5 Screenshots for a Portfolio PDF

| Order | File | Dashboard Page | Caption |
|---|---|---|---|
| **1 — Cover** | `01_experiment_demo.png` | Experiment Demo | "Simulated A/B testing framework: power analysis, SRM check, and two-proportion z-test on real GA4-modeled data" |
| **2** | `02_executive_overview.png` | Executive Overview | "$360K revenue · 360K sessions · 270K users — real GA4 data, Nov–Jan 2021" |
| **3** | `03_funnel.png` | Purchase Funnel | "79.5% drop at View Item → Add to Cart identified as primary optimization opportunity" |
| **4** | `04_ltv_channel.png` | Customer LTV | "Referral drives $3.84 revenue/user — 4× higher than organic search ($0.94)" |
| **5** | `05_data_quality.png` | Data Quality | "128 dbt tests across 4 model layers — 0 errors, 2 expected warnings" |

**Backup:** `06_geography_backup.png` — Revenue choropleth across 108 countries.
Use if you want a visually impactful map or need a 6th page.

---

## Recommended PDF Layout

```
Page 1 (cover)  →  01_experiment_demo.png
Page 2          →  02_executive_overview.png
Page 3          →  03_funnel.png
Page 4          →  04_ltv_channel.png
Page 5          →  05_data_quality.png
(Optional 6)    →  06_geography_backup.png
```

**Why lead with the experiment page?**
The A/B testing framework is the most technically differentiated component.
Leading with it signals immediately that this is more than a SQL or BI project —
it demonstrates end-to-end experimentation competency.

---

## Naming Convention

```
01_experiment_demo.png       → Experiment Demo page
02_executive_overview.png    → Executive Overview page
03_funnel.png                → Purchase Funnel page
04_ltv_channel.png           → Customer LTV / Channel page
05_data_quality.png          → Data Quality page
06_geography_backup.png      → Geography Performance page (backup)
```

Numbers prefix ensures alphabetical sort matches portfolio order in all file browsers.

---

## Folder Reference

| Folder | Contents | Git status |
|---|---|---|
| `screenshots/dashboard/raw/` | Full-page Playwright captures (1440×900) | Excluded from git |
| `screenshots/dashboard/edited/` | Same captures, committed reference | Committed |
| `screenshots/portfolio/raw/` | Pre-edit captures for manual crop (if needed) | Excluded from git |
| `screenshots/portfolio/final/` | Final portfolio-ready images | Committed |
| `screenshots/github/` | Images for embedding in README.md | Committed |

---

## Capture Instructions (if re-capturing)

```bash
# 1. Start the app
./scripts/run_app.sh          # app runs on http://localhost:8501

# 2. Run the capture script (two-pass: warms cache, then screenshots)
source .venv/bin/activate
python3 scripts/capture_screenshots.py

# 3. Review screenshots/dashboard/raw/
# 4. Copy clean captures to portfolio/final/
cp screenshots/dashboard/raw/*.png screenshots/portfolio/final/
```

If re-capturing manually in a browser:
- Use **1440 × 900px** window or full-screen with sidebar visible
- Let each page **fully load** before capturing (BigQuery queries: 2–5 sec first load, instant after)
- Use **light theme** (Streamlit default) — cleaner on white portfolio backgrounds
- On macOS: `Cmd+Shift+4` for region capture, or `Cmd+Shift+3` for full screen

---

## Theme and Presentation Notes

**Light theme (default):** Recommended for portfolio PDFs and case study slides.
Professional, clean, prints well on white backgrounds.

**Dark theme:** Higher visual impact for web/screen presentations, but harder to
read printed. Switch via Streamlit menu → Settings → Theme if desired.

**Sidebar visibility:** Keep the sidebar visible in all screenshots — it shows the
full 8-page navigation structure, demonstrating project scope at a glance.

---

## Note on the Experiment Page

The **Experiment Demo** screenshot shows a simulated A/B test and is clearly labeled:

- A yellow warning banner is visible at the top of the page
- The subtitle reads "Simulated A/B test"
- The source dataset is labeled `ga4_experiments.exp_simulated_results`

This is the correct and honest way to present portfolio experimentation work.
The GA4 event data underlying the experiment (purchases, sessions, checkout events)
is real — only the treatment group assignment is synthetic (deterministic hash split).

When captioning this screenshot in a portfolio:
> "Simulated A/B testing framework built on real GA4 e-commerce data.
> Demonstrates: eligibility design, deterministic assignment, power analysis,
> SRM check, two-proportion z-test, and CI visualization."
