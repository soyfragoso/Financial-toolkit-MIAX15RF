
from rich.align import Align
from rich.console import Console
from rich.panel import Panel
from rich.text import Text


console = Console()


LOGO = r"""
█   █ ███  ███  █   █      █   █████
██ ██  █  █   █  █ █      ██   █
█ █ █  █  █████   █        █   ████
█   █  █  █   █  █ █       █       █
█   █ ███ █   █ █   █     ███  ████


█████ ███ █   █  ███  █   █  ███  ███  ███  █
█      █  ██  █ █   █ ██  █ █      █  █   █ █
████   █  █ █ █ █████ █ █ █ █      █  █████ █
█      █  █  ██ █   █ █  ██ █      █  █   █ █
█     ███ █   █ █   █ █   █  ███  ███ █   █ █████


████   ███  █   █ █████ ████  █████  ███   ███  █
█   █ █   █ █   █ █     █   █   █   █   █ █   █ █
████  █   █ █ █ █ ████  ████    █   █   █ █   █ █
█     █   █ ██ ██ █     █  █    █   █   █ █   █ █
█      ███  █   █ █████ █   █   █    ███   ███  █████
"""

SUBTITLE = "MIAX 15 FINANCIAL POWERTOOL"
TAGLINE = "Portfolio Analytics  |  Risk Management  |  Monte Carlo"


def show_welcome() -> None:
    """Presenta la identidad visual del proyecto."""
    content = Text(LOGO, style="bold bright_cyan")
    content.append(f"\n{SUBTITLE}\n", style="bold white")
    content.append(TAGLINE, style="dim cyan")

    console.print()
    console.print(
        Panel(
            content,
            border_style="bright_blue",
            padding=(1, 2),
        )
    )


def show_module_banner(
    module_name: str,
    description: str = "",
) -> None:
    """Muestra un banner para cada módulo del asistente."""
    content = Text(module_name, style="bold bright_cyan")

    if description:
        content.append(f"\n{description}", style="dim white")

    console.print()
    console.print(
        Panel(
            Align.center(content),
            border_style="blue",
            padding=(1, 3),
        )
    )


def show_goodbye() -> None:
    """Muestra el mensaje de cierre."""
    console.print()
    console.print(
        Panel(
            Align.center(
                Text(
                    "Gracias por utilizar MIAX 15 Financial Powertool\n"
                    "Análisis cuantitativo para decisiones mejor informadas.",
                    style="bold cyan",
                    justify="center",
                )
            ),
            border_style="bright_blue",
            padding=(1, 2),
        )
    )
