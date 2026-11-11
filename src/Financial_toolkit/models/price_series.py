from dataclasses import dataclass, field

import numpy as np
import pandas as pd


@dataclass(init=False)
class PriceSeries:
    """
    Representa la serie histórica de precios de un activo financiero.

    Incluye estadísticas descriptivas, medias móviles y métricas de riesgo.
    """

    ticker: str
    prices: pd.Series
    mean: float = field(init=False)
    median: float = field(init=False)
    std: float = field(init=False)
    variance: float = field(init=False)
    minimum: float = field(init=False)
    maximum: float = field(init=False)

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

        self.mean = float(self.prices.mean())
        self.median = float(self.prices.median())
        self.std = float(self.prices.std(ddof=1)) if len(self.prices) > 1 else 0.0
        self.variance = (
            float(self.prices.var(ddof=1)) if len(self.prices) > 1 else 0.0
        )
        self.minimum = float(self.prices.min())
        self.maximum = float(self.prices.max())

    @classmethod
    def from_dataframe(cls, data: pd.DataFrame, ticker: str) -> "PriceSeries":
        """
        Crea un PriceSeries a partir del DataFrame estandarizado que
        devuelven los proveedores (columnas ticker, date y close).

        Funciona igual con cualquier proveedor porque todos comparten
        el mismo esquema de salida.
        """
        if not isinstance(data, pd.DataFrame):
            raise TypeError("Los datos deben estar en un DataFrame.")

        missing = {"ticker", "date", "close"} - set(data.columns)

        if missing:
            raise ValueError(f"Faltan columnas obligatorias: {sorted(missing)}")

        if not isinstance(ticker, str) or not ticker.strip():
            raise ValueError("El ticker debe ser una cadena no vacía.")

        symbol = ticker.strip().upper()
        asset_data = data[
            data["ticker"].astype(str).str.upper() == symbol
        ].sort_values("date")

        if asset_data.empty:
            raise ValueError(f"No hay datos para {symbol}.")

        prices = pd.Series(
            asset_data["close"].to_numpy(dtype=float),
            index=pd.DatetimeIndex(pd.to_datetime(asset_data["date"])),
            name=symbol,
        )

        return cls(ticker=symbol, prices=prices)

    @property
    def dates(self) -> pd.DatetimeIndex:
        """Devuelve las fechas de observación."""
        return pd.DatetimeIndex(self.prices.index)

    def returns(self) -> pd.Series:
        """Calcula las rentabilidades simples."""
        return self.prices.pct_change().dropna()

    def log_returns(self) -> pd.Series:
        """Calcula las rentabilidades logarítmicas."""
        return np.log(self.prices / self.prices.shift(1)).dropna()

    def moving_average(self, window: int = 20) -> pd.Series:
        """
        Calcula la media móvil simple conservando el índice de fechas.

        Los primeros window - 1 valores serán NaN.
        """
        if isinstance(window, bool) or not isinstance(window, int) or window <= 0:
            raise ValueError("La ventana debe ser un entero positivo.")

        return self.prices.rolling(window=window).mean()

    def maximum_drawdown(self) -> float:
        """
        Calcula la máxima caída porcentual desde un máximo histórico.
        """
        running_maximum = self.prices.cummax()
        drawdowns = self.prices / running_maximum - 1

        return float(drawdowns.min())

    def annualized_volatility(self, periods: int = 252) -> float:
        """
        Calcula la volatilidad anualizada de los rendimientos simples.
        """
        if isinstance(periods, bool) or not isinstance(periods, int) or periods <= 0:
            raise ValueError("Los períodos deben ser un entero positivo.")

        historical_returns = self.returns()

        if len(historical_returns) < 2:
            raise ValueError(
                "Se necesitan al menos dos rendimientos para calcular "
                "la volatilidad."
            )

        return float(historical_returns.std(ddof=1) * np.sqrt(periods))

    def skewness(self) -> float:
        """Calcula la asimetría de la distribución de rendimientos."""
        historical_returns = self.returns()

        if len(historical_returns) < 3:
            raise ValueError(
                "Se necesitan al menos tres rendimientos para calcular "
                "la asimetría."
            )

        return float(historical_returns.skew())

    def kurtosis(self) -> float:
        """
        Calcula la curtosis excedente de los rendimientos.

        Un valor cercano a cero indica una curtosis similar a la normal.
        """
        historical_returns = self.returns()

        if len(historical_returns) < 4:
            raise ValueError(
                "Se necesitan al menos cuatro rendimientos para calcular "
                "la curtosis."
            )

        return float(historical_returns.kurt())

    def to_dataframe(self) -> pd.DataFrame:
        """Devuelve los precios en formato DataFrame."""
        return pd.DataFrame({
            "ticker": self.ticker,
            "date": self.prices.index,
            "close": self.prices.values,
        })
