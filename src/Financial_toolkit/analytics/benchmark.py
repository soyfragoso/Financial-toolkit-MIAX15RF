from dataclasses import dataclass

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from Financial_toolkit.models.portfolio import Portfolio
from Financial_toolkit.models.price_series import PriceSeries


@dataclass(frozen=True)
class BenchmarkComparison:
    """
    Resultado de comparar una cartera con un índice de referencia
    sobre las fechas que tienen en común.
    """

    benchmark: str
    start: pd.Timestamp
    end: pd.Timestamp
    observations: int
    portfolio_return: float
    benchmark_return: float
    portfolio_annualized: float
    benchmark_annualized: float
    portfolio_volatility: float
    benchmark_volatility: float
    portfolio_max_drawdown: float
    benchmark_max_drawdown: float
    beta: float
    correlation: float
    tracking_error: float
    days_outperforming: float

    @property
    def excess_return(self) -> float:
        """Diferencia de rentabilidad acumulada (cartera - índice)."""
        return self.portfolio_return - self.benchmark_return

    @property
    def excess_annualized(self) -> float:
        """Diferencia de rentabilidad anualizada (cartera - índice)."""
        return self.portfolio_annualized - self.benchmark_annualized

    @property
    def beats_benchmark(self) -> bool:
        """True si la cartera acumula más rentabilidad que el índice."""
        return self.portfolio_return > self.benchmark_return


def _aligned_returns(
    portfolio: Portfolio,
    benchmark: PriceSeries,
) -> pd.DataFrame:
    if not isinstance(portfolio, Portfolio):
        raise TypeError("Se debe proporcionar una instancia de Portfolio.")

    if not isinstance(benchmark, PriceSeries):
        raise TypeError("El índice debe ser una instancia de PriceSeries.")

    aligned = pd.concat(
        {
            "portfolio": portfolio.returns(),
            "benchmark": benchmark.returns(),
        },
        axis=1,
    ).dropna()

    if len(aligned) < 2:
        raise ValueError(
            "La cartera y el índice no tienen suficientes fechas en común."
        )

    return aligned


def _max_drawdown(returns: pd.Series) -> float:
    values = pd.concat([
        pd.Series([1.0]),
        (1 + returns).cumprod().reset_index(drop=True),
    ])
    return float((values / values.cummax() - 1).min())


def compare_with_benchmark(
    portfolio: Portfolio,
    benchmark: PriceSeries,
    periods: int = 252,
) -> BenchmarkComparison:
    """
    Compara la cartera con un índice en las fechas comunes a ambos.

    Las fechas se alinean antes de calcular nada, de modo que activos
    e índices con calendarios distintos son comparables.
    """

    if isinstance(periods, bool) or not isinstance(periods, int) or periods <= 0:
        raise ValueError("Los períodos deben ser un entero positivo.")

    aligned = _aligned_returns(portfolio, benchmark)
    portfolio_returns = aligned["portfolio"]
    benchmark_returns = aligned["benchmark"]
    observations = len(aligned)

    def cumulative(returns: pd.Series) -> float:
        return float((1 + returns).prod() - 1)

    def annualized(returns: pd.Series) -> float:
        return float((1 + returns).prod() ** (periods / len(returns)) - 1)

    def volatility(returns: pd.Series) -> float:
        return float(returns.std(ddof=1) * np.sqrt(periods))

    benchmark_variance = float(benchmark_returns.var(ddof=1))

    beta = (
        float(portfolio_returns.cov(benchmark_returns) / benchmark_variance)
        if benchmark_variance > 0
        else float("nan")
    )

    correlation = float(portfolio_returns.corr(benchmark_returns))

    active_returns = portfolio_returns - benchmark_returns

    return BenchmarkComparison(
        benchmark=benchmark.ticker,
        start=aligned.index[0],
        end=aligned.index[-1],
        observations=observations,
        portfolio_return=cumulative(portfolio_returns),
        benchmark_return=cumulative(benchmark_returns),
        portfolio_annualized=annualized(portfolio_returns),
        benchmark_annualized=annualized(benchmark_returns),
        portfolio_volatility=volatility(portfolio_returns),
        benchmark_volatility=volatility(benchmark_returns),
        portfolio_max_drawdown=_max_drawdown(portfolio_returns),
        benchmark_max_drawdown=_max_drawdown(benchmark_returns),
        beta=beta,
        correlation=correlation,
        tracking_error=float(active_returns.std(ddof=1) * np.sqrt(periods)),
        days_outperforming=float((active_returns > 0).mean()),
    )


def _friendly_name(symbol: str) -> str:
    """Traduce un símbolo (^GSPC, SPY...) al nombre del índice."""
    from Financial_toolkit.data.benchmarks import INDEX_NAMES, INDEX_SYMBOLS

    for key, symbols in INDEX_SYMBOLS.items():
        if symbol in symbols.values():
            return f"{INDEX_NAMES[key]} ({symbol})"

    return symbol


def plot_benchmark_comparison(
    portfolio: Portfolio,
    benchmark: PriceSeries,
    benchmark_label: str | None = None,
) -> plt.Figure:
    """
    Gráfico de la cartera frente al índice.

    Arriba: crecimiento de 1 unidad invertida en cada uno.
    Abajo: rentabilidad relativa acumulada (por encima de 0 = la cartera
    va por delante del índice).
    """

    aligned = _aligned_returns(portfolio, benchmark)
    label = benchmark_label or _friendly_name(benchmark.ticker)

    growth = (1 + aligned).cumprod()
    relative = growth["portfolio"] / growth["benchmark"] - 1

    figure, (ax_growth, ax_relative) = plt.subplots(
        2,
        1,
        figsize=(10, 7),
        sharex=True,
        gridspec_kw={"height_ratios": [2, 1]},
    )

    ax_growth.plot(growth.index, growth["portfolio"], label="Cartera", linewidth=2)
    ax_growth.plot(
        growth.index,
        growth["benchmark"],
        label=label,
        linewidth=2,
        linestyle="--",
    )
    ax_growth.set_title(f"Cartera frente a {label}")
    ax_growth.set_ylabel("Crecimiento de 1 unidad")
    ax_growth.legend()
    ax_growth.grid(True, alpha=0.3)

    ax_relative.fill_between(
        relative.index,
        relative,
        0,
        where=relative >= 0,
        alpha=0.4,
        label="Por delante del índice",
    )
    ax_relative.fill_between(
        relative.index,
        relative,
        0,
        where=relative < 0,
        alpha=0.4,
        label="Por detrás del índice",
    )
    ax_relative.axhline(0, color="grey", linewidth=0.8)
    ax_relative.set_ylabel("Diferencia relativa")
    ax_relative.set_xlabel("Fecha")
    ax_relative.yaxis.set_major_formatter(
        plt.FuncFormatter(lambda value, _: f"{value:.0%}")
    )
    ax_relative.legend(loc="upper left")
    ax_relative.grid(True, alpha=0.3)

    figure.tight_layout()

    return figure


def compare_real_returns(
    portfolio: Portfolio,
    benchmark: PriceSeries,
    cpi: pd.Series,
    initial_capital: float = 100_000.0,
) -> dict:
    """
    Compara cartera e índice en términos reales (descontando inflación).

    Reutiliza calculate_real_performance (models/real_performance.py)
    con las mismas fechas comunes para la cartera y para el índice.
    El IPC es el que ya descarga el análisis macro de FRED (CPIAUCSL).
    """
    from Financial_toolkit.models.real_performance import (
        calculate_real_performance,
    )

    aligned = _aligned_returns(portfolio, benchmark)

    portfolio_real = calculate_real_performance(
        aligned["portfolio"],
        cpi,
        initial_capital,
    )
    benchmark_real = calculate_real_performance(
        aligned["benchmark"],
        cpi,
        initial_capital,
    )

    return {
        "inflation_accumulated": portfolio_real["inflation_accumulated"],
        "portfolio_real_return": portfolio_real["real_return"],
        "benchmark_real_return": benchmark_real["real_return"],
        "portfolio_real_final_value": portfolio_real["real_final_value"],
        "benchmark_real_final_value": benchmark_real["real_final_value"],
        "beats_benchmark_real": (
            portfolio_real["real_return"] > benchmark_real["real_return"]
        ),
        "portfolio_beats_inflation": portfolio_real["real_return"] > 0,
        "benchmark_beats_inflation": benchmark_real["real_return"] > 0,
    }
