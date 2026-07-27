"""Estimate an exploratory association between digitalization and employment."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import statsmodels.formula.api as smf


PROJECT_ROOT = Path(__file__).resolve().parents[1]
INPUT_PATH = PROJECT_ROOT / "data" / "processed" / "indicators_derived.csv"
COEFFICIENTS_PATH = PROJECT_ROOT / "outputs" / "tables" / "econometric_coefficients.csv"
REPORT_PATH = PROJECT_ROOT / "outputs" / "reports" / "econometric_summary.md"
MANIFEST_PATH = PROJECT_ROOT / "outputs" / "logs" / "econometric_manifest.json"
FORMULA = "employment_to_population_15plus_pct ~ digitalization_index_0_100 + year_centered + C(country_code)"


def prepare_sample(data: pd.DataFrame) -> pd.DataFrame:
    """Keep complete observations and centre the time trend for interpretability."""
    required = ["country_code", "year", "employment_to_population_15plus_pct", "digitalization_index_0_100"]
    missing = set(required) - set(data.columns)
    if missing:
        raise ValueError(f"Missing columns in {INPUT_PATH}: {sorted(missing)}")

    sample = data.dropna(subset=required).copy()
    if sample["country_code"].nunique() < 2 or len(sample) < 20:
        raise ValueError("At least 20 complete observations from two countries are required")
    sample["year_centered"] = sample["year"] - sample["year"].mean()
    return sample


def coefficient_table(model: object) -> pd.DataFrame:
    confidence_intervals = model.conf_int()
    return pd.DataFrame(
        {
            "term": model.params.index,
            "coefficient": model.params.values,
            "std_error_hc3": model.bse.values,
            "p_value": model.pvalues.values,
            "ci_95_lower": confidence_intervals.iloc[:, 0].values,
            "ci_95_upper": confidence_intervals.iloc[:, 1].values,
        }
    )


def write_report(model: object, sample: pd.DataFrame) -> None:
    coefficient = model.params["digitalization_index_0_100"]
    p_value = model.pvalues["digitalization_index_0_100"]
    report = f"""# Modelo econométrico exploratorio

## Especificación

`{FORMULA}`

- Observaciones completas: {int(model.nobs)}.
- Países: {sample['country_code'].nunique()}.
- Periodo efectivo: {int(sample['year'].min())}–{int(sample['year'].max())}.
- Estimación: MCO con efectos fijos por país y errores estándar robustos HC3.
- R² ajustado: {model.rsquared_adj:.3f}.

## Resultado principal

El coeficiente del índice de digitalización es {coefficient:.3f} puntos porcentuales de empleo/población por cada punto adicional del índice; su valor p robusto es {p_value:.3f}.

## Interpretación y límites

Este resultado describe una asociación condicionada por país y una tendencia temporal lineal. No identifica un efecto causal: la muestra es pequeña, el índice es un proxy construido con dos variables, pueden existir variables omitidas y la evolución temporal puede correlacionarse con ambas variables. No se deben usar estos resultados para inferencia de política sin un diseño causal adicional y más datos.
"""
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(report, encoding="utf-8")


def main() -> None:
    data = pd.read_csv(INPUT_PATH)
    sample = prepare_sample(data)
    model = smf.ols(FORMULA, data=sample).fit(cov_type="HC3")

    COEFFICIENTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    coefficients = coefficient_table(model)
    coefficients.to_csv(COEFFICIENTS_PATH, index=False)
    write_report(model, sample)

    manifest = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "input_file": str(INPUT_PATH.relative_to(PROJECT_ROOT)).replace("\\", "/"),
        "formula": FORMULA,
        "observations": int(model.nobs),
        "adjusted_r_squared": model.rsquared_adj,
        "coefficient_file": str(COEFFICIENTS_PATH.relative_to(PROJECT_ROOT)).replace("\\", "/"),
        "report_file": str(REPORT_PATH.relative_to(PROJECT_ROOT)).replace("\\", "/"),
    }
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Estimated exploratory model with {int(model.nobs)} observations")
    print(f"Coefficient table written to {COEFFICIENTS_PATH}")


if __name__ == "__main__":
    main()
