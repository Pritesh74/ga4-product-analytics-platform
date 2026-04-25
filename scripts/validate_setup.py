"""
validate_setup.py
─────────────────
Quick smoke-test that your environment is configured correctly before
running dbt. Checks:
  1. GCP_PROJECT_ID env var is set
  2. ADC credentials are valid (can initialise a BigQuery client)
  3. The public GA4 dataset is reachable and returns a row count
  4. Your working dataset (product_analytics_dev) exists and is writable

Usage:
  python scripts/validate_setup.py
"""

import os
import sys
from pathlib import Path

# Load .env if present
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent / ".env")
except ImportError:
    pass  # python-dotenv not installed yet — rely on shell env


def check(label: str, ok: bool, detail: str = "") -> bool:
    status = "✅" if ok else "❌"
    msg = f"  {status}  {label}"
    if detail:
        msg += f"\n       {detail}"
    print(msg)
    return ok


def main() -> int:
    print("\n── BigQuery Setup Validation ────────────────────────────────────\n")
    all_ok = True

    # ── 1. Env var ────────────────────────────────────────────────────────
    project_id = os.environ.get("GCP_PROJECT_ID", "")
    all_ok &= check(
        "GCP_PROJECT_ID is set",
        bool(project_id),
        f"Value: {project_id}" if project_id else "Set it in .env or export GCP_PROJECT_ID=...",
    )

    if not project_id:
        print("\nFix GCP_PROJECT_ID first, then re-run.\n")
        return 1

    # ── 2. BigQuery client ────────────────────────────────────────────────
    try:
        from google.cloud import bigquery
        client = bigquery.Client(project=project_id)
        all_ok &= check("BigQuery client initialised (ADC valid)", True)
    except Exception as exc:
        all_ok &= check(
            "BigQuery client initialised (ADC valid)",
            False,
            f"Error: {exc}\nRun: gcloud auth application-default login",
        )
        print("\nFix ADC credentials first, then re-run.\n")
        return 1

    # ── 3. Public GA4 dataset reachable ───────────────────────────────────
    try:
        test_table = "bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_20210131"
        row = (
            client
            .query(f"SELECT COUNT(*) AS n FROM `{test_table}`")
            .to_dataframe()
        )
        n = int(row["n"].iloc[0])
        all_ok &= check(
            "Public GA4 dataset reachable",
            n > 0,
            f"events_20210131 row count: {n:,}",
        )
    except Exception as exc:
        all_ok &= check("Public GA4 dataset reachable", False, str(exc))

    # ── 4. Working dataset writable ───────────────────────────────────────
    working_dataset = "product_analytics_dev"
    try:
        from google.cloud.bigquery import Dataset, DatasetReference
        ds_ref = DatasetReference(project_id, working_dataset)
        try:
            client.get_dataset(ds_ref)
            all_ok &= check(
                f"Working dataset '{working_dataset}' exists",
                True,
                f"Location: {client.get_dataset(ds_ref).location}",
            )
        except Exception:
            # Dataset doesn't exist — try to create it
            ds = Dataset(ds_ref)
            ds.location = "US"
            client.create_dataset(ds, exists_ok=True)
            all_ok &= check(
                f"Working dataset '{working_dataset}' created",
                True,
                "Created with location US",
            )
    except Exception as exc:
        all_ok &= check(f"Working dataset '{working_dataset}' writable", False, str(exc))

    # ── Summary ───────────────────────────────────────────────────────────
    print()
    if all_ok:
        print("── All checks passed. You're ready to run dbt. ─────────────────\n")
        print("  Next steps:")
        print("  1. cd to repo root")
        print("  2. source .venv/bin/activate")
        print("  3. ./scripts/run_dbt.sh\n")
    else:
        print("── Some checks failed. Fix the issues above and re-run. ─────────\n")

    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
