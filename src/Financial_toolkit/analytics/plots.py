import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from Financial_toolkit.models.portfolio import Portfolio


def generate_portfolio_plots(
    portfolio: Portfolio,
    show: bool = True,
    benchmark=None,
) -> dict[str, plt.Figure]:
    """
    Genera visualizaciones del rendimiento y riesgo de una cartera.

    Devuelve:
        - cumulative_returns: rentabilidad acumulada de los activos y cartera.
        - correlation_matrix: matriz de correlaciones entre activos.
        - portfolio_evolution: evolución del valor de la cartera.
        - returns_histogram: distribución de rentabilidades diarias de la
          cartera, con media, mediana y curva normal de referencia.
        - benchmark_comparison: cartera frente a un índice (solo si se
          pasa benchmark, un PriceSeries).
    """

    if not isinstance(portfolio, Portfolio):
        raise TypeError("Se debe proporcionar una instancia de Portfolio.")

    portfolio.validate_weights()

    asset_returns = pd.concat(
        {
            ticker: asset.returns()
            for ticker, asset in portfolio.assets.items()
        },
        axis=1,
    ).dropna()

    if asset_returns.empty:
        raise ValueError("No hay suficientes datos para generar gráficos.")

    weights = pd.Series(portfolio.weights)
    portfolio_returns = asset_returns.mul(weights).sum(axis=1)

    cumulative_assets = (1 + asset_returns).cumprod()
    cumulative_portfolio = (1 + portfolio_returns).cumprod()

    figures = {}

    # 1. Rentabilidad acumulada de los activos y de la cartera.
    fig_returns, ax_returns = plt.subplots(figsize=(10, 5))

    for ticker in cumulative_assets.columns:
        ax_returns.plot(
            cumulative_assets.index,
            cumulative_assets[ticker],
            label=ticker,
        )

    ax_returns.plot(
        cumulative_portfolio.index,
        cumulative_portfolio,
        label="Cartera",
        linewidth=2.5,
        linestyle="--",
    )

    ax_returns.set_title("Rentabilidad acumulada")
    ax_returns.set_xlabel("Fecha")
    ax_returns.set_ylabel("Crecimiento de 1 unidad invertida")
    ax_returns.legend()
    ax_returns.grid(True, alpha=0.3)
    fig_returns.tight_layout()

    figures["cumulative_returns"] = fig_returns

    # 2. Matriz de correlaciones entre activos.
    correlation = asset_returns.corr()

    fig_correlation, ax_correlation = plt.subplots(figsize=(7, 6))

    image = ax_correlation.imshow(
        correlation,
        vmin=-1,
        vmax=1,
        aspect="auto",
    )

    ax_correlation.set_xticks(range(len(correlation.columns)))
    ax_correlation.set_yticks(range(len(correlation.index)))
    ax_correlation.set_xticklabels(correlation.columns)
    ax_correlation.set_yticklabels(correlation.index)

    for i in range(len(correlation.index)):
        for j in range(len(correlation.columns)):
            value = correlation.iloc[i, j]
            ax_correlation.text(
                j,
                i,
                f"{value:.2f}",
                ha="center",
                va="center",
            )

    ax_correlation.set_title("Matriz de correlaciones")
    fig_correlation.colorbar(image, ax=ax_correlation)
    fig_correlation.tight_layout()

    figures["correlation_matrix"] = fig_correlation

    # 3. Evolución del valor de la cartera.
    fig_evolution, ax_evolution = plt.subplots(figsize=(10, 5))

    ax_evolution.plot(
        cumulative_portfolio.index,
        cumulative_portfolio,
        label="Valor relativo de la cartera",
        linewidth=2,
    )

    ax_evolution.set_title("Evolución de la cartera")
    ax_evolution.set_xlabel("Fecha")
    ax_evolution.set_ylabel("Valor relativo (base = 1)")
    ax_evolution.legend()
    ax_evolution.grid(True, alpha=0.3)
    fig_evolution.tight_layout()

    figures["portfolio_evolution"] = fig_evolution

    # 4. Histograma de rentabilidades diarias de la cartera.
    mean_return = float(portfolio_returns.mean())
    median_return = float(portfolio_returns.median())
    std_return = float(portfolio_returns.std(ddof=1)) if len(portfolio_returns) > 1 else 0.0

    fig_histogram, ax_histogram = plt.subplots(figsize=(10, 5))

    bins = min(50, max(10, len(portfolio_returns) // 5))

    ax_histogram.hist(
        portfolio_returns,
        bins=bins,
        density=True,
        alpha=0.6,
        edgecolor="white",
        label="Rentabilidades diarias",
    )

    if std_return > 0:
        x_values = np.linspace(
            portfolio_returns.min(),
            portfolio_returns.max(),
            200,
        )
        normal_density = (
            np.exp(-0.5 * ((x_values - mean_return) / std_return) ** 2)
            / (std_return * np.sqrt(2 * np.pi))
        )
        ax_histogram.plot(
            x_values,
            normal_density,
            color="black",
            linewidth=1.5,
            label="Normal de referencia",
        )

    ax_histogram.axvline(
        mean_return,
        color="tab:orange",
        linewidth=2,
        label=f"Media ({mean_return:.3%})",
    )
    ax_histogram.axvline(
        median_return,
        color="tab:green",
        linewidth=2,
        linestyle="--",
        label=f"Mediana ({median_return:.3%})",
    )

    ax_histogram.set_title("Distribución de rentabilidades diarias de la cartera")
    ax_histogram.set_xlabel("Rentabilidad diaria")
    ax_histogram.set_ylabel("Densidad")
    ax_histogram.xaxis.set_major_formatter(
        plt.FuncFormatter(lambda value, _: f"{value:.1%}")
    )
    ax_histogram.legend()
    ax_histogram.grid(True, alpha=0.3)
    fig_histogram.tight_layout()

    figures["returns_histogram"] = fig_histogram

    if benchmark is not None:
        from Financial_toolkit.analytics.benchmark import (
            plot_benchmark_comparison,
        )

        figures["benchmark_comparison"] = plot_benchmark_comparison(
            portfolio,
            benchmark,
        )

    if show:
        plt.show()

    return figures
