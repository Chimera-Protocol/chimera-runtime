"""
chimera-runtime CLI — Rich Display Components

Shared console, themes, and reusable display functions
for a beautiful terminal experience.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, Tuple

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.tree import Tree
from rich.syntax import Syntax
from rich.columns import Columns
from rich.markdown import Markdown
from rich import box


# ============================================================================
# GLOBAL CONSOLE
# ============================================================================

console = Console()
err_console = Console(stderr=True)


# ============================================================================
# COLOR THEME
# ============================================================================

class Theme:
    # Results
    ALLOWED = "bold green"
    BLOCKED = "bold red"
    OVERRIDE = "bold yellow"
    INTERRUPTED = "bold dim"

    # UI
    ACCENT = "cyan"
    MUTED = "dim"
    EMPHASIS = "bold white"
    SUCCESS = "bold green"
    ERROR = "bold red"
    WARNING = "bold yellow"
    INFO = "bold blue"

    # Domain-specific
    POLICY = "magenta"
    AUDIT = "blue"
    AGENT = "cyan"
    CONSTRAINT = "yellow"


RESULT_STYLES = {
    "ALLOWED": ("✅", Theme.ALLOWED, "green"),
    "BLOCKED": ("🚫", Theme.BLOCKED, "red"),
    "HUMAN_OVERRIDE": ("🧑", Theme.OVERRIDE, "yellow"),
    "INTERRUPTED": ("⏸️ ", Theme.INTERRUPTED, "dim"),
}


# ============================================================================
# BANNER
# ============================================================================

BANNER = r"""[cyan]
     ██████╗██╗  ██╗██╗███╗   ███╗███████╗██████╗  █████╗
    ██╔════╝██║  ██║██║████╗ ████║██╔════╝██╔══██╗██╔══██╗
    ██║     ███████║██║██╔████╔██║█████╗  ██████╔╝███████║
    ██║     ██╔══██║██║██║╚██╔╝██║██╔══╝  ██╔══██╗██╔══██║
    ╚██████╗██║  ██║██║██║ ╚═╝ ██║███████╗██║  ██║██║  ██║
     ╚═════╝╚═╝  ╚═╝╚═╝╚═╝   ╚═╝╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝[/cyan]
[dim]  Deterministic Runtime for AI Agents[/dim]
"""

BANNER_MINI = "[bold cyan]🛡️  chimera-runtime[/bold cyan] [dim]— Deterministic Runtime for AI Agents[/dim]"


def show_banner(mini: bool = False):
    if mini:
        console.print(BANNER_MINI)
    else:
        console.print(BANNER)


# ============================================================================
# RESULT BADGE
# ============================================================================

def result_badge(result: str) -> Text:
    """Create a styled result badge."""
    icon, style, _ = RESULT_STYLES.get(result, ("❓", "dim", "dim"))
    return Text(f" {icon} {result} ", style=style)


def result_panel(result: str, title: str = "") -> Panel:
    """Create a full panel for a result."""
    icon, style, border_color = RESULT_STYLES.get(result, ("❓", "dim", "dim"))
    content = Text(f"{icon} {result}", style=style, justify="center")
    return Panel(content, border_style=border_color, title=title, expand=False)


# ============================================================================
# DECISION RESULT DISPLAY
# ============================================================================

def display_decision_result(result, elapsed_ms: float, verbose: bool = False):
    """Display a full decision result with rich formatting."""
    icon, style, border_color = RESULT_STYLES.get(result.result, ("❓", "dim", "dim"))

    # Main result panel
    header = Text()
    header.append(f" {icon} ", style=style)
    header.append(result.result, style=style)
    header.append(f"  ", style="dim")
    header.append(f"({elapsed_ms:.0f}ms)", style="dim italic")

    # Info table
    info = Table(show_header=False, box=None, padding=(0, 2))
    info.add_column("Key", style="dim", width=16)
    info.add_column("Value")

    info.add_row("Action", Text(result.action, style="bold"))
    info.add_row("Explanation", Text(result.explanation, style="italic"))

    if result.parameters:
        params_text = Syntax(
            json.dumps(result.parameters, indent=2, ensure_ascii=False),
            "json", theme="monokai", line_numbers=False,
        )
        info.add_row("Parameters", params_text)

    info.add_row("Decision ID", Text(result.decision_id, style="dim cyan"))

    if verbose and result.audit:
        info.add_row("Attempts", str(result.audit.reasoning.total_attempts))
        info.add_row("Candidates", str(result.audit.reasoning.total_candidates))

    panel = Panel(
        info,
        title=header,
        border_style=border_color,
        padding=(1, 2),
    )
    console.print(panel)


# ============================================================================
# POLICY DISPLAY
# ============================================================================

def display_policy_info(pm, title: str = "Policy Verified"):
    """Display policy metadata in a beautiful format."""
    tree = Tree(
        f"[bold green]✅ {title}[/bold green]",
        guide_style="dim",
    )

    meta = tree.add("[bold]📋 Metadata")
    meta.add(f"[dim]Domain:[/dim]      [bold]{pm.domain_name}[/bold]")
    meta.add(f"[dim]Hash:[/dim]        [cyan]{pm.hash}[/cyan]")
    meta.add(f"[dim]Constraints:[/dim] [yellow]{pm.constraint_count}[/yellow]")
    meta.add(f"[dim]Variables:[/dim]   [yellow]{len(pm.variable_names)}[/yellow]")

    if pm.constraint_names:
        constraints = tree.add("[bold]⚡ Constraints")
        for name in pm.constraint_names:
            constraints.add(f"[yellow]{name}[/yellow]")

    if pm.variable_names:
        variables = tree.add("[bold]📊 Variables")
        domains = pm.variable_domains
        for name in pm.variable_names:
            domain = domains.get(name, "any")
            variables.add(f"[magenta]{name}[/magenta]: [dim]{domain}[/dim]")

    console.print(tree)
    console.print()


def display_simulation_result(i: int, ctx_input: dict, result, dry_run: bool = False):
    """Display a policy simulation result."""
    icon, style, border_color = RESULT_STYLES.get(result.result, ("❓", "dim", "dim"))

    table = Table(show_header=False, box=None, padding=(0, 1))
    table.add_column("Key", style="dim", width=12)
    table.add_column("Value")

    table.add_row("Input", Syntax(
        json.dumps(ctx_input, ensure_ascii=False),
        "json", theme="monokai", line_numbers=False,
    ))
    table.add_row("Duration", f"{result.duration_ms:.3f}ms")

    if result.violations:
        for v in result.violations:
            table.add_row(
                "Violation",
                Text(f"{v.constraint}: {v.explanation}", style="red"),
            )

    title = Text()
    title.append(f" Case {i} ", style="bold")
    title.append(f" {icon} {result.result} ", style=style)
    if dry_run:
        title.append(" (dry-run) ", style="dim italic")

    console.print(Panel(table, title=title, border_style=border_color, padding=(0, 1)))


# ============================================================================
# AUDIT DISPLAY
# ============================================================================

def display_audit_table(records):
    """Display audit records as a rich table."""
    table = Table(
        title="📋 Audit Records",
        box=box.ROUNDED,
        show_lines=False,
        header_style="bold cyan",
        title_style="bold",
    )

    table.add_column("Decision ID", style="dim cyan", width=26)
    table.add_column("Result", width=14)
    table.add_column("Action", max_width=30)
    table.add_column("Duration", justify="right", width=10)
    table.add_column("Timestamp", style="dim", width=22)

    for r in records:
        icon, style, _ = RESULT_STYLES.get(r.decision.result, ("❓", "dim", "dim"))
        result_text = Text(f"{icon} {r.decision.result}", style=style)
        action = r.decision.action_taken[:29]
        duration = f"{r.performance.total_duration_ms:.1f}ms"
        ts = r.timestamp[:21]

        table.add_row(r.decision_id, result_text, action, duration, ts)

    console.print(table)
    console.print(f"  [dim]Total: {len(records)} records[/dim]\n")


def display_audit_detail(record):
    """Display a single audit record in detail."""
    d = record.decision
    icon, style, border_color = RESULT_STYLES.get(d.result, ("❓", "dim", "dim"))

    info = Table(show_header=False, box=None, padding=(0, 2))
    info.add_column("Key", style="bold dim", width=16)
    info.add_column("Value")

    info.add_row("Decision ID", Text(record.decision_id, style="cyan"))
    info.add_row("Timestamp", record.timestamp)
    info.add_row("Result", Text(f"{icon} {d.result}", style=style))
    info.add_row("Action", Text(d.action_taken, style="bold"))
    info.add_row("Policy", f"{d.policy_file}")
    info.add_row("Policy Hash", Text(d.policy_hash, style="dim"))
    info.add_row("Attempts", str(record.reasoning.total_attempts))
    info.add_row("Candidates", str(record.reasoning.total_candidates))
    info.add_row("Selected", record.reasoning.selected_candidate or "None")
    info.add_row("Duration", f"{record.performance.total_duration_ms:.1f}ms")

    if d.final_parameters:
        info.add_row("Parameters", Syntax(
            json.dumps(d.final_parameters, indent=2, ensure_ascii=False),
            "json", theme="monokai", line_numbers=False,
        ))

    console.print(Panel(
        info,
        title=f"🔍 [bold]Decision Detail[/bold]",
        border_style=border_color,
        padding=(1, 2),
    ))


def display_audit_stats(stats):
    """Display audit statistics with rich formatting."""
    # Main metrics
    grid = Table(box=box.SIMPLE_HEAVY, show_header=True, header_style="bold cyan")
    grid.add_column("Metric", style="bold")
    grid.add_column("Value", justify="right")
    grid.add_column("", width=20)

    # Visual bar for allow/block ratio
    total = stats.total_decisions
    if total > 0:
        bar_width = 16
        allow_width = int(stats.allow_rate * bar_width)
        block_width = bar_width - allow_width
        bar = Text()
        bar.append("█" * allow_width, style="green")
        bar.append("█" * block_width, style="red")
    else:
        bar = Text("—", style="dim")

    grid.add_row("Total Decisions", str(total), bar)
    grid.add_row("✅ Allowed", f"{stats.allowed_count} ({stats.allow_rate:.1%})", "")
    grid.add_row("🚫 Blocked", f"{stats.blocked_count} ({stats.block_rate:.1%})", "")
    grid.add_row("🧑 Human Override", str(stats.human_override_count), "")
    grid.add_row("⏸️  Interrupted", str(stats.interrupted_count), "")
    grid.add_row("", "", "")
    grid.add_row("Avg Duration", f"{stats.avg_duration_ms:.1f}ms", "")
    grid.add_row("Avg Candidates", f"{stats.avg_candidates_per_decision:.1f}", "")
    grid.add_row("Total Violations", str(stats.total_violations), "")

    if stats.period_start:
        grid.add_row("Period", f"{stats.period_start[:10]} → {stats.period_end[:10]}", "")

    console.print(Panel(
        grid,
        title="📊 [bold]Audit Statistics[/bold]",
        border_style="blue",
        padding=(1, 2),
    ))


def display_violations_table(violations: List[Tuple[str, int]]):
    """Display top violations as a rich table."""
    if not violations:
        console.print("[dim]ℹ️  No violations found.[/dim]")
        return

    table = Table(
        title="⚠️  Top Constraint Violations",
        box=box.ROUNDED,
        header_style="bold yellow",
        title_style="bold",
    )
    table.add_column("#", style="dim", width=4, justify="right")
    table.add_column("Constraint", style="yellow")
    table.add_column("Count", justify="right", style="bold")
    table.add_column("", width=20)

    max_count = violations[0][1] if violations else 1
    for i, (name, count) in enumerate(violations, 1):
        bar_width = int((count / max_count) * 16)
        bar = Text("█" * bar_width, style="yellow")
        table.add_row(str(i), name, str(count), bar)

    console.print(table)
    console.print()


# ============================================================================
# STATUS DISPLAY
# ============================================================================

def display_agent_status(agent):
    """Display agent status panel."""
    halted = agent.is_halted
    status_style = "red" if halted else "green"
    status_text = "🛑 HALTED" if halted else "🟢 ACTIVE"

    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Key", style="dim", width=20)
    table.add_column("Value")

    table.add_row("Status", Text(status_text, style=f"bold {status_style}"))
    table.add_row("Decisions Made", str(agent.decision_count))
    table.add_row("Consecutive Blocks", str(agent.consecutive_blocks))

    console.print(Panel(
        table,
        title="📊 [bold]Agent Status[/bold]",
        border_style=status_style,
    ))


# ============================================================================
# DOCS STATUS DISPLAY
# ============================================================================

def display_docs_status(status: dict):
    """Display documentation coverage status."""
    filled = status["filled"]
    total = status["total"]
    pct = filled / total * 100

    # Progress bar
    bar_width = 19
    filled_width = int(filled / total * bar_width)
    bar = Text()
    bar.append("█" * filled_width, style="green")
    bar.append("░" * (bar_width - filled_width), style="dim")
    bar.append(f"  {filled}/{total} ({pct:.0f}%)", style="bold")

    tree = Tree("[bold]📄 Annex IV Documentation Status", guide_style="dim")

    coverage = tree.add(bar)

    data_node = tree.add("[bold]📡 Data Sources")
    audit_icon = "✅" if status["has_audit_data"] else "❌"
    policy_icon = "✅" if status["has_policy_data"] else "❌"
    data_node.add(f"{audit_icon} Audit data")
    data_node.add(f"{policy_icon} Policy data")

    if status["auto_sections"]:
        auto_node = tree.add(f"[bold green]✅ Auto-filled ({len(status['auto_sections'])})")
        for s in status["auto_sections"]:
            auto_node.add(f"[green]Section {s['section']}:[/green] [dim]{s['title']}[/dim]")

    if status["pending_sections"]:
        pending_node = tree.add(f"[bold yellow]⏳ Pending ({len(status['pending_sections'])})")
        for s in status["pending_sections"]:
            pending_node.add(f"[yellow]Section {s['section']}:[/yellow] [dim]{s['title']}[/dim]")

    manual_node = tree.add(f"[bold red]✏️  Manual Required ({len(status['manual_sections'])})")
    for s in status["manual_sections"]:
        manual_node.add(f"[red]Section {s['section']}:[/red] [dim]{s['title']}[/dim]")

    console.print(tree)
    console.print()


# ============================================================================
# INIT DISPLAY
# ============================================================================

def display_init_complete(config_path: str, policy_file: str, steps: List[str]):
    """Display initialization completion."""
    tree = Tree("[bold green]🎉 Project Initialized!", guide_style="dim")

    files_node = tree.add("[bold]📁 Created")
    files_node.add(f"[cyan]{config_path}[/cyan]")
    files_node.add(f"[magenta]{policy_file}[/magenta]")

    next_node = tree.add("[bold]🚀 Next Steps")
    for i, step in enumerate(steps, 1):
        next_node.add(f"[dim]{i}.[/dim] {step}")

    console.print(tree)
    console.print()


# ============================================================================
# POLICY LIST DISPLAY
# ============================================================================

def display_policy_list(policies: List[Dict[str, Any]], policy_dir: str):
    """Display policy files in a rich table."""
    table = Table(
        title=f"📜 Policies in [cyan]{policy_dir}[/cyan]",
        box=box.ROUNDED,
        header_style="bold magenta",
        title_style="bold",
    )

    table.add_column("File", style="cyan")
    table.add_column("Domain", style="bold")
    table.add_column("Constraints", justify="center")
    table.add_column("Variables", justify="center")
    table.add_column("Status")

    for p in policies:
        if p["valid"]:
            status = Text("✅ Valid", style="green")
        else:
            status = Text(f"❌ {p['error'][:30]}", style="red")

        table.add_row(
            p["file"],
            p.get("domain", "?"),
            str(p.get("constraints", "?")),
            str(p.get("variables", "?")),
            status,
        )

    console.print(table)
    console.print()


# ============================================================================
# INTERACTIVE PROMPT
# ============================================================================

def interactive_header(model: str, policy_path: str, dry_run: bool = False):
    """Display the interactive mode header."""
    show_banner(mini=True)
    console.print()

    info = Table(show_header=False, box=None, padding=(0, 1))
    info.add_column(style="dim", width=10)
    info.add_column()

    info.add_row("Model", f"[bold]{model}[/bold]")
    info.add_row("Policy", f"[magenta]{policy_path}[/magenta]")
    if dry_run:
        info.add_row("Mode", "[yellow bold]⚠️  DRY RUN[/yellow bold]")

    console.print(Panel(
        info,
        border_style="cyan",
        padding=(0, 1),
    ))
    console.print()
    console.print("[dim]Commands: [bold]quit[/bold] · [bold]halt[/bold] · [bold]resume[/bold] · [bold]status[/bold][/dim]")
    console.print()
