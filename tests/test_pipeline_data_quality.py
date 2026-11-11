import numpy as np
import pandas as pd
import pytest

from Financial_toolkit.data.pipeline import DataPipeline
from Financial_toolkit.data.providers import DataProvider


class QualityMockProvider(DataProvider):
    def __init__(self, data):
        self.data = data.copy()

    def download_prices(self, tickers, start, end):
        return self.data.copy()


@pytest.fixture
def incomplete_data():
    return pd.DataFrame({
        "ticker": ["AAPL", "AAPL", "MSFT"],
        "date": [
            "2025-01-02",
            "2025-01-03",
            "2025-01-02",
        ],
        "close": [100.0, np.nan, 200.0],
    })


def make_pipeline(data, policy="strict"):
    return DataPipeline(
        QualityMockProvider(data),
        missing_policy=policy,
    )


def run_pipeline(pipeline):
    return pipeline.run(
        tickers=["AAPL", "MSFT"],
        start="2025-01-01",
        end="2025-01-10",
    )


def test_strict_policy_stops_when_close_is_missing(incomplete_data):
    pipeline = make_pipeline(incomplete_data)

    with pytest.raises(ValueError, match="close"):
        run_pipeline(pipeline)

    assert pipeline.last_quality_report is not None
    assert pipeline.last_quality_report.missing_by_column["close"] == 1


def test_drop_policy_removes_incomplete_observations(incomplete_data):
    pipeline = make_pipeline(incomplete_data, "drop")

    result = run_pipeline(pipeline)

    assert len(result) == 2
    assert result["close"].notna().all()
    assert pipeline.last_processing_summary["rows_received"] == 3
    assert pipeline.last_processing_summary["rows_returned"] == 2
    assert pipeline.last_processing_summary["rows_removed"] == 1


def test_preserve_policy_keeps_missing_values(incomplete_data):
    pipeline = make_pipeline(incomplete_data, "preserve")

    result = run_pipeline(pipeline)

    assert len(result) == 3
    assert result["close"].isna().sum() == 1
    assert pipeline.last_processing_summary["rows_returned"] == 3


def test_forward_fill_uses_last_recorded_close():
    data = pd.DataFrame({
        "ticker": ["AAPL", "AAPL", "AAPL"],
        "date": [
            "2025-01-02",
            "2025-01-03",
            "2025-01-06",
        ],
        "close": [100.0, np.nan, 105.0],
    })

    pipeline = make_pipeline(data, "forward_fill")

    result = run_pipeline(pipeline)

    assert len(result) == 3
    assert result["close"].tolist() == [100.0, 100.0, 105.0]
    assert pipeline.last_processing_summary["close_values_filled"] == 1
    assert pipeline.last_processing_summary["rows_removed"] == 0


def test_forward_fill_does_not_fill_two_consecutive_missing_values():
    data = pd.DataFrame({
        "ticker": ["AAPL", "AAPL", "AAPL", "AAPL"],
        "date": [
            "2025-01-02",
            "2025-01-03",
            "2025-01-06",
            "2025-01-07",
        ],
        "close": [100.0, np.nan, np.nan, 105.0],
    })

    pipeline = make_pipeline(data, "forward_fill")

    result = run_pipeline(pipeline)

    assert len(result) == 3
    assert result["close"].tolist() == [100.0, 100.0, 105.0]
    assert pipeline.last_processing_summary["close_values_filled"] == 1
    assert pipeline.last_processing_summary["rows_removed"] == 1


def test_strict_policy_allows_missing_optional_adjusted_close():
    data = pd.DataFrame({
        "ticker": ["AAPL", "AAPL"],
        "date": ["2025-01-02", "2025-01-03"],
        "close": [100.0, 101.0],
        "adj_close": [np.nan, np.nan],
    })

    pipeline = make_pipeline(data, "strict")

    result = run_pipeline(pipeline)

    assert len(result) == 2
    assert result["adj_close"].isna().all()


def test_run_can_override_constructor_policy(incomplete_data):
    pipeline = make_pipeline(incomplete_data, "strict")

    result = pipeline.run(
        tickers=["AAPL", "MSFT"],
        start="2025-01-01",
        end="2025-01-10",
        missing_policy="drop",
    )

    assert len(result) == 2
    assert pipeline.last_processing_summary["policy"] == "drop"


def test_invalid_policy_is_rejected(incomplete_data):
    with pytest.raises(ValueError, match="Política"):
        make_pipeline(incomplete_data, "interpolate")


def test_strict_policy_rejects_duplicate_observations():
    data = pd.DataFrame({
        "ticker": ["AAPL", "AAPL"],
        "date": ["2025-01-02", "2025-01-02"],
        "close": [100.0, 101.0],
    })

    pipeline = make_pipeline(data, "strict")

    with pytest.raises(ValueError, match="duplicados"):
        run_pipeline(pipeline)


def test_preserve_policy_does_not_modify_original_data(incomplete_data):
    original = incomplete_data.copy(deep=True)

    pipeline = make_pipeline(incomplete_data, "preserve")
    run_pipeline(pipeline)

    pd.testing.assert_frame_equal(incomplete_data, original)


def test_quality_summary_contains_missing_data_metrics(incomplete_data):
    pipeline = make_pipeline(incomplete_data, "drop")
    run_pipeline(pipeline)

    summary = pipeline.last_processing_summary

    assert summary["missing_percentage"] > 0
    assert summary["completeness_percentage"] < 100
    assert summary["quality_report"]["missing_cells"] == 1
