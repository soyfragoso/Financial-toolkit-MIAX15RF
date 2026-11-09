"""
Métricas de rentabilidad ajustada al riesgo: ratio de Sharpe y ratio de Sortino.

El tipo libre de riesgo puede indicarse a mano o calcularse a partir de una
serie de tipos de interés de FRED (por ejemplo, FEDFUNDS o GS10), que el
toolkit ya descarga en su análisis macroeconómico.
"""

from numbers import Real

import numpy as np
import pandas as pd

from Financial_toolkit.models.macro_series import MacroSeries


def _validate_periods(periods: int) -> None:
    """Comprueba que los períodos por año sean un entero positivo."""

    if isinstance(periods, bool) or not isinstance(periods, int) or periods <= 0:
        raise ValueError("Los períodos deben ser un entero positivo.")


def _validate_rate(risk_free_rate: float) -> None:
    """Comprueba que el tipo libre de riesgo sea un número razonable."""

    if (
        isinstance(risk_free_rate, bool)
        or not isinstance(risk_free_rate, Real)
        or not np.isfinite(risk_free_rate)
    ):
        raise ValueError("El tipo libre de riesgo debe ser numérico y finito.")

    if not -1 < risk_free_rate < 1:
        raise ValueError(
            "El tipo libre de riesgo se expresa en tanto por uno "
            "(por ejemplo, 0.04 para un 4 %)."
        )


def _get_returns(source) -> pd.Series:
    """
    Obtiene las rentabilidades periódicas de una cartera, un activo o una serie.

    Acepta un Portfolio o un PriceSeries (cualquier objeto con un método
    returns()) o directamente una pd.Series de rentabilidades.
    """

    if isinstance(source, pd.Series):
        returns = source
    elif hasattr(source, "returns") and callable(source.returns):
        returns = source.returns()
    else:
        raise TypeError(
            "Se necesita una cartera, un activo o una pd.Series de rentabilidades."
        )

    returns = pd.to_numeric(returns, errors="coerce").dropna()

    if len(returns) < 2:
        raise ValueError(
            "Se necesitan al menos dos rentabilidades para calcular el ratio."
        )

    if not np.isfinite(returns.to_numpy()).all():
        raise ValueError("Las rentabilidades contienen valores no finitos.")

    return returns


def risk_free_rate_from_macro(
    series: MacroSeries,
    start: str | None = None,
    end: str | None = None,
) -> float:
    """
    Calcula el tipo libre de riesgo medio a partir de una serie de FRED.

    Pensado para series de tipos de interés expresadas en porcentaje, como
    FEDFUNDS (tipo de los fondos federales) o GS10 (bono del Tesoro a
    10 años). No debe usarse con índices como el IPC.

    Parameters
    ----------
    series : MacroSeries
        Serie de tipos de interés en porcentaje (4.33 significa 4,33 %).
    start, end : str, optional
        Fechas que delimitan el periodo, en formato YYYY-MM-DD. Lo normal
        es usar el mismo periodo que el de la cartera.

    Returns
    -------
    float
        Tipo medio anual en tanto por uno (0.0433 para un 4,33 %).
    """

    if not isinstance(series, MacroSeries):
        raise TypeError("La serie debe ser un objeto MacroSeries.")

    values = series.values

    if start is not None:
        values = values[values.index >= pd.Timestamp(start)]

    if end is not None:
        values = values[values.index <= pd.Timestamp(end)]

    if values.empty:
        raise ValueError("La serie no tiene datos en el periodo indicado.")

    rate = float(values.mean()) / 100
    _validate_rate(rate)

    return rate


def sharpe_ratio(
    source,
    risk_free_rate: float = 0.0,
    periods: int = 252,
) -> float:
    """
    Calcula el ratio de Sharpe anualizado.

    Mide cuánta rentabilidad extra, por encima del tipo libre de riesgo,
    se obtiene por cada unidad de volatilidad.

    Sharpe = media(r - rf) / desviación(r - rf) × raíz(períodos)

    Parameters
    ----------
    source : Portfolio, PriceSeries o pd.Series
        Cartera, activo o serie de rentabilidades periódicas.
    risk_free_rate : float
        Tipo libre de riesgo anual en tanto por uno (0.04 para un 4 %).
    periods : int
        Número de períodos de negociación por año.

    Returns
    -------
    float
        Ratio de Sharpe anualizado.
    """

    _validate_rate(risk_free_rate)
    _validate_periods(periods)

    excess = _get_returns(source) - risk_free_rate / periods
    volatility = excess.std(ddof=1)

    if volatility == 0:
        raise ValueError(
            "La volatilidad es nula: el ratio de Sharpe no está definido."
        )

    return float(excess.mean() / volatility * np.sqrt(periods))


def sortino_ratio(
    source,
    risk_free_rate: float = 0.0,
    periods: int = 252,
) -> float:
    """
    Calcula el ratio de Sortino anualizado.

    Es como el ratio de Sharpe, pero solo penaliza la volatilidad negativa:
    los días en que la rentabilidad queda por debajo del tipo libre de riesgo.

    Sortino = media(r - rf) × períodos / desviación a la baja anualizada

    Parameters
    ----------
    source : Portfolio, PriceSeries o pd.Series
        Cartera, activo o serie de rentabilidades periódicas.
    risk_free_rate : float
        Tipo libre de riesgo anual en tanto por uno (0.04 para un 4 %).
    periods : int
        Número de períodos de negociación por año.

    Returns
    -------
    float
        Ratio de Sortino anualizado. Si no hay ningún período por debajo
        del tipo libre de riesgo, devuelve infinito.
    """

    _validate_rate(risk_free_rate)
    _validate_periods(periods)

    excess = _get_returns(source) - risk_free_rate / periods
    downside = np.minimum(excess, 0)
    downside_deviation = np.sqrt((downside ** 2).mean()) * np.sqrt(periods)

    if downside_deviation == 0:
        return float("inf")

    return float(excess.mean() * periods / downside_deviation)


def risk_adjusted_summary(
    source,
    risk_free_rate: float = 0.0,
    periods: int = 252,
) -> pd.Series:
    """
    Resume en una tabla el tipo libre de riesgo y los ratios de Sharpe y Sortino.
    """

    return pd.Series({
        "Tipo libre de riesgo": risk_free_rate,
        "Ratio de Sharpe": sharpe_ratio(source, risk_free_rate, periods),
        "Ratio de Sortino": sortino_ratio(source, risk_free_rate, periods),
    })


def interpret_ratio(value: float) -> str:
    """
    Traduce un ratio de Sharpe o de Sortino a una lectura cualitativa.

    Los umbrales son una referencia habitual, no una regla universal.
    Compara siempre Sharpe con Sharpe y Sortino con Sortino.
    """

    if isinstance(value, bool) or not isinstance(value, Real) or np.isnan(value):
        raise ValueError("El ratio debe ser numérico.")

    if value < 0:
        return "Negativo: un activo sin riesgo habría rendido más"
    if value < 1:
        return "Aceptable: compensa el riesgo, pero de forma moderada"
    if value < 2:
        return "Bueno: compensa bien el riesgo asumido"
    return "Excelente: muy buena rentabilidad por unidad de riesgo"