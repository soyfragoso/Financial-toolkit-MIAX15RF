
from abc import ABC, abstractmethod

import pandas as pd
import yfinance as yf


class DataProvider(ABC):
    """
    Interfaz abstracta común para proveedores de datos financieros.
    """

    @abstractmethod
    def download_prices(
        self,
        tickers: list[str],
        start: str,
        end: str
    ) -> pd.DataFrame:
        """
        Descarga precios históricos de uno o varios activos.
        """
        pass


class YahooFinanceProvider(DataProvider):
    """
    Proveedor de datos financieros mediante Yahoo Finance.

    Devuelve los precios en formato tabular estandarizado,
    independientemente del número de activos descargados.
    """

    def download_prices(
        self,
        tickers: list[str],
        start: str,
        end: str
    ) -> pd.DataFrame:

        if isinstance(tickers, str):
            tickers = [tickers]

        if not tickers:
            raise ValueError("Debes proporcionar al menos un ticker.")

        tickers = list(dict.fromkeys(
            ticker.strip().upper() for ticker in tickers
        ))

        if any(not ticker for ticker in tickers):
            raise ValueError("Los tickers no pueden estar vacíos.")

        if start >= end:
            raise ValueError("La fecha inicial debe ser anterior a la final.")

        raw_data = yf.download(
            tickers=tickers,
            start=start,
            end=end,
            group_by="ticker",
            auto_adjust=False,
            progress=False,
            threads=True
        )

        if raw_data.empty:
            raise ValueError("Yahoo Finance no ha devuelto datos.")

        columns = [
            "ticker",
            "date",
            "open",
            "high",
            "low",
            "close",
            "adj_close",
            "volume"
        ]

        results = []

        for ticker in tickers:

            # Extraer los datos de cada activo.
            if isinstance(raw_data.columns, pd.MultiIndex):

                if ticker in raw_data.columns.get_level_values(0):
                    asset_data = raw_data[ticker]

                elif ticker in raw_data.columns.get_level_values(1):
                    asset_data = raw_data.xs(
                        ticker, axis=1, level=1
                    )

                else:
                    continue

            else:
                if len(tickers) != 1:
                    continue

                asset_data = raw_data

            # Normalizar nombres de columnas.
            asset_data = asset_data.rename(columns={
                "Open": "open",
                "High": "high",
                "Low": "low",
                "Close": "close",
                "Adj Close": "adj_close",
                "Volume": "volume"
            })

            # Garantizar que todos los proveedores
            # devuelvan las mismas columnas.
            for column in columns[2:]:
                if column not in asset_data.columns:
                    asset_data[column] = float("nan")

            asset_data = asset_data[columns[2:]].copy()

            asset_data["ticker"] = ticker
            asset_data["date"] = asset_data.index

            asset_data = asset_data.reset_index(drop=True)
            asset_data = asset_data[columns]

            results.append(asset_data)

        if not results:
            raise ValueError(
                "No se han podido extraer datos para los tickers solicitados."
            )

        final_data = pd.concat(results, ignore_index=True)

        final_data["date"] = pd.to_datetime(final_data["date"])

        numeric_columns = columns[2:]

        for column in numeric_columns:
            final_data[column] = pd.to_numeric(
                final_data[column], errors="coerce"
            )

        final_data = final_data.dropna(subset=["close"])

        if final_data.empty:
            raise ValueError("No hay precios de cierre válidos.")

        return final_data.sort_values(
            ["ticker", "date"]
        ).reset_index(drop=True)
