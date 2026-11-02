import numpy as np
import pandas as pd


class PriceSeries:
    """
    Representa la serie histórica de precios de un activo financiero.
    """

    def __init__(
        self,
        ticker: str,
        prices: pd.Series,
        dates: pd.Series | None = None,
    ):
        if not isinstance(ticker, str) or not ticker.strip():
            raise ValueError("El ticker debe ser una cadena no vacía.")

        if not isinstance(prices, pd.Series):
            raise TypeError("Los precios deben proporcionarse como pandas.Series.")

        if prices.empty:
            raise ValueError("La serie de precios no puede estar vacía.")

        clean_prices = pd.to_numeric(prices.copy(), errors="coerce")

        if clean_prices.isna().any():
            raise ValueError("Los precios contienen valores nulos o no numéricos.")

        if not np.isfinite(clean_prices.to_numpy(dtype=float)).all():
            raise ValueError("Los precios deben ser valores finitos.")

        if (clean_prices <= 0).any():
            raise ValueError("Los precios deben ser positivos.")

        if dates is not None:
            if not isinstance(dates, (pd.Series, pd.DatetimeIndex)):
                raise TypeError("Las fechas deben ser una Series o DatetimeIndex.")

            if len(dates) != len(clean_prices):
                raise ValueError("El número de fechas debe coincidir con los precios.")

            clean_dates = pd.to_datetime(dates, errors="coerce")

            if pd.isna(clean_dates).any():
                raise ValueError("Las fechas contienen valores inválidos.")

            if clean_dates.duplicated().any():
                raise ValueError("Las fechas no pueden estar duplicadas.")

            clean_prices.index = clean_dates

        elif isinstance(clean_prices.index, pd.DatetimeIndex):
            if clean_prices.index.has_duplicates:
                raise ValueError("Las fechas no pueden estar duplicadas.")

        self.ticker = ticker.strip().upper()
        self.prices = clean_prices.astype(float).sort_index()

    @property
    def dates(self) -> pd.DatetimeIndex:
        return pd.DatetimeIndex(self.prices.index)

    def returns(self) -> pd.Series:
        """Calcula las rentabilidades simples."""
        return self.prices.pct_change().dropna()

    def log_returns(self) -> pd.Series:
        """Calcula las rentabilidades logarítmicas."""
        return np.log(self.prices / self.prices.shift(1)).dropna()

    def to_dataframe(self) -> pd.DataFrame:
        """Devuelve los precios en formato DataFrame."""
        return pd.DataFrame({
            "ticker": self.ticker,
            "date": self.prices.index,
            "close": self.prices.values,
        })
