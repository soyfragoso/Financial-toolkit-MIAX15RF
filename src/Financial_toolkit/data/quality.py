"""Diagnóstico de calidad e integridad de datos financieros.

Este módulo inspecciona los datos recibidos sin modificarlos ni limpiarlos.
El tratamiento de las incidencias corresponde al preprocesador.
"""

from dataclasses import asdict, dataclass
from typing import Any

import numpy as np
import pandas as pd


OHLC_COLUMNS = ("open", "high", "low", "close")

NUMERIC_COLUMNS = (
    "open",
    "high",
    "low",
    "close",
    "adj_close",
    "volume",
)


@dataclass(frozen=True)
class DataQualityReport:
    """Resultados del diagnóstico de calidad de un conjunto de datos."""

    total_rows: int
    total_columns: int
    total_cells: int
    missing_cells: int
    missing_percentage: float
    completeness_percentage: float
    missing_by_column: dict[str, int]
    missing_percentage_by_column: dict[str, float]
    missing_by_ticker: dict[str, dict[str, int]]
    invalid_numeric_by_column: dict[str, int]
    infinite_by_column: dict[str, int]
    invalid_date_rows: int
    duplicate_rows: int
    non_positive_close_rows: int
    negative_volume_rows: int
    invalid_ohlc_rows: int

    def to_dict(self) -> dict[str, Any]:
        """Devuelve el informe como diccionario serializable."""
        return asdict(self)

    def to_markdown(self) -> str:
        """Genera un resumen Markdown del diagnóstico."""
        lines = [
            "# Informe de calidad de datos",
            "",
            f"- Registros recibidos: **{self.total_rows}**",
            f"- Columnas recibidas: **{self.total_columns}**",
            f"- Celdas ausentes: **{self.missing_cells}/{self.total_cells}**",
            f"- Porcentaje de datos faltantes: **{self.missing_percentage:.2f}%**",
            f"- Completitud: **{self.completeness_percentage:.2f}%**",
            "",
            "## Datos faltantes por columna",
            "",
            "| Columna | Ausencias | Ausencias (%) |",
            "|---|---:|---:|",
        ]

        for column, count in self.missing_by_column.items():
            percentage = self.missing_percentage_by_column[column]
            lines.append(f"| {column} | {count} | {percentage:.2f}% |")

        lines.extend([
            "",
            "## Incidencias de integridad",
            "",
            "| Comprobación | Registros afectados |",
            "|---|---:|",
            f"| Fechas inválidas | {self.invalid_date_rows} |",
            f"| Duplicados adicionales por activo y fecha | {self.duplicate_rows} |",
            f"| Cierres no positivos | {self.non_positive_close_rows} |",
            f"| Volúmenes negativos | {self.negative_volume_rows} |",
            f"| Velas OHLC incoherentes | {self.invalid_ohlc_rows} |",
        ])

        if self.invalid_numeric_by_column:
            lines.extend([
                "",
                "## Valores numéricos no convertibles",
                "",
                "| Columna | Registros |",
                "|---|---:|",
            ])
            for column, count in self.invalid_numeric_by_column.items():
                lines.append(f"| {column} | {count} |")

        if self.infinite_by_column:
            lines.extend([
                "",
                "## Valores infinitos",
                "",
                "| Columna | Registros |",
                "|---|---:|",
            ])
            for column, count in self.infinite_by_column.items():
                lines.append(f"| {column} | {count} |")

        return "\n".join(lines)


def analyze_data_quality(data: pd.DataFrame) -> DataQualityReport:
    """Analiza ausencias e integridad sin alterar el DataFrame original.

    Los porcentajes de ausencia se calculan sobre las filas recibidas.
    Los valores no convertibles se contabilizan aparte de los NaN originales.
    Las filas duplicadas cuentan únicamente las repeticiones adicionales,
    no todas las filas que participan en un grupo duplicado.
    """
    if not isinstance(data, pd.DataFrame):
        raise TypeError("Los datos deben ser un DataFrame.")

    rows, columns = data.shape
    total_cells = rows * columns

    missing_by_column = {
        str(column): int(data[column].isna().sum())
        for column in data.columns
    }

    missing_percentage_by_column = {
        column: (
            count / rows * 100.0
            if rows
            else 0.0
        )
        for column, count in missing_by_column.items()
    }

    missing_cells = int(data.isna().sum().sum())
    missing_percentage = (
        missing_cells / total_cells * 100.0
        if total_cells
        else 0.0
    )
    completeness_percentage = 100.0 - missing_percentage

    # Ausencias desglosadas por activo y columna.
    missing_by_ticker: dict[str, dict[str, int]] = {}

    if "ticker" in data.columns:
        ticker_values = data["ticker"].astype("string").fillna("<SIN TICKER>")

        for ticker in ticker_values.unique():
            mask = ticker_values == ticker
            missing_by_ticker[str(ticker)] = {
                str(column): int(data.loc[mask, column].isna().sum())
                for column in data.columns
            }

    invalid_numeric_by_column: dict[str, int] = {}
    infinite_by_column: dict[str, int] = {}
    numeric_data: dict[str, pd.Series] = {}

    for column in NUMERIC_COLUMNS:
        if column not in data.columns:
            continue

        original = data[column]
        converted = pd.to_numeric(original, errors="coerce")
        numeric_data[column] = converted

        invalid_mask = original.notna() & converted.isna()
        invalid_count = int(invalid_mask.sum())

        if invalid_count:
            invalid_numeric_by_column[column] = invalid_count

        finite_values = converted.dropna().to_numpy(dtype=float)
        infinite_count = int(np.isinf(finite_values).sum())

        if infinite_count:
            infinite_by_column[column] = infinite_count

    # Fechas inválidas: excluye las fechas originalmente ausentes.
    invalid_date_rows = 0
    parsed_dates = None

    if "date" in data.columns:
        parsed_dates = pd.to_datetime(
            data["date"],
            format="mixed",
            errors="coerce",
        )
        invalid_date_rows = int(
            (data["date"].notna() & parsed_dates.isna()).sum()
        )

    # Repeticiones adicionales de una misma combinación ticker/fecha.
    duplicate_rows = 0

    if "ticker" in data.columns and parsed_dates is not None:
        valid_keys = data["ticker"].notna() & parsed_dates.notna()
        keys = pd.DataFrame({
            "ticker": data.loc[valid_keys, "ticker"].astype("string").str.strip().str.upper(),
            "date": parsed_dates.loc[valid_keys],
        })
        duplicate_rows = int(keys.duplicated(keep="first").sum())

    close = numeric_data.get("close")
    non_positive_close_rows = (
        int((close.notna() & (close <= 0)).sum())
        if close is not None
        else 0
    )

    volume = numeric_data.get("volume")
    negative_volume_rows = (
        int((volume.notna() & (volume < 0)).sum())
        if volume is not None
        else 0
    )

    invalid_ohlc_rows = 0

    if all(column in numeric_data for column in OHLC_COLUMNS):
        ohlc = pd.DataFrame({
            column: numeric_data[column]
            for column in OHLC_COLUMNS
        })
        complete = ohlc.notna().all(axis=1)

        valid = (
            (ohlc["high"] >= ohlc["low"])
            & (ohlc["high"] >= ohlc["open"])
            & (ohlc["high"] >= ohlc["close"])
            & (ohlc["low"] <= ohlc["open"])
            & (ohlc["low"] <= ohlc["close"])
        )

        invalid_ohlc_rows = int((complete & ~valid).sum())

    return DataQualityReport(
        total_rows=rows,
        total_columns=columns,
        total_cells=total_cells,
        missing_cells=missing_cells,
        missing_percentage=missing_percentage,
        completeness_percentage=completeness_percentage,
        missing_by_column=missing_by_column,
        missing_percentage_by_column=missing_percentage_by_column,
        missing_by_ticker=missing_by_ticker,
        invalid_numeric_by_column=invalid_numeric_by_column,
        infinite_by_column=infinite_by_column,
        invalid_date_rows=invalid_date_rows,
        duplicate_rows=duplicate_rows,
        non_positive_close_rows=non_positive_close_rows,
        negative_volume_rows=negative_volume_rows,
        invalid_ohlc_rows=invalid_ohlc_rows,
    )
