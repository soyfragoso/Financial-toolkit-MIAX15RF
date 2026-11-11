import numpy as np
import pandas as pd


class DataPreprocessor:
    """
    Limpia, valida y estandariza datos financieros.

    Por defecto valida la integridad financiera y elimina registros
    incompletos, manteniendo la compatibilidad con el comportamiento
    anterior.

    También permite conservar observaciones incompletas o inválidas
    para inspección, sin que ello autorice cálculos financieros.
    """

    REQUIRED_COLUMNS = ["ticker", "date", "close"]

    NUMERIC_COLUMNS = [
        "open",
        "high",
        "low",
        "close",
        "adj_close",
        "volume",
    ]

    def preprocess(
        self,
        data: pd.DataFrame,
        drop_incomplete: bool = True,
        validate_integrity: bool = True,
    ) -> pd.DataFrame:
        """
        Normaliza y procesa los datos financieros.

        Parameters
        ----------
        data : pd.DataFrame
            Datos recibidos del proveedor.

        drop_incomplete : bool, default=True
            True:
                Elimina registros sin ticker, fecha o cierre válido
                y elimina duplicados.

            False:
                Conserva observaciones incompletas y duplicados.

        validate_integrity : bool, default=True
            True:
                Rechaza valores infinitos, cierres no positivos
                y registros OHLC incoherentes.

            False:
                No rechaza esas incidencias. Permite conservar
                los datos para inspección, no para cálculos.

        Returns
        -------
        pd.DataFrame
            Copia normalizada y ordenada de los datos.
        """

        if not isinstance(data, pd.DataFrame):
            raise TypeError(
                "Los datos deben estar en un DataFrame."
            )

        if not isinstance(drop_incomplete, bool):
            raise TypeError(
                "drop_incomplete debe ser True o False."
            )

        if not isinstance(validate_integrity, bool):
            raise TypeError(
                "validate_integrity debe ser True o False."
            )

        if data.empty:
            raise ValueError(
                "El DataFrame está vacío."
            )

        missing_columns = [
            column
            for column in self.REQUIRED_COLUMNS
            if column not in data.columns
        ]

        if missing_columns:
            raise ValueError(
                f"Faltan columnas obligatorias: {missing_columns}"
            )

        result = data.copy()

        result["ticker"] = (
            result["ticker"]
            .astype("string")
            .str.strip()
            .str.upper()
        )

        result["date"] = pd.to_datetime(
            result["date"],
            errors="coerce",
        )

        for column in self.NUMERIC_COLUMNS:
            if column in result.columns:
                result[column] = pd.to_numeric(
                    result[column],
                    errors="coerce",
                )

        if validate_integrity:
            for column in self.NUMERIC_COLUMNS:
                if column not in result.columns:
                    continue

                values = (
                    result[column]
                    .dropna()
                    .to_numpy(dtype=float)
                )

                if not np.isfinite(values).all():
                    raise ValueError(
                        f"La columna {column} contiene valores no finitos."
                    )

            if (result["close"].dropna() <= 0).any():
                raise ValueError(
                    "Los precios de cierre deben ser positivos."
                )

        if drop_incomplete:
            result = result.dropna(
                subset=self.REQUIRED_COLUMNS
            )

            result = result[
                result["ticker"] != ""
            ]

            if result.empty:
                raise ValueError(
                    "No quedan registros con ticker, fecha "
                    "y cierre válidos."
                )

            result = result.drop_duplicates(
                subset=["ticker", "date"],
                keep="last",
            )

        if validate_integrity:
            ohlc_columns = [
                "open",
                "high",
                "low",
                "close",
            ]

            if all(
                column in result.columns
                for column in ohlc_columns
            ):
                complete_ohlc = (
                    result[ohlc_columns]
                    .notna()
                    .all(axis=1)
                )

                valid_ohlc = (
                    (result["high"] >= result["low"])
                    & (result["high"] >= result["open"])
                    & (result["high"] >= result["close"])
                    & (result["low"] <= result["open"])
                    & (result["low"] <= result["close"])
                )

                invalid_rows = (
                    complete_ohlc & ~valid_ohlc
                )

                if invalid_rows.any():
                    raise ValueError(
                        "Se han encontrado registros con precios OHLC "
                        "incoherentes."
                    )

        result = result.sort_values(
            ["ticker", "date"],
            na_position="last",
        ).reset_index(drop=True)

        return result
