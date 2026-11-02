import numpy as np
import pandas as pd
import pytest

from Financial_toolkit.models.portfolio import Portfolio
from Financial_toolkit.models.price_series import PriceSeries


@pytest.fixture
def portfolio():
    dates = pd.date_range("2025-01-01", periods=4)

    asset_a = PriceSeries(
        "AAPL",
        pd.Series([100, 105, 110, 115], index=dates),
    )

    asset_b = PriceSeries(
        "MSFT",
        pd.Series([200, 202, 206, 210], index=dates),
    )

    result = Portfolio()
    result.add_asset(asset_a, 0.6)
    result.add_asset(asset_b, 0.4)

    return result


def test_portfolio_adds_assets(portfolio):
    assert len(portfolio.assets) == 2
    assert portfolio.weights["AAPL"] == 0.6
    assert portfolio.weights["MSFT"] == 0.4


def test_portfolio_validates_weights(portfolio):
    assert portfolio.validate_weights() is True


def test_portfolio_rejects_invalid_asset():
    portfolio = Portfolio()

    with pytest.raises(TypeError):
        portfolio.add_asset("AAPL", 1.0)


def test_portfolio_rejects_duplicate_assets(portfolio):
    asset = portfolio.assets["AAPL"]

    with pytest.raises(ValueError, match="ya existe"):
        portfolio.add_asset(asset, 0.2)


def test_portfolio_rejects_invalid_weights():
    portfolio = Portfolio()

    asset = PriceSeries("AAPL", pd.Series([100, 105]))

    with pytest.raises(ValueError):
        portfolio.add_asset(asset, 0)


def test_portfolio_rejects_weights_not_summing_to_one():
    portfolio = Portfolio()

    asset_a = PriceSeries("AAPL", pd.Series([100, 105]))
    asset_b = PriceSeries("MSFT", pd.Series([200, 205]))

    portfolio.add_asset(asset_a, 0.6)
    portfolio.add_asset(asset_b, 0.3)

    with pytest.raises(ValueError):
        portfolio.validate_weights()


def test_portfolio_calculates_returns(portfolio):
    result = portfolio.returns()

    assert len(result) == 3
    assert np.isfinite(result.to_numpy()).all()


def test_portfolio_calculates_annualized_return(portfolio):
    result = portfolio.annualized_return()

    assert isinstance(result, float)
    assert np.isfinite(result)


def test_portfolio_calculates_volatility(portfolio):
    result = portfolio.volatility()

    assert isinstance(result, float)
    assert result >= 0


def test_portfolio_rejects_invalid_periods(portfolio):
    with pytest.raises(ValueError):
        portfolio.volatility(periods=0)