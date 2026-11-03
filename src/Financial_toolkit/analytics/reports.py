import numpy as np

from Financial_toolkit.models.portfolio import Portfolio


def generate_portfolio_report(
    portfolio: Portfolio,
    periods: int = 252,
) -> str:
    """
    Genera un informe Markdown con las métricas y diagnósticos de una cartera.

    Parameters
    ----------
    portfolio : Portfolio
        Cartera que se desea analizar.
    periods : int
        Número de períodos de negociación por año.

    Returns
    -------
    str
        Informe estructurado en formato Markdown.
    """

    if not isinstance(portfolio, Portfolio):
        raise TypeError("Se debe proporcionar una instancia de Portfolio.")

    if (
        isinstance(periods, bool)
        or not isinstance(periods, int)
        or periods <= 0
    ):
        raise ValueError("Los períodos deben ser un entero positivo.")

    portfolio.validate_weights()

    returns = portfolio.returns()

    if returns.empty:
        raise ValueError(
            "No hay suficientes datos para generar el informe."
        )

    annualized_return = portfolio.annualized_return(periods)
    annualized_volatility = portfolio.volatility(periods)

    cumulative_return = float((1 + returns).prod() - 1)

    observations = len(returns)
    number_of_assets = len(portfolio.assets)

    report = [
        "# Informe de análisis de cartera",
        "",
        "## 1. Composición de la cartera",
        "",
        "| Activo | Ponderación |",
        "|---|---:|",
    ]

    for ticker, weight in portfolio.weights.items():
        report.append(f"| {ticker} | {weight:.2%} |")

    report.extend([
        "",
        "## 2. Métricas de rendimiento y riesgo",
        "",
        "| Métrica | Resultado |",
        "|---|---:|",
        f"| Rentabilidad acumulada | {cumulative_return:.2%} |",
        f"| Rentabilidad anualizada | {annualized_return:.2%} |",
        f"| Volatilidad anualizada | {annualized_volatility:.2%} |",
        f"| Observaciones disponibles | {observations} |",
        f"| Número de activos | {number_of_assets} |",
        "",
        "## 3. Diagnóstico de riesgo",
        "",
    ])

    warnings = []

    largest_weight = max(portfolio.weights.values())

    if largest_weight >= 0.50:
        warnings.append(
            "La cartera presenta concentración: un activo representa "
            "al menos el 50 % de la inversión."
        )

    if annualized_volatility >= 0.30:
        warnings.append(
            "La volatilidad anualizada es elevada (30 % o superior)."
        )

    if annualized_return < 0:
        warnings.append(
            "La rentabilidad anualizada histórica es negativa."
        )

    if observations < periods:
        warnings.append(
            "El histórico disponible es inferior a un año de negociación; "
            "las métricas anualizadas deben interpretarse con cautela."
        )

    if warnings:
        report.extend(f"- **Advertencia:** {warning}" for warning in warnings)
    else:
        report.append(
            "No se han detectado advertencias según los umbrales "
            "básicos establecidos."
        )

    report.extend([
        "",
        "## 4. Metodología y limitaciones",
        "",
        f"- Las métricas utilizan {periods} períodos por año.",
        "- La rentabilidad de cartera se calcula aplicando las ponderaciones "
        "a las rentabilidades históricas de los activos.",
        "- Las rentabilidades se alinean por fecha y se eliminan las "
        "observaciones incompletas.",
        "- Los resultados históricos no garantizan rendimientos futuros.",
        "- Este informe no constituye asesoramiento financiero.",
        "",
    ])

    return "\n".join(report)
