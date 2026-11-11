import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pytest

from Financial_toolkit.analytics.benchmark import (
    BenchmarkComparison,
    compare_with_benchmark,
    plot_benchmark_comparison,
)
from Financial_toolkit.data.benchmarks import download_index, index_symbol
from Financial_toolkit.data.providers import (
    DataProvider,
    TwelveDataProvider,
    YahooFinanceProvider,
)
from Financial_toolkit.models.portfolio import Portfolio
from Financial_toolkit.models.price_series import PriceSeries


@pytest.fixture
def dates():
    return pd.date_range("2024-01-01", periods=6)


@pytest.fixture
def benchmark(dates):
    # Índice: +1 % diario.
    return PriceSeries("^GSPC", pd.Series(100 * 1.01 ** np.arange(6), index=dates))


@pytest.fixture
def portfolio(dates):
    # Cartera: +2 % diario.
    result = Portfolio()
    result.add_asset(
        PriceSeries("AAA", pd.Series(50 * 1.02 ** np.arange(6), index=dates)),
        1.0,
    )
    return result


def test_portfolio_beats_benchmark(portfolio, benchmark):
    comparison = portfolio.compare_to_benchmark(benchmark)

    assert isinstance(comparison, BenchmarkComparison)
    assert comparison.benchmark == "^GSPC"
    assert comparison.portfolio_return == pytest.approx(1.02 ** 5 - 1)
    assert comparison.benchmark_return == pytest.approx(1.01 ** 5 - 1)
    assert comparison.excess_return > 0
    assert comparison.beats_benchmark
    assert comparison.days_outperforming == pytest.approx(1.0)


def test_portfolio_does_not_beat_benchmark(dates, benchmark):
    result = Portfolio()
    result.add_asset(
        PriceSeries("BBB", pd.Series(50 * 0.99 ** np.arange(6), index=dates)),
        1.0,
    )

    comparison = result.compare_to_benchmark(benchmark)

    assert not comparison.beats_benchmark
    assert comparison.excess_return < 0


def test_beta_and_correlation(dates):
    rng = np.random.default_rng(0)
    long_dates = pd.date_range("2024-01-01", periods=200)
    index_returns = rng.normal(0, 0.01, 199)

    index_prices = 100 * np.cumprod(np.r_[1, 1 + index_returns])
    asset_prices = 100 * np.cumprod(np.r_[1, 1 + 2 * index_returns])

    benchmark = PriceSeries("IDX", pd.Series(index_prices, index=long_dates))
    result = Portfolio()
    result.add_asset(PriceSeries("LEV", pd.Series(asset_prices, index=long_dates)), 1.0)

    comparison = compare_with_benchmark(result, benchmark)

    assert comparison.beta == pytest.approx(2.0)
    assert comparison.correlation == pytest.approx(1.0)


def test_uses_only_common_dates(portfolio):
    # El índice cotiza solo en parte de los días de la cartera.
    other_dates = pd.date_range("2024-01-03", periods=10)
    benchmark = PriceSeries("IDX", pd.Series(np.linspace(100, 110, 10), index=other_dates))

    comparison = compare_with_benchmark(portfolio, benchmark)

    assert comparison.start == pd.Timestamp("2024-01-04")
    assert comparison.end == pd.Timestamp("2024-01-06")
    assert comparison.observations == 3


def test_rejects_without_common_dates(portfolio):
    other_dates = pd.date_range("2025-01-01", periods=5)
    benchmark = PriceSeries("IDX", pd.Series(np.linspace(100, 110, 5), index=other_dates))

    with pytest.raises(ValueError):
        compare_with_benchmark(portfolio, benchmark)


def test_rejects_invalid_inputs(portfolio, benchmark):
    with pytest.raises(TypeError):
        compare_with_benchmark("invalid", benchmark)

    with pytest.raises(TypeError):
        compare_with_benchmark(portfolio, "^GSPC")


def test_plot_and_plots_report(portfolio, benchmark):
    figure = plot_benchmark_comparison(portfolio, benchmark, "S&P 500")
    assert isinstance(figure, plt.Figure)
    plt.close(figure)

    figures = portfolio.plots_report(show=False, benchmark=benchmark)
    assert "benchmark_comparison" in figures

    for item in figures.values():
        plt.close(item)


def test_index_symbol_per_provider():
    assert index_symbol("SP500", YahooFinanceProvider()) == "^GSPC"
    assert index_symbol("sp500", TwelveDataProvider(api_key="test")) == "SPY"
    assert index_symbol("IBEX35", YahooFinanceProvider()) == "^IBEX"


def test_index_symbol_rejects_unknown_or_unavailable():
    with pytest.raises(ValueError):
        index_symbol("UNKNOWN", YahooFinanceProvider())

    with pytest.raises(ValueError):
        index_symbol("IBEX35", TwelveDataProvider(api_key="test"))

    with pytest.raises(TypeError):
        index_symbol("SP500", "yahoo")


def test_download_index_returns_price_series(dates):
    class FakeYahoo(YahooFinanceProvider):
        def download_prices(self, tickers, start, end):
            return pd.DataFrame({
                "ticker": tickers[0],
                "date": dates,
                "open": 100.0,
                "high": 102.0,
                "low": 99.0,
                "close": np.linspace(100, 101, len(dates)),
                "adj_close": np.linspace(100, 101, len(dates)),
                "volume": 0.0,
            })

    benchmark = download_index(FakeYahoo(), "2024-01-01", "2024-01-07", "SP500")

    assert isinstance(benchmark, PriceSeries)
    assert benchmark.ticker == "^GSPC"
    assert len(benchmark.prices) == len(dates)


def test_price_series_from_dataframe():
    data = pd.DataFrame({
        "ticker": ["AAA", "BBB", "AAA"],
        "date": ["2024-01-02", "2024-01-01", "2024-01-01"],
        "close": [11.0, 50.0, 10.0],
    })

    series = PriceSeries.from_dataframe(data, "aaa")

    assert series.ticker == "AAA"
    assert list(series.prices) == [10.0, 11.0]

    with pytest.raises(ValueError):
        PriceSeries.from_dataframe(data, "ZZZ")

    with pytest.raises(ValueError):
        PriceSeries.from_dataframe(data.drop(columns="close"), "AAA")


def test_compare_real_returns_reuses_real_performance(portfolio, benchmark):
    from Financial_toolkit.analytics.benchmark import compare_real_returns

    cpi = pd.Series(
        [100.0, 110.0],
        index=pd.to_datetime(["2023-12-01", "2024-01-03"]),
    )

    result = compare_real_returns(portfolio, benchmark, cpi, 1_000.0)

    # Primer retorno el 2024-01-02 (IPC 100), último el 2024-01-06 (IPC 110).
    assert result["inflation_accumulated"] == pytest.approx(0.10)
    assert result["portfolio_real_return"] == pytest.approx(1.02 ** 5 / 1.10 - 1)
    assert result["benchmark_real_return"] == pytest.approx(1.01 ** 5 / 1.10 - 1)
    assert result["beats_benchmark_real"]
    assert not result["benchmark_beats_inflation"]
