import numpy as np
import pandas as pd
import pytest

from Financial_toolkit.models.real_performance import (
    calculate_real_performance,
)


@pytest.fixture
def sample_data():
    returns = pd.Series(
        [0.10, 0.10],
        index=pd.to_datetime(["2024-01-15", "2024-03-15"]),
    )
    cpi = pd.Series(
        [100.0, 105.0],
        index=pd.to_datetime(["2024-01-01", "2024-03-01"]),
    )
    return returns, cpi


def test_calculates_nominal_and_real_performance(sample_data):
    returns, cpi = sample_data

    result = calculate_real_performance(
        returns, cpi, initial_capital=10_000
    )

    assert result["nominal_return"] == pytest.approx(0.21)
    assert result["inflation_accumulated"] == pytest.approx(0.05)
    assert result["real_return"] == pytest.approx((1 + 0.21) / 1.05 - 1)
    assert result["nominal_final_value"] == pytest.approx(12_100)
    assert result["real_final_value"] == pytest.approx(12_100 / 1.05)
    assert result["inflation_impact"] == pytest.approx(
        12_100 - 12_100 / 1.05
    )


def test_returns_real_value_path(sample_data):
    returns, cpi = sample_data

    result = calculate_real_performance(returns, cpi, 10_000)
    path = result["path"]

    assert list(path.columns) == [
        "nominal_value",
        "cpi",
        "inflation_factor",
        "real_value",
    ]
    assert len(path) == 2
    assert path["nominal_value"].iloc[-1] == pytest.approx(12_100)
    assert path["real_value"].iloc[-1] == pytest.approx(12_100 / 1.05)


def test_uses_last_known_cpi_without_looking_ahead():
    returns = pd.Series(
        [0.05, 0.05],
        index=pd.to_datetime(["2024-01-15", "2024-02-15"]),
    )
    cpi = pd.Series(
        [100.0, 110.0],
        index=pd.to_datetime(["2024-01-01", "2024-03-01"]),
    )

    result = calculate_real_performance(returns, cpi, 1_000)

    assert result["inflation_accumulated"] == pytest.approx(0.0)
    assert result["real_final_value"] == pytest.approx(1_102.5)


def test_rejects_missing_initial_cpi():
    returns = pd.Series(
        [0.05],
        index=pd.to_datetime(["2024-01-15"]),
    )
    cpi = pd.Series(
        [100.0],
        index=pd.to_datetime(["2024-02-01"]),
    )

    with pytest.raises(ValueError, match="igual o anterior"):
        calculate_real_performance(returns, cpi, 1_000)


@pytest.mark.parametrize("capital", [0, -1, float("inf"), float("nan")])
def test_rejects_invalid_initial_capital(capital, sample_data):
    returns, cpi = sample_data

    with pytest.raises(ValueError, match="capital inicial"):
        calculate_real_performance(returns, cpi, capital)


def test_rejects_non_series_inputs():
    with pytest.raises(TypeError, match="rentabilidades"):
        calculate_real_performance([0.1], pd.Series([100.0]), 1_000)

    with pytest.raises(TypeError, match="IPC"):
        calculate_real_performance(
            pd.Series([0.1]), [100.0], 1_000
        )


def test_rejects_returns_below_minus_one(sample_data):
    _, cpi = sample_data
    returns = pd.Series(
        [-1.0],
        index=pd.to_datetime(["2024-01-15"]),
    )

    with pytest.raises(ValueError, match="-100 %"):
        calculate_real_performance(returns, cpi, 1_000)


def test_rejects_non_positive_cpi(sample_data):
    returns, _ = sample_data
    cpi = pd.Series(
        [0.0],
        index=pd.to_datetime(["2024-01-01"]),
    )

    with pytest.raises(ValueError, match="positivos"):
        calculate_real_performance(returns, cpi, 1_000)


def test_rejects_empty_series():
    with pytest.raises(ValueError, match="no pueden estar vacías"):
        calculate_real_performance(
            pd.Series(dtype=float),
            pd.Series(dtype=float),
            1_000,
        )
