import numpy as np
import pandas as pd
from Financial_toolkit.models.portfolio import Portfolio


class MonteCarloSimulator:
    """
    Simula trayectorias de precios mediante movimiento browniano geométrico.
    """

    def __init__(
        self,
        initial_price: float,
        expected_return: float,
        volatility: float,
        days: int = 252,
        simulations: int = 1000,
        seed: int | None = None,
    ):
        if not np.isfinite(initial_price) or initial_price <= 0:
            raise ValueError("El precio inicial debe ser positivo y finito.")

        if not np.isfinite(expected_return):
            raise ValueError("La rentabilidad esperada debe ser finita.")

        if not np.isfinite(volatility) or volatility < 0:
            raise ValueError("La volatilidad debe ser finita y no negativa.")

        if isinstance(days, bool) or not isinstance(days, int) or days <= 0:
            raise ValueError("Los días deben ser un entero positivo.")

        if (
            isinstance(simulations, bool)
            or not isinstance(simulations, int)
            or simulations <= 0
        ):
            raise ValueError("El número de simulaciones debe ser positivo.")

        self.initial_price = float(initial_price)
        self.expected_return = float(expected_return)
        self.volatility = float(volatility)
        self.days = days
        self.simulations = simulations
        self.seed = seed

    def simulate(self) -> pd.DataFrame:
        """
        Genera trayectorias de precios mediante GBM.
        """

        rng = np.random.default_rng(self.seed)

        dt = 1 / 252

        random_shocks = rng.standard_normal(
            (self.days, self.simulations)
        )

        daily_returns = (
            (self.expected_return - 0.5 * self.volatility ** 2) * dt
            + self.volatility * np.sqrt(dt) * random_shocks
        )

        log_returns = np.vstack([
            np.zeros(self.simulations),
            daily_returns,
        ])

        log_prices = np.cumsum(log_returns, axis=0)

        prices = self.initial_price * np.exp(log_prices)

        return pd.DataFrame(
            prices,
            columns=[
                f"simulation_{i + 1}"
                for i in range(self.simulations)
            ],
        )

    def final_values(self) -> pd.Series:
        """Devuelve el precio final de cada simulación."""

        return self.simulate().iloc[-1]

    def value_at_risk(self, confidence_level: float = 0.95) -> float:
        """
        Calcula el VaR como pérdida monetaria respecto al precio inicial.
        """

        self._validate_confidence_level(confidence_level)

        losses = self.initial_price - self.final_values()

        return float(
            np.quantile(losses, confidence_level)
        )

    def conditional_value_at_risk(
        self,
        confidence_level: float = 0.95,
    ) -> float:
        """
        Calcula el CVaR como pérdida media en la cola de pérdidas.
        """

        self._validate_confidence_level(confidence_level)

        losses = self.initial_price - self.final_values()

        var = np.quantile(losses, confidence_level)

        tail_losses = losses[losses >= var]

        return float(tail_losses.mean())

    @staticmethod
    def _validate_confidence_level(confidence_level: float) -> None:
        if (
            isinstance(confidence_level, bool)
            or not isinstance(confidence_level, (int, float))
            or not np.isfinite(confidence_level)
            or not 0 < confidence_level < 1
        ):
            raise ValueError(
                "El nivel de confianza debe estar entre 0 y 1."
            )


class PortfolioMonteCarloSimulator:
    """
    Simula la evolución de una cartera mediante movimiento browniano geométrico
    multivariante, teniendo en cuenta la correlación entre sus activos.
    """

    def __init__(
        self,
        portfolio: Portfolio,
        initial_value: float = 100_000,
        days: int = 252,
        simulations: int = 1000,
        seed: int | None = None,
    ):
        if not isinstance(portfolio, Portfolio):
            raise TypeError("Se debe proporcionar una instancia de Portfolio.")

        if (
            isinstance(initial_value, bool)
            or not isinstance(initial_value, (int, float))
            or not np.isfinite(initial_value)
            or initial_value <= 0
        ):
            raise ValueError("El valor inicial debe ser positivo y finito.")

        if isinstance(days, bool) or not isinstance(days, int) or days <= 0:
            raise ValueError("Los días deben ser un entero positivo.")

        if (
            isinstance(simulations, bool)
            or not isinstance(simulations, int)
            or simulations <= 0
        ):
            raise ValueError("El número de simulaciones debe ser positivo.")

        portfolio.validate_weights()

        self.portfolio = portfolio
        self.initial_value = float(initial_value)
        self.days = days
        self.simulations = simulations
        self.seed = seed

    def simulate(self) -> pd.DataFrame:
        """Genera trayectorias del valor total de la cartera."""

        tickers = list(self.portfolio.assets)

        historical_returns = pd.concat(
            {
                ticker: self.portfolio.assets[ticker].log_returns()
                for ticker in tickers
            },
            axis=1,
        ).dropna()

        if len(historical_returns) < 2:
            raise ValueError(
                "Se necesitan al menos dos observaciones de rentabilidad "
                "histórica por activo."
            )

        mean_returns = historical_returns.mean().to_numpy()
        covariance = np.atleast_2d(
            historical_returns.cov().to_numpy()
        )

        latest_prices = np.array([
            self.portfolio.assets[ticker].prices.iloc[-1]
            for ticker in tickers
        ])

        weights = np.array([
            self.portfolio.weights[ticker]
            for ticker in tickers
        ])

        quantities = (
            self.initial_value * weights / latest_prices
        )

        rng = np.random.default_rng(self.seed)

        simulated_returns = rng.multivariate_normal(
            mean_returns,
            covariance,
            size=(self.days, self.simulations),
        )

        log_prices = np.log(latest_prices)[None, None, :] + np.cumsum(
            simulated_returns,
            axis=0,
        )

        log_prices = np.concatenate(
            [
                np.broadcast_to(
                    np.log(latest_prices),
                    (1, self.simulations, len(tickers)),
                ),
                log_prices,
            ],
            axis=0,
        )

        simulated_prices = np.exp(log_prices)

        portfolio_values = np.sum(
            simulated_prices * quantities[None, None, :],
            axis=2,
        )

        return pd.DataFrame(
            portfolio_values,
            columns=[
                f"simulation_{i + 1}"
                for i in range(self.simulations)
            ],
        )

    def final_values(self) -> pd.Series:
        """Devuelve el valor final de cada simulación."""

        return self.simulate().iloc[-1]

    def value_at_risk(self, confidence_level: float = 0.95) -> float:
        """Calcula el VaR como pérdida monetaria respecto al valor inicial."""

        MonteCarloSimulator._validate_confidence_level(confidence_level)

        losses = self.initial_value - self.final_values()

        return float(np.quantile(losses, confidence_level))

    def conditional_value_at_risk(
        self,
        confidence_level: float = 0.95,
    ) -> float:
        """Calcula el CVaR como pérdida media en la cola de pérdidas."""

        MonteCarloSimulator._validate_confidence_level(confidence_level)

        losses = self.initial_value - self.final_values()
        var = np.quantile(losses, confidence_level)
        tail_losses = losses[losses >= var]

        return float(tail_losses.mean())
