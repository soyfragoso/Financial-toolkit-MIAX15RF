
import pandas as pd
import pytest

from Financial_toolkit.data.downloader import DataDownloader
from Financial_toolkit.data.providers import DataProvider


class MockProvider(DataProvider):

    def download_prices(self, tickers, start, end):
        return pd.DataFrame({
            "ticker": tickers,
            "date": pd.to_datetime(["2025-01-02"] * len(tickers)),
            "close": [100.0] * len(tickers)
        })


def test_downloader_accepts_valid_provider():
    provider = MockProvider()

    downloader = DataDownloader(provider)

    assert downloader.provider is provider


def test_downloader_rejects_invalid_provider():
    with pytest.raises(TypeError):
        DataDownloader("invalid provider")


def test_downloader_rejects_empty_tickers():
    downloader = DataDownloader(MockProvider())

    with pytest.raises(ValueError):
        downloader.download([], "2025-01-01", "2025-01-31")


def test_downloader_rejects_invalid_date_range():
    downloader = DataDownloader(MockProvider())

    with pytest.raises(ValueError):
        downloader.download(
            ["AAPL"],
            "2025-01-31",
            "2025-01-01"
        )


def test_downloader_returns_dataframe():
    downloader = DataDownloader(MockProvider())

    result = downloader.download(
        ["AAPL"],
        "2025-01-01",
        "2025-01-31"
    )

    assert isinstance(result, pd.DataFrame)
    assert result.iloc[0]["ticker"] == "AAPL"
    assert result.iloc[0]["close"] == 100.0


def test_downloader_accepts_multiple_tickers():
    downloader = DataDownloader(MockProvider())

    result = downloader.download(
        ["AAPL", "MSFT"],
        "2025-01-01",
        "2025-01-31"
    )

    assert len(result) == 2
    assert set(result["ticker"]) == {"AAPL", "MSFT"}


def test_downloader_rejects_non_dataframe_response():

    class InvalidProvider(DataProvider):

        def download_prices(self, tickers, start, end):
            return None

    downloader = DataDownloader(InvalidProvider())

    with pytest.raises(TypeError):
        downloader.download(
            ["AAPL"],
            "2025-01-01",
            "2025-01-31"
        )
