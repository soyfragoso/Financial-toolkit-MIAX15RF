import numpy as np
import pandas as pd
import pytest

from Financial_toolkit.models.portfolio import Portfolio
from Financial_toolkit.models.price_series import PriceSeries


@pytest.fixture
def dates():
    return pd.date_range("2024-01-01", periods=5)


@pytest.fixture
def portfolio(dates):
    result = Portfolio()
    result.add_asset(
        PriceSeries("AAA", pd.Series([100, 110, 99, 108.9, 119.79], index=dates)),
        0.5,
    )
    result.add_asset(
        PriceSeries("BBB", pd.Series([50, 50, 50, 50, 50], index=dates)),
        0.5,
    )
    return result


def test_portfolio_mean_and_median(portfolio):
    # AAA: +10 %, -10 %, +10 %, +10 %; BBB: 0 %. Cartera = mitad.
    assert portfolio.mean_return() == pytest.approx(0.025)
    assert portfolio.median_return() == pytest.approx(0.05)


def test_portfolio_maximum_drawdown(portfolio):
    # Cartera: +5 %, -5 % => 1.05 -> 0.9975, caída de -5 % desde el máximo.
    assert portfolio.maximum_drawdown() == pytest.approx(-0.05)


def test_portfolio_maximum_drawdown_from_first_day(dates):
    result = Portfolio()
    result.add_asset(
        PriceSeries("AAA", pd.Series([100, 90, 95, 96, 97], index=dates)),
        1.0,
    )

    assert result.maximum_drawdown() == pytest.approx(-0.10)
