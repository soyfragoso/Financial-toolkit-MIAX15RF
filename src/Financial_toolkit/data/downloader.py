
from datetime import datetime

import pandas as pd

from Financial_toolkit.data.providers import DataProvider


class DataDownloader:
    """
    Coordinador de descargas de datos financieros.

    Permite descargar uno o varios activos utilizando
    cualquier proveedor que implemente DataProvider.
    """

    def __init__(self, provider: DataProvider):
        if not isinstance(provider, DataProvider):
            raise TypeError(
                "El proveedor debe implementar DataProvider."
            )

        self.provider = provider

    def download(
        self,
        tickers: list[str],
        start: str,
        end: str
    ) -> pd.DataFrame:
        """
        Descarga y devuelve datos históricos estandarizados.
        """

        if isinstance(tickers, str):
            tickers = [tickers]

        if not tickers:
            raise ValueError("Debes indicar al menos un activo.")

        start_date = datetime.strptime(start, "%Y-%m-%d")
        end_date = datetime.strptime(end, "%Y-%m-%d")

        if start_date >= end_date:
            raise ValueError(
                "La fecha inicial debe ser anterior a la final."
            )

        data = self.provider.download_prices(
            tickers=tickers,
            start=start,
            end=end
        )

        if not isinstance(data, pd.DataFrame):
            raise TypeError(
                "El proveedor debe devolver un DataFrame."
            )

        return data
