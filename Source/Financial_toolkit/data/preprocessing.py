import pandas as pd


class DataPreprocessor:
    """
    Limpia, valida y estandariza datos financieros.

    Recibe un DataFrame procedente de un proveedor de datos
    y devuelve una copia preparada para su análisis.
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

    def preprocess(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Ejecuta el proceso completo de preprocesamiento.
        """

        if not isinstance(data, pd.DataFrame):
            raise TypeError("Los datos deben estar en un DataFrame.")

        if data.empty:
            raise ValueError("El DataFrame está vacío.")

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

        # Normalizar los identificadores de los activos.
        result["ticker"] = (
            result["ticker"]
            .astype("string")
            .str.strip()
            .str.upper()
        )

        # Convertir fechas y valores numéricos.
        result["date"] = pd.to_datetime(
            result["date"],
            errors="coerce"
        )

        for column in self.NUMERIC_COLUMNS:
            if column in result.columns:
                result[column] = pd.to_numeric(
                    result[column],
                    errors="coerce"
                )

        # Eliminar registros sin información esencial.
        result = result.dropna(
            subset=self.REQUIRED_COLUMNS
        )

        result = result[
            result["ticker"] != ""
        ]

        if result.empty:
            raise ValueError(
                "No quedan registros con ticker, fecha y cierre válidos."
            )

        # Eliminar duplicados conservando el último registro.
        result = result.drop_duplicates(
            subset=["ticker", "date"],
            keep="last"
        )

        # Comprobar la coherencia de los precios OHLC.
        ohlc_columns = ["open", "high", "low", "close"]

        if all(column in result.columns for column in ohlc_columns):

            complete_ohlc = result[ohlc_columns].notna().all(axis=1)

            valid_ohlc = (
                (result["high"] >= result["low"])
                & (result["high"] >= result["open"])
                & (result["high"] >= result["close"])
                & (result["low"] <= result["open"])
                & (result["low"] <= result["close"])
            )

            invalid_rows = complete_ohlc & ~valid_ohlc

            if invalid_rows.any():
                raise ValueError(
                    "Se han encontrado registros con precios OHLC "
                    "incoherentes."
                )

        # Ordenar por activo y fecha.
        result = result.sort_values(
            ["ticker", "date"]
        ).reset_index(drop=True)

        return result
        return result
