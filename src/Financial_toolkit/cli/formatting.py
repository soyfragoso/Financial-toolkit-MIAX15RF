
from __future__ import annotations

from datetime import date, datetime
from numbers import Real


def format_currency(
    value: Real,
    currency: str = "USD",
    decimals: int = 2,
) -> str:
    """Formatea un importe monetario."""
    return f"{currency} {float(value):,.{decimals}f}"


def format_percentage(
    value: Real,
    decimals: int = 2,
) -> str:
    """Formatea una proporción como porcentaje."""
    return f"{float(value) * 100:,.{decimals}f}%"


def format_number(
    value: Real,
    decimals: int = 2,
) -> str:
    """Formatea un número con separadores de miles."""
    return f"{float(value):,.{decimals}f}"


def format_date(value: date | datetime | str) -> str:
    """Normaliza la presentación de fechas."""
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d")

    if isinstance(value, date):
        return value.strftime("%Y-%m-%d")

    return str(value)


def format_metric(
    name: str,
    value: Real,
    percentage: bool = False,
    currency: str | None = None,
    decimals: int = 2,
) -> str:
    """Presenta una métrica con su nombre y unidad."""
    if percentage:
        formatted_value = format_percentage(value, decimals)
    elif currency:
        formatted_value = format_currency(
            value,
            currency=currency,
            decimals=decimals,
        )
    else:
        formatted_value = format_number(value, decimals)

    return f"{name}: {formatted_value}"


def format_change(value: Real, decimals: int = 2) -> str:
    """Añade signo positivo o negativo a una variación."""
    number = float(value) * 100
    return f"{number:+,.{decimals}f}%"


def format_status(value: bool) -> str:
    """Devuelve un indicador textual de estado."""
    return "Correcto" if value else "Advertencia"
