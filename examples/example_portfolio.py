
"""
MIAX 15 Financial Powertool (miniagente interactivo)

Run from the project root:
    python examples/example_portfolio.py

The miniagent uses the Financial_toolkit package without modifying
its core financial logic.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

from rich.panel import Panel

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from Financial_toolkit.data.pipeline import DataPipeline
from Financial_toolkit.data.company_universe import (
    CATEGORIES,
    generate_proposals,
    rank_companies,
)
from Financial_toolkit.data.providers import (
    TwelveDataProvider,
    YahooFinanceProvider,
)
from Financial_toolkit.models.portfolio import Portfolio
from Financial_toolkit.models.price_series import PriceSeries

from Financial_toolkit.cli.banners import (
    show_welcome,
    show_module_banner,
    show_goodbye,
)

from Financial_toolkit.cli.interface import (
    console,
    print_section,
    print_success,
    print_warning,
    print_error,
    print_info,
    print_table,
    print_quality_status,
    show_progress,
)

from Financial_toolkit.cli.formatting import (
    format_currency,
    format_percentage,
    format_date,
    format_change,
    format_number,
)

# ---------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_ROOT = PROJECT_ROOT / "outputs"

# ---------------------------------------------------------------------
# Terminal interface and input validation
# ---------------------------------------------------------------------

def print_header(title: str) -> None:
    print_section(title)


def ask_text(prompt: str, default: str | None = None) -> str:
    while True:
        value = console.input(
            f"[bold cyan]{prompt}[/bold cyan]"
            f"{f' [{default}]' if default is not None else ''}: "
        ).strip()

        if not value and default is not None:
            return default

        if value:
            return value

        print_warning("Introduce un valor válido.")


def ask_choice(prompt: str, options: dict[str, str]) -> str:
    print_section(prompt)

    rows = [
        (key, description)
        for key, description in options.items()
    ]

    print_table("Opciones disponibles", ["Opción", "Descripción"], rows)

    while True:
        choice = ask_text("Selecciona una opción")

        if choice in options:
            return choice

        print_warning("Opción no válida. Inténtalo de nuevo.")


def ask_yes_no(prompt: str, default: bool = True) -> bool:
    default_value = "s" if default else "n"

    while True:
        answer = ask_text(
            f"{prompt} (s/n)",
            default_value,
        ).lower()

        if answer in {"s", "si", "sí", "y", "yes"}:
            return True

        if answer in {"n", "no"}:
            return False

        print_warning("Responde sí o no.")


def ask_integer(
    prompt: str,
    default: int,
    minimum: int = 1,
    maximum: int | None = None,
) -> int:
    while True:
        raw = ask_text(prompt, str(default))

        try:
            value = int(raw)
        except ValueError:
            print_warning("Introduce un número entero.")
            continue

        if value < minimum or (
            maximum is not None and value > maximum
        ):
            print_warning(
                f"El valor debe estar entre {minimum} "
                f"y {maximum if maximum is not None else 'sin límite'}."
            )
            continue

        return value


def ask_float(
    prompt: str,
    default: float,
    minimum: float = 0.0,
) -> float:
    while True:
        raw = ask_text(prompt, str(default))

        try:
            value = float(raw.replace(",", "."))
        except ValueError:
            print_warning("Introduce un número válido.")
            continue

        if not np.isfinite(value) or value < minimum:
            print_warning(
                f"El valor debe ser finito y no inferior a {minimum}."
            )
            continue

        return value


def ask_date(prompt: str, default: str) -> str:
    while True:
        value = ask_text(prompt, default)

        try:
            if re.fullmatch(r"\d{4}", value):
                value = f"{value}-01-01"

            parsed = datetime.strptime(value, "%Y-%m-%d")
            return parsed.strftime("%Y-%m-%d")
        except ValueError:
            print_warning(
                "Utiliza YYYY, que equivale al 1 de enero, "
                "o el formato completo YYYY-MM-DD."
            )
# ---------------------------------------------------------------------
# 1–2. Welcome and provider selection
# ---------------------------------------------------------------------

def choose_provider():
    show_welcome()

    print_info(
        "Este asistente permite analizar activos, construir carteras, "
        "estudiar riesgos y comparar fuentes de datos financieros."
    )

    print_warning(
        "Los resultados son análisis cuantitativos históricos y "
        "escenarios estadísticos, no recomendaciones de inversión."
    )

    while True:
        choice = ask_choice(
            "¿Qué proveedor deseas utilizar?",
            {
                "1": "Yahoo Finance (sin API key)",
                "2": "Twelve Data (requiere API key)",
            },
        )

        if choice == "1":
            print_success("Proveedor seleccionado: Yahoo Finance")
            return YahooFinanceProvider(), "Yahoo Finance"

        if not os.getenv("TWELVE_DATA_API_KEY"):
            print_error(
                "No se ha encontrado TWELVE_DATA_API_KEY. "
                "Configura la variable de entorno o el secreto "
                "de Codespaces y vuelve a intentarlo."
            )
            continue

        print_success("Proveedor seleccionado: Twelve Data")
        return TwelveDataProvider(), "Twelve Data"
# ---------------------------------------------------------------------
# 3–5. Assets, weights and historical period
# ---------------------------------------------------------------------

def collect_tickers() -> list[str]:
    show_module_banner(
        "SELECCIÓN DE ACTIVOS",
        "Construye tu cartera manualmente o utiliza el universo de compañías.",
    )

    mode = ask_choice(
        "¿Cómo deseas seleccionar tus compañías?",
        {
            "1": "Introducir mis propias compañías",
            "2": "Utilizar la base de datos de MIAX 15",
        },
    )

    if mode == "1":
        while True:
            raw = ask_text(
                "Introduce tus tickers separados por comas",
                "AAPL, MSFT, NVDA",
            )
            tickers = [
                ticker.strip().upper()
                for ticker in raw.split(",")
                if ticker.strip()
            ]

            if not tickers:
                print_warning("Debes indicar al menos un activo.")
                continue

            if len(tickers) != len(set(tickers)):
                print_warning("Hay tickers duplicados. Corrige la selección.")
                continue

            print_success(
                f"Se han seleccionado {len(tickers)} activos: "
                f"{', '.join(tickers)}"
            )
            return tickers

    print_info(
        "Calculando el rendimiento histórico de cinco años "
        "de las compañías candidatas mediante Yahoo Finance."
    )
    print_warning(
        "Esta consulta requiere conexión a Internet y puede tardar. "
        "Los resultados históricos no garantizan rendimientos futuros."
    )

    try:
        rankings = rank_companies(years=5, limit=25)
    except Exception as error:
        print_error(f"No se pudo construir el universo: {error}")
        raise

    for category, category_name in CATEGORIES.items():
        ranked = rankings.get(category, [])
        print_section(
            f"UNIVERSO {category}: {category_name} "
            f"({len(ranked)} compañías válidas)"
        )
        if ranked:
            print_table(
                f"25 mejores candidatas — {category_name}",
                ["Ticker", "Rendimiento acumulado 5 años"],
                [
                    (ticker, format_percentage(performance))
                    for ticker, performance in ranked
                ],
            )
        else:
            print_warning(
                f"No se encontraron datos suficientes para {category_name}."
            )

    while True:
        try:
            proposals = generate_proposals(rankings)
        except ValueError as error:
            print_error(str(error))
            print_warning(
                "Comprueba la conexión con Yahoo Finance y vuelve a ejecutar."
            )
            raise

        print_section("PROPUESTAS ALEATORIAS DE CARTERA")
        print_info(
            "A-E: cinco compañías de una misma categoría. "
            "Z: una compañía de cada categoría."
        )

        rows = []
        for option, tickers in proposals.items():
            if option == "Z":
                description = "Una compañía de cada categoría"
            else:
                description = CATEGORIES[option]

            rows.append((option, description, ", ".join(tickers)))

        print_table(
            "Selecciona tu cartera",
            ["Opción", "Categoría", "Tickers"],
            rows,
        )

        print_info(
            "Pulsa A, B, C, D o E para elegir una categoría; "
            "Z para diversificar; R para sortear de nuevo."
        )

        choice = ask_text("Tu selección").strip().upper()

        if choice == "R":
            print_info("Generando nuevas combinaciones aleatorias...")
            continue

        if choice not in proposals:
            print_warning("Opción no válida. Elige A, B, C, D, E, Z o R.")
            continue

        selected = proposals[choice]
        print_success(
            f"Cartera seleccionada ({choice}): {', '.join(selected)}"
        )
        return selected


def collect_weights(tickers: list[str]) -> dict[str, float]:
    show_module_banner(
        "PONDERACIÓN DE LA CARTERA",
        "Distribuye el capital entre los activos seleccionados.",
    )
    equal_weight = 100.0 / len(tickers)

    print_info(
        f"Distribución equitativa sugerida: {equal_weight:.4f} % por activo."
    )
    print_info(
        "Pulsa Enter en cada línea para aceptar el peso sugerido, "
        "o escribe I para distribuir todo equitativamente en un solo paso."
    )

    while True:
        weights = {}
        invalid = False

        for ticker in tickers:
            raw = console.input(
                f"[bold cyan]Peso de {ticker} (%)"
                f" [{equal_weight:.4f}]: [/bold cyan]"
            ).strip()

            if raw.lower() == "i":
                weights = {
                    symbol: 1.0 / len(tickers)
                    for symbol in tickers
                }
                print_success("Distribución equitativa aplicada a toda la cartera.")
                break

            if not raw:
                value = equal_weight
            else:
                try:
                    value = float(raw.replace(",", "."))
                except ValueError:
                    print_warning("Introduce un porcentaje válido o pulsa I.")
                    invalid = True
                    break

            if not np.isfinite(value) or value <= 0:
                print_warning("El peso debe ser un número positivo y finito.")
                invalid = True
                break

            weights[ticker] = value / 100.0

        if not invalid and not weights:
            pass
        elif not invalid:
            total = sum(weights.values())
            if np.isclose(total, 1.0, atol=1e-6):
                print_success(f"Ponderaciones validadas: {total:.6%}")
                print_table(
                    "Composición de la cartera",
                    ["Activo", "Peso"],
                    [
                        (ticker, format_percentage(weight))
                        for ticker, weight in weights.items()
                    ],
                )
                return weights
            print_warning(
                f"La suma actual es {total:.6%}, no 100 %. "
                "Vuelve a introducir las ponderaciones."
            )

        if len(weights) == len(tickers) and np.isclose(
            sum(weights.values()), 1.0, atol=1e-6
        ):
            return weights


def collect_dates() -> tuple[str, str]:
    show_module_banner(
        "PERIODO HISTÓRICO",
        "Selecciona el intervalo de precios para el análisis.",
    )

    today = date.today()
    default_end = today.isoformat()
    default_start = (today - timedelta(days=365 * 5)).isoformat()

    while True:
        start = ask_date("Fecha inicial", default_start)
        end = ask_date("Fecha final", default_end)

        if start >= end:
            print("La fecha inicial debe ser anterior a la final.")
            continue

        return start, end


# ---------------------------------------------------------------------
# 6. Download, preprocess and build financial models
# ---------------------------------------------------------------------

def download_data(
    provider,
    provider_name: str,
    tickers: list[str],
    start: str,
    end: str,
) -> pd.DataFrame:
    print_header("DESCARGA Y PREPROCESAMIENTO")

    print(f"Proveedor: {provider_name}")
    print(f"Activos: {', '.join(tickers)}")
    print(
        f"Periodo: {format_date(start)} a {format_date(end)}"
    )

    pipeline = DataPipeline(provider)
    with show_progress() as progress:
        task = progress.add_task("Descargando y procesando datos...", total=1)
        data = pipeline.run(tickers=tickers, start=start, end=end)
        progress.update(task, completed=1)

    if data.empty:
        raise ValueError("La descarga no ha producido datos.")

    available = set(data["ticker"].unique())
    missing = sorted(set(tickers) - available)

    if missing:
        raise ValueError(
            "No se han recibido datos para: " + ", ".join(missing)
        )

    print_success(f"Registros válidos: {len(data):,}")
    print_success(f"Activos recibidos: {len(available)}")
    print_success("Preprocesamiento completado.")

    return data


def build_portfolio(
    data: pd.DataFrame,
    weights: dict[str, float],
) -> Portfolio:
    portfolio = Portfolio()

    for ticker, weight in weights.items():
        asset_data = (
            data[data["ticker"] == ticker]
            .sort_values("date")
            .copy()
        )

        prices = pd.Series(
            asset_data["close"].to_numpy(dtype=float),
            index=pd.DatetimeIndex(
                pd.to_datetime(asset_data["date"])
            ),
            name=ticker,
        )

        price_series = PriceSeries(
            ticker=ticker,
            prices=prices,
        )

        portfolio.add_asset(price_series, weight)

    portfolio.validate_weights()
    return portfolio


# ---------------------------------------------------------------------
# 6. Historical analysis
# ---------------------------------------------------------------------

def show_asset_statistics(portfolio: Portfolio) -> dict[str, dict]:
    print_header("ANÁLISIS INDIVIDUAL DE ACTIVOS")
    statistics = {}
    rows = []
    for ticker, asset in portfolio.assets.items():
        returns = asset.returns()
        cumulative_return = float((1 + returns).prod() - 1)
        maximum_drawdown = asset.maximum_drawdown()
        statistics[ticker] = {
            "observations": len(asset.prices),
            "mean": asset.mean,
            "volatility": asset.std,
            "cumulative_return": cumulative_return,
            "maximum_drawdown": maximum_drawdown,
        }
        rows.append((
            ticker,
            f"{len(asset.prices):,}",
            format_number(asset.mean),
            format_number(asset.std),
            format_percentage(cumulative_return),
            format_percentage(maximum_drawdown),
        ))
    print_table(
        "Estadísticas históricas por activo",
        ["Activo", "Observaciones", "Precio medio", "Desv. estándar",
         "Rentabilidad total", "Máx. drawdown"],
        rows,
    )
    return statistics


def show_portfolio_statistics(portfolio: Portfolio) -> dict:
    print_header("ANÁLISIS DE CARTERA")
    annual_return = portfolio.annualized_return()
    annual_volatility = portfolio.volatility()
    returns = portfolio.returns()
    cumulative_return = float((1 + returns).prod() - 1)
    print_table(
        "Indicadores de la cartera",
        ["Indicador", "Resultado"],
        [
            ("Rentabilidad acumulada", format_percentage(cumulative_return)),
            ("Rentabilidad anualizada", format_percentage(annual_return)),
            ("Volatilidad anualizada", format_percentage(annual_volatility)),
            ("Observaciones", f"{len(returns):,}"),
        ],
    )
    return {
        "annual_return": annual_return,
        "annual_volatility": annual_volatility,
        "cumulative_return": cumulative_return,
        "observations": len(returns),
    }



# ---------------------------------------------------------------------
# 7. Reports and historical visualizations
# ---------------------------------------------------------------------

def save_historical_outputs(
    portfolio: Portfolio,
    data: pd.DataFrame,
    output_dir: Path,
) -> str:
    print_header("INFORMES Y VISUALIZACIONES")

    report = portfolio.report()
    report_path = output_dir / "portfolio_report.md"
    report_path.write_text(report, encoding="utf-8")

    data.to_csv(output_dir / "historical_data.csv", index=False)

    figures = portfolio.plots_report(show=False)

    for name, figure in figures.items():
        figure.savefig(
            output_dir / f"{name}.png",
            dpi=160,
            bbox_inches="tight",
        )
        plt.close(figure)

    print_success("Informe Markdown guardado.")
    print_success("Datos históricos exportados a CSV.")
    print_success(f"Gráficas guardadas: {len(figures)}")

    return report


# ---------------------------------------------------------------------
# 8. Monte Carlo simulation
# ---------------------------------------------------------------------

def run_monte_carlo(
    portfolio: Portfolio,
    output_dir: Path,
) -> dict | None:
    print_header("SIMULACIÓN MONTE CARLO")

    if not ask_yes_no("¿Deseas ejecutar la simulación?", True):
        print("Simulación omitida.")
        return None

    initial_value = ask_float(
        "Capital inicial USD (¿Cuánto quieres invertir?)",
        100_000.0,
        minimum=0.01,
    )
    days = ask_integer(
        "Horizonte en días de negociación "
        "(¿Durante cuántos días quieres proyectar?)",
        252,
    )
    simulations = ask_integer(
        "Número de simulaciones "
        "(¿Cuántos escenarios quieres calcular?)",
        1000,
        maximum=100_000,
    )

    seed = ask_integer(
        "Semilla aleatoria (¿Qué número permite repetir el mismo experimento?)",
        default=42,
        minimum=0,
    )

    simulator = portfolio.monte_carlo(
        initial_value=initial_value,
        days=days,
        simulations=simulations,
        seed=seed,
    )

    trajectories = simulator.simulate()
    final_values = simulator.final_values()

    var_95 = simulator.value_at_risk(0.95)
    cvar_95 = simulator.conditional_value_at_risk(0.95)

    probability_loss = float(
        (final_values < initial_value).mean()
    )

    print_table(
        "Resultados de la simulación Monte Carlo",
        ["Indicador", "Resultado"],
        [
            ("Capital inicial", format_currency(initial_value)),
            ("Valor final mediano", format_currency(final_values.median())),
            ("Percentil 5", format_currency(final_values.quantile(0.05))),
            ("Percentil 95", format_currency(final_values.quantile(0.95))),
            ("VaR 95 % (pérdida)", format_currency(var_95)),
            ("CVaR 95 % (pérdida media)", format_currency(cvar_95)),
            ("Probabilidad simulada de pérdida", format_percentage(probability_loss)),
        ],
    )

    trajectories.to_csv(
        output_dir / "monte_carlo_trajectories.csv",
        index=False,
    )

    final_values.to_csv(
        output_dir / "monte_carlo_final_values.csv",
        header=["final_value"],
    )

    # Save a readable sample of simulated trajectories.
    figure, axes = plt.subplots(1, 2, figsize=(13, 5))

    sample_size = min(30, trajectories.shape[1])

    trajectories.iloc[:, :sample_size].plot(
        ax=axes[0],
        legend=False,
        alpha=0.35,
    )
    axes[0].set_title("Trayectorias Monte Carlo")
    axes[0].set_xlabel("Día de simulación")
    axes[0].set_ylabel("Valor de la cartera (USD)")
    axes[0].grid(alpha=0.25)

    axes[1].hist(final_values, bins=40)
    axes[1].axvline(
        initial_value,
        linestyle="--",
        label="Capital inicial (USD)",
    )
    axes[1].set_title("Distribución de valores finales")
    axes[1].set_xlabel("Valor final (USD)")
    axes[1].set_ylabel("Frecuencia")
    axes[1].legend()
    axes[1].grid(alpha=0.25)

    figure.tight_layout()
    figure.savefig(
        output_dir / "monte_carlo_analysis.png",
        dpi=160,
        bbox_inches="tight",
    )
    plt.close(figure)

    return {
        "initial_value": initial_value,
        "days": days,
        "simulations": simulations,
        "median": float(final_values.median()),
        "percentile_5": float(final_values.quantile(0.05)),
        "percentile_95": float(final_values.quantile(0.95)),
        "var_95": var_95,
        "cvar_95": cvar_95,
        "probability_loss": probability_loss,
    }


# ---------------------------------------------------------------------
# 10. Compare Yahoo Finance and Twelve Data
# ---------------------------------------------------------------------

def compare_sources(
    primary_name: str,
    primary_data: pd.DataFrame,
    tickers: list[str],
    start: str,
    end: str,
    output_dir: Path,
) -> tuple[str, pd.DataFrame | None]:
    print_header("COMPARACIÓN ENTRE PROVEEDORES")

    if primary_name == "Yahoo Finance":
        secondary_name = "Twelve Data"

        if not os.getenv("TWELVE_DATA_API_KEY"):
            message = (
                "No se pudo realizar la comparación: falta "
                "TWELVE_DATA_API_KEY para consultar Twelve Data."
            )
            print(message)
            return message, None

        secondary_provider = TwelveDataProvider()

    else:
        secondary_name = "Yahoo Finance"
        secondary_provider = YahooFinanceProvider()

    print(f"Fuente principal: {primary_name}")
    print(f"Fuente de contraste: {secondary_name}")

    try:
        secondary_data = DataPipeline(
            secondary_provider
        ).run(
            tickers=tickers,
            start=start,
            end=end,
        )
    except Exception as error:
        message = (
            f"No se pudo consultar {secondary_name}: "
            f"{type(error).__name__}: {error}"
        )
        print(message)
        return message, None

    comparison_rows = []

    for ticker in tickers:
        first = primary_data[
            primary_data["ticker"] == ticker
        ][["date", "close"]].copy()

        second = secondary_data[
            secondary_data["ticker"] == ticker
        ][["date", "close"]].copy()

        first["date"] = pd.to_datetime(first["date"])
        second["date"] = pd.to_datetime(second["date"])

        merged = first.merge(
            second,
            on="date",
            how="inner",
            suffixes=("_primary", "_secondary"),
        )

        if merged.empty:
            continue

        merged["ticker"] = ticker
        merged["difference"] = (
            merged["close_primary"] - merged["close_secondary"]
        )
        merged["difference_pct"] = (
            merged["difference"] / merged["close_secondary"] * 100
        )

        comparison_rows.append(merged)

    if not comparison_rows:
        message = (
            "No existen fechas coincidentes suficientes para comparar "
            "los proveedores."
        )
        print_warning(message)
        return message, None

    comparison = pd.concat(
        comparison_rows,
        ignore_index=True,
    )

    comparison.to_csv(
        output_dir / "provider_comparison.csv",
        index=False,
    )

    lines = [
        f"Comparación: {primary_name} frente a {secondary_name}",
        "",
        f"Fechas coincidentes: {len(comparison):,}",
        "",
    ]

    for ticker, group in comparison.groupby("ticker"):
        mean_difference = group["difference_pct"].abs().mean()
        max_difference = group["difference_pct"].abs().max()

        mean_difference_formatted = format_change(
            mean_difference / 100
        )
        max_difference_formatted = format_change(
            max_difference / 100
        )

        lines.extend([
            f"{ticker}:",
            f"- Observaciones coincidentes: {len(group)}",
            f"- Diferencia porcentual absoluta media: {mean_difference_formatted}",
            f"- Diferencia porcentual absoluta máxima: {max_difference_formatted}",
            "",
        ])

        print_table(
            f"Comparación de {ticker}",
            ["Indicador", "Resultado"],
            [
                ("Observaciones coincidentes", f"{len(group):,}"),
                ("Diferencia absoluta media", mean_difference_formatted),
                ("Diferencia absoluta máxima", max_difference_formatted),
            ],
        )

    lines.extend([
        "Advertencia metodológica:",
        "Los proveedores pueden aplicar criterios diferentes de ajuste "
        "de precios. Las diferencias observadas no implican necesariamente "
        "un error de datos. Deben interpretarse teniendo en cuenta la "
        "metodología de cada fuente.",
    ])

    message = "\n".join(lines)
    print_warning(
        "Los precios pueden utilizar criterios de ajuste distintos."
    )
    print_success("Comparación entre proveedores completada.")

    return message, comparison


# ---------------------------------------------------------------------
# 12. Automated quality and integrity test summary
# ---------------------------------------------------------------------

def run_quality_checks() -> dict:
    print_header("CALIDAD E INTEGRIDAD DEL SISTEMA")

    print_info("Ejecutando la suite automatizada de pruebas...")

    try:
        with show_progress() as progress:
            task = progress.add_task("Ejecutando pytest...", total=1)
            result = subprocess.run(
                [sys.executable, "-m", "pytest", "-q"],
                cwd=PROJECT_ROOT,
                capture_output=True,
                text=True,
                timeout=300,
                check=False,
            )
            progress.update(task, completed=1)
    except subprocess.TimeoutExpired:
        return {
            "status": "No verificado",
            "message": "La ejecución superó el límite de 300 segundos.",
            "passed": 0,
            "issues": 0,
            "failed": 0,
            "total": 0,
        }
    except OSError as error:
        return {
            "status": "No verificado",
            "message": f"No se pudo ejecutar pytest: {error}",
            "passed": 0,
            "issues": 0,
            "failed": 0,
            "total": 0,
        }

    output = result.stdout + "\n" + result.stderr

    def extract_count(pattern: str) -> int:
        match = re.search(pattern, output)
        return int(match.group(1)) if match else 0

    passed = extract_count(r"(\d+)\s+passed")
    failed = extract_count(r"(\d+)\s+failed")
    errors = extract_count(r"(\d+)\s+errors?")
    warnings = extract_count(r"(\d+)\s+warnings?")
    skipped = extract_count(r"(\d+)\s+skipped")

    issues = errors + warnings
    total = passed + failed + errors + skipped

    if failed > 0:
        status = "Revisión necesaria"
        message = "Una o más pruebas no superaron la validación."
    elif issues > 0:
        status = "Advertencia"
        message = "Se detectaron errores o advertencias que conviene revisar."
    elif passed > 0 and result.returncode == 0:
        status = "Correcto"
        message = "Todas las pruebas ejecutadas fueron superadas."
    else:
        status = "No verificado"
        message = "No fue posible confirmar que la suite se superó correctamente."

    return {
        "status": status,
        "message": message,
        "passed": passed,
        "issues": issues,
        "failed": failed,
        "skipped": skipped,
        "total": total,
        "return_code": result.returncode,
    }


def show_quality_summary(quality: dict) -> None:
    print_quality_status(
        status=quality["status"],
        passed=quality["passed"],
        issues=quality["issues"],
        failed=quality["failed"],
        skipped=quality.get("skipped", 0),
        total=quality["total"],
    )
    if quality.get("message"):
        if quality["status"] == "Correcto":
            print_success(quality["message"])
        else:
            print_warning(quality["message"])



# ---------------------------------------------------------------------
# 11. Executive summary for decision support
# ---------------------------------------------------------------------

def generate_executive_summary(
    portfolio: Portfolio,
    asset_statistics: dict,
    portfolio_statistics: dict,
    monte_carlo: dict | None,
    comparison_message: str | None,
    quality: dict | None,
) -> str:
    lines = [
        "# Resumen ejecutivo — Análisis de cartera",
        "",
        "## Composición",
        "",
    ]

    for ticker, weight in portfolio.weights.items():
        lines.append(f"- {ticker}: {weight:.2%}")

    lines.extend([
        "",
        "## Hallazgos principales",
        "",
        f"- Rentabilidad acumulada de la cartera: "
        f"{portfolio_statistics['cumulative_return']:.2%}.",
        f"- Rentabilidad anualizada: "
        f"{portfolio_statistics['annual_return']:.2%}.",
        f"- Volatilidad anualizada: "
        f"{portfolio_statistics['annual_volatility']:.2%}.",
    ])

    best_asset = max(
        asset_statistics,
        key=lambda ticker: asset_statistics[ticker]["cumulative_return"],
    )
    worst_asset = min(
        asset_statistics,
        key=lambda ticker: asset_statistics[ticker]["cumulative_return"],
    )

    lines.extend([
        f"- Mejor comportamiento histórico entre los activos: "
        f"{best_asset} ({asset_statistics[best_asset]['cumulative_return']:.2%}).",
        f"- Peor comportamiento histórico entre los activos: "
        f"{worst_asset} ({asset_statistics[worst_asset]['cumulative_return']:.2%}).",
    ])

    largest_weight_ticker = max(
        portfolio.weights,
        key=portfolio.weights.get,
    )
    largest_weight = portfolio.weights[largest_weight_ticker]

    if largest_weight >= 0.50:
        lines.append(
            f"- **Concentración:** {largest_weight_ticker} representa "
            f"{largest_weight:.2%} de la cartera."
        )
    else:
        lines.append(
            "- Ningún activo representa por sí solo el 50 % o más de la cartera."
        )

    returns = pd.concat(
        {
            ticker: asset.returns()
            for ticker, asset in portfolio.assets.items()
        },
        axis=1,
    ).dropna()

    if len(returns.columns) > 1:
        correlation = returns.corr()
        upper = correlation.where(
            np.triu(np.ones(correlation.shape), k=1).astype(bool)
        )
        pairs = upper.stack()

        if not pairs.empty:
            pair = pairs.abs().idxmax()
            value = correlation.loc[pair[0], pair[1]]
            lines.append(
                f"- Correlación más intensa: {pair[0]} / {pair[1]} "
                f"({value:.2f})."
            )

    if monte_carlo:
        lines.extend([
            "",
            "## Escenarios Monte Carlo",
            "",
            f"- Simulaciones: {monte_carlo['simulations']:,}.",
            f"- Horizonte: {monte_carlo['days']} días de negociación.",
            f"- Valor final mediano (USD): {monte_carlo['median']:,.2f}.",
            f"- Percentil 5 (USD): {monte_carlo['percentile_5']:,.2f}.",
            f"- VaR 95 % (USD): {monte_carlo['var_95']:,.2f}.",
            f"- CVaR 95 % (USD): {monte_carlo['cvar_95']:,.2f}.",
            f"- Probabilidad simulada de terminar por debajo del capital "
            f"inicial: {monte_carlo['probability_loss']:.2%}.",
        ])

    if comparison_message:
        lines.extend([
            "",
            "## Comparación de proveedores",
            "",
            comparison_message,
        ])

    if quality:
        lines.extend([
            "",
            "## Calidad e integridad del sistema",
            "",
            f"- Estado: **{quality['status']}**.",
            f"- Pruebas aprobadas: {quality['passed']}.",
            f"- Errores / advertencias: {quality['issues']}.",
            f"- Pruebas fallidas: {quality['failed']}.",
            f"- Casos reportados: {quality['total']}.",
            f"- Diagnóstico: {quality['message']}",
        ])

    lines.extend([
        "",
        "## Consideraciones para la toma de decisiones",
        "",
        "- Los resultados describen el comportamiento histórico del periodo "
        "seleccionado; no garantizan resultados futuros.",
        "- Las simulaciones dependen de los supuestos estadísticos y de las "
        "correlaciones históricas utilizadas.",
        "- Antes de tomar decisiones, conviene revisar la concentración, "
        "la volatilidad, las correlaciones y la calidad de los datos.",
        "- Este análisis es informativo y no constituye asesoramiento financiero.",
        "",
    ])

    return "\n".join(lines)


# ---------------------------------------------------------------------
# 9. Export and final workflow
# ---------------------------------------------------------------------

def main() -> None:
    output_dir = OUTPUT_ROOT / datetime.now().strftime(
        "analysis_%Y%m%d_%H%M%S"
    )
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        # 1–5. Configuration
        provider, provider_name = choose_provider()
        tickers = collect_tickers()
        weights = collect_weights(tickers)
        start, end = collect_dates()

        # 6. Data acquisition and financial models
        data = download_data(
            provider,
            provider_name,
            tickers,
            start,
            end,
        )

        portfolio = build_portfolio(data, weights)

        asset_statistics = show_asset_statistics(portfolio)
        portfolio_statistics = show_portfolio_statistics(portfolio)

        # 7. Reports and historical charts
        save_historical_outputs(portfolio, data, output_dir)

        # 8. Monte Carlo
        monte_carlo_results = run_monte_carlo(
            portfolio,
            output_dir,
        )

        # 10. Provider comparison
        comparison_message = None

        if ask_yes_no(
            "¿Deseas contrastar los datos con el otro proveedor?",
            False,
        ):
            comparison_message, _ = compare_sources(
                provider_name,
                data,
                tickers,
                start,
                end,
                output_dir,
            )

        # 12. Quality and integrity checks
        quality_results = None

        if ask_yes_no(
            "¿Deseas ejecutar las pruebas de calidad e integridad del proyecto?",
            True,
        ):
            quality_results = run_quality_checks()
            show_quality_summary(quality_results)

        # 11. Executive summary
        print_header("RESUMEN EJECUTIVO")

        executive_summary = generate_executive_summary(
            portfolio,
            asset_statistics,
            portfolio_statistics,
            monte_carlo_results,
            comparison_message,
            quality_results,
        )

        console.print(
            Panel(
                executive_summary,
                title="[bold cyan]RESUMEN EJECUTIVO[/bold cyan]",
                border_style="blue",
                padding=(1, 2),
            )
        )

        summary_path = output_dir / "executive_summary.md"
        summary_path.write_text(
            executive_summary,
            encoding="utf-8",
        )

        # Export a compact portfolio returns series.
        portfolio.returns().rename(
            "portfolio_return"
        ).to_csv(output_dir / "portfolio_returns.csv")

        print_header("ANÁLISIS COMPLETADO")
        print_success(f"Resultados guardados en: {output_dir}")
        print_table(
            "Archivos generados",
            ["Archivo"],
            [(path.name,) for path in sorted(output_dir.iterdir())],
        )
        show_goodbye()

    except KeyboardInterrupt:
        print_warning("Operación cancelada por el usuario.")
        show_goodbye()

    except Exception as error:
        print_header("NO SE PUDO COMPLETAR EL ANÁLISIS")
        print_error(f"{type(error).__name__}: {error}")
        print_info(
            "Revisa los parámetros, la conexión de datos y la "
            "configuración del proveedor. Puedes volver a ejecutar "
            "el asistente."
        )


if __name__ == "__main__":
    main()
