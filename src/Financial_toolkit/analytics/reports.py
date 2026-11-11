import numpy as np

from Financial_toolkit.models.portfolio import Portfolio


def generate_portfolio_report(
    portfolio: Portfolio,
    periods: int = 252,
    benchmark=None,
) -> str:
    """
    Genera un informe Markdown con las métricas y diagnósticos de una cartera.

    Parameters
    ----------
    portfolio : Portfolio
        Cartera que se desea analizar.
    periods : int
        Número de períodos de negociación por año.
    benchmark : PriceSeries, opcional
        Índice de referencia (por ejemplo, el S&P 500).

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
    mean_return = portfolio.mean_return()
    median_return = portfolio.median_return()
    maximum_drawdown = portfolio.maximum_drawdown()

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
        f"| Máximo drawdown | {maximum_drawdown:.2%} |",
        f"| Rentabilidad diaria media | {mean_return:.4%} |",
        f"| Rentabilidad diaria mediana | {median_return:.4%} |",
        f"| Observaciones disponibles | {observations} |",
        f"| Número de activos | {number_of_assets} |",
    ])

    section = 3
    warnings = []

    if benchmark is not None:
        from Financial_toolkit.analytics.benchmark import compare_with_benchmark

        comparison = compare_with_benchmark(portfolio, benchmark, periods)
        verdict = (
            "**La cartera bate al índice** en el periodo analizado."
            if comparison.beats_benchmark
            else "**La cartera no bate al índice** en el periodo analizado."
        )

        report.extend([
            "",
            f"## {section}. Comparación con el índice ({comparison.benchmark})",
            "",
            f"Periodo común: {comparison.start.date()} a {comparison.end.date()} "
            f"({comparison.observations} observaciones).",
            "",
            "| Métrica | Cartera | Índice |",
            "|---|---:|---:|",
            f"| Rentabilidad acumulada | {comparison.portfolio_return:.2%} | "
            f"{comparison.benchmark_return:.2%} |",
            f"| Rentabilidad anualizada | {comparison.portfolio_annualized:.2%} | "
            f"{comparison.benchmark_annualized:.2%} |",
            f"| Volatilidad anualizada | {comparison.portfolio_volatility:.2%} | "
            f"{comparison.benchmark_volatility:.2%} |",
            f"| Máximo drawdown | {comparison.portfolio_max_drawdown:.2%} | "
            f"{comparison.benchmark_max_drawdown:.2%} |",
            "",
            f"- Diferencia de rentabilidad acumulada: {comparison.excess_return:+.2%}.",
            f"- Diferencia de rentabilidad anualizada: {comparison.excess_annualized:+.2%}.",
            f"- Beta frente al índice: {comparison.beta:.2f}. "
            f"Correlación: {comparison.correlation:.2f}.",
            f"- Tracking error: {comparison.tracking_error:.2%}.",
            f"- Días en que la cartera supera al índice: "
            f"{comparison.days_outperforming:.2%}.",
            f"- {verdict}",
        ])
        section += 1

        if comparison.beta >= 1.2:
            warnings.append(
                "La beta frente al índice es elevada (1,2 o superior): la "
                "cartera amplifica los movimientos del mercado."
            )

    report.extend([
        "",
        f"## {section}. Diagnóstico de riesgo",
        "",
    ])

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

    if maximum_drawdown <= -0.20:
        warnings.append(
            "La cartera ha sufrido una caída máxima del 20 % o superior "
            "desde un máximo."
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
        f"## {section + 1}. Metodología y limitaciones",
        "",
        f"- Las métricas utilizan {periods} períodos por año.",
        "- La rentabilidad de cartera se calcula aplicando las ponderaciones "
        "a las rentabilidades históricas de los activos.",
        "- Si la mediana diaria difiere mucho de la media, la distribución "
        "de rentabilidades es asimétrica o tiene días extremos.",
        "- Las rentabilidades se alinean por fecha y se eliminan las "
        "observaciones incompletas.",
        "- La comparación con el índice usa solo las fechas comunes a "
        "cartera e índice; la rentabilidad del índice no incluye dividendos.",
        "- Los resultados históricos no garantizan rendimientos futuros.",
        "- Este informe no constituye asesoramiento financiero.",
        "",
    ])

    return "\n".join(report)
