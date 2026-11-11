"""
Descarga de índices bursátiles de referencia (benchmarks).

Cada proveedor usa su propio símbolo para el mismo índice. Este módulo
traduce un nombre común ("SP500", "IBEX35"...) al símbolo de cada
proveedor y devuelve siempre un PriceSeries, con independencia de la
fuente utilizada.
"""

from Financial_toolkit.data.pipeline import DataPipeline
from Financial_toolkit.data.providers import (
    DataProvider,
    TwelveDataProvider,
    YahooFinanceProvider,
)
from Financial_toolkit.models.price_series import PriceSeries


# Símbolo de cada índice según el proveedor.
# Twelve Data no ofrece índices en su plan gratuito, por lo que para el
# S&P 500 se usa el ETF SPY, que replica el índice.
INDEX_SYMBOLS: dict[str, dict[str, str]] = {
    "SP500": {"yahoo": "^GSPC", "twelve_data": "SPY"},
    "NASDAQ100": {"yahoo": "^NDX", "twelve_data": "QQQ"},
    "IBEX35": {"yahoo": "^IBEX"},
    "EUROSTOXX50": {"yahoo": "^STOXX50E"},
}

INDEX_NAMES: dict[str, str] = {
    "SP500": "S&P 500",
    "NASDAQ100": "Nasdaq 100",
    "IBEX35": "IBEX 35",
    "EUROSTOXX50": "Euro Stoxx 50",
}


def _provider_key(provider: DataProvider) -> str:
    if isinstance(provider, YahooFinanceProvider):
        return "yahoo"

    if isinstance(provider, TwelveDataProvider):
        return "twelve_data"

    raise ValueError(
        f"No hay símbolos de índices definidos para {type(provider).__name__}."
    )


def index_symbol(index: str, provider: DataProvider) -> str:
    """Devuelve el símbolo de un índice para el proveedor indicado."""

    if not isinstance(provider, DataProvider):
        raise TypeError("El proveedor debe implementar DataProvider.")

    if not isinstance(index, str) or index.strip().upper() not in INDEX_SYMBOLS:
        raise ValueError(
            f"Índice no soportado. Opciones: {', '.join(INDEX_SYMBOLS)}."
        )

    key = _provider_key(provider)
    symbols = INDEX_SYMBOLS[index.strip().upper()]

    if key not in symbols:
        raise ValueError(
            f"El índice {index} no está disponible en "
            f"{type(provider).__name__}."
        )

    return symbols[key]


def download_index(
    provider: DataProvider,
    start: str,
    end: str,
    index: str = "SP500",
) -> PriceSeries:
    """
    Descarga un índice de referencia y lo devuelve como PriceSeries.

    Usa el mismo DataPipeline que los activos de la cartera, por lo que
    el índice pasa por la misma limpieza y validación.
    """

    symbol = index_symbol(index, provider)

    data = DataPipeline(provider).run(
        tickers=[symbol],
        start=start,
        end=end,
    )

    return PriceSeries.from_dataframe(data, symbol)
