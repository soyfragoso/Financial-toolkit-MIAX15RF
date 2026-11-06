"""Cálculo de rentabilidad y valor de cartera ajustados por inflación."""

import numpy as np
import pandas as pd


def calculate_real_performance(
    portfolio_returns: pd.Series,
    cpi: pd.Series,
    initial_capital: float,
) -> dict:
    """
    Calcula la evolución nominal y real de una inversión.

    El IPC se alinea mediante la última observación cuya fecha de
    referencia sea igual o anterior a cada fecha de rentabilidad.

    Esta alineación evita utilizar observaciones con fechas de referencia
    posteriores, pero no garantiza que los datos ya estuvieran publicados
    en esas fechas. FRED proporciona fechas de observación, no necesariamente
    fechas de publicación. Por tanto, el resultado es una estimación histórica
    ajustada por inflación, no un backtest point-in-time libre de look-ahead
    bias. Tampoco se controlan posibles revisiones históricas de los datos.

    CPI debe contener una observación igual o anterior a la primera
    fecha de rentabilidad.
    """
    if not isinstance(portfolio_returns, pd.Series):
        raise TypeError("Las rentabilidades deben ser una pd.Series.")

    if not isinstance(cpi, pd.Series):
        raise TypeError("El IPC debe proporcionarse como una pd.Series.")

    if portfolio_returns.empty or cpi.empty:
        raise ValueError("Las series de rentabilidad e IPC no pueden estar vacías.")

    if (
        not isinstance(initial_capital, (int, float))
        or not np.isfinite(initial_capital)
        or initial_capital <= 0
    ):
        raise ValueError("El capital inicial debe ser un número positivo y finito.")

    returns = portfolio_returns.copy()
    inflation_index = cpi.copy()

    returns.index = pd.DatetimeIndex(
        pd.to_datetime(returns.index, errors="coerce")
    )
    inflation_index.index = pd.DatetimeIndex(
        pd.to_datetime(inflation_index.index, errors="coerce")
    )

    if returns.index.isna().any() or inflation_index.index.isna().any():
        raise ValueError("Las series contienen fechas no válidas.")

    if returns.index.has_duplicates or inflation_index.index.has_duplicates:
        raise ValueError("Las series no pueden contener fechas duplicadas.")

    returns = pd.to_numeric(returns, errors="coerce").sort_index()
    inflation_index = pd.to_numeric(
        inflation_index, errors="coerce"
    ).sort_index()

    if not np.isfinite(returns.to_numpy(dtype=float)).all():
        raise ValueError("Las rentabilidades contienen valores no finitos.")

    if (returns <= -1).any():
        raise ValueError("Las rentabilidades no pueden ser iguales o inferiores al -100 %.")

    if not np.isfinite(inflation_index.to_numpy(dtype=float)).all():
        raise ValueError("El IPC contiene valores no finitos.")

    if (inflation_index <= 0).any():
        raise ValueError("Los valores del IPC deben ser positivos.")

    # Alineación temporal: utiliza únicamente el último IPC conocido.
    aligned_cpi = inflation_index.reindex(returns.index, method="ffill")

    if aligned_cpi.isna().any():
        raise ValueError(
            "Falta una observación del IPC igual o anterior "
            "a la fecha inicial de la cartera."
        )

    nominal_growth = (1.0 + returns).cumprod()
    nominal_values = float(initial_capital) * nominal_growth

    inflation_factor = aligned_cpi / float(aligned_cpi.iloc[0])
    real_values = nominal_values / inflation_factor

    nominal_final = float(nominal_values.iloc[-1])
    real_final = float(real_values.iloc[-1])
    inflation_accumulated = float(inflation_factor.iloc[-1] - 1.0)

    path = pd.DataFrame({
        "nominal_value": nominal_values,
        "cpi": aligned_cpi,
        "inflation_factor": inflation_factor,
        "real_value": real_values,
    })
    path.index.name = "date"

    return {
        "initial_capital": float(initial_capital),
        "nominal_return": float(nominal_growth.iloc[-1] - 1.0),
        "real_return": float(real_final / initial_capital - 1.0),
        "inflation_accumulated": inflation_accumulated,
        "nominal_final_value": nominal_final,
        "real_final_value": real_final,
        "inflation_impact": float(nominal_final - real_final),
        "path": path,
    }
