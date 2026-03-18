"""chimera-runtime stop — Halt the running agent."""

from __future__ import annotations

import json
from pathlib import Path

import click

from .main import pass_ctx, CLIContext
from .display import console, err_console
from rich.panel import Panel
from rich.text import Text


@click.command("stop")
@click.option("--force", "-f", is_flag=True, help="Force immediate halt")
@pass_ctx
def stop_cmd(ctx: CLIContext, force: bool):
    """🛑 Stop the chimera-runtime.

    Sends a halt signal to any running agent instance.
    With --force: immediate stop, logs INTERRUPTED for pending decisions.
    """
    halt_path = Path(ctx.config_dir) / ".halt"
    signal = {"action": "HALT", "force": force}

    try:
        halt_path.parent.mkdir(parents=True, exist_ok=True)
        halt_path.write_text(json.dumps(signal), encoding="utf-8")
    except OSError as e:
        err_console.print(f"[bold red]❌ Cannot write halt signal:[/bold red] {e}")
        raise SystemExit(1)

    if force:
        content = Text()
        content.append("FORCE HALT", style="bold red")
        content.append(" signal sent\n", style="")
        content.append("Pending decisions will be logged as ", style="dim")
        content.append("INTERRUPTED", style="bold yellow")
    else:
        content = Text()
        content.append("Graceful HALT", style="bold yellow")
        content.append(" signal sent\n", style="")
        content.append("Agent will stop after current decision", style="dim")

    console.print(Panel(
        content,
        title="🛑 [bold]Agent Stop[/bold]",
        border_style="red" if force else "yellow",
        padding=(1, 2),
    ))
    console.print(f"  [dim]Signal file: {halt_path}[/dim]")
    console.print(f"  [dim]To restart:  [bold]chimera-runtime run[/bold][/dim]\n")
