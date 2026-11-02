import pandas as pd
import pytest

from Financial_toolkit.data.pipeline import DataPipeline
from Financial_toolkit.data.providers import (
    DataProvider,
    TwelveDataProvider,
)


class MockProvider(DataProvider):
    def download_prices(self, tickers, start, end):
        return pd.DataFrame({
            "ticker": ["aapl", "MSFT"],
            "date": ["2025-01-02", "2025-01-02"],
            "close": ["105", "205"],
        })


def test_pipeline_downloads_and_preprocesses_data():
    pipeline = DataPipeline(MockProvider())

    result = pipeline.run(
        tickers=["AAPL", "MSFT"],
        start="2025-01-01",
        end="2025-01-10",
    )

    assert len(result) == 2
    assert result["ticker"].tolist() == ["AAPL", "MSFT"]
    assert pd.api.types.is_datetime64_any_dtype(result["date"])
    assert pd.api.types.is_numeric_dtype(result["close"])


def test_pipeline_rejects_invalid_provider():
    with pytest.raises(TypeError):
        DataPipeline(object())


def test_pipeline_propagates_download_errors():
    class FailingProvider(DataProvider):
        def download_prices(self, tickers, start, end):
            raise ValueError("Fallo simulado de descarga")

    pipeline = DataPipeline(FailingProvider())

    with pytest.raises(ValueError, match="Fallo simulado"):
        pipeline.run(
            tickers=["AAPL"],
            start="2025-01-01",
            end="2025-01-10",
        )


def test_pipeline_with_twelve_data_provider(monkeypatch):

    response_data = {
        "status": "ok",
        "meta": {"symbol": "AAPL"},
        "values": [
            {
                "datetime": "2025-01-02",
                "open": "98.0",
                "high": "102.0",
                "low": "97.0",
                "close": "100.0",
                "volume": "1000",
            },
            {
                "datetime": "2025-01-03",
                "open": "99.0",
                "high": "103.0",
                "low": "98.0",
                "close": "101.0",
                "volume": "1200",
            },
        ],
    }

    class FakeResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return response_data

    def fake_get(*args, **kwargs):
        return FakeResponse()

    monkeypatch.setattr(
        "Financial_toolkit.data.providers.requests.get",
        fake_get,
    )

    provider = TwelveDataProvider(api_key="test_api_key")
    pipeline = DataPipeline(provider)

    result = pipeline.run(
        tickers=["AAPL"],
        start="2025-01-01",
        end="2025-01-10",
    )

    assert len(result) == 2
    assert result["ticker"].unique().tolist() == ["AAPL"]
    assert result["close"].tolist() == [100.0, 101.0]
    assert pd.api.types.is_datetime64_any_dtype(result["date"])
    assert pd.api.types.is_numeric_dtype(result["close"])
    assert result["adj_close"].isna().all()