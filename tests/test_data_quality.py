import numpy as np
import pandas as pd
import pytest

from Financial_toolkit.data.quality import (
    DataQualityReport,
    analyze_data_quality,
)


@pytest.fixture
def quality_data():
    return pd.DataFrame({
        "ticker": ["AAPL", "AAPL", "MSFT", "MSFT"],
        "date": [
            "2025-01-02",
            "2025-01-03",
            "2025-01-02",
            "2025-01-03",
        ],
        "open": [100, 105, 200, 205],
        "high": [110, 115, 210, 215],
        "low": [95, 100, 195, 200],
        "close": [105, 110, 205, 210],
        "volume": [1000, 1200, 2000, 2200],
    })


def test_quality_report_returns_dataclass(quality_data):
    report = analyze_data_quality(quality_data)

    assert isinstance(report, DataQualityReport)
    assert report.total_rows == 4
    assert report.total_columns == 7
    assert report.missing_cells == 0
    assert report.missing_percentage == 0
    assert report.completeness_percentage == 100


def test_quality_report_detects_missing_values():
    data = pd.DataFrame({
        "ticker": ["AAPL", "AAPL", "MSFT"],
        "date": ["2025-01-02", "2025-01-03", "2025-01-02"],
        "close": [100, np.nan, 200],
        "volume": [1000, 1100, np.nan],
    })

    report = analyze_data_quality(data)

    assert report.missing_cells == 2
    assert report.missing_percentage == pytest.approx(2 / 12 * 100)
    assert report.completeness_percentage == pytest.approx(10 / 12 * 100)
    assert report.missing_by_column["close"] == 1
    assert report.missing_by_column["volume"] == 1
    assert report.missing_percentage_by_column["close"] == pytest.approx(100 / 3)
    assert report.missing_by_ticker["AAPL"]["close"] == 1
    assert report.missing_by_ticker["MSFT"]["volume"] == 1


def test_quality_report_detects_invalid_numeric_values():
    data = pd.DataFrame({
        "ticker": ["AAPL", "MSFT", "NVDA"],
        "date": ["2025-01-02", "2025-01-02", "2025-01-02"],
        "close": ["100", "invalid", np.inf],
    })

    report = analyze_data_quality(data)

    assert report.invalid_numeric_by_column["close"] == 1
    assert report.infinite_by_column["close"] == 1
    assert report.missing_by_column["close"] == 0


def test_quality_report_detects_invalid_dates():
    data = pd.DataFrame({
        "ticker": ["AAPL", "MSFT", "NVDA"],
        "date": ["2025-01-02", "not-a-date", None],
        "close": [100, 200, 300],
    })

    report = analyze_data_quality(data)

    assert report.invalid_date_rows == 1
    assert report.missing_by_column["date"] == 1


def test_quality_report_detects_duplicate_asset_dates():
    data = pd.DataFrame({
        "ticker": ["AAPL", "aapl", "MSFT"],
        "date": ["2025-01-02", "2025-01-02", "2025-01-02"],
        "close": [100, 101, 200],
    })

    report = analyze_data_quality(data)

    assert report.duplicate_rows == 1


def test_quality_report_detects_non_positive_close_and_negative_volume():
    data = pd.DataFrame({
        "ticker": ["AAPL", "MSFT", "NVDA"],
        "date": ["2025-01-02", "2025-01-02", "2025-01-02"],
        "close": [100, 0, -10],
        "volume": [1000, -1, 2000],
    })

    report = analyze_data_quality(data)

    assert report.non_positive_close_rows == 2
    assert report.negative_volume_rows == 1


def test_quality_report_detects_inconsistent_ohlc():
    data = pd.DataFrame({
        "ticker": ["AAPL", "MSFT"],
        "date": ["2025-01-02", "2025-01-02"],
        "open": [100, 200],
        "high": [110, 190],
        "low": [95, 195],
        "close": [105, 205],
    })

    report = analyze_data_quality(data)

    assert report.invalid_ohlc_rows == 1


def test_quality_report_does_not_modify_original_data(quality_data):
    original = quality_data.copy(deep=True)

    analyze_data_quality(quality_data)

    pd.testing.assert_frame_equal(quality_data, original)


def test_quality_report_supports_markdown_and_dict(quality_data):
    report = analyze_data_quality(quality_data)

    markdown = report.to_markdown()
    serialized = report.to_dict()

    assert "# Informe de calidad de datos" in markdown
    assert "Porcentaje de datos faltantes" in markdown
    assert serialized["total_rows"] == 4
    assert serialized["missing_percentage"] == 0


def test_quality_report_handles_empty_dataframe():
    report = analyze_data_quality(pd.DataFrame())

    assert report.total_rows == 0
    assert report.total_cells == 0
    assert report.missing_percentage == 0
    assert report.completeness_percentage == 100


def test_quality_report_rejects_non_dataframe():
    with pytest.raises(TypeError, match="DataFrame"):
        analyze_data_quality([1, 2, 3])
