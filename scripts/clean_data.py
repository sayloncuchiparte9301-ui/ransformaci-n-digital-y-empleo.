"""Build the validated annual comparison panel from raw World Bank API files."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCES_PATH = PROJECT_ROOT / "config" / "sources.yaml"
SCHEMA_PATH = PROJECT_ROOT / "data" / "metadata" / "schema.yaml"
RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_PATH = PROJECT_ROOT / "data" / "processed" / "indicators_annual.csv"
SUMMARY_PATH = PROJECT_ROOT / "data" / "metadata" / "cleaning_summary.json"


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as source_file:
        return yaml.safe_load(source_file)


def read_indicator_file(path: Path, column_name: str, indicator_code: str) -> pd.DataFrame:
    """Read one raw API response into a country-year-value table."""
    with path.open(encoding="utf-8") as raw_file:
        payload = json.load(raw_file)

    if not isinstance(payload, list) or len(payload) != 2 or not isinstance(payload[1], list):
        raise ValueError(f"Invalid raw response: {path}")

    rows = []
    for observation in payload[1]:
        if observation.get("indicator", {}).get("id") != indicator_code:
            raise ValueError(f"Unexpected indicator in {path}: {observation.get('indicator')}")
        rows.append(
            {
                "country_code": observation["countryiso3code"],
                "country_name": observation["country"]["value"],
                "year": int(observation["date"]),
                column_name: observation["value"],
            }
        )

    frame = pd.DataFrame(rows)
    if frame.duplicated(["country_code", "year"]).any():
        raise ValueError(f"Duplicate country-year observations in {path}")
    return frame


def validate_panel(panel: pd.DataFrame, schema: dict[str, Any]) -> None:
    """Raise a descriptive error if the output violates the data contract."""
    definition = schema["dataset"]
    rules = definition["validation_rules"]
    required = definition["required_columns"]

    missing_columns = set(required) - set(panel.columns)
    if missing_columns:
        raise ValueError(f"Missing required columns: {sorted(missing_columns)}")
    if panel.empty:
        raise ValueError("The cleaned panel is empty")
    if panel.duplicated(definition["primary_key"]).any():
        raise ValueError("The cleaned panel has duplicate country-year keys")
    if not set(panel["country_code"]).issubset(rules["country_code"]):
        raise ValueError("The cleaned panel contains a country outside the configured scope")
    if panel["year"].min() < rules["year"]["minimum"]:
        raise ValueError("The cleaned panel contains a year before the configured minimum")

    lower, upper = rules["percentage_range"]
    for column in rules["percentage_columns"]:
        invalid = panel[column].dropna().loc[lambda values: ~values.between(lower, upper)]
        if not invalid.empty:
            raise ValueError(f"Out-of-range values in {column}: {invalid.tolist()}")
    if (panel["fixed_broadband_per_100"].dropna() < 0).any():
        raise ValueError("Fixed broadband subscriptions cannot be negative")


def build_panel(sources: dict[str, Any], schema: dict[str, Any]) -> pd.DataFrame:
    """Merge each configured raw indicator into one country-year panel."""
    indicators = sources["primary_source"]["indicators"]
    panel: pd.DataFrame | None = None

    for column_name, indicator in indicators.items():
        file_name = f"wdi_{indicator['code'].replace('.', '_')}.json"
        frame = read_indicator_file(RAW_DIR / file_name, column_name, indicator["code"])
        if panel is None:
            panel = frame
        else:
            panel = panel.merge(frame, on=["country_code", "country_name", "year"], how="outer", validate="one_to_one")

    assert panel is not None
    panel = panel.sort_values(["country_code", "year"]).reset_index(drop=True)
    for column in schema["dataset"]["required_columns"]:
        if column not in panel:
            panel[column] = pd.NA
    return panel[schema["dataset"]["required_columns"]]


def main() -> None:
    sources = load_yaml(SOURCES_PATH)
    schema = load_yaml(SCHEMA_PATH)
    panel = build_panel(sources, schema)
    validate_panel(panel, schema)

    PROCESSED_PATH.parent.mkdir(parents=True, exist_ok=True)
    panel.to_csv(PROCESSED_PATH, index=False, na_rep="")

    summary = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "output_file": str(PROCESSED_PATH.relative_to(PROJECT_ROOT)).replace("\\", "/"),
        "rows": len(panel),
        "countries": sorted(panel["country_code"].unique().tolist()),
        "year_range": [int(panel["year"].min()), int(panel["year"].max())],
        "missing_values_by_column": {column: int(panel[column].isna().sum()) for column in panel.columns},
    }
    SUMMARY_PATH.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Validated {len(panel)} rows and wrote {PROCESSED_PATH}")
    print(f"Cleaning summary written to {SUMMARY_PATH}")


if __name__ == "__main__":
    main()
