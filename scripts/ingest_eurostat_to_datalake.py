#!/usr/bin/env python3
"""Ingest required Eurostat datasets into the data-lake and emit a catalog index.

Ingests 3 Eurostat JSON-stat API responses (NUTS2 regional GDP, national GDP,
population) via the data-lake CLI, then writes scripts/datalake_eurostat_index.json
mapping every (dataset|geo) pair to a data-lake source_id.

Idempotent: re-running will re-ingest (data-lake deduplicates by canonical URL)
and overwrite the index with current source IDs.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

DATALAKE_ROOT = Path("/Users/guillem/vault/projects/personal/data-lake")
SCRIPT_DIR = Path(__file__).resolve().parent
INDEX_PATH = SCRIPT_DIR / "datalake_eurostat_index.json"

EXISTING_ES53_SOURCE_ID = "01KPWPQ902XYG9BT12QCXKFG4K"

EU15_GEOS = ("AT", "BE", "DK", "FI", "FR", "DE", "EL", "IE", "IT", "LU", "NL", "PT", "ES", "SE", "UK")

INGESTION_JOBS: list[dict] = [
    {
        "name": "nama_10r_2gdp NUTS2 batch (ES43, ES61)",
        "dataset": "nama_10r_2gdp",
        "geos": ["ES43", "ES61"],
        "url": (
            "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/nama_10r_2gdp"
            "?format=JSON&lang=en&unit=EUR_HAB&geo=ES43&geo=ES61"
        ),
    },
    {
        "name": "nama_10_pc national GDP batch (EU-15)",
        "dataset": "nama_10_pc",
        "geos": list(EU15_GEOS),
        "url": (
            "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/nama_10_pc"
            "?format=JSON&lang=en&unit=CLV10_EUR_HAB&na_item=B1GQ"
            "&geo=AT&geo=BE&geo=DK&geo=FI&geo=FR&geo=DE&geo=EL"
            "&geo=IE&geo=IT&geo=LU&geo=NL&geo=PT&geo=ES&geo=SE&geo=UK"
        ),
    },
    {
        "name": "demo_pjan population batch (EU-15)",
        "dataset": "demo_pjan",
        "geos": list(EU15_GEOS),
        "url": (
            "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/demo_pjan"
            "?format=JSON&lang=en&sex=T&age=TOTAL"
            "&geo=AT&geo=BE&geo=DK&geo=FI&geo=FR&geo=DE&geo=EL"
            "&geo=IE&geo=IT&geo=LU&geo=NL&geo=PT&geo=ES&geo=SE&geo=UK"
        ),
    },
]


def ingest_url(url: str) -> str:
    """Call data-lake CLI to ingest a URL and return the source_id."""
    result = subprocess.run(
        ["uv", "run", "python", "-m", "data_lake.ingest.cli.app", "ingest", url, "--format", "json"],
        cwd=DATALAKE_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    match = re.search(r"source_id=([0-9A-Z]{26})", result.stdout)
    if not match:
        raise RuntimeError(f"Could not parse source_id from CLI output: {result.stdout!r}")
    return match.group(1)


def main() -> None:
    index: dict[str, str | dict] = {
        "_meta": {
            "created": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "datalake_root": str(DATALAKE_ROOT),
        },
    }

    # Hardcode existing ES53 source
    index["nama_10r_2gdp|ES53"] = EXISTING_ES53_SOURCE_ID

    for job in INGESTION_JOBS:
        print(f"Ingesting: {job['name']}...")
        source_id = ingest_url(job["url"])
        print(f"  source_id={source_id}")

        raw_path = DATALAKE_ROOT / "lake" / "sources" / source_id / "raw.json"
        if not raw_path.exists():
            print(f"  WARNING: raw.json not found at {raw_path}", file=sys.stderr)

        for geo in job["geos"]:
            key = f"{job['dataset']}|{geo}"
            index[key] = source_id

    INDEX_PATH.write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")
    non_meta = [k for k in index if not k.startswith("_")]
    print(f"\nIndex written to {INDEX_PATH}")
    print(f"Total entries: {len(non_meta)} (expected ≥33)")


if __name__ == "__main__":
    main()
