"""
BigQuery client utilities for the Streamlit app.
Authentication uses Application Default Credentials (ADC) — no key file needed.
Run once: gcloud auth application-default login
"""

import os
from pathlib import Path
from functools import lru_cache
from typing import Optional

import pandas as pd
from google.cloud import bigquery
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent.parent / ".env")


@lru_cache(maxsize=1)
def get_client() -> bigquery.Client:
    project = os.environ.get("APP_BQ_PROJECT", "")
    if not project or project == "your-gcp-project-id":
        raise ConnectionError(
            "APP_BQ_PROJECT not configured. "
            "Add your GCP project ID to .env and restart the app."
        )
    return bigquery.Client(project=project)


def run_query(sql: str) -> pd.DataFrame:
    """Execute SQL and return a DataFrame. Caching is handled by callers."""
    client = get_client()
    return client.query(sql).to_dataframe()


def marts_table(table_name: str) -> str:
    """Fully-qualified reference to a ga4_marts table."""
    project = os.environ.get("APP_BQ_PROJECT", "unknown-project")
    dataset = os.environ.get("APP_BQ_DATASET_MARTS", "ga4_marts")
    return f"`{project}.{dataset}.{table_name}`"


def experiments_table(table_name: str) -> str:
    """Fully-qualified reference to a ga4_experiments table."""
    project = os.environ.get("APP_BQ_PROJECT", "unknown-project")
    dataset = os.environ.get("APP_BQ_DATASET_EXPERIMENTS", "ga4_experiments")
    return f"`{project}.{dataset}.{table_name}`"
