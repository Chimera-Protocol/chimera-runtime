"""chimera-runtime verify — Verify a CSL policy file."""

from __future__ import annotations

import click

from .main import pass_ctx, CLIContext
from .display import console, err_console, display_policy_info


@click.command("verify")
@click.argument("policy_file", required=False)
@pass_ctx
def verify_cmd(ctx: CLIContext, policy_file: str):
    """⚡ Verify a CSL policy file.

    Runs the full CSL-Core verification pipeline:
    syntax → semantics → Z3 logic → IR compilation.

    If no POLICY_FILE is given, uses the one from config.
    """
    from ..config import load_config
    from ..policy import PolicyManager, PolicyError

    if not policy_file:
        try:
            config = load_config(ctx.config_path)
            policy_file = config.policy.file
        except Exception:
            err_console.print("[bold red]❌ No policy file specified and no config found.[/bold red]")
            err_console.print("[dim]Usage: chimera-runtime verify <policy_file>[/dim]")
            raise SystemExit(1)

    console.print(f"\n[bold]⚡ Verifying:[/bold] [magenta]{policy_file}[/magenta]\n")

    try:
        with console.status("[cyan]Running verification pipeline...[/cyan]", spinner="dots"):
            pm = PolicyManager(policy_file, auto_verify=True)
    except PolicyError as e:
        err_console.print(f"[bold red]❌ Verification FAILED:[/bold red] {e}")
        raise SystemExit(1)
    except FileNotFoundError as e:
        err_console.print(f"[bold red]❌ File not found:[/bold red] {e}")
        raise SystemExit(1)

    display_policy_info(pm, title="Policy Verified")
