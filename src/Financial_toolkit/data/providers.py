import os
from abc import ABC, abstractmethod
from datetime import datetime, timedelta

import pandas as pd
import requests
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
        if not all(isinstance(ticker, str) for ticker in tickers):
            raise ValueError("Todos los tickers deben ser cadenas de texto.")

        tickers = list(dict.fromkeys(
            ticker.strip().upper() for ticker in tickers
        ))

        if any(not ticker for ticker in tickers):
            raise ValueError("Los tickers no pueden estar vacíos.")

        try:
            start_date = datetime.strptime(start, "%Y-%m-%d")
            end_date = datetime.strptime(end, "%Y-%m-%d")
        except (TypeError, ValueError):
            raise ValueError(
                "Las fechas deben tener el formato YYYY-MM-DD."
            )

        if start_date >= end_date:
            raise ValueError(
                "La fecha inicial debe ser anterior a la final."
            )

        import logging

        self.last_download_diagnostic = None

        class YahooLogCapture(logging.Handler):
            def __init__(self):
                super().__init__()
                self.messages = []

            def emit(self, record):
                self.messages.append(self.format(record))

        capture = YahooLogCapture()
        yahoo_logger = logging.getLogger("yfinance")
        previous_propagate = yahoo_logger.propagate
        yahoo_logger.addHandler(capture)
        yahoo_logger.propagate = False

        try:
            try:
                raw_data = yf.download(
                    tickers=tickers,
                    start=start,
                    end=end,
                    group_by="ticker",
                    auto_adjust=False,
                    progress=False,
                    threads=True
                )
            except Exception as error:
                diagnostic_text = " ".join(
                    capture.messages + [str(error)]
                ).lower()

                if (
                    "quote not found" in diagnostic_text
                    or "symbol not found" in diagnostic_text
                    or "http error 404" in diagnostic_text
                ):
                    category = "SYMBOL_NOT_FOUND"
                    detail = (
                        "Yahoo Finance no ha encontrado el símbolo "
                        "solicitado."
                    )
                elif (
                    "possibly delisted" in diagnostic_text
                    or "may be delisted" in diagnostic_text
                ):
                    category = "POSSIBLE_DELISTING"
                    detail = (
                        "Yahoo Finance indica una posible exclusión "
                        "de cotización. No es una confirmación."
                    )
                elif any(term in diagnostic_text for term in (
                    "timeout", "timed out", "connection",
                    "network", "name resolution", "dns",
                    "max retries",
                )):
                    category = "CONNECTION_ERROR"
                    detail = (
                        "No se pudo completar la conexión con "
                        "Yahoo Finance."
                    )
                else:
                    category = "PROVIDER_ERROR"
                    detail = (
                        "Yahoo Finance ha producido un error "
                        "durante la descarga."
                    )

                self.last_download_diagnostic = {
                    "category": category,
                    "detail": detail,
                    "provider_message": " | ".join(capture.messages),
                }
                raise
        finally:
            yahoo_logger.removeHandler(capture)
            yahoo_logger.propagate = previous_propagate

        if raw_data.empty:
            diagnostic_text = " ".join(capture.messages).lower()

            if (
                "quote not found" in diagnostic_text
                or "symbol not found" in diagnostic_text
                or "http error 404" in diagnostic_text
            ):
                category = "SYMBOL_NOT_FOUND"
                detail = (
                    "Yahoo Finance no ha encontrado el símbolo "
                    "solicitado."
                )
            elif (
                "possibly delisted" in diagnostic_text
                or "may be delisted" in diagnostic_text
            ):
                category = "POSSIBLE_DELISTING"
                detail = (
                    "Yahoo Finance indica una posible exclusión "
                    "de cotización. No es una confirmación."
                )
            elif any(term in diagnostic_text for term in (
                "timeout", "timed out", "connection",
                "network", "name resolution", "dns",
                "max retries",
            )):
                category = "CONNECTION_ERROR"
                detail = (
                    "No se pudo completar la conexión con Yahoo Finance."
                )
            else:
                category = "EMPTY_RESPONSE"
                detail = (
                    "Yahoo Finance no ha devuelto observaciones "
                    "y no se ha podido identificar la causa."
                )

            self.last_download_diagnostic = {
                "category": category,
                "detail": detail,
                "provider_message": " | ".join(capture.messages),
            }
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
                    asset_data = raw_data[ticker].copy()

                elif ticker in raw_data.columns.get_level_values(1):
                    asset_data = raw_data.xs(
                        ticker, axis=1, level=1
                    ).copy()

                else:
                    continue

            else:
                if len(tickers) != 1:
                    continue

                asset_data = raw_data.copy()

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

        final_data["date"] = pd.to_datetime(
            final_data["date"],
            errors="coerce"
        )

        numeric_columns = columns[2:]

        for column in numeric_columns:
            final_data[column] = pd.to_numeric(
                final_data[column], errors="coerce"
            )

        # Se conservan las observaciones incompletas para que
        # Data Quality pueda diagnosticarlas antes de procesarlas.
        return final_data.sort_values(
            ["ticker", "date"]
        ).reset_index(drop=True)

class TwelveDataProvider(DataProvider):
    """
    Proveedor de datos financieros mediante Twelve Data.

    Descarga series temporales diarias y devuelve los datos
    en el mismo formato estandarizado que YahooFinanceProvider.
    """

    API_URL = "https://api.twelvedata.com/time_series"
    TIMEOUT = 30

    COLUMNS = [
        "ticker",
        "date",
        "open",
        "high",
        "low",
        "close",
        "adj_close",
        "volume"
    ]

    def __init__(
        self,
        api_key: str | None = None,
        timeout: int = TIMEOUT
    ):
        self.api_key = api_key or os.getenv("TWELVE_DATA_API_KEY")

        if not self.api_key:
            raise ValueError(
                "Debes proporcionar una API key de Twelve Data "
                "o configurar la variable TWELVE_DATA_API_KEY."
            )

        if not isinstance(timeout, int) or timeout <= 0:
            raise ValueError(
                "El tiempo de espera debe ser un entero positivo."
            )

        self.timeout = timeout

    def download_prices(
        self,
        tickers: list[str],
        start: str,
        end: str
    ) -> pd.DataFrame:
        """
        Descarga precios diarios de uno o varios activos.

        Twelve Data utiliza una fecha final inclusiva.
        Este método mantiene la convención de Yahoo Finance,
        donde la fecha final es exclusiva.
        """

        if isinstance(tickers, str):
            tickers = [tickers]

        if not tickers:
            raise ValueError(
                "Debes proporcionar al menos un ticker."
            )

        if any(not isinstance(ticker, str) for ticker in tickers):
            raise ValueError(
                "Todos los tickers deben ser cadenas de texto."
            )

        tickers = list(dict.fromkeys(
            ticker.strip().upper() for ticker in tickers
        ))

        if any(not ticker for ticker in tickers):
            raise ValueError(
                "Los tickers no pueden estar vacíos."
            )

        try:
            start_date = datetime.strptime(start, "%Y-%m-%d")
            end_date = datetime.strptime(end, "%Y-%m-%d")

        except (TypeError, ValueError) as error:
            raise ValueError(
                "Las fechas deben tener el formato YYYY-MM-DD."
            ) from error

        if start_date >= end_date:
            raise ValueError(
                "La fecha inicial debe ser anterior a la final."
            )

        # Ajustar la fecha final para mantener
        # la convención exclusiva de Yahoo Finance.
        inclusive_end_date = end_date - timedelta(days=1)

        results = []

        for ticker in tickers:

            params = {
                "symbol": ticker,
                "interval": "1day",
                "start_date": start_date.strftime("%Y-%m-%d"),
                "end_date": inclusive_end_date.strftime("%Y-%m-%d"),
                "apikey": self.api_key
            }

            # La clave viaja como parámetro de la petición.
            # Nunca propagamos excepciones HTTP originales porque
            # pueden incluir la URL completa y revelar la API key.
            try:
                response = requests.get(
                    self.API_URL,
                    params=params,
                    timeout=self.timeout
                )
                response.raise_for_status()

            except requests.RequestException as error:
                status_code = getattr(
                    getattr(error, "response", None),
                    "status_code",
                    None,
                )

                status_detail = (
                    f"HTTP {status_code}"
                    if status_code is not None
                    else "error de conexión o solicitud"
                )

                safe_message = (
                    f"No se pudo consultar Twelve Data para "
                    f"{ticker}: {status_detail}. "
                    "La URL y las credenciales se han omitido."
                )

                exception_type = (
                    requests.HTTPError
                    if isinstance(error, requests.HTTPError)
                    else RuntimeError
                )

                raise exception_type(safe_message) from None

            payload = response.json()

            if not isinstance(payload, dict):
                raise ValueError(
                    f"Respuesta no válida de Twelve Data para {ticker}."
                )

            if payload.get("status") == "error":
                # Evita que un mensaje del proveedor pueda devolver
                # accidentalmente la clave en texto claro.
                message = str(
                    payload.get("message", "Error desconocido")
                )
                message = message.replace(
                    self.api_key,
                    "[CLAVE OCULTA]",
                )

                raise ValueError(
                    f"Error de Twelve Data para {ticker}: {message}."
                )

            values = payload.get("values")

            if not isinstance(values, list) or not values:
                raise ValueError(
                    f"Twelve Data no ha devuelto datos para {ticker}."
                )

            asset_data = pd.DataFrame(values)

            asset_data = asset_data.rename(columns={
                "datetime": "date"
            })

            # Garantizar un esquema común entre proveedores.
            for column in self.COLUMNS[1:]:
                if column not in asset_data.columns:
                    asset_data[column] = float("nan")

            asset_data["ticker"] = ticker

            asset_data = asset_data[self.COLUMNS]

            results.append(asset_data)

        final_data = pd.concat(
            results,
            ignore_index=True
        )

        final_data["date"] = pd.to_datetime(
            final_data["date"],
            errors="coerce"
        )

        numeric_columns = self.COLUMNS[2:]

        for column in numeric_columns:
            final_data[column] = pd.to_numeric(
                final_data[column],
                errors="coerce"
            )

        # Se conservan fechas y precios ausentes o inválidos.
        # El diagnóstico y la política de tratamiento corresponden
        # al pipeline de calidad de datos.
        return final_data.sort_values(
            ["ticker", "date"]
        ).reset_index(drop=True)
