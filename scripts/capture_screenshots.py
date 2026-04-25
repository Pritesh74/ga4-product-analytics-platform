"""
Captures portfolio screenshots from the live Streamlit app.

Prerequisites:
  - Streamlit app running on http://localhost:8501  (./scripts/run_app.sh)
  - Playwright installed in venv  (pip install playwright && playwright install chromium)

Usage:
  source .venv/bin/activate
  python scripts/capture_screenshots.py
"""

import os
import sys
import time

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("Playwright not installed. Run: pip install playwright && playwright install chromium")
    sys.exit(1)

BASE = "http://localhost:8501"
RAW  = "screenshots/dashboard/raw"
os.makedirs(RAW, exist_ok=True)

PAGES = [
    ("/executive_overview", "02_executive_overview.png", 4),
    ("/funnel",             "03_funnel.png",             4),
    ("/ltv",                "04_ltv_channel.png",        4),
    ("/data_quality",       "05_data_quality.png",       4),
    ("/geography",          "06_geography_backup.png",   5),
    ("/experiment_demo",    "01_experiment_demo.png",    6),
]

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(viewport={"width": 1440, "height": 900})
        page = ctx.new_page()

        # Pass 1: warm BigQuery cache (first visit triggers queries)
        print("Pass 1 — warming BigQuery cache...")
        for path, _, _ in PAGES:
            page.goto(BASE + path, wait_until="domcontentloaded")
            page.wait_for_selector("[data-testid='stMetric']", timeout=60000)
            print(f"  cached {path}")

        # Pass 2: screenshot from cache (instant load)
        print("\nPass 2 — capturing screenshots...")
        for path, filename, settle in PAGES:
            page.goto(BASE + path, wait_until="domcontentloaded")
            page.wait_for_selector("[data-testid='stMetric']", timeout=30000)
            time.sleep(settle)
            out = f"{RAW}/{filename}"
            page.screenshot(path=out, full_page=True)
            size_kb = os.path.getsize(out) // 1024
            print(f"  ✓ {filename}  ({size_kb} KB)")

        browser.close()

    print(f"\nRaw screenshots saved to {RAW}/")
    print("Copy to portfolio/final/ when satisfied:")
    print("  cp screenshots/dashboard/raw/*.png screenshots/portfolio/final/")

if __name__ == "__main__":
    main()
