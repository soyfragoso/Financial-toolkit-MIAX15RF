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

    assert "Diagnóstico de riesgo" in report
    assert "Advertencia" in report


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
