from dataclasses import dataclass, field

import numpy as np
import pandas as pd


@dataclass
class MacroSeries:
    """
    Representa una serie temporal de un indicador macroeconómico.
    """

    series_id: str
    values: pd.Series
    name: str = ""
    units: str = ""
    frequency: str = ""

    mean: float = field(init=False)
    median: float = field(init=False)
    std: float = field(init=False)
    minimum: float = field(init=False)
    maximum: float = field(init=False)

    def __post_init__(self):
        if not isinstance(self.series_id, str) or not self.series_id.strip():
            raise ValueError(
                "El identificador de la serie no puede estar vacío."
            )

        self.series_id = self.series_id.strip().upper()

        if not isinstance(self.values, pd.Series):
            raise TypeError(
                "Los valores deben proporcionarse como pd.Series."
            )

        if self.values.empty:
            raise ValueError(
                "La serie macroeconómica no puede estar vacía."
            )

        dates = pd.to_datetime(
            self.values.index,
            errors="coerce",
            format="mixed",
        )

        if dates.isna().any():
            raise ValueError(
                "La serie contiene fechas no válidas."
            )

        if dates.has_duplicates:
            raise ValueError(
                "La serie no puede contener fechas duplicadas."
            )

        numeric_values = pd.to_numeric(
            self.values,
            errors="coerce"
        )

        if numeric_values.isna().any():
            raise ValueError(
                "La serie contiene valores no numéricos o ausentes."
            )

        numeric_values = numeric_values.astype(float)

        if not np.isfinite(numeric_values.to_numpy()).all():
            raise ValueError(
                "La serie contiene valores no finitos."
            )

        numeric_values.index = pd.DatetimeIndex(dates)
        self.values = numeric_values.sort_index()
        self.values.index.name = "date"

        self.mean = float(self.values.mean())
        self.median = float(self.values.median())
        self.std = (
            float(self.values.std(ddof=1))
            if len(self.values) > 1
            else 0.0
        )
        self.minimum = float(self.values.min())
        self.maximum = float(self.values.max())

    @property
    def dates(self) -> pd.DatetimeIndex:
        return pd.DatetimeIndex(self.values.index)

    def to_dataframe(self) -> pd.DataFrame:
        """Devuelve la serie en formato tabular normalizado."""
        return pd.DataFrame({
            "series_id": self.series_id,
            "date": self.values.index,
            "value": self.values.to_numpy(),
        })
