from unittest.mock import Mock

import pandas as pd
import pytest

from Financial_toolkit.data.macro_pipeline import MacroDataPipeline
from Financial_toolkit.data.macro_providers import MacroDataProvider
from Financial_toolkit.models.macro_series import MacroSeries


class FakeMacroProvider(MacroDataProvider):
    def __init__(self, result=None):
        self.result = result or {}
        self.calls = []

    def download_series(self, series_ids, start, end):
        self.calls.append((series_ids, start, end))
        return self.result


def make_series(series_id, dates, values):
    return MacroSeries(
        series_id=series_id,
        values=pd.Series(
            values,
            index=pd.to_datetime(dates),
            dtype=float,
        ),
    )


def test_pipeline_requires_macro_provider():
    with pytest.raises(TypeError, match="MacroDataProvider"):
        MacroDataPipeline(provider=object())


def test_pipeline_downloads_series():
    expected = {
        "FEDFUNDS": make_series(
            "FEDFUNDS",
            ["2024-01-01", "2024-02-01"],
            [5.33, 5.33],
        )
    }
    provider = FakeMacroProvider(expected)
    pipeline = MacroDataPipeline(provider)

    result = pipeline.download(
        ["FEDFUNDS"],
        "2024-01-01",
        "2024-02-29",
    )

    assert result == expected
    assert provider.calls == [
        (["FEDFUNDS"], "2024-01-01", "2024-02-29")
    ]


def test_pipeline_rejects_mapping_key_that_differs_from_series_id():
    provider = FakeMacroProvider({
        "FEDFUNDS": make_series(
            "CPIAUCSL", ["2024-01-01"], [308.4]
        )
    })
    pipeline = MacroDataPipeline(provider)

    with pytest.raises(ValueError, match="no coincide"):
        pipeline.download(
            ["FEDFUNDS"], "2024-01-01", "2024-02-01"
        )


def test_pipeline_rejects_missing_requested_series():
    provider = FakeMacroProvider({
        "FEDFUNDS": make_series(
            "FEDFUNDS", ["2024-01-01"], [5.33]
        )
    })
    pipeline = MacroDataPipeline(provider)

    with pytest.raises(ValueError, match="faltan: CPIAUCSL"):
        pipeline.download(
            ["FEDFUNDS", "CPIAUCSL"],
            "2024-01-01",
            "2024-02-01",
        )


def test_pipeline_combines_multiple_series():
    provider = FakeMacroProvider()
    pipeline = MacroDataPipeline(provider)

    series = {
        "FEDFUNDS": make_series(
            "FEDFUNDS",
            ["2024-02-01", "2024-01-01"],
            [5.33, 5.33],
        ),
        "CPIAUCSL": make_series(
            "CPIAUCSL",
            ["2024-01-01"],
            [308.4],
        ),
    }

    result = pipeline.to_dataframe(series)

    assert list(result.columns) == ["series_id", "date", "value"]
    assert len(result) == 3
    assert result.iloc[0]["series_id"] == "CPIAUCSL"
    assert result.iloc[1]["date"] == pd.Timestamp("2024-01-01")
    assert result.iloc[2]["date"] == pd.Timestamp("2024-02-01")


def test_pipeline_run_downloads_and_normalizes():
    expected = {
        "FEDFUNDS": make_series(
            "FEDFUNDS",
            ["2024-01-01"],
            [5.33],
        )
    }
    provider = FakeMacroProvider(expected)
    pipeline = MacroDataPipeline(provider)

    result = pipeline.run(
        ["FEDFUNDS"],
        "2024-01-01",
        "2024-02-01",
    )

    assert len(result) == 1
    assert result.iloc[0]["series_id"] == "FEDFUNDS"
    assert result.iloc[0]["value"] == pytest.approx(5.33)
    assert len(provider.calls) == 1


def test_pipeline_rejects_empty_provider_result():
    pipeline = MacroDataPipeline(FakeMacroProvider({}))

    with pytest.raises(ValueError, match="no ha devuelto"):
        pipeline.download(
            ["FEDFUNDS"],
            "2024-01-01",
            "2024-02-01",
        )


def test_pipeline_rejects_non_macro_series_from_provider():
    provider = FakeMacroProvider({"FEDFUNDS": pd.Series([1.0])})
    pipeline = MacroDataPipeline(provider)

    with pytest.raises(TypeError, match="no es MacroSeries"):
        pipeline.download(
            ["FEDFUNDS"],
            "2024-01-01",
            "2024-02-01",
        )


def test_pipeline_rejects_empty_dataframe_input():
    pipeline = MacroDataPipeline(FakeMacroProvider({}))

    with pytest.raises(ValueError, match="al menos una serie"):
        pipeline.to_dataframe({})


def test_pipeline_rejects_invalid_series_in_dataframe_input():
    pipeline = MacroDataPipeline(FakeMacroProvider({}))

    with pytest.raises(TypeError, match="no es un objeto MacroSeries"):
        pipeline.to_dataframe({"FEDFUNDS": pd.Series([1.0])})
