import pandas as pd
import pytest

from Financial_toolkit.data.providers import YahooFinanceProvider


def test_yahoo_provider_rejects_empty_tickers():
    provider = YahooFinanceProvider()

    with pytest.raises(ValueError):
        provider.download_prices(
            [],
            "2025-01-01",
            "2025-01-31"
        )


def test_yahoo_provider_rejects_invalid_dates():
    provider = YahooFinanceProvider()

    with pytest.raises(ValueError):
        provider.download_prices(
            ["AAPL"],
            "2025-01-31",
            "2025-01-01"
        )


def test_yahoo_provider_rejects_empty_response(monkeypatch):

    provider = YahooFinanceProvider()

    def fake_download(**kwargs):
        return pd.DataFrame()

    monkeypatch.setattr(
        "Financial_toolkit.data.providers.yf.download",
        fake_download
    )

    with pytest.raises(ValueError):
        provider.download_prices(
            ["AAPL"],
            "2025-01-01",
            "2025-01-31"
        )


def test_yahoo_provider_normalizes_single_ticker(monkeypatch):

    provider = YahooFinanceProvider()

    raw_data = pd.DataFrame({
        "Open": [98.0, 99.0],
        "High": [102.0, 103.0],
        "Low": [97.0, 98.0],
        "Close": [100.0, 101.0],
        "Adj Close": [100.0, 101.0],
        "Volume": [1000, 1200]
    }, index=pd.to_datetime([
        "2025-01-02",
        "2025-01-03"
    ]))

    def fake_download(**kwargs):
        return raw_data

    monkeypatch.setattr(
        "Financial_toolkit.data.providers.yf.download",
        fake_download
    )

    result = provider.download_prices(
        ["aapl"],
        "2025-01-01",
        "2025-01-31"
    )

    assert len(result) == 2
    assert result["ticker"].unique().tolist() == ["AAPL"]
    assert "adj_close" in result.columns
    assert result["close"].tolist() == [100.0, 101.0]
    assert pd.api.types.is_datetime64_any_dtype(result["date"])


def test_yahoo_provider_normalizes_multiple_tickers(monkeypatch):

    provider = YahooFinanceProvider()

    dates = pd.to_datetime([
        "2025-01-02",
        "2025-01-03"
    ])

    columns = pd.MultiIndex.from_product(
        [
            ["AAPL", "MSFT"],
            ["Open", "High", "Low", "Close", "Adj Close", "Volume"]
        ]
    )

    raw_data = pd.DataFrame(
        [
            [
                98, 102, 97, 100, 100, 1000,
                198, 202, 197, 200, 200, 2000
            ],
            [
                99, 103, 98, 101, 101, 1200,
                199, 203, 198, 201, 201, 2200
            ]
        ],
        index=dates,
        columns=columns
    )

    def fake_download(**kwargs):
        return raw_data

    monkeypatch.setattr(
        "Financial_toolkit.data.providers.yf.download",
        fake_download
    )

    result = provider.download_prices(
        ["AAPL", "MSFT"],
        "2025-01-01",
        "2025-01-31"
    )

    assert len(result) == 4
    assert set(result["ticker"]) == {"AAPL", "MSFT"}
    assert set(result.columns) == {
        "ticker",
        "date",
        "open",
        "high",
        "low",
        "close",
        "adj_close",
        "volume"
    }
    