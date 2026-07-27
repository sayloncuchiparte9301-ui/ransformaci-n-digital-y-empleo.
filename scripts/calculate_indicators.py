"""Calculate derived annual indicators from the validated comparison panel."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
INPUT_PATH = PROJECT_ROOT / "data" / "processed" / "indicators_annual.csv"
OUTPUT_PATH = PROJECT_ROOT / "data" / "processed" / "indicators_derived.csv"
SUMMARY_PATH = PROJECT_ROOT / "data" / "metadata" / "indicators_summary.json"
BASE_INDICATORS = [
    "employment_to_population_15plus_pct",
    "unemployment_rate_pct",
    "internet_users_pct",
    "fixed_broadband_per_100",
]
DIGITAL_INDICATORS = ["internet_users_pct", "fixed_broadband_per_100"]


def min_max_score(series: pd.Series) -> pd.Series:
    """Return a 0–100 score while preserving unavailable observations."""
    minimum = series.min(skipna=True)
    maximum = series.max(skipna=True)
    if pd.isna(minimum) or pd.isna(maximum):
        return pd.Series(pd.NA, index=series.index, dtype="Float64")
    if minimum == maximum:
        return series.notna().astype(float) * 100
    return (series - minimum) / (maximum - minimum) * 100


def validate_input(panel: pd.DataFrame) -> None:
    required = {"country_code", "country_name", "year", *BASE_INDICATORS}
    missing = required - set(panel.columns)
    if missing:
        raise ValueError(f"Missing columns in {INPUT_PATH}: {sorted(missing)}")
    if panel.duplicated(["country_code", "year"]).any():
        raise ValueError("Input panel has duplicate country-year keys")
    if "ECU" not in set(panel["country_code"]):
        raise ValueError("Input panel must include Ecuador (ECU) as the reference country")


def calculate_indicators(panel: pd.DataFrame) -> pd.DataFrame:
    """Add year-over-year changes, Ecuador gaps, and a transparent digital index."""
    result = panel.copy().sort_values(["country_code", "year"]).reset_index(drop=True)

    for column in BASE_INDICATORS:
        result[f"{column}_yoy_change"] = result.groupby("country_code")[column].diff()

    scores = [min_max_score(result[column]) for column in DIGITAL_INDICATORS]
    result["digitalization_index_0_100"] = pd.concat(scores, axis=1).mean(axis=1, skipna=False)

    ecuador = result.loc[result["country_code"] == "ECU", ["year", *BASE_INDICATORS]].set_index("year")
    for column in BASE_INDICATORS:
        result[f"{column}_gap_vs_ecu"] = result[column] - result["year"].map(ecuador[column])

    return result


def main() -> None:
    panel = pd.read_csv(INPUT_PATH)
    validate_input(panel)
    result = calculate_indicators(panel)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(OUTPUT_PATH, index=False, na_rep="")

    summary = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "input_file": str(INPUT_PATH.relative_to(PROJECT_ROOT)).replace("\\", "/"),
        "output_file": str(OUTPUT_PATH.relative_to(PROJECT_ROOT)).replace("\\", "/"),
        "formula": "digitalization_index_0_100 = mean(min-max score of internet_users_pct, min-max score of fixed_broadband_per_100)",
        "normalization_population": "all available country-year observations in the input panel",
        "rows": len(result),
    }
    SUMMARY_PATH.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Calculated derived indicators for {len(result)} rows and wrote {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
