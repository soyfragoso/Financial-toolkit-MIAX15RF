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