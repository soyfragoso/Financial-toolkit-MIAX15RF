import matplotlib.pyplot as plt
import pandas as pd

from Financial_toolkit.models.portfolio import Portfolio


def generate_portfolio_plots(
    portfolio: Portfolio,
    show: bool = True,
) -> dict[str, plt.Figure]:
    """
    Genera visualizaciones del rendimiento y riesgo de una cartera.

    Devuelve:
        - cumulative_returns: rentabilidad acumulada de los activos y cartera.
        - correlation_matrix: matriz de correlaciones entre activos.
        - portfolio_evolution: evolución del valor de la cartera.
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

    if show:
        plt.show()

    return figures
