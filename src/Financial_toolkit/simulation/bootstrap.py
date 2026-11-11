from numbers import Integral

import numpy as np
import pandas as pd

from Financial_toolkit.simulation.monte_carlo import PortfolioMonteCarloSimulator


class PortfolioBootstrapSimulator(PortfolioMonteCarloSimulator):
    """
    Simula la evolución de una cartera mediante bootstrap histórico.

    En lugar de suponer rentabilidades normales (GBM), cada día simulado
    toma una fecha real del histórico al azar y aplica las rentabilidades
    de todos los activos de esa fecha. Así se conservan las colas gordas,
    la asimetría y la correlación observadas entre activos.

    Con block_size > 1 se usa un bootstrap por bloques: se copian rachas
    de días consecutivos, lo que conserva parte de la dependencia temporal
    (por ejemplo, periodos de alta volatilidad seguidos).

    La cartera se mantiene sin rebalancear (buy and hold), igual que en
    PortfolioMonteCarloSimulator. Hereda final_values(), reset(),
    value_at_risk() y conditional_value_at_risk().
    """

    def __init__(
        self,
        portfolio,
        initial_value: float = 100_000,
        days: int = 252,
        simulations: int = 1000,
        block_size: int = 1,
        seed: int | None = None,
    ):
        super().__init__(
            portfolio=portfolio,
            initial_value=initial_value,
            days=days,
            simulations=simulations,
            seed=seed,
        )

        if (
            isinstance(block_size, bool)
            or not isinstance(block_size, Integral)
            or block_size <= 0
        ):
            raise ValueError("El tamaño de bloque debe ser un entero positivo.")

        self.block_size = int(block_size)

    def simulate(self) -> pd.DataFrame:
        """Genera trayectorias del valor total de la cartera."""

        tickers = list(self.portfolio.assets)

        historical_returns = pd.concat(
            {
                ticker: self.portfolio.assets[ticker].returns()
                for ticker in tickers
            },
            axis=1,
        ).dropna()

        observations = len(historical_returns)

        if observations < 2:
            raise ValueError(
                "Se necesitan al menos dos observaciones de rentabilidad "
                "histórica por activo."
            )

        if self.block_size > observations:
            raise ValueError(
                "El tamaño de bloque no puede superar el número de "
                "observaciones históricas."
            )

        returns_array = historical_returns.to_numpy(dtype=float)

        if not np.isfinite(returns_array).all():
            raise ValueError(
                "Los rendimientos históricos contienen valores no finitos."
            )

        rng = np.random.default_rng(self.seed)

        # Índices de los días históricos que se usarán en cada simulación.
        number_of_blocks = int(np.ceil(self.days / self.block_size))

        block_starts = rng.integers(
            0,
            observations - self.block_size + 1,
            size=(number_of_blocks, self.simulations),
        )

        indices = (
            block_starts[:, None, :]
            + np.arange(self.block_size)[None, :, None]
        ).reshape(number_of_blocks * self.block_size, self.simulations)

        indices = indices[: self.days]

        # Forma (días, simulaciones, activos).
        sampled_returns = returns_array[indices]

        growth = np.cumprod(1 + sampled_returns, axis=0)
        growth = np.concatenate(
            [
                np.ones((1, self.simulations, len(tickers))),
                growth,
            ],
            axis=0,
        )

        weights = np.array([
            self.portfolio.weights[ticker]
            for ticker in tickers
        ])

        # Cada activo arranca con initial_value * peso y evoluciona
        # con su propio crecimiento (sin rebalanceo).
        portfolio_values = self.initial_value * np.sum(
            growth * weights[None, None, :],
            axis=2,
        )

        result = pd.DataFrame(
            portfolio_values,
            columns=[
                f"simulation_{i + 1}"
                for i in range(self.simulations)
            ],
        )

        self._last_simulation = result
        return result
