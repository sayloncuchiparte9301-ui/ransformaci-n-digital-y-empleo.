"""Generate reproducible charts and a latest-year comparison table."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import pandas as pd


matplotlib.use("Agg")

PROJECT_ROOT = Path(__file__).resolve().parents[1]
INPUT_PATH = PROJECT_ROOT / "data" / "processed" / "indicators_derived.csv"
CHARTS_DIR = PROJECT_ROOT / "outputs" / "charts"
TABLES_DIR = PROJECT_ROOT / "outputs" / "tables"
LOG_PATH = PROJECT_ROOT / "outputs" / "logs" / "chart_manifest.json"
COUNTRY_ORDER = ["ECU", "COL", "CHL", "PER"]
COLORS = {"ECU": "#2563eb", "COL": "#f59e0b", "CHL": "#dc2626", "PER": "#16a34a"}


def setup_directories() -> None:
    for directory in (CHARTS_DIR, TABLES_DIR, LOG_PATH.parent):
        directory.mkdir(parents=True, exist_ok=True)


def line_chart(data: pd.DataFrame, column: str, title: str, y_label: str, output_name: str) -> Path:
    fig, ax = plt.subplots(figsize=(10, 6))
    for country in COUNTRY_ORDER:
        subset = data.loc[data["country_code"] == country].sort_values("year")
        ax.plot(
            subset["year"],
            subset[column],
            marker="o",
            linewidth=2,
            label=subset["country_name"].iloc[0],
            color=COLORS[country],
        )
    ax.set_title(title, fontweight="bold")
    ax.set_xlabel("Año")
    ax.set_ylabel(y_label)
    ax.grid(axis="y", alpha=0.25)
    ax.legend(title="País")
    fig.tight_layout()
    output = CHARTS_DIR / output_name
    fig.savefig(output, dpi=160, bbox_inches="tight")
    plt.close(fig)
    return output


def digital_vs_employment_chart(data: pd.DataFrame) -> Path:
    complete = data.dropna(subset=["digitalization_index_0_100", "employment_to_population_15plus_pct"])
    fig, ax = plt.subplots(figsize=(9, 6))
    for country in COUNTRY_ORDER:
        subset = complete.loc[complete["country_code"] == country]
        ax.scatter(
            subset["digitalization_index_0_100"],
            subset["employment_to_population_15plus_pct"],
            label=subset["country_name"].iloc[0],
            color=COLORS[country],
            alpha=0.75,
        )
    ax.set_title("Digitalización y empleo: observaciones anuales", fontweight="bold")
    ax.set_xlabel("Índice de digitalización (0–100)")
    ax.set_ylabel("Empleo / población de 15+ (%)")
    ax.grid(alpha=0.25)
    ax.legend(title="País")
    fig.tight_layout()
    output = CHARTS_DIR / "digitalization_vs_employment.png"
    fig.savefig(output, dpi=160, bbox_inches="tight")
    plt.close(fig)
    return output


def latest_complete_year(data: pd.DataFrame) -> int:
    required = [
        "employment_to_population_15plus_pct",
        "unemployment_rate_pct",
        "internet_users_pct",
        "fixed_broadband_per_100",
    ]
    counts = data.dropna(subset=required).groupby("year")["country_code"].nunique()
    valid_years = counts.loc[counts == len(COUNTRY_ORDER)]
    if valid_years.empty:
        raise ValueError("No year has complete data for every configured country")
    return int(valid_years.index.max())


def latest_year_table(data: pd.DataFrame, year: int) -> Path:
    columns = [
        "country_code",
        "country_name",
        "year",
        "employment_to_population_15plus_pct",
        "unemployment_rate_pct",
        "internet_users_pct",
        "fixed_broadband_per_100",
        "digitalization_index_0_100",
    ]
    table = data.loc[data["year"] == year, columns].sort_values("country_code")
    output = TABLES_DIR / "latest_complete_year_comparison.csv"
    table.to_csv(output, index=False)
    return output


def main() -> None:
    data = pd.read_csv(INPUT_PATH)
    if data.empty:
        raise ValueError(f"No rows found in {INPUT_PATH}")
    setup_directories()

    artifacts = [
        line_chart(data, "digitalization_index_0_100", "Evolución del índice de digitalización", "Índice (0–100)", "digitalization_trend.png"),
        line_chart(data, "employment_to_population_15plus_pct", "Evolución del empleo", "Empleo / población de 15+ (%)", "employment_trend.png"),
        line_chart(data, "unemployment_rate_pct", "Evolución del desempleo", "Desempleo (% de la fuerza laboral)", "unemployment_trend.png"),
        digital_vs_employment_chart(data),
    ]
    comparison_year = latest_complete_year(data)
    table = latest_year_table(data, comparison_year)
    manifest = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "input_file": str(INPUT_PATH.relative_to(PROJECT_ROOT)).replace("\\", "/"),
        "latest_complete_year": comparison_year,
        "charts": [str(path.relative_to(PROJECT_ROOT)).replace("\\", "/") for path in artifacts],
        "table": str(table.relative_to(PROJECT_ROOT)).replace("\\", "/"),
    }
    LOG_PATH.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Generated {len(artifacts)} charts and comparison table for {comparison_year}")


if __name__ == "__main__":
    main()
