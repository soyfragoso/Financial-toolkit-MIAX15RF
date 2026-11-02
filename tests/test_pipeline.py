import pandas as pd
import pytest

from Financial_toolkit.data.pipeline import DataPipeline
from Financial_toolkit.data.providers import DataProvider


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
