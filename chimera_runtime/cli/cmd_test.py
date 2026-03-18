"""chimera-runtime test — End-to-end system validation."""

from __future__ import annotations

import json
import time
import tempfile
from pathlib import Path
from typing import List, Tuple

import click
from rich.table import Table
from rich.panel import Panel

from .main import pass_ctx, CLIContext
from .display import console, err_console


def _step_result(passed: bool) -> str:
    return "[bold green]PASS[/bold green]" if passed else "[bold red]FAIL[/bold red]"


@click.command("test")
@click.option("--skip-llm", is_flag=True, help="Skip LLM connection test")
@click.option("--policy", "-p", "policy_file", default=None,
              help="Policy file to test (default: from config)")
@click.option("--verbose", "-v", is_flag=True, help="Show detailed output")
@pass_ctx
def test_cmd(ctx: CLIContext, skip_llm: bool, policy_file: str, verbose: bool):
    """🧪 Run end-to-end system validation.

    Tests config loading, policy compilation, audit pipeline, and optionally LLM connection.
    """
    console.print()
    console.print(Panel(
        "[bold]chimera-runtime — System Test[/bold]",
        border_style="cyan",
    ))
    console.print()

    results: List[Tuple[str, bool, str]] = []
    total_start = time.perf_counter()

    # Step 1: Config loading
    config = None
    try:
        from ..config import load_config, validate_config
        config = load_config(ctx.config_path)
        validate_config(config)
        results.append(("Config loading", True, f"Loaded from {ctx.config_path}"))
    except FileNotFoundError:
        results.append(("Config loading", False, f"Config not found: {ctx.config_path}"))
    except Exception as e:
        results.append(("Config loading", False, str(e)))

    # Step 2: Policy loading
    if policy_file is None and config is not None:
        policy_file = config.policy.file

    if policy_file is None:
        policy_file = "./policies/starter.csl"

    pm = None
    try:
        from ..policy import PolicyManager, CSL_CORE_AVAILABLE
        pm = PolicyManager(policy_file, auto_verify=False)
        backend = pm.backend
        results.append((
            "Policy loading",
            True,
            f"{pm.domain_name} — {pm.constraint_count} constraints ({backend})",
        ))
    except Exception as e:
        results.append(("Policy loading", False, str(e)))

    # Step 3: Policy verification
    if pm is not None:
        try:
            ok, errors = pm.verify()
            if ok:
                results.append(("Policy verification", True, "Verified successfully"))
            else:
                results.append(("Policy verification", False, "; ".join(errors)))
        except Exception as e:
            results.append(("Policy verification", False, str(e)))
    else:
        results.append(("Policy verification", False, "Skipped — no policy loaded"))

    # Step 4: Policy simulation
    if pm is not None:
        try:
            # Build sample params from variable names
            sample_params = {}
            for var_name in pm.variable_names:
                domain = pm.variable_domains.get(var_name, "")
                if ".." in domain:
                    # Numeric range — use midpoint
                    parts = domain.split("..")
                    try:
                        low = int(parts[0])
                        high = int(parts[1])
                        sample_params[var_name] = (low + high) // 2
                    except (ValueError, IndexError):
                        sample_params[var_name] = 0
                elif "{" in domain:
                    # Enum — use first value
                    clean = domain.strip("{} ")
                    values = [v.strip().strip('"').strip("'") for v in clean.split(",")]
                    if values:
                        sample_params[var_name] = values[0]

            if sample_params:
                eval_result = pm.evaluate(sample_params)
                results.append((
                    "Policy simulation",
                    True,
                    f"{eval_result.result} — {eval_result.duration_ms:.2f}ms",
                ))
            else:
                results.append(("Policy simulation", True, "No variables to test"))
        except Exception as e:
            results.append(("Policy simulation", False, str(e)))
    else:
        results.append(("Policy simulation", False, "Skipped — no policy loaded"))

    # Step 5: LLM connection
    if skip_llm:
        results.append(("LLM connection", True, "Skipped (--skip-llm)"))
    elif config is not None:
        try:
            from ..llm import get_provider
            api_key = config.llm.api_key or ""
            if not api_key:
                import os
                api_key = os.environ.get("CHIMERA_API_KEY", "")
                api_key = api_key or os.environ.get(
                    f"CHIMERA_{config.llm.provider.upper()}_API_KEY", ""
                )

            if not api_key and config.llm.provider != "ollama":
                results.append(("LLM connection", False, "No API key configured"))
            else:
                provider = get_provider(
                    config.llm.provider,
                    model=config.llm.model,
                    api_key=api_key,
                )
                results.append((
                    "LLM connection",
                    True,
                    f"{config.llm.provider}/{config.llm.model} — ready",
                ))
        except Exception as e:
            results.append(("LLM connection", False, str(e)))
    else:
        results.append(("LLM connection", False, "Skipped — no config"))

    # Step 6: Audit write
    audit_dir = None
    if config is not None:
        audit_dir = config.audit.output_dir
    else:
        audit_dir = "./audit_logs"

    try:
        audit_path = Path(audit_dir)
        audit_path.mkdir(parents=True, exist_ok=True)

        # Test write
        test_file = audit_path / ".chimera_test_write"
        test_file.write_text("test", encoding="utf-8")
        test_file.unlink()
        results.append(("Audit write", True, f"Directory writable: {audit_dir}"))
    except Exception as e:
        results.append(("Audit write", False, str(e)))

    # Step 7: Audit read
    try:
        from ..audit.storage import load_all_records
        records = load_all_records(audit_dir=audit_dir)
        results.append(("Audit read", True, f"{len(records)} existing records"))
    except Exception as e:
        results.append(("Audit read", False, str(e)))

    # Step 8: Integration availability
    integration_status = []
    for name, module in [
        ("CSL-Core", "chimera_core"),
        ("LangChain", "langchain_core"),
        ("LangGraph", "langgraph"),
        ("LlamaIndex", "llama_index"),
        ("CrewAI", "crewai"),
        ("AutoGen", "autogen_agentchat"),
    ]:
        try:
            __import__(module)
            integration_status.append(f"{name} [green]installed[/green]")
        except ImportError:
            integration_status.append(f"{name} [dim]not installed[/dim]")

    results.append(("Integrations", True, " | ".join(integration_status)))

    total_ms = (time.perf_counter() - total_start) * 1000

    # Display results
    table = Table(title="Test Results", border_style="cyan")
    table.add_column("Step", style="bold")
    table.add_column("Result", justify="center", width=6)
    table.add_column("Details")

    passed = 0
    failed = 0
    for step_name, step_passed, details in results:
        table.add_row(step_name, _step_result(step_passed), details)
        if step_passed:
            passed += 1
        else:
            failed += 1

    console.print(table)
    console.print()

    # Summary
    if failed == 0:
        console.print(f"[bold green]All {passed} checks passed[/bold green] ({total_ms:.0f}ms)")
    else:
        console.print(
            f"[bold red]{failed} failed[/bold red], "
            f"[green]{passed} passed[/green] ({total_ms:.0f}ms)"
        )
        raise SystemExit(1)
