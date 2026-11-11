import numpy as np
import pandas as pd
import pytest

from Financial_toolkit.models.portfolio import Portfolio
from Financial_toolkit.models.price_series import PriceSeries
from Financial_toolkit.analytics.reports import generate_portfolio_report


@pytest.fixture
def portfolio():
    dates = pd.date_range("2024-01-01", periods=100)

    prices_a = pd.Series(
        np.linspace(100, 120, 100),
        index=dates,
    )

    prices_b = pd.Series(
        np.linspace(80, 90, 100),
        index=dates,
    )

    result = Portfolio()
    result.add_asset(PriceSeries("AAA", prices_a), 0.6)
    result.add_asset(PriceSeries("BBB", prices_b), 0.4)

    return result


def test_generates_markdown_report(portfolio):
    report = generate_portfolio_report(portfolio)

    assert isinstance(report, str)
    assert "# Informe de análisis de cartera" in report
    assert "## 1. Composición de la cartera" in report


def test_report_contains_assets_and_weights(portfolio):
    report = generate_portfolio_report(portfolio)

    assert "AAA" in report
    assert "BBB" in report
    assert "60.00%" in report
    assert "40.00%" in report


def test_report_contains_performance_metrics(portfolio):
    report = generate_portfolio_report(portfolio)

    assert "Rentabilidad acumulada" in report
    assert "Rentabilidad anualizada" in report
    assert "Volatilidad anualizada" in report


def test_report_contains_risk_diagnostics(portfolio):
    report = generate_portfolio_report(portfolio)

    assert "Advertencia" in report
    assert "inferior a un año de negociación" in report

def test_report_contains_methodology(portfolio):
    report = generate_portfolio_report(portfolio)

    assert "Metodología y limitaciones" in report
    assert "no garantizan rendimientos futuros" in report


def test_rejects_invalid_portfolio():
    with pytest.raises(TypeError):
        generate_portfolio_report("invalid")


def test_rejects_invalid_periods(portfolio):
    with pytest.raises(ValueError):
        generate_portfolio_report(portfolio, periods=0)


def test_rejects_empty_portfolio():
    with pytest.raises(ValueError):
        generate_portfolio_report(Portfolio())


def test_portfolio_report_method(portfolio):
    report = portfolio.report()

    assert isinstance(report, str)
    assert "# Informe de análisis de cartera" in report
    assert "AAA" in report
    assert "BBB" in report


@pytest.mark.parametrize(
    "periods",
    [True, False, -1, 1.5, "252", None],
)
def test_report_rejects_invalid_period_types(portfolio, periods):
    with pytest.raises(ValueError):
        generate_portfolio_report(portfolio, periods=periods)


def test_report_warns_about_concentrated_portfolio(portfolio):
    report = generate_portfolio_report(portfolio)

    assert "presenta concentración" in report
    assert "al menos el 50 %" in report


def test_report_warns_about_high_volatility():
    dates = pd.date_range("2024-01-01", periods=100)

    prices_a = pd.Series(
        [100 * (1.05 if i % 2 == 0 else 0.95) for i in range(100)],
        index=dates,
    )

    prices_b = pd.Series(
        np.linspace(100, 110, 100),
        index=dates,
    )

    portfolio = Portfolio()
    portfolio.add_asset(PriceSeries("VOL", prices_a), 0.5)
    portfolio.add_asset(PriceSeries("STABLE", prices_b), 0.5)

    report = generate_portfolio_report(portfolio)

    assert "volatilidad anualizada es elevada" in report
    assert "30 % o superior" in report


def test_report_warns_about_negative_annualized_return():
    dates = pd.date_range("2024-01-01", periods=100)

    prices_a = pd.Series(
        np.linspace(100, 70, 100),
        index=dates,
    )

    prices_b = pd.Series(
        np.linspace(100, 80, 100),
        index=dates,
    )

    portfolio = Portfolio()
    portfolio.add_asset(PriceSeries("DOWN_A", prices_a), 0.5)
    portfolio.add_asset(PriceSeries("DOWN_B", prices_b), 0.5)

    report = generate_portfolio_report(portfolio)

    assert "rentabilidad anualizada histórica es negativa" in report


def test_report_contains_new_statistics(portfolio):
    report = generate_portfolio_report(portfolio)

    assert "Máximo drawdown" in report
    assert "Rentabilidad diaria media" in report
    assert "Rentabilidad diaria mediana" in report



def test_report_with_benchmark(portfolio):
    dates = pd.date_range("2024-01-01", periods=100)
    benchmark = PriceSeries("^GSPC", pd.Series(np.linspace(100, 101, 100), index=dates))

    report = generate_portfolio_report(portfolio, benchmark=benchmark)

    assert "## 3. Comparación con el índice (^GSPC)" in report
    assert "La cartera bate al índice" in report
    assert "## 4. Diagnóstico de riesgo" in report
    assert "## 5. Metodología y limitaciones" in report
