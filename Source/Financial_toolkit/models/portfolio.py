import numpy as np
import pandas as pd

from Financial_toolkit.models.price_series import PriceSeries


class Portfolio:
    """
    Representa una cartera de activos financieros.
    """

    def __init__(self):
        self.assets: dict[str, PriceSeries] = {}
        self.weights: dict[str, float] = {}

    def add_asset(
        self,
        price_series: PriceSeries,
        weight: float,
    ) -> None:
        """Añade un activo con su ponderación."""

        if not isinstance(price_series, PriceSeries):
            raise TypeError("El activo debe ser una instancia de PriceSeries.")

        ticker = price_series.ticker

        if ticker in self.assets:
            raise ValueError(f"El activo {ticker} ya existe en la cartera.")

        if isinstance(weight, bool) or not isinstance(weight, (int, float)):
            raise TypeError("La ponderación debe ser numérica.")

        if not np.isfinite(weight) or weight <= 0 or weight > 1:
            raise ValueError("La ponderación debe ser mayor que 0 y menor o igual a 1.")

        self.assets[ticker] = price_series
        self.weights[ticker] = float(weight)

    def validate_weights(self) -> bool:
        """Comprueba que las ponderaciones sumen 1."""

        if not self.weights:
            raise ValueError("La cartera no contiene activos.")

        if not np.isclose(sum(self.weights.values()), 1.0):
            raise ValueError("Las ponderaciones deben sumar 1.")

        return True

    def returns(self) -> pd.Series:
        """Calcula las rentabilidades históricas de la cartera."""

        self.validate_weights()

        returns = pd.concat(
            {
                ticker: asset.returns()
                for ticker, asset in self.assets.items()
            },
            axis=1,
        ).dropna()

        weights = pd.Series(self.weights)

        return returns.mul(weights).sum(axis=1)

    def annualized_return(self, periods: int = 252) -> float:
        """Calcula la rentabilidad anualizada."""

        if isinstance(periods, bool) or not isinstance(periods, int) or periods <= 0:
            raise ValueError("Los períodos deben ser un entero positivo.")

        portfolio_returns = self.returns()

        if portfolio_returns.empty:
            raise ValueError("No hay suficientes datos para calcular la rentabilidad.")

        cumulative_return = (1 + portfolio_returns).prod()

        return float(cumulative_return ** (periods / len(portfolio_returns)) - 1)

    def volatility(self, periods: int = 252) -> float:
        """Calcula la volatilidad anualizada."""

        if isinstance(periods, bool) or not isinstance(periods, int) or periods <= 0:
            raise ValueError("Los períodos deben ser un entero positivo.")

        portfolio_returns = self.returns()

        if len(portfolio_returns) < 2:
            raise ValueError("Se necesitan al menos dos rentabilidades.")

        return float(portfolio_returns.std(ddof=1) * np.sqrt(periods))

    def report(self, periods: int = 252) -> str:
        """
        Genera un informe Markdown con las métricas y diagnósticos
        de la cartera.
        """
        from Financial_toolkit.analytics.reports import (
            generate_portfolio_report,
        )

        return generate_portfolio_report(self, periods=periods)

    def plots_report(self, show: bool = True):
        """
        Genera las visualizaciones de rendimiento y riesgo de la cartera.
        """
        from Financial_toolkit.analytics.plots import (
            generate_portfolio_plots,
        )

        return generate_portfolio_plots(self, show=show)

    def monte_carlo(
        self,
        initial_value: float = 100_000,
        days: int = 252,
        simulations: int = 1000,
        seed: int | None = None,
    ):
        """
        Crea un simulador Monte Carlo para la cartera.

        Devuelve una instancia de PortfolioMonteCarloSimulator.
        """
        from Financial_toolkit.simulation.monte_carlo import (
            PortfolioMonteCarloSimulator,
        )

        return PortfolioMonteCarloSimulator(
            portfolio=self,
            initial_value=initial_value,
            days=days,
            simulations=simulations,
            seed=seed,
        )
