import numpy as np
import pandas as pd
import pytest

from Financial_toolkit.data.pipeline import DataPipeline
from Financial_toolkit.data.providers import DataProvider


class ExtendedQualityProvider(DataProvider):
    def __init__(self, data):
        self.data = data.copy()
        self.download_calls = 0

    def download_prices(self, tickers, start, end):
        self.download_calls += 1
        return self.data.copy()


def make_pipeline(data, policy="strict"):
    provider = ExtendedQualityProvider(data)
    return DataPipeline(provider, missing_policy=policy), provider


def run_pipeline(pipeline):
    return pipeline.run(
        tickers=["AAPL", "MSFT"],
        start="2025-01-01",
        end="2025-01-10",
    )


def valid_data():
    return pd.DataFrame({
        "ticker": ["AAPL", "AAPL", "MSFT"],
        "date": ["2025-01-02", "2025-01-03", "2025-01-02"],
        "open": [100.0, 105.0, 200.0],
        "high": [110.0, 115.0, 210.0],
        "low": [95.0, 100.0, 195.0],
        "close": [105.0, 110.0, 205.0],
        "volume": [1000, 1200, 2000],
    })


@pytest.mark.parametrize("column", ["open", "high", "low", "volume"])
def test_strict_detects_missing_ohlc_and_volume(column):
    data = valid_data()
    data.loc[0, column] = np.nan

    pipeline, _ = make_pipeline(data, "strict")

    with pytest.raises(ValueError, match=column):
        run_pipeline(pipeline)


@pytest.mark.parametrize("column", ["open", "high", "low", "volume"])
def test_drop_removes_rows_missing_ohlc_and_volume(column):
    data = valid_data()
    data.loc[0, column] = np.nan

    pipeline, _ = make_pipeline(data, "drop")
    result = run_pipeline(pipeline)

    assert len(result) == 2
    assert result[column].notna().all()


@pytest.mark.parametrize(
    "close",
    [0.0, -1.0],
)
def test_drop_removes_non_positive_close(close):
    data = valid_data()
    data.loc[0, "close"] = close

    pipeline, _ = make_pipeline(data, "drop")
    result = run_pipeline(pipeline)

    assert len(result) == 2
    assert (result["close"] > 0).all()


def test_drop_removes_negative_volume():
    data = valid_data()
    data.loc[0, "volume"] = -1

    pipeline, _ = make_pipeline(data, "drop")
    result = run_pipeline(pipeline)

    assert len(result) == 2
    assert (result["volume"] >= 0).all()


def test_drop_removes_infinite_prices():
    data = valid_data()
    data.loc[0, "close"] = np.inf

    pipeline, _ = make_pipeline(data, "drop")
    result = run_pipeline(pipeline)

    assert len(result) == 2
    assert np.isfinite(result["close"]).all()


def test_drop_removes_invalid_dates():
    data = valid_data()
    data.loc[0, "date"] = "fecha-invalida"

    pipeline, _ = make_pipeline(data, "drop")
    result = run_pipeline(pipeline)

    assert len(result) == 2
    assert result["date"].notna().all()


def test_drop_removes_incoherent_ohlc():
    data = valid_data()
    data.loc[0, "high"] = 90.0

    pipeline, _ = make_pipeline(data, "drop")
    result = run_pipeline(pipeline)

    assert len(result) == 2


def test_forward_fill_is_independent_for_each_ticker():
    data = pd.DataFrame({
        "ticker": ["AAPL", "AAPL", "MSFT", "MSFT"],
        "date": [
            "2025-01-02",
            "2025-01-03",
            "2025-01-02",
            "2025-01-03",
        ],
        "close": [100.0, np.nan, 200.0, np.nan],
    })

    pipeline, _ = make_pipeline(data, "forward_fill")
    result = run_pipeline(pipeline)

    closes = result.set_index("ticker")["close"]

    assert closes.loc["AAPL"].tolist() == [100.0, 100.0]
    assert closes.loc["MSFT"].tolist() == [200.0, 200.0]
    assert pipeline.last_processing_summary["close_values_filled"] == 2


def test_forward_fill_does_not_modify_other_columns():
    data = pd.DataFrame({
        "ticker": ["AAPL", "AAPL"],
        "date": ["2025-01-02", "2025-01-03"],
        "open": [99.0, np.nan],
        "high": [110.0, np.nan],
        "low": [95.0, np.nan],
        "close": [105.0, np.nan],
        "volume": [1000.0, np.nan],
    })

    pipeline, _ = make_pipeline(data, "forward_fill")
    result = run_pipeline(pipeline)

    assert len(result) == 1
    assert result.iloc[0]["close"] == 105.0
    assert result.iloc[0]["open"] == 99.0
    assert result.iloc[0]["volume"] == 1000.0


def test_inspect_does_not_modify_raw_data():
    data = valid_data()
    data.loc[0, "close"] = np.nan
    original = data.copy(deep=True)

    pipeline, _ = make_pipeline(data)
    pipeline.inspect(data)

    pd.testing.assert_frame_equal(data, original)


def test_process_raw_does_not_download_again():
    data = valid_data()
    pipeline, provider = make_pipeline(data, "drop")

    raw = pipeline.download_raw(
        ["AAPL", "MSFT"],
        "2025-01-01",
        "2025-01-10",
    )
    pipeline.process_raw(raw)

    assert provider.download_calls == 1


def test_summary_records_recommendation_and_user_decision():
    data = valid_data()
    pipeline, _ = make_pipeline(data, "drop")

    pipeline.process_raw(
        data,
        recommendation="drop",
        decision="Eliminación aceptada por el usuario",
    )

    summary = pipeline.last_processing_summary

    assert summary["recommendation"] == "drop"
    assert summary["decision"] == "Eliminación aceptada por el usuario"
    assert summary["calculations_allowed"] is True
    assert summary["rows_received"] == 3
    assert summary["rows_returned"] == 3


def test_preserve_marks_calculations_as_not_allowed():
    data = valid_data()
    data.loc[0, "close"] = np.nan

    pipeline, _ = make_pipeline(data, "preserve")
    result = run_pipeline(pipeline)

    assert result["close"].isna().sum() == 1
    assert pipeline.last_processing_summary["calculations_allowed"] is False


def test_preserve_allows_inspection_of_non_positive_close():
    data = valid_data()
    data.loc[0, "close"] = 0.0

    pipeline, _ = make_pipeline(data, "preserve")

    result = run_pipeline(pipeline)

    assert len(result) == 3
    assert pipeline.last_processing_summary["calculations_allowed"] is False


def test_preserve_allows_inspection_of_infinite_values():
    data = valid_data()
    data.loc[0, "close"] = np.inf

    pipeline, _ = make_pipeline(data, "preserve")

    result = run_pipeline(pipeline)

    assert len(result) == 3
    assert pipeline.last_processing_summary["calculations_allowed"] is False



# DATA_QUALITY_FINAL_AUDIT_TESTS

@pytest.mark.parametrize(
    ("column", "value", "message"),
    [
        ("close", 0.0, "cero"),
        ("volume", -1, "volumen negativo"),
        ("date", "fecha-invalida", "Fechas no válidas"),
        ("high", 90.0, "OHLC incoherentes"),
        ("close", np.inf, "infinitos"),
        ("close", "no-es-numero", "no válidos"),
    ],
)
def test_strict_blocks_critical_integrity_issues(
    column, value, message
):
    data = valid_data()
    if isinstance(value, str) and column in data.columns:
        data[column] = data[column].astype(object)
    data.loc[0, column] = value
    pipeline, _ = make_pipeline(data, "strict")

    with pytest.raises(ValueError):
        run_pipeline(pipeline)

    assert pipeline.last_quality_issues


def test_drop_duplicate_observations_keeps_last_record():
    data = valid_data()
    duplicate = data.iloc[[0]].copy()
    duplicate.loc[:, "close"] = 106.0
    data = pd.concat([data, duplicate], ignore_index=True)

    pipeline, _ = make_pipeline(data, "drop")
    result = run_pipeline(pipeline)

    selected = result[
        (result["ticker"] == "AAPL")
        & (pd.to_datetime(result["date"]) == pd.Timestamp("2025-01-02"))
    ]

    assert len(selected) == 1
    assert selected.iloc[0]["close"] == 106.0


def test_forward_fill_changes_only_close_without_mutating_source():
    data = pd.DataFrame({
        "ticker": ["AAPL", "AAPL"],
        "date": ["2025-01-02", "2025-01-03"],
        "open": [99.0, 98.0],
        "high": [110.0, 109.0],
        "low": [95.0, 94.0],
        "close": [105.0, np.nan],
        "volume": [1000.0, 900.0],
    })
    original = data.copy(deep=True)

    result, filled = DataPipeline._fill_last_close(data)

    assert filled == 1
    assert result["close"].tolist() == [105.0, 105.0]

    for column in ("open", "high", "low", "volume"):
        pd.testing.assert_series_equal(
            result[column], original[column],
            check_names=True,
        )

    pd.testing.assert_frame_equal(data, original)


def test_temporal_report_calculates_common_dates_and_coverage():
    import runpy
    build_data_quality_report = runpy.run_path(
        "examples/example_portfolio.py"
    )["build_data_quality_report"]

    data = pd.DataFrame({
        "ticker": ["AAPL", "AAPL", "AAPL", "MSFT", "MSFT"],
        "date": [
            "2025-01-02", "2025-01-03", "2025-01-06",
            "2025-01-02", "2025-01-06",
        ],
        "close": [100.0, 101.0, 103.0, 200.0, 203.0],
    })

    pipeline, _ = make_pipeline(data, "drop")
    result = pipeline.process_raw(data)

    report = build_data_quality_report(
        pipeline=pipeline,
        raw_data=data,
        tickers=["AAPL", "MSFT"],
        recommendation="drop",
        decision="drop",
        result=result,
    )

    assert "- AAPL: 3 fechas válidas." in report
    assert "- MSFT: 2 fechas válidas." in report
    assert "- Fechas comunes a todos los activos: 2." in report
    assert "- Fechas distintas en el conjunto: 3." in report
    assert "66.67%" in report
