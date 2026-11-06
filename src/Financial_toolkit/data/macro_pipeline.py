import pandas as pd

from Financial_toolkit.data.macro_providers import MacroDataProvider
from Financial_toolkit.models.macro_series import MacroSeries


class MacroDataPipeline:
    """
    Pipeline independiente para descargar y organizar
    series temporales macroeconómicas.
    """

    def __init__(self, provider: MacroDataProvider):
        if not isinstance(provider, MacroDataProvider):
            raise TypeError(
                "El proveedor debe implementar MacroDataProvider."
            )

        self.provider = provider

    def download(
        self,
        series_ids: list[str],
        start: str,
        end: str,
    ) -> dict[str, MacroSeries]:
        """Descarga varias series y devuelve objetos MacroSeries."""
        result = self.provider.download_series(
            series_ids=series_ids,
            start=start,
            end=end,
        )

        if not isinstance(result, dict) or not result:
            raise ValueError(
                "El proveedor no ha devuelto series macroeconómicas."
            )

        for series_id, series in result.items():
            if not isinstance(series, MacroSeries):
                raise TypeError(
                    f"El resultado de {series_id} no es MacroSeries."
                )
            if series_id != series.series_id:
                raise ValueError(
                    f"La clave {series_id} no coincide con el identificador "
                    f"de la serie {series.series_id}."
                )

        if isinstance(series_ids, str):
            requested_ids = [series_ids]
        elif isinstance(series_ids, list):
            requested_ids = series_ids
        else:
            requested_ids = []

        expected_ids = {
            item.strip().upper()
            for item in requested_ids
            if isinstance(item, str) and item.strip()
        }
        returned_ids = set(result)
        missing_ids = expected_ids - returned_ids
        unexpected_ids = returned_ids - expected_ids

        if missing_ids or unexpected_ids:
            details = []
            if missing_ids:
                details.append("faltan: " + ", ".join(sorted(missing_ids)))
            if unexpected_ids:
                details.append(
                    "no solicitadas: " + ", ".join(sorted(unexpected_ids))
                )
            raise ValueError(
                "El proveedor no ha devuelto exactamente las series "
                "solicitadas (" + "; ".join(details) + ")."
            )

        return result

    def to_dataframe(
        self,
        series: dict[str, MacroSeries],
    ) -> pd.DataFrame:
        """Combina varias series en un DataFrame normalizado."""
        if not isinstance(series, dict) or not series:
            raise ValueError(
                "Debes proporcionar al menos una serie macroeconómica."
            )

        frames = []

        for series_id, macro_series in series.items():
            if not isinstance(macro_series, MacroSeries):
                raise TypeError(
                    f"La serie {series_id} no es un objeto MacroSeries."
                )

            frames.append(macro_series.to_dataframe())

        return (
            pd.concat(frames, ignore_index=True)
            .sort_values(["series_id", "date"])
            .reset_index(drop=True)
        )

    def run(
        self,
        series_ids: list[str],
        start: str,
        end: str,
    ) -> pd.DataFrame:
        """Descarga y devuelve todas las series en formato tabular."""
        series = self.download(series_ids, start, end)
        return self.to_dataframe(series)
