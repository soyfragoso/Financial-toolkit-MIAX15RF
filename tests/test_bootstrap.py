import numpy as np
import pandas as pd
import pytest

from Financial_toolkit.models.portfolio import Portfolio
from Financial_toolkit.models.price_series import PriceSeries
from Financial_toolkit.simulation.bootstrap import PortfolioBootstrapSimulator


@pytest.fixture
def portfolio():
    rng = np.random.default_rng(0)
    dates = pd.date_range("2024-01-01", periods=300)

    prices_a = 100 * np.cumprod(1 + rng.normal(0.0005, 0.01, 300))
    prices_b = 50 * np.cumprod(1 + rng.normal(0.0003, 0.02, 300))

    result = Portfolio()
    result.add_asset(PriceSeries("AAA", pd.Series(prices_a, index=dates)), 0.6)
    result.add_asset(PriceSeries("BBB", pd.Series(prices_b, index=dates)), 0.4)
    return result


def test_shape_and_initial_value(portfolio):
    simulator = portfolio.bootstrap(
        initial_value=10_000,
        days=20,
        simulations=50,
        seed=1,
    )
    paths = simulator.simulate()

    assert isinstance(simulator, PortfolioBootstrapSimulator)
    assert paths.shape == (21, 50)
    assert np.allclose(paths.iloc[0], 10_000)
    assert (paths > 0).all().all()


def test_reproducible_with_seed(portfolio):
    first = portfolio.bootstrap(days=10, simulations=20, seed=7).simulate()
    second = portfolio.bootstrap(days=10, simulations=20, seed=7).simulate()

    pd.testing.assert_frame_equal(first, second)


def test_only_uses_historical_returns(portfolio):
    # Con un solo día simulado, cada rentabilidad de la cartera debe
    # coincidir con la de alguna fecha histórica.
    simulator = portfolio.bootstrap(
        initial_value=1.0,
        days=1,
        simulations=200,
        seed=3,
    )
    simulated = simulator.final_values().to_numpy() - 1.0
    historical = portfolio.returns().to_numpy()

    for value in simulated:
        assert np.isclose(historical, value).any()


def test_block_bootstrap_copies_consecutive_days(portfolio):
    # Con un solo activo y bloques de 5 días, cada trayectoria de 5 días
    # debe reproducir exactamente una racha histórica consecutiva.
    single = Portfolio()
    single.add_asset(portfolio.assets["AAA"], 1.0)

    paths = single.bootstrap(
        initial_value=1.0,
        days=5,
        simulations=30,
        block_size=5,
        seed=11,
    ).simulate()

    simulated_returns = paths.pct_change().dropna().to_numpy()
    windows = np.lib.stride_tricks.sliding_window_view(
        portfolio.assets["AAA"].returns().to_numpy(),
        5,
    )

    for column in simulated_returns.T:
        assert np.isclose(windows, column).all(axis=1).any()


def test_risk_metrics_inherited(portfolio):
    simulator = portfolio.bootstrap(days=30, simulations=500, seed=5)

    var = simulator.value_at_risk(0.95)
    cvar = simulator.conditional_value_at_risk(0.95)

    assert cvar >= var


@pytest.mark.parametrize("block_size", [0, -1, 1.5, True])
def test_rejects_invalid_block_size(portfolio, block_size):
    with pytest.raises(ValueError):
        PortfolioBootstrapSimulator(portfolio, block_size=block_size)


def test_rejects_block_larger_than_history(portfolio):
    simulator = portfolio.bootstrap(block_size=10_000)

    with pytest.raises(ValueError):
        simulator.simulate()


def test_rejects_invalid_portfolio():
    with pytest.raises(TypeError):
        PortfolioBootstrapSimulator("invalid")
