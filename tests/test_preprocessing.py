import pandas as pd
import pytest

from Financial_toolkit.data.preprocessing import DataPreprocessor


@pytest.fixture
def sample_data():
    return pd.DataFrame({
        "ticker": ["aapl", "MSFT", "aapl"],
        "date": ["2025-01-02", "2025-01-02", "2025-01-03"],
        "open": [100, 200, 102],
        "high": [110, 210, 112],
        "low": [95, 195, 98],
        "close": [105, 205, 108],
        "adj_close": [104, 204, 107],
        "volume": [1000, 2000, 1500],
    })


def test_preprocess_returns_dataframe(sample_data):
    preprocessor = DataPreprocessor()

    result = preprocessor.preprocess(sample_data)

    assert isinstance(result, pd.DataFrame)
    assert len(result) == 3


def test_preprocess_normalizes_tickers(sample_data):
    result = DataPreprocessor().preprocess(sample_data)

    assert result["ticker"].tolist() == ["AAPL", "AAPL", "MSFT"]


def test_preprocess_converts_dates_and_prices(sample_data):
    result = DataPreprocessor().preprocess(sample_data)

    assert pd.api.types.is_datetime64_any_dtype(result["date"])
    assert pd.api.types.is_numeric_dtype(result["close"])


def test_preprocess_removes_duplicates():
    data = pd.DataFrame({
        "ticker": ["AAPL", "AAPL"],
        "date": ["2025-01-02", "2025-01-02"],
        "close": [100, 105],
    })

    result = DataPreprocessor().preprocess(data)

    assert len(result) == 1
    assert result.iloc[0]["close"] == 105


def test_preprocess_removes_incomplete_rows():
    data = pd.DataFrame({
        "ticker": ["AAPL", None, "MSFT"],
        "date": ["2025-01-02", "2025-01-02", "invalid"],
        "close": [100, 200, 300],
    })

    result = DataPreprocessor().preprocess(data)

    assert len(result) == 1
    assert result.iloc[0]["ticker"] == "AAPL"


def test_preprocess_rejects_missing_required_columns():
    data = pd.DataFrame({
        "ticker": ["AAPL"],
        "date": ["2025-01-02"],
    })

    with pytest.raises(ValueError, match="Faltan columnas obligatorias"):
        DataPreprocessor().preprocess(data)


def test_preprocess_rejects_inconsistent_ohlc():
    data = pd.DataFrame({
        "ticker": ["AAPL"],
        "date": ["2025-01-02"],
        "open": [100],
        "high": [90],
        "low": [95],
        "close": [105],
    })

    with pytest.raises(ValueError, match="OHLC"):
        DataPreprocessor().preprocess(data)


def test_preprocess_does_not_modify_original_data(sample_data):
    original = sample_data.copy(deep=True)

    DataPreprocessor().preprocess(sample_data)

    pd.testing.assert_frame_equal(sample_data, original)
