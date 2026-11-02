import numpy as np
import pandas as pd
import pytest

from Financial_toolkit.models.portfolio import Portfolio
from Financial_toolkit.models.price_series import PriceSeries
from Financial_toolkit.simulation.monte_carlo import (
    PortfolioMonteCarloSimulator,
)


@pytest.fixture
def portfolio():
    dates = pd.date_range("2024-01-01", periods=100)

    prices_a = pd.Series(
        100 * np.exp(np.cumsum(np.linspace(-0.002, 0.003, 100))),
        index=dates,
    )

    prices_b = pd.Series(
        80 * np.exp(np.cumsum(np.linspace(0.001, -0.002, 100))),
        index=dates,
    )

    result = Portfolio()
    result.add_asset(PriceSeries("AAA", prices_a), 0.6)
    result.add_asset(PriceSeries("BBB", prices_b), 0.4)

    return result


def test_simulation_shape(portfolio):
    simulator = PortfolioMonteCarloSimulator(
        portfolio, days=10, simulations=50, seed=42
    )

    result = simulator.simulate()

    assert result.shape == (11, 50)


def test_simulation_starts_at_initial_value(portfolio):
    simulator = PortfolioMonteCarloSimulator(
        portfolio, initial_value=100_000, days=10, seed=42
    )

    result = simulator.simulate()

    assert np.allclose(result.iloc[0], 100_000)


def test_simulated_values_are_positive(portfolio):
    simulator = PortfolioMonteCarloSimulator(
        portfolio, days=10, simulations=50, seed=42
    )

    result = simulator.simulate()

    assert (result > 0).all().all()


def test_simulation_is_reproducible(portfolio):
    first = PortfolioMonteCarloSimulator(
        portfolio, days=10, simulations=20, seed=42
    ).simulate()

    second = PortfolioMonteCarloSimulator(
        portfolio, days=10, simulations=20, seed=42
    ).simulate()

    pd.testing.assert_frame_equal(first, second)


def test_final_values_returns_series(portfolio):
    simulator = PortfolioMonteCarloSimulator(
        portfolio, days=10, simulations=20, seed=42
    )

    result = simulator.final_values()

    assert isinstance(result, pd.Series)
    assert len(result) == 20


def test_value_at_risk_is_finite(portfolio):
    simulator = PortfolioMonteCarloSimulator(
        portfolio, days=10, simulations=100, seed=42
    )

    assert np.isfinite(simulator.value_at_risk())


def test_conditional_value_at_risk_is_finite(portfolio):
    simulator = PortfolioMonteCarloSimulator(
        portfolio, days=10, simulations=100, seed=42
    )

    assert np.isfinite(simulator.conditional_value_at_risk())


def test_rejects_invalid_initial_value(portfolio):
    with pytest.raises(ValueError):
        PortfolioMonteCarloSimulator(portfolio, initial_value=0)


def test_rejects_invalid_days(portfolio):
    with pytest.raises(ValueError):
        PortfolioMonteCarloSimulator(portfolio, days=0)


def test_rejects_invalid_simulations(portfolio):
    with pytest.raises(ValueError):
        PortfolioMonteCarloSimulator(portfolio, simulations=0)


def test_rejects_empty_portfolio():
    with pytest.raises(ValueError):
        PortfolioMonteCarloSimulator(Portfolio())


def test_rejects_invalid_confidence_level(portfolio):
    simulator = PortfolioMonteCarloSimulator(portfolio)

    with pytest.raises(ValueError):
        simulator.value_at_risk(1.0)

    with pytest.raises(ValueError):
        simulator.conditional_value_at_risk(0)
