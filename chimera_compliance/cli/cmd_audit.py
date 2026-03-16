"""chimera-compliance audit — Query and manage audit records."""

from __future__ import annotations

import click

from .main import pass_ctx, CLIContext
from .display import (
    console, err_console,
    display_audit_table, display_audit_detail,
    display_audit_stats, display_violations_table,
)


@click.command("audit")
@click.option("--last", "-n", type=int, default=None, help="Show last N decisions")
@click.option("--result", "-r", type=click.Choice(["ALLOWED", "BLOCKED", "HUMAN_OVERRIDE", "INTERRUPTED"]),
              default=None, help="Filter by result")
@click.option("--after", type=str, default=None, help="After datetime (ISO format)")
@click.option("--before", type=str, default=None, help="Before datetime (ISO format)")
@click.option("--id", "decision_id", type=str, default=None, help="Show specific decision by ID")
@click.option("--stats", is_flag=True, help="Show aggregate statistics")
@click.option("--violations", is_flag=True, help="Show top constraint violations")
@click.option("--export", "export_path", type=str, default=None, help="Export to file")
@click.option("--format", "export_format", type=click.Choice(["json", "compact", "stats"]),
              default="json", help="Export format")
@click.option("--audit-dir", type=str, default=None, help="Override audit directory")
@pass_ctx
def audit_cmd(ctx, last, result, after, before, decision_id, stats,
              violations, export_path, export_format, audit_dir):
    """📋 Query and manage audit records.

    \b
    Examples:
        chimera-compliance audit --last 10
        chimera-compliance audit --result BLOCKED --after 2026-01-01T00:00:00Z
        chimera-compliance audit --stats
        chimera-compliance audit --id dec_abc123
        chimera-compliance audit --export ./report.json --format compact
    """
    from ..config import load_config
    from ..audit import AuditQuery, load_record, AuditStorageError

    if not audit_dir:
        try:
            config = load_config(ctx.config_path)
            audit_dir = config.audit.output_dir
        except Exception:
            audit_dir = "./audit_logs"

    # Single record lookup
    if decision_id:
        try:
            record = load_record(decision_id, audit_dir=audit_dir)
            display_audit_detail(record)
        except AuditStorageError as e:
            err_console.print(f"[bold red]❌ {e}[/bold red]")
            raise SystemExit(1)
        return

    query = AuditQuery(audit_dir)

    if stats:
        s = query.stats()
        display_audit_stats(s)
        return

    if violations:
        top = query.top_violations(n=20)
        display_violations_table(top)
        return

    if export_path:
        try:
            with console.status("[cyan]Exporting...[/cyan]", spinner="dots"):
                path = query.export(export_path, format=export_format)
            console.print(f"[bold green]✅ Exported to[/bold green] [cyan]{path}[/cyan]")
        except Exception as e:
            err_console.print(f"[bold red]❌ Export failed:[/bold red] {e}")
            raise SystemExit(1)
        return

    records = query.filter(result=result, after=after, before=before)
    if last is not None:
        records = records[:last]

    if not records:
        console.print("[dim]ℹ️  No audit records found matching criteria.[/dim]")
        return

    display_audit_table(records)
