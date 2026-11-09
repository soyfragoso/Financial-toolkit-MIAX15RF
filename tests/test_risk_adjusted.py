import numpy as np
import pandas as pd
import pytest

from Financial_toolkit.analytics.risk_adjusted import (
    risk_adjusted_summary,
    risk_free_rate_from_macro,
    sharpe_ratio,
    sortino_ratio,
)
from Financial_toolkit.models.macro_series import MacroSeries
from Financial_toolkit.models.portfolio import Portfolio
from Financial_toolkit.models.price_series import PriceSeries


@pytest.fixture
def returns():
    rng = np.random.default_rng(42)
    dates = pd.bdate_range("2024-01-01", periods=500)
    return pd.Series(rng.normal(0.0005, 0.01, 500), index=dates)


@pytest.fixture
def portfolio(returns):
    prices_a = 100 * (1 + returns).cumprod()
    prices_b = 50 * (1 + returns.shift(5).fillna(0)).cumprod()

    result = Portfolio()
    result.add_asset(PriceSeries("AAA", prices_a), 0.6)
    result.add_asset(PriceSeries("BBB", prices_b), 0.4)
    return result


@pytest.fixture
def fed_funds():
    dates = pd.date_range("2024-01-01", periods=24, freq="MS")
    return MacroSeries("FEDFUNDS", pd.Series(np.full(24, 4.0), index=dates))


def test_sharpe_matches_manual_formula(returns):
    rf = 0.04
    excess = returns - rf / 252
    expected = excess.mean() / excess.std(ddof=1) * np.sqrt(252)

    assert sharpe_ratio(returns, rf) == pytest.approx(expected)


def test_higher_risk_free_rate_lowers_sharpe(returns):
    assert sharpe_ratio(returns, 0.05) < sharpe_ratio(returns, 0.0)


def test_sortino_matches_manual_formula(returns):
    rf = 0.02
    excess = returns - rf / 252
    downside = np.minimum(excess, 0)
    expected = excess.mean() * 252 / (np.sqrt((downside ** 2).mean()) * np.sqrt(252))

    assert sortino_ratio(returns, rf) == pytest.approx(expected)


def test_sortino_is_infinite_without_downside():
    positive = pd.Series([0.01, 0.02, 0.015, 0.01])

    assert sortino_ratio(positive) == float("inf")


def test_works_with_portfolio_and_price_series(portfolio):
    asset = portfolio.assets["AAA"]

    assert np.isfinite(sharpe_ratio(portfolio, 0.03))
    assert np.isfinite(sortino_ratio(portfolio, 0.03))
    assert np.isfinite(sharpe_ratio(asset, 0.03))


def test_risk_free_rate_from_fred_series(fed_funds):
    assert risk_free_rate_from_macro(fed_funds) == pytest.approx(0.04)


def test_risk_free_rate_respects_dates():
    dates = pd.date_range("2024-01-01", periods=4, freq="MS")
    series = MacroSeries("FEDFUNDS", pd.Series([5.0, 5.0, 3.0, 3.0], index=dates))

    assert risk_free_rate_from_macro(series, start="2024-03-01") == pytest.approx(0.03)


def test_risk_free_rate_without_data_in_period(fed_funds):
    with pytest.raises(ValueError):
        risk_free_rate_from_macro(fed_funds, start="2030-01-01")


def test_risk_free_rate_requires_macro_series():
    with pytest.raises(TypeError):
        risk_free_rate_from_macro(pd.Series([4.0, 4.1]))


@pytest.mark.parametrize("rate", [4.0, -2.0, float("nan"), "0.04", True])
def test_invalid_risk_free_rate(returns, rate):
    with pytest.raises(ValueError):
        sharpe_ratio(returns, rate)


@pytest.mark.parametrize("periods", [0, -252, 252.5, True])
def test_invalid_periods(returns, periods):
    with pytest.raises(ValueError):
        sortino_ratio(returns, 0.0, periods)


def test_zero_volatility_raises():
    with pytest.raises(ValueError):
        sharpe_ratio(pd.Series([0.01, 0.01, 0.01]))


def test_invalid_source_raises():
    with pytest.raises(TypeError):
        sharpe_ratio([0.01, 0.02])


def test_too_few_returns_raises():
    with pytest.raises(ValueError):
        sharpe_ratio(pd.Series([0.01]))


def test_summary_contains_both_ratios(returns):
    summary = risk_adjusted_summary(returns, 0.03)

    assert list(summary.index) == [
        "Tipo libre de riesgo",
        "Ratio de Sharpe",
        "Ratio de Sortino",
    ]
    assert summary["Tipo libre de riesgo"] == 0.03
    