
from __future__ import annotations

from typing import Iterable, Sequence

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
)
from rich.prompt import Confirm, FloatPrompt, IntPrompt, Prompt
from rich.table import Table
from rich.text import Text


console = Console()


def print_banner(title: str, subtitle: str | None = None) -> None:
    """Muestra un encabezado visual uniforme."""
    content = Text(title, style="bold cyan", justify="center")

    if subtitle:
        content.append(f"\n{subtitle}", style="dim white")

    console.print(
        Panel(
            content,
            border_style="bright_blue",
            box=box.DOUBLE,
            padding=(1, 3),
        )
    )


def print_section(title: str) -> None:
    """Muestra el inicio de una sección."""
    console.print()
    console.rule(f"[bold cyan]{title}[/bold cyan]", style="blue")


def print_success(message: str) -> None:
    console.print(f"[bold green]✓[/bold green] {message}")


def print_warning(message: str) -> None:
    console.print(f"[bold yellow]![/bold yellow] {message}")


def print_error(message: str) -> None:
    console.print(f"[bold red]✗[/bold red] {message}")


def print_info(message: str) -> None:
    console.print(f"[cyan]ℹ[/cyan] {message}")


def print_table(
    title: str,
    columns: Sequence[str],
    rows: Iterable[Sequence[object]],
) -> None:
    """Muestra información tabular con Rich."""
    table = Table(
        title=title,
        box=box.ROUNDED,
        header_style="bold cyan",
        border_style="blue",
        show_lines=True,
    )

    for column in columns:
        table.add_column(str(column), justify="center")

    for row in rows:
        table.add_row(*(str(value) for value in row))

    console.print(table)


def ask_choice(
    question: str,
    choices: Sequence[str],
    default: str | None = None,
) -> str:
    """Solicita una opción y valida la respuesta."""
    return Prompt.ask(
        question,
        choices=list(choices),
        default=default,
        console=console,
    )


def ask_text(
    question: str,
    default: str | None = None,
) -> str:
    return Prompt.ask(
        question,
        default=default,
        console=console,
    )


def ask_yes_no(
    question: str,
    default: bool = True,
) -> bool:
    return Confirm.ask(
        question,
        default=default,
        console=console,
    )


def ask_integer(
    question: str,
    default: int | None = None,
    minimum: int | None = None,
    maximum: int | None = None,
) -> int:
    return IntPrompt.ask(
        question,
        default=default,
        show_default=default is not None,
        console=console,
        **_numeric_bounds(minimum, maximum),
    )


def ask_float(
    question: str,
    default: float | None = None,
    minimum: float | None = None,
    maximum: float | None = None,
) -> float:
    return FloatPrompt.ask(
        question,
        default=default,
        show_default=default is not None,
        console=console,
        **_numeric_bounds(minimum, maximum),
    )


def _numeric_bounds(
    minimum: float | int | None,
    maximum: float | int | None,
) -> dict[str, float | int]:
    bounds = {}

    if minimum is not None:
        bounds["min_value"] = minimum

    if maximum is not None:
        bounds["max_value"] = maximum

    return bounds


def show_progress() -> Progress:
    """Devuelve un contexto de progreso para operaciones largas."""
    return Progress(
        SpinnerColumn(),
        TextColumn("[bold cyan]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    )


def print_quality_status(
    status: str,
    passed: int,
    issues: int,
    failed: int,
    skipped: int,
    total: int,
) -> None:
    """Muestra el resultado de las pruebas de calidad."""
    styles = {
        "Correcto": "bold green",
        "Advertencia": "bold yellow",
        "Revisión necesaria": "bold red",
        "No verificado": "bold white",
    }

    style = styles.get(status, "bold white")

    table = Table(
        title="Control de calidad e integridad",
        box=box.ROUNDED,
        border_style="blue",
        header_style="bold cyan",
    )

    table.add_column("Indicador", style="white")
    table.add_column("Resultado", justify="right")

    table.add_row("Estado", f"[{style}]{status}[/{style}]")
    table.add_row("Pruebas superadas", f"[green]{passed}[/green]")
    table.add_row("Errores / advertencias", f"[yellow]{issues}[/yellow]")
    table.add_row("Pruebas fallidas", f"[red]{failed}[/red]")
    table.add_row("Pruebas omitidas", str(skipped))
    table.add_row("Total de casos", str(total))

    percentage = (passed / total * 100) if total else 0.0
    table.add_row("Porcentaje superado", f"{percentage:.1f}%")

    console.print(table)


def wait_for_enter(
    message: str = "Presiona ENTER para continuar...",
) -> None:
    console.input(f"\n[dim]{message}[/dim]")
