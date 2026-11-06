import numpy as np
import pandas as pd
import pytest

from Financial_toolkit.models.macro_series import MacroSeries


@pytest.fixture
def macro_series():
    dates = pd.date_range("2024-01-01", periods=4, freq="MS")
    values = pd.Series([5.25, 5.25, 5.00, 4.75], index=dates)

    return MacroSeries(
        series_id="fedfunds",
        values=values,
        name="Effective Federal Funds Rate",
        units="Percent",
        frequency="Monthly",
    )


def test_macro_series_normalizes_identifier(macro_series):
    assert macro_series.series_id == "FEDFUNDS"


def test_macro_series_calculates_statistics(macro_series):
    assert macro_series.mean == pytest.approx(5.0625)
    assert macro_series.median == pytest.approx(5.125)
    assert macro_series.std > 0
    assert macro_series.minimum == 4.75
    assert macro_series.maximum == 5.25


def test_macro_series_sorts_dates():
    dates = pd.to_datetime(["2024-03-01", "2024-01-01", "2024-02-01"])
    values = pd.Series([3.0, 1.0, 2.0], index=dates)

    result = MacroSeries("TEST", values)

    assert result.values.tolist() == [1.0, 2.0, 3.0]
    assert result.dates.is_monotonic_increasing


def test_macro_series_accepts_negative_values():
    dates = pd.date_range("2024-01-01", periods=2)
    values = pd.Series([-0.5, 0.25], index=dates)

    result = MacroSeries("TEST", values)

    assert result.minimum == -0.5


def test_macro_series_to_dataframe(macro_series):
    result = macro_series.to_dataframe()

    assert list(result.columns) == ["series_id", "date", "value"]
    assert len(result) == 4
    assert result["series_id"].unique().tolist() == ["FEDFUNDS"]


def test_macro_series_rejects_invalid_identifier():
    with pytest.raises(ValueError):
        MacroSeries("", pd.Series([1.0], index=pd.to_datetime(["2024-01-01"])))


def test_macro_series_rejects_non_series_values():
    with pytest.raises(TypeError):
        MacroSeries("TEST", [1.0, 2.0])


def test_macro_series_rejects_empty_values():
    with pytest.raises(ValueError):
        MacroSeries("TEST", pd.Series(dtype=float))


def test_macro_series_rejects_missing_values():
    dates = pd.date_range("2024-01-01", periods=2)

    with pytest.raises(ValueError):
        MacroSeries("TEST", pd.Series([1.0, np.nan], index=dates))


def test_macro_series_rejects_infinite_values():
    dates = pd.date_range("2024-01-01", periods=2)

    with pytest.raises(ValueError):
        MacroSeries("TEST", pd.Series([1.0, np.inf], index=dates))


def test_macro_series_rejects_duplicate_dates():
    dates = pd.to_datetime(["2024-01-01", "2024-01-01"])

    with pytest.raises(ValueError):
        MacroSeries("TEST", pd.Series([1.0, 2.0], index=dates))


def test_macro_series_rejects_invalid_dates():
    values = pd.Series([1.0, 2.0], index=["invalid", "2024-01-01"])

    with pytest.raises(ValueError):
        MacroSeries("TEST", values)
