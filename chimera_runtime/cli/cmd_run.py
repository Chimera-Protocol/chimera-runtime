"""chimera-runtime run — Start the agent in interactive or daemon mode."""

from __future__ import annotations

import json
import sys
import time

import click

from .main import pass_ctx, CLIContext
from .display import (
    console, err_console,
    display_decision_result, display_agent_status,
    interactive_header,
)

from chimera_runtime import AgentHalted, ChimeraAgentError


@click.command("run")
@click.option("--daemon", "-d", is_flag=True, help="Run as background daemon (stdin pipe mode)")
@click.option("--require-confirmation", is_flag=True, help="Require human confirmation for each decision")
@click.option("--human-override", is_flag=True, help="Allow human override of decisions")
@click.option("--dry-run", is_flag=True, help="Evaluate policies but never block")
@click.option("--model", "-m", default=None, help="Override LLM model")
@click.option("--policy", "-p", default=None, help="Override policy file path")
@pass_ctx
def run_cmd(ctx, daemon, require_confirmation, human_override, dry_run, model, policy):
    """🤖 Run the chimera-runtime.

    Default: Interactive prompt loop with real-time reasoning display.
    With --daemon: Reads JSON requests from stdin, writes results to stdout.
    """
    from ..config import load_config
    from ..agent import ChimeraAgent, AgentHalted

    try:
        config = load_config(ctx.config_path)
    except Exception as e:
        err_console.print(f"[bold red]❌ Failed to load config:[/bold red] {e}")
        err_console.print("[dim]Run 'chimera-runtime init' to create a config file.[/dim]")
        raise SystemExit(1)

    overrides = {}
    if model:
        overrides["model"] = model
    if policy:
        overrides["policy"] = policy
    if dry_run:
        overrides["dry_run"] = True

    oversight_mode = "auto"
    if require_confirmation:
        oversight_mode = "interactive"

    try:
        agent = ChimeraAgent.from_config(
            config, config_path=ctx.config_path,
            oversight_mode=oversight_mode, **overrides,
        )
    except Exception as e:
        err_console.print(f"[bold red]❌ Failed to create agent:[/bold red] {e}")
        raise SystemExit(1)

    if daemon:
        _run_daemon(agent, ctx)
    else:
        _run_interactive(agent, ctx, dry_run=dry_run)


def _run_interactive(agent, ctx, dry_run=False):
    from rich.prompt import Prompt

    interactive_header(
        model=agent._llm.model,
        policy_path=str(agent._policy.policy_path),
        dry_run=dry_run,
    )

    while True:
        try:
            request = Prompt.ask("[bold cyan]chimera[/bold cyan]")
        except (EOFError, KeyboardInterrupt):
            console.print("\n[dim]👋 Goodbye![/dim]")
            break

        request = request.strip()
        if not request:
            continue
        if request.lower() in ("quit", "exit"):
            console.print("[dim]👋 Goodbye![/dim]")
            break
        if request.lower() == "halt":
            agent.halt()
            console.print("[bold red]🛑 Agent HALTED.[/bold red] [dim]Use 'chimera-runtime run' to restart.[/dim]")
            break
        if request.lower() == "resume":
            agent.resume()
            console.print("[bold green]✅ Agent resumed.[/bold green]")
            continue
        if request.lower() == "status":
            display_agent_status(agent)
            continue

        context = {}
        if " --context " in request:
            parts = request.split(" --context ", 1)
            request = parts[0].strip()
            try:
                context = json.loads(parts[1])
            except json.JSONDecodeError:
                console.print("[yellow]⚠️  Invalid JSON context. Ignoring.[/yellow]")

        try:
            with console.status("[bold cyan]Generating candidates...[/bold cyan]", spinner="dots"):
                start = time.time()
                result = agent.decide(request, context=context)
                elapsed = (time.time() - start) * 1000

            display_decision_result(result, elapsed, ctx.verbose)

        except AgentHalted:
            console.print("[bold red]🛑 Agent is HALTED.[/bold red] [dim]Type 'resume' to reactivate.[/dim]")
        except Exception as e:
            err_console.print(f"[bold red]❌ Error:[/bold red] {e}")


def _run_daemon(agent, ctx):
    err_console.print("[dim]🤖 chimera-runtime daemon mode. Send JSON to stdin.[/dim]")
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            payload = json.loads(line)
            result = agent.decide(payload.get("request", ""), context=payload.get("context", {}))
            click.echo(json.dumps(result.to_dict(), ensure_ascii=False))
        except Exception as e:
            click.echo(json.dumps({"error": str(e), "type": type(e).__name__}, ensure_ascii=False))
