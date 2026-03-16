"""chimera-compliance explain — Art. 86 Right to Explanation."""

from __future__ import annotations

from pathlib import Path

import click

from .main import pass_ctx, CLIContext
from .display import console, err_console, RESULT_STYLES
from rich.panel import Panel
from rich.text import Text


@click.command("explain")
@click.option("--id", "decision_id", required=True, help="Decision ID to explain")
@click.option("--output", "-o", type=str, default=None, help="Output HTML file path")
@click.option("--audit-dir", type=str, default=None, help="Override audit directory")
@click.option("--open", "open_browser", is_flag=True, help="Open in browser after generating")
@pass_ctx
def explain_cmd(ctx, decision_id, output, audit_dir, open_browser):
    """📖 Generate Art. 86 explanation report for a decision.

    Produces a self-contained HTML report explaining why a specific
    decision was made, including full reasoning trace and compliance info.

    \b
    Examples:
        chimera-compliance explain --id dec_abc123
        chimera-compliance explain --id dec_abc123 --output ./reports/explanation.html --open
    """
    from ..config import load_config
    from ..audit import load_record, generate_html, AuditStorageError

    if not audit_dir:
        try:
            config = load_config(ctx.config_path)
            audit_dir = config.audit.output_dir
        except Exception:
            audit_dir = "./audit_logs"

    try:
        with console.status("[cyan]Loading audit record...[/cyan]", spinner="dots"):
            record = load_record(decision_id, audit_dir=audit_dir)
    except AuditStorageError as e:
        err_console.print(f"[bold red]❌ {e}[/bold red]")
        raise SystemExit(1)

    with console.status("[cyan]Generating HTML report...[/cyan]", spinner="dots"):
        html_content = generate_html(record)

    if not output:
        output = str(Path(audit_dir) / f"{decision_id}_explanation.html")

    out_path = Path(output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html_content, encoding="utf-8")

    # Display summary
    d = record.decision
    icon, style, border_color = RESULT_STYLES.get(d.result, ("❓", "dim", "dim"))

    info = Text()
    info.append("Decision:  ", style="dim")
    info.append(f"{decision_id}\n", style="cyan")
    info.append("Result:    ", style="dim")
    info.append(f"{icon} {d.result}\n", style=style)
    info.append("Action:    ", style="dim")
    info.append(f"{d.action_taken}\n", style="bold")
    info.append("Output:    ", style="dim")
    info.append(str(out_path), style="cyan underline")

    console.print(Panel(
        info,
        title="📖 [bold]Art. 86 Explanation Report[/bold]",
        border_style="blue",
        padding=(1, 2),
    ))

    if open_browser:
        try:
            import webbrowser
            webbrowser.open(f"file://{out_path.resolve()}")
            console.print("  [dim]🌐 Opened in browser[/dim]")
        except Exception:
            console.print("  [yellow]⚠️  Could not open browser[/yellow]")

    console.print()
