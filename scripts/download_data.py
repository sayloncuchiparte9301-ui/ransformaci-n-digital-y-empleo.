"""Download the raw international indicator series defined in config/sources.yaml."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests
import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = PROJECT_ROOT / "config" / "sources.yaml"
RAW_DIR = PROJECT_ROOT / "data" / "raw"
METADATA_DIR = PROJECT_ROOT / "data" / "metadata"
REQUEST_TIMEOUT_SECONDS = 30


def load_config(path: Path = CONFIG_PATH) -> dict[str, Any]:
    """Load and minimally validate the data-source configuration."""
    with path.open(encoding="utf-8") as config_file:
        config = yaml.safe_load(config_file)

    if not config or "primary_source" not in config or "project_scope" not in config:
        raise ValueError(f"Invalid source configuration: {path}")
    return config


def build_url(template: str, countries: str, indicator: str, start_year: int, end_year: int) -> str:
    return template.format(
        countries=countries,
        indicator=indicator,
        start_year=start_year,
        end_year=end_year,
    )


def download_indicator(url: str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Fetch one World Bank API response and return its metadata and observations."""
    response = requests.get(url, timeout=REQUEST_TIMEOUT_SECONDS)
    response.raise_for_status()
    payload = response.json()

    if not isinstance(payload, list) or len(payload) != 2 or not isinstance(payload[0], dict):
        raise ValueError(f"Unexpected API response for {url}")
    if isinstance(payload[1], dict) and "message" in payload[1]:
        message = payload[1]["message"]
        raise ValueError(f"World Bank API error for {url}: {message}")
    if not isinstance(payload[1], list):
        raise ValueError(f"No observations returned for {url}")

    return payload[0], payload[1]


def run_download(config: dict[str, Any], end_year: int | None = None) -> list[dict[str, Any]]:
    """Download every configured international series and return its manifest entries."""
    scope = config["project_scope"]
    source = config["primary_source"]
    countries = ";".join(scope["countries"].keys())
    start_year = int(scope["period"]["start_year"])
    final_year = end_year or datetime.now(timezone.utc).year
    template = source["access"]["url_template"]

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    METADATA_DIR.mkdir(parents=True, exist_ok=True)
    downloaded_at = datetime.now(timezone.utc).isoformat()
    manifest: list[dict[str, Any]] = []

    for column_name, indicator in source["indicators"].items():
        code = indicator["code"]
        url = build_url(template, countries, code, start_year, final_year)
        api_metadata, observations = download_indicator(url)
        raw_file = RAW_DIR / f"wdi_{code.replace('.', '_')}.json"
        raw_file.write_text(json.dumps([api_metadata, observations], ensure_ascii=False, indent=2), encoding="utf-8")

        manifest.append(
            {
                "column_name": column_name,
                "indicator_code": code,
                "indicator_name": indicator["name"],
                "source": source["name"],
                "url": url,
                "downloaded_at_utc": downloaded_at,
                "raw_file": str(raw_file.relative_to(PROJECT_ROOT)).replace("\\", "/"),
                "observations_returned": len(observations),
                "api_pagination": api_metadata,
            }
        )

    manifest_path = METADATA_DIR / "wdi_download_manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--end-year",
        type=int,
        help="Last requested year. Defaults to the current calendar year; unavailable values remain absent.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    manifest = run_download(load_config(), end_year=args.end_year)
    print(f"Downloaded {len(manifest)} indicators to {RAW_DIR}")
    print(f"Manifest written to {METADATA_DIR / 'wdi_download_manifest.json'}")


if __name__ == "__main__":
    main()
