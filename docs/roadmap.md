# Roadmap

## Completed

### Data Pipeline
- [x] BigQuery Sandbox setup — ADC/oauth authentication, no service account key required
- [x] `generate_schema_name` macro — clean dataset names (`ga4_staging`, not `project_ga4_staging`)
- [x] Staging layer — `stg_ga4__events` (40+ columns, surrogate keys, boolean flags) + `stg_ga4__event_items` (UNNEST items array)
- [x] Intermediate layer — `int_sessions`, `int_user_spine`, `int_funnel_events`
- [x] Mart layer — `dim_users`, 5× `fct_*` tables, 5× `mart_*` aggregates
- [x] Experiment layer — `exp_simulated_assignment` (FARM_FINGERPRINT 50/50 split), `exp_simulated_results` (per-variant aggregates)
- [x] 128 dbt tests across all layers — 0 errors

### Dashboard
- [x] Executive Overview — KPI cards, daily revenue, channel breakdown
- [x] Funnel — `go.Funnel` chart, drop-off table, daily trend
- [x] Retention — cohort heatmap matrix
- [x] LTV — revenue per user by channel
- [x] Channel & Device — tabbed layout, browser breakdown
- [x] Geography — choropleth map with metric toggle
- [x] Experiment Demo — power analysis, SRM check, z-test visualization (labeled simulated)
- [x] Data Quality — model inventory, test pass rates, data quality notes

### Documentation
- [x] `README.md` — case study format with real computed findings
- [x] `docs/setup_bigquery.md` — full walkthrough (Sandbox + ADC)
- [x] `docs/architecture.md` — Mermaid diagram + technical decisions
- [x] `docs/metric_dictionary.md` — all metrics defined with computed values
- [x] `docs/dashboard_spec.md` — per-page component inventory
- [x] `docs/executive_summary_template.md` — completed example with real numbers

---

## Potential Future Enhancements

- [ ] Connect to a live GA4 export from a real property (Pub/Sub or scheduled BigQuery export)
- [ ] Incremental dbt models with `is_incremental()` for production data freshness
- [ ] CUPED variance reduction in the experiment layer to reduce required sample size
- [ ] Sequential testing / always-valid p-values for early stopping decisions
- [ ] `dbt docs generate` + GitHub Actions to publish live lineage graph
- [ ] Deploy Streamlit to Cloud Run or Streamlit Community Cloud for a shareable URL
- [ ] Looker Studio or Metabase as an alternative visualization layer
