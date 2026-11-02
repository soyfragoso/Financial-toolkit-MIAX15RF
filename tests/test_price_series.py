import numpy as np
import pandas as pd
import pytest

from Financial_toolkit.models.price_series import PriceSeries


@pytest.fixture
def price_series():
    prices = pd.Series(
        [100, 105, 110, 108],
        index=pd.to_datetime([
            "2025-01-01",
            "2025-01-02",
            "2025-01-03",
            "2025-01-04",
        ]),
    )
    return PriceSeries("aapl", prices)


def test_price_series_normalizes_ticker(price_series):
    assert price_series.ticker == "AAPL"


def test_price_series_stores_prices(price_series):
    assert len(price_series.prices) == 4
    assert price_series.prices.iloc[0] == 100


def test_price_series_calculates_simple_returns(price_series):
    result = price_series.returns()

    assert len(result) == 3
    assert result.iloc[0] == pytest.approx(0.05)


def test_price_series_calculates_log_returns(price_series):
    result = price_series.log_returns()

    assert len(result) == 3
    assert result.iloc[0] == pytest.approx(np.log(105 / 100))


def test_price_series_converts_to_dataframe(price_series):
    result = price_series.to_dataframe()

    assert list(result.columns) == ["ticker", "date", "close"]
    assert len(result) == 4
    assert result["ticker"].unique().tolist() == ["AAPL"]


def test_price_series_rejects_empty_ticker():
    with pytest.raises(ValueError):
        PriceSeries("", pd.Series([100, 105]))


def test_price_series_rejects_empty_prices():
    with pytest.raises(ValueError):
        PriceSeries("AAPL", pd.Series(dtype=float))


def test_price_series_rejects_non_positive_prices():
    with pytest.raises(ValueError):
        PriceSeries("AAPL", pd.Series([100, 0, 105]))


def test_price_series_rejects_non_numeric_prices():
    with pytest.raises(ValueError):
        PriceSeries("AAPL", pd.Series([100, "invalid", 105]))


def test_price_series_rejects_mismatched_dates():
    prices = pd.Series([100, 105, 110])
    dates = pd.Series(pd.to_datetime(["2025-01-01", "2025-01-02"]))

    with pytest.raises(ValueError):
        PriceSeries("AAPL", prices, dates)

def test_descriptive_statistics():
    prices = pd.Series([100.0, 110.0, 120.0, 130.0])
    asset = PriceSeries("TEST", prices)

    assert asset.mean == pytest.approx(115.0)
    assert asset.median == pytest.approx(115.0)
    assert asset.std == pytest.approx(prices.std())
    assert asset.variance == pytest.approx(prices.var())
    assert asset.minimum == pytest.approx(100.0)
    assert asset.maximum == pytest.approx(130.0)


def test_moving_average_preserves_dates():
    dates = pd.date_range("2024-01-01", periods=5)
    prices = pd.Series([100, 110, 120, 130, 140], index=dates)

    asset = PriceSeries("TEST", prices)
    moving_average = asset.moving_average(window=3)

    assert moving_average.index.equals(dates)
    assert moving_average.iloc[:2].isna().all()
    assert moving_average.iloc[2] == pytest.approx(110.0)
    assert moving_average.iloc[4] == pytest.approx(130.0)


def test_moving_average_rejects_invalid_window():
    asset = PriceSeries("TEST", pd.Series([100, 110, 120]))

    with pytest.raises(ValueError):
        asset.moving_average(window=0)


def test_maximum_drawdown():
    prices = pd.Series([100, 120, 90, 110, 80])
    asset = PriceSeries("TEST", prices)

    assert asset.maximum_drawdown() == pytest.approx(-1 / 3)


def test_annualized_volatility():
    prices = pd.Series([100, 110, 105, 120, 115])
    asset = PriceSeries("TEST", prices)

    expected = asset.returns().std(ddof=1) * np.sqrt(252)

    assert asset.annualized_volatility() == pytest.approx(expected)


def test_skewness_and_kurtosis():
    prices = pd.Series([100, 103, 101, 108, 105, 112, 109, 115])
    asset = PriceSeries("TEST", prices)

    assert asset.skewness() == pytest.approx(asset.returns().skew())
    assert asset.kurtosis() == pytest.approx(asset.returns().kurt())


def test_single_price_has_zero_dispersion():
    asset = PriceSeries("TEST", pd.Series([100.0]))

    assert asset.std == 0.0
    assert asset.variance == 0.0
