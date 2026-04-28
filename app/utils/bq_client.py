"""
BigQuery client utilities for the Streamlit app.

On Streamlit Cloud: authenticates via st.secrets["gcp_service_account"].
Locally: falls back to Application Default Credentials (ADC).
  Run once: gcloud auth application-default login
"""

import os
from pathlib import Path
from functools import lru_cache

import pandas as pd
from google.cloud import bigquery
from google.oauth2 import service_account
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent.parent / ".env")


def _sa_info() -> dict | None:
    """Return the service account dict from st.secrets, or None if not present."""
    try:
        import streamlit as st
        return dict(st.secrets["gcp_service_account"])
    except Exception:
        return None


@lru_cache(maxsize=1)
def get_client() -> bigquery.Client:
    sa = _sa_info()
    if sa:
        creds = service_account.Credentials.from_service_account_info(
            sa,
            scopes=["https://www.googleapis.com/auth/cloud-platform"],
        )
        return bigquery.Client(project=sa.get("project_id"), credentials=creds)

    project = os.environ.get("APP_BQ_PROJECT", "")
    if not project or project == "your-gcp-project-id":
        raise ConnectionError(
            "APP_BQ_PROJECT not configured. "
            "Add your GCP project ID to .env and restart the app."
        )
    return bigquery.Client(project=project)


def _project() -> str:
    sa = _sa_info()
    if sa:
        return sa.get("project_id", "unknown-project")
    return os.environ.get("APP_BQ_PROJECT", "unknown-project")


def run_query(sql: str) -> pd.DataFrame:
    """Execute SQL and return a DataFrame. Caching is handled by callers."""
    return get_client().query(sql).to_dataframe()


def marts_table(table_name: str) -> str:
    """Fully-qualified reference to a ga4_marts table."""
    dataset = os.environ.get("APP_BQ_DATASET_MARTS", "ga4_marts")
    return f"`{_project()}.{dataset}.{table_name}`"


def experiments_table(table_name: str) -> str:
    """Fully-qualified reference to a ga4_experiments table."""
    dataset = os.environ.get("APP_BQ_DATASET_EXPERIMENTS", "ga4_experiments")
    return f"`{_project()}.{dataset}.{table_name}`"
