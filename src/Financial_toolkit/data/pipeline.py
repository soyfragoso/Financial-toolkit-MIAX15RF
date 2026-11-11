"""Pipeline de descarga, diagnóstico y preparación de datos financieros."""

import numpy as np
import pandas as pd

from Financial_toolkit.data.downloader import DataDownloader
from Financial_toolkit.data.preprocessing import DataPreprocessor
from Financial_toolkit.data.providers import DataProvider
from Financial_toolkit.data.quality import analyze_data_quality


class DataPipeline:
    """
    Coordina descarga, diagnóstico y preparación de datos financieros.

    Operaciones:
        download_raw(): descarga sin eliminar observaciones.
        inspect(): diagnostica sin modificar los datos.
        process_raw(): aplica una política sobre datos ya descargados.
        run(): mantiene la interfaz anterior y ejecuta el flujo completo.

    Políticas:
        strict: detiene el proceso ante incidencias críticas.
        drop: elimina observaciones incompletas o inválidas.
        preserve: conserva los datos para inspección, no para cálculos.
        forward_fill: completa como máximo un cierre consecutivo por activo.
    """

    MISSING_POLICIES = {
        "strict",
        "drop",
        "preserve",
        "forward_fill",
    }

    OPTIONAL_COLUMNS = {"adj_close"}

    NUMERIC_COLUMNS = [
        "open",
        "high",
        "low",
        "close",
        "adj_close",
        "volume",
    ]

    def __init__(
        self,
        provider: DataProvider,
        missing_policy: str = "strict",
    ):
        self.downloader = DataDownloader(provider)
        self.preprocessor = DataPreprocessor()

        self._validate_policy(missing_policy)

        self.missing_policy = missing_policy
        self.last_quality_report = None
        self.last_post_quality_report = None
        self.last_processing_summary = None
        self.last_quality_issues = []
        self.last_download_diagnostic = None

    @classmethod
    def _validate_policy(cls, policy: str) -> None:
        if (
            not isinstance(policy, str)
            or policy not in cls.MISSING_POLICIES
        ):
            available = ", ".join(sorted(cls.MISSING_POLICIES))
            raise ValueError(
                "Política de datos faltantes no válida. "
                f"Opciones disponibles: {available}"
            )

    @staticmethod
    def _strict_issues(data: pd.DataFrame, report) -> list[str]:
        """Identifica incidencias que pueden comprometer el análisis."""

        issues = []

        for column in (
            "ticker",
            "date",
            "open",
            "high",
            "low",
            "close",
            "volume",
        ):
            # Solo se exige la integridad de las columnas presentes.
            # adj_close permanece como campo opcional.
            if column not in data.columns:
                continue

            missing = report.missing_by_column.get(column, 0)

            if missing:
                issues.append(
                    f"{column}: {missing} observaciones sin dato"
                )

        if report.invalid_date_rows:
            issues.append(
                f"Fechas no válidas: {report.invalid_date_rows}"
            )

        if report.duplicate_rows:
            issues.append(
                f"Registros duplicados: {report.duplicate_rows}"
            )

        if report.non_positive_close_rows:
            issues.append(
                "Precios de cierre iguales o inferiores a cero: "
                f"{report.non_positive_close_rows}"
            )

        if report.invalid_ohlc_rows:
            issues.append(
                "Registros con precios OHLC incoherentes: "
                f"{report.invalid_ohlc_rows}"
            )

        if report.negative_volume_rows:
            issues.append(
                f"Registros con volumen negativo: "
                f"{report.negative_volume_rows}"
            )

        for column, count in report.invalid_numeric_by_column.items():
            if count:
                issues.append(
                    f"Valores numéricos no válidos en {column}: {count}"
                )

        for column, count in report.infinite_by_column.items():
            if count:
                issues.append(
                    f"Valores infinitos en {column}: {count}"
                )

        return issues

    def download_raw(
        self,
        tickers: list[str],
        start: str,
        end: str,
    ) -> pd.DataFrame:
        """
        Descarga los datos originales sin aplicar tratamientos.

        La descarga se realiza una sola vez. El DataFrame devuelto
        puede utilizarse posteriormente en inspect() y process_raw().
        """

        self.last_quality_report = None
        self.last_post_quality_report = None
        self.last_processing_summary = None
        self.last_quality_issues = []
        self.last_download_diagnostic = None

        try:
            raw_data = self.downloader.download(
                tickers=tickers,
                start=start,
                end=end,
            )
        except Exception as error:
            provider = self.downloader.provider
            diagnostic = getattr(
                provider,
                "last_download_diagnostic",
                None,
            )

            if not diagnostic:
                diagnostic = {
                    "category": "PROVIDER_ERROR",
                    "detail": (
                        "El proveedor no pudo completar la descarga."
                    ),
                    "provider_message": str(error),
                }

            self.last_download_diagnostic = diagnostic.copy()
            self.last_quality_issues = [
                (
                    f"{diagnostic['category']}: "
                    f"{diagnostic['detail']}"
                )
            ]
            raise

        if not isinstance(raw_data, pd.DataFrame):
            raise TypeError(
                "El proveedor debe devolver un DataFrame."
            )

        if raw_data.empty:
            self.last_download_diagnostic = {
                "category": "EMPTY_RESPONSE",
                "detail": (
                    "El proveedor ha devuelto un DataFrame vacío."
                ),
                "provider_message": "",
            }
            self.last_quality_issues = [
                "EMPTY_RESPONSE: no se recibieron observaciones."
            ]
            raise ValueError(
                "El proveedor no ha devuelto observaciones."
            )

        return raw_data.copy()

    def inspect(self, raw_data: pd.DataFrame) -> dict:
        """
        Diagnostica los datos sin modificarlos.

        Devuelve el informe, las incidencias críticas y el número
        de filas recibidas.
        """

        if not isinstance(raw_data, pd.DataFrame):
            raise TypeError("raw_data debe ser un DataFrame.")

        if raw_data.empty:
            raise ValueError(
                "No hay datos que puedan someterse a inspección."
            )

        report = analyze_data_quality(raw_data)
        issues = self._strict_issues(raw_data, report)

        self.last_quality_report = report
        self.last_quality_issues = issues

        return {
            "report": report,
            "issues": list(issues),
            "rows_received": len(raw_data),
            "has_issues": bool(issues),
        }

    @staticmethod
    def _fill_last_close(
        data: pd.DataFrame,
    ) -> tuple[pd.DataFrame, int]:
        """
        Completa como máximo un cierre consecutivo por activo.

        Solo utiliza observaciones existentes. No crea fechas,
        no completa OHLC ni modifica el volumen.
        """

        result = data.copy()

        if "close" not in result.columns:
            return result, 0

        if not {"ticker", "date"}.issubset(result.columns):
            return result, 0

        result["ticker"] = (
            result["ticker"]
            .astype("string")
            .str.strip()
            .str.upper()
        )

        result["date"] = pd.to_datetime(
            result["date"],
            format="mixed",
            errors="coerce",
        )

        result["close"] = pd.to_numeric(
            result["close"],
            errors="coerce",
        )

        result = result.sort_values(
            ["ticker", "date"],
            na_position="last",
        )

        missing_before = int(result["close"].isna().sum())

        eligible = (
            result["ticker"].notna()
            & result["ticker"].ne("")
            & result["date"].notna()
        )

        eligible_rows = result.loc[eligible].copy()

        filled_close = (
            eligible_rows
            .groupby("ticker", sort=False)["close"]
            .ffill(limit=1)
        )

        result.loc[eligible, "close"] = filled_close

        missing_after = int(result["close"].isna().sum())

        return (
            result.reset_index(drop=True),
            missing_before - missing_after,
        )

    def _prepare_drop(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Elimina filas incompletas o inválidas antes del preprocesamiento.

        No modifica la fuente original. adj_close es opcional y su
        ausencia no provoca la eliminación de una observación.
        """

        result = data.copy()

        required = {"ticker", "date", "close"}
        missing_columns = required - set(result.columns)

        if missing_columns:
            raise ValueError(
                "Faltan columnas esenciales: "
                + ", ".join(sorted(missing_columns))
            )

        result["ticker"] = (
            result["ticker"]
            .astype("string")
            .str.strip()
            .str.upper()
        )
        result["date"] = pd.to_datetime(
            result["date"],
            format="mixed",
            errors="coerce",
        )

        valid = (
            result["ticker"].notna()
            & result["ticker"].ne("")
            & result["date"].notna()
        )

        for column in self.NUMERIC_COLUMNS:
            if column not in result.columns:
                continue

            original = result[column]
            converted = pd.to_numeric(original, errors="coerce")

            # Los campos opcionales ausentes no invalidan una fila.
            if column == "adj_close":
                invalid_text = original.notna() & converted.isna()
                valid &= ~invalid_text
            else:
                valid &= converted.notna()

            valid &= ~np.isinf(
                converted.fillna(0).to_numpy(dtype=float)
            )

            result[column] = converted

        if "close" in result.columns:
            valid &= result["close"].gt(0)

        if "volume" in result.columns:
            valid &= result["volume"].ge(0)

        ohlc_columns = {"open", "high", "low", "close"}

        if ohlc_columns.issubset(result.columns):
            complete_ohlc = result[
                ["open", "high", "low", "close"]
            ].notna().all(axis=1)

            coherent = (
                result["high"]
                >= result[["open", "close", "low"]].max(axis=1)
            ) & (
                result["low"]
                <= result[["open", "close", "high"]].min(axis=1)
            )

            valid &= (~complete_ohlc) | coherent

        result = result.loc[valid].copy()

        if result.empty:
            raise ValueError(
                "No quedan observaciones válidas después de "
                "eliminar los registros incompletos o inválidos."
            )

        return result

    def process_raw(
        self,
        raw_data: pd.DataFrame,
        missing_policy: str | None = None,
        recommendation: str | None = None,
        decision: str | None = None,
    ) -> pd.DataFrame:
        """
        Aplica una política a datos ya descargados y repite el diagnóstico.

        preserve permite inspección, pero no autoriza cálculos financieros
        cuando permanecen incidencias críticas.
        """

        policy = (
            self.missing_policy
            if missing_policy is None
            else missing_policy
        )
        self._validate_policy(policy)

        if not isinstance(raw_data, pd.DataFrame):
            raise TypeError("raw_data debe ser un DataFrame.")

        if raw_data.empty:
            raise ValueError("No hay datos para procesar.")

        initial = self.inspect(raw_data)
        initial_report = initial["report"]
        initial_issues = initial["issues"]

        rows_received = len(raw_data)
        filled_count = 0

        if policy == "strict":
            if initial_issues:
                details = "\n".join(
                    f"- {issue}" for issue in initial_issues
                )
                raise ValueError(
                    "No se puede continuar con el análisis porque "
                    "se han detectado problemas en los datos:\n"
                    f"{details}"
                )

            processed = self.preprocessor.preprocess(
                raw_data,
                drop_incomplete=True,
            )

        elif policy == "drop":
            cleaned = self._prepare_drop(raw_data)
            processed = self.preprocessor.preprocess(
                cleaned,
                drop_incomplete=True,
            )

        elif policy == "preserve":
            # Conserva incidencias para inspección.
            # Esta política nunca autoriza cálculos financieros.
            processed = self.preprocessor.preprocess(
                raw_data,
                drop_incomplete=False,
                validate_integrity=False,
            )

        else:
            filled_data, filled_count = self._fill_last_close(
                raw_data
            )
            cleaned = self._prepare_drop(filled_data)
            processed = self.preprocessor.preprocess(
                cleaned,
                drop_incomplete=True,
            )

        post_report = analyze_data_quality(processed)
        post_issues = self._strict_issues(processed, post_report)

        self.last_post_quality_report = post_report

        if policy != "preserve" and post_issues:
            details = "\n".join(
                f"- {issue}" for issue in post_issues
            )
            raise ValueError(
                "La validación posterior al tratamiento ha detectado "
                "problemas que impiden continuar:\n"
                f"{details}"
            )

        self.last_processing_summary = {
            "policy": policy,
            "recommendation": recommendation,
            "decision": decision or policy,
            "rows_received": rows_received,
            "rows_returned": len(processed),
            "rows_removed": rows_received - len(processed),
            "close_values_filled": filled_count,
            "missing_percentage": initial_report.missing_percentage,
            "completeness_percentage": (
                initial_report.completeness_percentage
            ),
            "quality_report": initial_report.to_dict(),
            "post_quality_report": post_report.to_dict(),
            "initial_issues": list(initial_issues),
            "remaining_issues": list(post_issues),
            "calculations_allowed": (
                policy != "preserve" and not post_issues
            ),
        }

        return processed

    def run(
        self,
        tickers: list[str],
        start: str,
        end: str,
        missing_policy: str | None = None,
    ) -> pd.DataFrame:
        """
        Mantiene la interfaz histórica: descarga y procesa en una llamada.
        """

        raw_data = self.download_raw(
            tickers=tickers,
            start=start,
            end=end,
        )

        return self.process_raw(
            raw_data=raw_data,
            missing_policy=missing_policy,
        )
