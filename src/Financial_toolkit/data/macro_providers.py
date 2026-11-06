import os
from abc import ABC, abstractmethod
from datetime import datetime

import pandas as pd
import requests

from Financial_toolkit.models.macro_series import MacroSeries


class MacroDataProvider(ABC):
    """Interfaz para proveedores de indicadores macroeconómicos."""

    @abstractmethod
    def download_series(
        self,
        series_ids: list[str],
        start: str,
        end: str,
    ) -> dict[str, MacroSeries]:
        """Descarga una o varias series macroeconómicas."""
        raise NotImplementedError


class FredDataProvider(MacroDataProvider):
    """
    Proveedor de indicadores macroeconómicos de FRED.

    Utiliza la API de observaciones de Federal Reserve Economic Data.
    La fecha final es inclusiva.
    """

    API_URL = "https://api.stlouisfed.org/fred/series/observations"
    TIMEOUT = 30

    def __init__(
        self,
        api_key: str | None = None,
        timeout: int = TIMEOUT,
    ):
        self.api_key = api_key or os.getenv("FRED_API_KEY")

        if not self.api_key:
            raise ValueError(
                "Debes proporcionar una API key de FRED "
                "o configurar la variable FRED_API_KEY."
            )

        if not isinstance(timeout, int) or timeout <= 0:
            raise ValueError(
                "El tiempo de espera debe ser un entero positivo."
            )

        self.timeout = timeout

    @staticmethod
    def _validate_dates(start: str, end: str) -> None:
        """Valida fechas con formato YYYY-MM-DD."""
        try:
            start_date = datetime.strptime(start, "%Y-%m-%d")
            end_date = datetime.strptime(end, "%Y-%m-%d")
        except (TypeError, ValueError) as error:
            raise ValueError(
                "Las fechas deben tener el formato YYYY-MM-DD."
            ) from error

        if start_date >= end_date:
            raise ValueError(
                "La fecha inicial debe ser anterior a la fecha final."
            )

    @staticmethod
    def _normalize_series_ids(series_ids: list[str]) -> list[str]:
        """Valida y normaliza los identificadores solicitados."""
        if isinstance(series_ids, str):
            series_ids = [series_ids]

        if not isinstance(series_ids, list) or not series_ids:
            raise ValueError(
                "Debes proporcionar al menos un identificador de serie."
            )

        if any(not isinstance(series_id, str) for series_id in series_ids):
            raise ValueError(
                "Todos los identificadores deben ser cadenas de texto."
            )

        normalized = list(dict.fromkeys(
            series_id.strip().upper()
            for series_id in series_ids
        ))

        if any(not series_id for series_id in normalized):
            raise ValueError(
                "Los identificadores de serie no pueden estar vacíos."
            )

        return normalized

    def download_series(
        self,
        series_ids: list[str],
        start: str,
        end: str,
    ) -> dict[str, MacroSeries]:
        """
        Descarga series de FRED y devuelve objetos MacroSeries.

        Las observaciones ausentes, representadas por ".", se descartan.
        La fecha final se envía a FRED de forma inclusiva.
        """
        self._validate_dates(start, end)
        normalized_ids = self._normalize_series_ids(series_ids)

        results: dict[str, MacroSeries] = {}

        for series_id in normalized_ids:
            params = {
                "series_id": series_id,
                "api_key": self.api_key,
                "file_type": "json",
                "observation_start": start,
                "observation_end": end,
            }

            try:
                response = requests.get(
                    self.API_URL,
                    params=params,
                    timeout=self.timeout,
                )
                response.raise_for_status()

            except requests.HTTPError as error:
                status_code = getattr(
                    getattr(error, "response", None),
                    "status_code",
                    None,
                )
                detail = (
                    f"HTTP {status_code}"
                    if status_code is not None
                    else "error HTTP"
                )
                raise requests.HTTPError(
                    f"FRED no pudo consultar la serie "
                    f"{series_id}: {detail}. "
                    "La URL y las credenciales se han omitido."
                ) from None

            except requests.RequestException:
                raise RuntimeError(
                    f"No se pudo conectar con FRED para la serie "
                    f"{series_id}. La URL y las credenciales "
                    "se han omitido."
                ) from None

            payload = response.json()

            if not isinstance(payload, dict):
                raise ValueError(
                    f"Respuesta no válida de FRED para {series_id}."
                )

            if payload.get("error_code") or payload.get("error_message"):
                message = str(
                    payload.get("error_message", "Error desconocido")
                )
                message = message.replace(
                    self.api_key,
                    "[CLAVE OCULTA]",
                )
                raise ValueError(
                    f"Error de FRED para {series_id}: {message}."
                )

            observations = payload.get("observations")

            if not isinstance(observations, list):
                raise ValueError(
                    f"FRED no ha devuelto observaciones válidas "
                    f"para {series_id}."
                )

            dates = []
            values = []

            for observation in observations:
                if not isinstance(observation, dict):
                    raise ValueError(
                        f"Observación no válida en la serie {series_id}."
                    )

                raw_value = observation.get("value")
                raw_date = observation.get("date")

                # FRED utiliza "." para representar datos ausentes.
                if raw_value in (None, "", "."):
                    continue

                date = pd.to_datetime(raw_date, errors="coerce")
                value = pd.to_numeric(raw_value, errors="coerce")

                if pd.isna(date) or pd.isna(value):
                    raise ValueError(
                        f"Observación con fecha o valor no válido "
                        f"en la serie {series_id}."
                    )

                dates.append(date)
                values.append(float(value))

            if not values:
                raise ValueError(
                    f"FRED no ha devuelto observaciones válidas "
                    f"para {series_id} en el periodo solicitado."
                )

            series = pd.Series(
                values,
                index=pd.DatetimeIndex(dates),
                name=series_id,
                dtype=float,
            )

            results[series_id] = MacroSeries(
                series_id=series_id,
                values=series,
            )

        return results
