import numpy as np
import pandas as pd
import pytest

from Financial_toolkit.simulation.monte_carlo import MonteCarloSimulator


@pytest.fixture
def simulator():
    return MonteCarloSimulator(
        initial_price=100,
        expected_return=0.08,
        volatility=0.20,
        days=252,
        simulations=1000,
        seed=42,
    )


def test_simulator_returns_dataframe(simulator):
    result = simulator.simulate()

    assert isinstance(result, pd.DataFrame)
    assert result.shape == (253, 1000)


def test_simulator_starts_at_initial_price(simulator):
    result = simulator.simulate()

    assert np.allclose(result.iloc[0].values, 100)


def test_simulator_generates_positive_prices(simulator):
    result = simulator.simulate()

    assert (result > 0).all().all()


def test_simulator_is_reproducible(simulator):
    first = simulator.simulate()
    second = simulator.simulate()

    pd.testing.assert_frame_equal(first, second)


def test_simulator_final_values(simulator):
    result = simulator.final_values()

    assert isinstance(result, pd.Series)
    assert len(result) == 1000
    assert (result > 0).all()


def test_simulator_calculates_var(simulator):
    result = simulator.value_at_risk()

    assert isinstance(result, float)
    assert np.isfinite(result)


def test_simulator_calculates_cvar(simulator):
    result = simulator.conditional_value_at_risk()

    assert isinstance(result, float)
    assert np.isfinite(result)


def test_simulator_rejects_invalid_initial_price():
    with pytest.raises(ValueError):
        MonteCarloSimulator(
            initial_price=0,
            expected_return=0.08,
            volatility=0.20,
        )


def test_simulator_rejects_negative_volatility():
    with pytest.raises(ValueError):
        MonteCarloSimulator(
            initial_price=100,
            expected_return=0.08,
            volatility=-0.20,
        )


def test_simulator_rejects_invalid_days():
    with pytest.raises(ValueError):
        MonteCarloSimulator(
            initial_price=100,
            expected_return=0.08,
            volatility=0.20,
            days=0,
        )


def test_simulator_rejects_invalid_simulations():
    with pytest.raises(ValueError):
        MonteCarloSimulator(
            initial_price=100,
            expected_return=0.08,
            volatility=0.20,
            simulations=0,
        )


def test_simulator_rejects_invalid_confidence_level(simulator):
    with pytest.raises(ValueError):
        simulator.value_at_risk(confidence_level=1.0)
@pytest.mark.parametrize(
    "parameter",
    ["initial_price", "expected_return", "volatility"],
)
def test_simulator_rejects_boolean_parameters(parameter):
    params = {
        "initial_price": 100,
        "expected_return": 0.08,
        "volatility": 0.20,
    }

    params[parameter] = True

    with pytest.raises(ValueError):
        MonteCarloSimulator(**params)

@pytest.mark.parametrize("seed", ["42", -1, 42.5, True])
def test_simulator_rejects_invalid_seed(seed):
    with pytest.raises(ValueError):
        MonteCarloSimulator(
            initial_price=100,
            expected_return=0.08,
            volatility=0.20,
            seed=seed,
        )
def test_var_and_cvar_reuse_same_simulation(simulator, monkeypatch):
    calls = 0
    original_simulate = simulator.simulate

    def counted_simulate():
        nonlocal calls
        calls += 1
        return original_simulate()

    monkeypatch.setattr(simulator, "simulate", counted_simulate)

    simulator.value_at_risk()
    simulator.conditional_value_at_risk()

    assert calls == 1


def test_reset_generates_new_simulation(simulator, monkeypatch):
    calls = 0
    original_simulate = simulator.simulate

    def counted_simulate():
        nonlocal calls
        calls += 1
        return original_simulate()

    monkeypatch.setattr(simulator, "simulate", counted_simulate)

    simulator.final_values()
    assert calls == 1

    simulator.reset()
    simulator.final_values()

    assert calls == 2