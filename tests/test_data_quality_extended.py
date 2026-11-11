import numpy as np
import pandas as pd
import pytest

from Financial_toolkit.data.quality import analyze_data_quality


def valid_data():
    return pd.DataFrame({
        "ticker": ["AAPL", "AAPL", "MSFT"],
        "date": ["2025-01-02", "2025-01-03", "2025-01-02"],
        "open": [100.0, 105.0, 200.0],
        "high": [110.0, 115.0, 210.0],
        "low": [95.0, 100.0, 195.0],
        "close": [105.0, 110.0, 205.0],
        "adj_close": [105.0, 110.0, 205.0],
        "volume": [1000, 1200, 2000],
    })


@pytest.mark.parametrize(
    "column",
    ["open", "high", "low", "close", "adj_close", "volume"],
)
def test_detects_missing_values_in_each_numeric_column(column):
    data = valid_data()
    data.loc[0, column] = np.nan

    report = analyze_data_quality(data)

    assert report.missing_by_column[column] == 1
    assert report.missing_percentage_by_column[column] == pytest.approx(
        100 / 3
    )


@pytest.mark.parametrize(
    "column",
    ["open", "high", "low", "close", "adj_close", "volume"],
)
def test_detects_non_numeric_values_in_each_numeric_column(column):
    data = valid_data()
    data[column] = data[column].astype(object)
    data.loc[0, column] = "dato-invalido"

    report = analyze_data_quality(data)

    assert report.invalid_numeric_by_column[column] == 1


@pytest.mark.parametrize(
    "column",
    ["open", "high", "low", "close", "adj_close", "volume"],
)
def test_detects_infinite_values_in_each_numeric_column(column):
    data = valid_data()
    data[column] = data[column].astype(float)
    data.loc[0, column] = np.inf

    report = analyze_data_quality(data)

    assert report.infinite_by_column[column] == 1


def test_missing_percentage_is_calculated_over_all_cells():
    data = valid_data()
    data.loc[0, "open"] = np.nan
    data.loc[1, "volume"] = np.nan

    report = analyze_data_quality(data)

    assert report.total_cells == data.size
    assert report.missing_cells == 2
    assert report.missing_percentage == pytest.approx(
        2 / data.size * 100
    )


def test_missing_data_by_ticker_is_independent():
    data = valid_data()
    data.loc[0, "close"] = np.nan
    data.loc[2, "volume"] = np.nan

    report = analyze_data_quality(data)

    assert report.missing_by_ticker["AAPL"]["close"] == 1
    assert report.missing_by_ticker["MSFT"]["close"] == 0
    assert report.missing_by_ticker["MSFT"]["volume"] == 1


def test_duplicate_detection_normalizes_ticker_and_date():
    data = pd.DataFrame({
        "ticker": ["AAPL", " aapl ", "MSFT"],
        "date": [
            "2025-01-02",
            "2025-01-02",
            "2025-01-02",
        ],
        "close": [100, 101, 200],
    })

    report = analyze_data_quality(data)

    assert report.duplicate_rows == 1


def test_missing_ohlc_values_are_not_misclassified_as_incoherent():
    data = valid_data()
    data.loc[0, "high"] = np.nan

    report = analyze_data_quality(data)

    assert report.invalid_ohlc_rows == 0
    assert report.missing_by_column["high"] == 1


def test_quality_analysis_does_not_mutate_data_with_invalid_values():
    data = valid_data()
    data["close"] = data["close"].astype(object)
    data.loc[0, "close"] = "invalid"
    original = data.copy(deep=True)

    analyze_data_quality(data)

    pd.testing.assert_frame_equal(data, original)


def test_report_handles_dataframe_without_ticker_column():
    data = pd.DataFrame({
        "date": ["2025-01-02"],
        "close": [100.0],
    })

    report = analyze_data_quality(data)

    assert report.total_rows == 1
    assert report.missing_by_ticker == {}
