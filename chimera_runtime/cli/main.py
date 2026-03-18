"""
chimera-runtime CLI — Main entry point

Usage:
    chimera-runtime --help
    chimera-runtime init
    chimera-runtime run [--daemon] [--require-confirmation]
    chimera-runtime stop [--force]
    chimera-runtime verify [POLICY]
    chimera-runtime audit [--last N] [--result RESULT] [--stats]
    chimera-runtime policy [new|list|simulate]
    chimera-runtime explain --id <decision_id>
    chimera-runtime docs [generate|status|refresh]
"""

from __future__ import annotations

import sys

import click

from .. import __version__


# ============================================================================
# GLOBAL OPTIONS & GROUP
# ============================================================================

class CLIContext:
    """Shared context for all CLI commands."""
    def __init__(self):
        self.config_dir: str = ".chimera"
        self.config_path: str = ".chimera/config.yaml"
        self.verbose: bool = False


pass_ctx = click.make_pass_decorator(CLIContext, ensure=True)


@click.group()
@click.version_option(version=__version__, prog_name="chimera-runtime")
@click.option("--config", "-c", default=".chimera/config.yaml",
              help="Path to config file", show_default=True)
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
@click.pass_context
def cli(ctx, config, verbose):
    """🛡️ chimera-runtime — Deterministic Runtime for AI Agents

    Every decision enforced. Every constraint proven. Every action auditable.
    """
    ctx.ensure_object(CLIContext)
    ctx.obj.config_path = config
    ctx.obj.config_dir = str(config).rsplit("/", 1)[0] if "/" in str(config) else ".chimera"
    ctx.obj.verbose = verbose


# ============================================================================
# REGISTER SUBCOMMANDS
# ============================================================================

def _register_commands():
    """Import and register all subcommands."""
    from .cmd_init import init_cmd
    from .cmd_run import run_cmd
    from .cmd_stop import stop_cmd
    from .cmd_verify import verify_cmd
    from .cmd_audit import audit_cmd
    from .cmd_policy import policy_cmd
    from .cmd_explain import explain_cmd
    from .cmd_docs import docs_cmd
    from .cmd_test import test_cmd
    from .cmd_license import license_cmd

    cli.add_command(init_cmd, "init")
    cli.add_command(run_cmd, "run")
    cli.add_command(stop_cmd, "stop")
    cli.add_command(verify_cmd, "verify")
    cli.add_command(audit_cmd, "audit")
    cli.add_command(policy_cmd, "policy")
    cli.add_command(explain_cmd, "explain")
    cli.add_command(docs_cmd, "docs")
    cli.add_command(test_cmd, "test")
    cli.add_command(license_cmd, "license")


_register_commands()
