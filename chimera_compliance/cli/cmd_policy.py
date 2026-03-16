"""chimera-compliance policy — Policy management commands."""

from __future__ import annotations

import json
from pathlib import Path

import click

from .main import pass_ctx, CLIContext
from .display import (
    console, err_console,
    display_policy_info, display_policy_list, display_simulation_result,
)


@click.group("policy")
def policy_cmd():
    """📜 Manage CSL policy files."""
    pass


@policy_cmd.command("new")
@click.argument("name")
@click.option("--dir", "-d", "policy_dir", default="./policies", help="Policy directory")
@pass_ctx
def policy_new(ctx, name, policy_dir):
    """Create a new policy file from template.

    NAME: Name for the policy domain (e.g., PaymentGuard)
    """
    safe_name = name.lower().replace(" ", "_")
    filepath = Path(policy_dir) / f"{safe_name}.csl"

    if filepath.exists():
        if not click.confirm(f"⚠️  {filepath} already exists. Overwrite?", default=False):
            console.print("[dim]Aborted.[/dim]")
            return

    template = f'''CONFIG {{
  ENFORCEMENT_MODE: BLOCK
}}

DOMAIN {name} {{
  VARIABLES {{
    // Define your variables here
    // amount: 0..1000000
    // role: {{"ADMIN", "USER", "MANAGER"}}
    // action: {{"APPROVE", "DENY", "ESCALATE"}}
  }}

  // Add your constraints here
  // STATE_CONSTRAINT example_constraint {{
  //   WHEN amount > 10000
  //   THEN role == "ADMIN"
  // }}
}}
'''

    filepath.parent.mkdir(parents=True, exist_ok=True)
    filepath.write_text(template, encoding="utf-8")

    from rich.syntax import Syntax
    from rich.panel import Panel

    console.print(f"\n[bold green]✅ Created policy:[/bold green] [cyan]{filepath}[/cyan]")
    console.print(f"   [dim]Domain:[/dim] [bold]{name}[/bold]\n")
    console.print(Panel(
        Syntax(template, "text", theme="monokai", line_numbers=True),
        title=f"[bold]{filepath}[/bold]",
        border_style="magenta",
        padding=(0, 1),
    ))
    console.print(f"  [dim]Next: Edit the file, then run [bold]chimera-compliance verify {filepath}[/bold][/dim]\n")


@policy_cmd.command("list")
@click.option("--dir", "-d", "policy_dir", default="./policies", help="Policy directory")
@pass_ctx
def policy_list(ctx, policy_dir):
    """List all policy files and their status."""
    from ..policy import PolicyManager, PolicyError

    dir_path = Path(policy_dir)
    if not dir_path.exists():
        console.print(f"[dim]ℹ️  No policy directory found at {policy_dir}[/dim]")
        return

    csl_files = sorted(dir_path.glob("*.csl"))
    yaml_files = sorted(dir_path.glob("*.yaml")) + sorted(dir_path.glob("*.yml"))
    policy_files = csl_files + [f for f in yaml_files if f not in csl_files]
    if not policy_files:
        console.print(f"[dim]ℹ️  No policy files found in {policy_dir}[/dim]")
        return

    csl_files = policy_files

    policies = []
    for f in csl_files:
        try:
            pm = PolicyManager(str(f), auto_verify=True)
            policies.append({
                "file": f.name,
                "domain": pm.domain_name,
                "constraints": pm.constraint_count,
                "variables": len(pm.variable_names),
                "valid": True,
            })
        except Exception as e:
            policies.append({
                "file": f.name,
                "domain": "?",
                "constraints": "?",
                "variables": "?",
                "valid": False,
                "error": str(e),
            })

    display_policy_list(policies, policy_dir)


@policy_cmd.command("simulate")
@click.argument("policy_file")
@click.argument("context_json", required=False)
@click.option("--input", "-i", "input_file", type=str, default=None,
              help="JSON file with test context")
@click.option("--dry-run", is_flag=True, help="Dry-run mode (evaluate but never block)")
@pass_ctx
def policy_simulate(ctx, policy_file, context_json, input_file, dry_run):
    """Simulate a policy against test input.

    \b
    POLICY_FILE: Path to .csl file
    CONTEXT_JSON: Inline JSON (e.g. '{"amount": 50000, "role": "MANAGER"}')

    \b
    Examples:
        chimera-compliance policy simulate policies/gov.csl '{"amount": 50000}'
        chimera-compliance policy simulate policies/gov.csl --input test_cases.json
    """
    from ..policy import PolicyManager, PolicyError

    try:
        with console.status("[cyan]Loading policy...[/cyan]", spinner="dots"):
            pm = PolicyManager(policy_file, auto_verify=True, dry_run=dry_run)
    except PolicyError as e:
        err_console.print(f"[bold red]❌ Policy error:[/bold red] {e}")
        raise SystemExit(1)

    if input_file:
        try:
            inputs = json.loads(Path(input_file).read_text(encoding="utf-8"))
        except Exception as e:
            err_console.print(f"[bold red]❌ Cannot read input file:[/bold red] {e}")
            raise SystemExit(1)
    elif context_json:
        try:
            inputs = json.loads(context_json)
        except json.JSONDecodeError as e:
            err_console.print(f"[bold red]❌ Invalid JSON:[/bold red] {e}")
            raise SystemExit(1)
    else:
        err_console.print("[bold red]❌ Provide context as argument or --input file[/bold red]")
        raise SystemExit(1)

    if isinstance(inputs, dict):
        inputs = [inputs]

    console.print(f"\n[bold]⚡ Simulating:[/bold] [magenta]{policy_file}[/magenta]")
    console.print(f"   [dim]Domain:[/dim] [bold]{pm.domain_name}[/bold]")
    if dry_run:
        console.print("   [yellow bold]⚠️  DRY RUN mode[/yellow bold]")
    console.print()

    for i, ctx_input in enumerate(inputs, 1):
        result = pm.evaluate(ctx_input)
        display_simulation_result(i, ctx_input, result, dry_run=dry_run)
