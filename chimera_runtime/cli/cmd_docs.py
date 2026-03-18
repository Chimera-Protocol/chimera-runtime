"""chimera-runtime docs — Annex IV documentation management."""

from __future__ import annotations

import click

from .main import pass_ctx, CLIContext
from .display import console, err_console, display_docs_status
from rich.panel import Panel
from rich.text import Text


@click.group("docs")
def docs_cmd():
    """📄 Manage EU AI Act Annex IV documentation."""
    pass


@docs_cmd.command("generate")
@click.option("--output", "-o", type=str, default="./docs/annex_iv_technical_documentation.md",
              help="Output file path", show_default=True)
@click.option("--audit-dir", type=str, default=None, help="Override audit directory")
@click.option("--policy", "-p", type=str, default=None, help="Override policy file")
@click.option("--period", type=int, default=90, help="Stats period in days", show_default=True)
@pass_ctx
def docs_generate(ctx, output, audit_dir, policy, period):
    """Generate Annex IV technical documentation.

    Auto-fills 14 of 19 sections from config, audit, and policy data.
    """
    from ..config import load_config
    from ..docs import AnnexIVGenerator, DocsGeneratorError
    from ..models import AgentConfig

    try:
        config = load_config(ctx.config_path)
    except Exception:
        config = AgentConfig()
        console.print("[yellow]⚠️  No config found, using defaults[/yellow]")

    if not audit_dir:
        audit_dir = config.audit.output_dir

    gen = AnnexIVGenerator(
        config=config, audit_dir=audit_dir,
        policy_path=policy or config.policy.file,
        stats_period_days=period,
    )

    try:
        with console.status("[cyan]Generating Annex IV documentation...[/cyan]", spinner="dots"):
            path = gen.generate(output_path=output)
            status = gen.status()

        info = Text()
        info.append("Output:   ", style="dim")
        info.append(f"{path}\n", style="cyan underline")
        info.append("Coverage: ", style="dim")
        info.append(f"{status['filled']}/19", style="bold green")
        info.append(" sections auto-filled\n", style="")
        info.append("Manual:   ", style="dim")
        info.append(f"{status['manual_required']}", style="yellow")
        info.append(" sections require manual input", style="")

        console.print(Panel(
            info,
            title="📄 [bold]Annex IV Documentation Generated[/bold]",
            border_style="green",
            padding=(1, 2),
        ))

        if status["pending_sections"]:
            console.print("\n  [yellow]⏳ Pending (need audit data):[/yellow]")
            for s in status["pending_sections"]:
                console.print(f"     [yellow]Section {s['section']}:[/yellow] [dim]{s['title']}[/dim]")

        console.print("\n  [dim]✏️  Manual sections to complete:[/dim]")
        for s in status["manual_sections"]:
            console.print(f"     [red]Section {s['section']}:[/red] [dim]{s['title']}[/dim]")
        console.print()

    except DocsGeneratorError as e:
        err_console.print(f"[bold red]❌ Generation failed:[/bold red] {e}")
        raise SystemExit(1)


@docs_cmd.command("status")
@click.option("--audit-dir", type=str, default=None, help="Override audit directory")
@pass_ctx
def docs_status(ctx, audit_dir):
    """Check documentation coverage status."""
    from ..config import load_config
    from ..docs import AnnexIVGenerator
    from ..models import AgentConfig

    try:
        config = load_config(ctx.config_path)
    except Exception:
        config = AgentConfig()

    if not audit_dir:
        audit_dir = config.audit.output_dir

    gen = AnnexIVGenerator(config=config, audit_dir=audit_dir)
    status = gen.status()
    display_docs_status(status)


@docs_cmd.command("refresh")
@click.option("--output", "-o", type=str, default=None, help="Override output path")
@click.option("--audit-dir", type=str, default=None, help="Override audit directory")
@pass_ctx
def docs_refresh(ctx, output, audit_dir):
    """Re-generate documentation with latest data."""
    from ..config import load_config
    from ..docs import AnnexIVGenerator, DocsGeneratorError
    from ..models import AgentConfig

    try:
        config = load_config(ctx.config_path)
    except Exception:
        config = AgentConfig()

    if not audit_dir:
        audit_dir = config.audit.output_dir

    gen = AnnexIVGenerator(config=config, audit_dir=audit_dir)

    try:
        with console.status("[cyan]Refreshing documentation...[/cyan]", spinner="dots"):
            path = gen.refresh(output_path=output)
        console.print(f"[bold green]✅ Documentation refreshed:[/bold green] [cyan]{path}[/cyan]")
    except DocsGeneratorError as e:
        err_console.print(f"[bold red]❌ Refresh failed:[/bold red] {e}")
        raise SystemExit(1)
