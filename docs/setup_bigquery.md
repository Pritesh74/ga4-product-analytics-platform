# BigQuery Setup Guide

> **Sandbox-first:** This guide uses BigQuery Sandbox (no billing required) and
> Application Default Credentials (ADC) via the `gcloud` CLI.
> No service account key file is needed anywhere.

**Time to complete:** ~20 minutes (most of that is waiting for `pip install`)

---

## Cost Profile

All BigQuery usage stays well within the free tier:

| Operation | Bytes scanned | Free tier impact |
|---|---|---|
| `dbt build --select staging` | ~100–200 MB | Negligible |
| `dbt build --select intermediate+marts` | ~500 MB–1 GB | Minimal |
| Full `dbt build` (all layers) | ~1–1.5 GB | Well within 10 GB/mo free |
| Dashboard tab load (per query) | ~10–50 MB | Negligible |

Staging and intermediate models are **views** — they scan bytes only when a downstream
model or dashboard query touches them. Mart models are **tables** — they pay the scan
cost once at build time and serve all future dashboard queries from cached storage.

---

## Prerequisites

| Tool | Version | Install |
|---|---|---|
| Python | 3.9+ | `pyenv install 3.11` or system Python |
| `gcloud` CLI | Latest | [cloud.google.com/sdk/docs/install](https://cloud.google.com/sdk/docs/install) |
| Git | Any | Pre-installed on macOS / Linux |

---

## Step 1 — Create a GCP Project (Sandbox)

1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. **Select a project → New Project**
3. Name it e.g. `ga4-analytics-portfolio`
4. **Do not enable billing** — leave the project on the free Sandbox tier
5. Copy the **Project ID** shown below the project name (it looks like `ga4-analytics-portfolio` or an auto-generated ID like `project-2cf2196d-ea65-445b-ad1`)

---

## Step 2 — Enable the BigQuery API

```bash
gcloud config set project YOUR_PROJECT_ID
gcloud services enable bigquery.googleapis.com
```

BigQuery is usually already enabled in new projects; this command is idempotent.

---

## Step 3 — Authenticate with Application Default Credentials

```bash
gcloud auth application-default login
```

This opens a browser window. Sign in with the Google account that owns the GCP project.
Credentials are saved to `~/.config/gcloud/application_default_credentials.json`.

**Why ADC instead of a service account key?**
ADC is the recommended approach for local development. It uses your own Google identity,
requires no key file to manage or rotate, and works automatically with `dbt-bigquery`
when `method: oauth` is set in `profiles.yml`.

---

## Step 4 — Install Python Dependencies

```bash
# From the repo root
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

This installs dbt Core 1.8, dbt-bigquery, Streamlit, Plotly, scipy, and the Google Cloud
Python libraries.

---

## Step 5 — Configure Your .env

```bash
cp .env.example .env
```

Edit `.env` — only the project ID needs changing:

```
GCP_PROJECT_ID=your-actual-project-id
APP_BQ_PROJECT=your-actual-project-id
APP_BQ_DATASET_MARTS=ga4_marts
APP_BQ_DATASET_EXPERIMENTS=ga4_experiments
```

No `GOOGLE_APPLICATION_CREDENTIALS` path is needed — ADC handles authentication automatically.

---

## Step 6 — Validate Setup

```bash
python scripts/validate_setup.py
```

Expected output:

```
── BigQuery Setup Validation ────────────────────────────────────

  ✅  GCP_PROJECT_ID is set
       Value: your-project-id
  ✅  BigQuery client initialised (ADC valid)
  ✅  Public GA4 dataset reachable
       events_20210131 row count: 118,535
  ✅  Working dataset 'product_analytics_dev' exists
       Location: US

── All checks passed. You're ready to run dbt. ─────────────────
```

If you see `DefaultCredentialsError`, run Step 3 again.

---

## Step 7 — Install dbt Packages

```bash
cd dbt
dbt deps --profiles-dir .
cd ..
```

This installs `dbt_utils` (declared in `packages.yml`) into `dbt/dbt_packages/`.

---

## Step 8 — Build dbt Models

```bash
# Recommended: build in layers (easier to debug if something fails)
cd dbt
dbt build --profiles-dir . --select staging          # 2 models, ~29 tests
dbt build --profiles-dir . --select intermediate     # 3 models, ~20 tests
dbt build --profiles-dir . --select marts            # 11 models, ~62 tests
dbt build --profiles-dir . --select experiments      # 2 models, ~17 tests
cd ..

# Or build everything at once:
./scripts/run_dbt.sh
```

After a full build you should see `PASS=128 WARN=2 ERROR=0` in the dbt output.
The 2 warnings are expected GA4 data quality gaps (see `docs/metric_dictionary.md`).

---

## Step 9 — Verify BigQuery Datasets

In the [BigQuery console](https://console.cloud.google.com/bigquery), under your project you should see:

| Dataset | Contents | Materialization |
|---|---|---|
| `ga4_staging` | `stg_ga4__events`, `stg_ga4__event_items` | Views |
| `ga4_intermediate` | `int_sessions`, `int_user_spine`, `int_funnel_events` | Views |
| `ga4_marts` | `dim_users`, 5× `fct_*`, 5× `mart_*` | Tables |
| `ga4_experiments` | `exp_simulated_assignment`, `exp_simulated_results` | Tables |

**Why separate datasets?** This mirrors how real data teams separate access control by layer —
analysts query marts, engineers maintain staging. It also matches production patterns where
each layer can have different IAM permissions.

---

## Step 10 — Launch the Dashboard

```bash
./scripts/run_app.sh
# Open http://localhost:8501
```

The app loads BigQuery data on first visit to each tab; subsequent loads use a 1-hour
`@st.cache_data` cache so queries don't re-run on every page interaction.

---

## Useful dbt Commands

All commands assume you're in the **repo root** with `.venv` active.

```bash
# Build one layer
dbt build --project-dir dbt --profiles-dir dbt --select staging
dbt build --project-dir dbt --profiles-dir dbt --select intermediate
dbt build --project-dir dbt --profiles-dir dbt --select marts
dbt build --project-dir dbt --profiles-dir dbt --select experiments

# Run tests only (no model builds)
dbt test --project-dir dbt --profiles-dir dbt

# Build a specific model + its tests
dbt build --project-dir dbt --profiles-dir dbt --select fct_sessions

# Narrow the date range (reduces scan cost during development)
dbt build --project-dir dbt --profiles-dir dbt \
  --select staging \
  --vars '{"start_date": "2021-01-01", "end_date": "2021-01-07"}'

# Generate and serve dbt Docs (DAG lineage graph)
dbt docs generate --project-dir dbt --profiles-dir dbt
dbt docs serve --project-dir dbt --profiles-dir dbt
# Opens http://localhost:8080 with full lineage graph
```

---

## Troubleshooting

| Error | Cause | Fix |
|---|---|---|
| `DefaultCredentialsError` | ADC not set up | Run `gcloud auth application-default login` |
| `403 bigquery.tables.create access denied` | Wrong project or API not enabled | Check `GCP_PROJECT_ID` in `.env`; re-run `gcloud services enable bigquery.googleapis.com` |
| `Not found: Dataset ga4_staging` | dbt hasn't run yet | Run `dbt build --select staging` |
| `dbt_utils not found` | Packages not installed | Run `dbt deps --profiles-dir .` from `dbt/` directory |
| `Syntax error: Unexpected keyword ROWS` | Reserved word conflict | This was a known bug in early versions — fixed in current codebase |
| `Dataset location US mismatch` | Dataset created in wrong region | Delete and recreate: `bq rm -r -f YOUR_PROJECT:ga4_staging` then re-run dbt |
| `streamlit: command not found` | Virtual env not active | `source .venv/bin/activate` before running `./scripts/run_app.sh` |
| `ConnectionError: APP_BQ_PROJECT not configured` | `.env` not set up | Copy `.env.example` to `.env` and set your project ID |
