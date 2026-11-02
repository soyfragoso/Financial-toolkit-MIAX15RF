import matplotlib
matplotlib.use("Agg")

import numpy as np
import pandas as pd
import pytest

from Financial_toolkit.models.portfolio import Portfolio
from Financial_toolkit.models.price_series import PriceSeries
from Financial_toolkit.analytics.plots import generate_portfolio_plots


@pytest.fixture
def portfolio():
    dates = pd.date_range("2024-01-01", periods=100)

    prices_a = pd.Series(
        np.linspace(100, 120, 100),
        index=dates,
    )

    prices_b = pd.Series(
        np.linspace(80, 95, 100),
        index=dates,
    )

    result = Portfolio()
    result.add_asset(PriceSeries("AAA", prices_a), 0.6)
    result.add_asset(PriceSeries("BBB", prices_b), 0.4)

    return result


def test_generates_three_figures(portfolio):
    figures = generate_portfolio_plots(portfolio, show=False)

    assert set(figures) == {
        "cumulative_returns",
        "correlation_matrix",
        "portfolio_evolution",
    }


def test_figures_are_matplotlib_figures(portfolio):
    import matplotlib.pyplot as plt

    figures = generate_portfolio_plots(portfolio, show=False)

    for figure in figures.values():
        assert isinstance(figure, plt.Figure)
        plt.close(figure)


def test_rejects_invalid_portfolio():
    with pytest.raises(TypeError):
        generate_portfolio_plots("invalid")


def test_rejects_empty_portfolio():
    with pytest.raises(ValueError):
        generate_portfolio_plots(Portfolio())


def test_portfolio_plots_report_method(portfolio):
    import matplotlib.pyplot as plt

    figures = portfolio.plots_report(show=False)

    assert set(figures) == {
        "cumulative_returns",
        "correlation_matrix",
        "portfolio_evolution",
    }

    for figure in figures.values():
        plt.close(figure)
