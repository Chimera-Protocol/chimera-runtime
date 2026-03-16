"""chimera-compliance init — Project initialization wizard."""

from __future__ import annotations

import os
from pathlib import Path

import click

from .main import pass_ctx, CLIContext
from .display import console, show_banner, display_init_complete


PROVIDERS = ["openai", "anthropic", "google", "ollama"]
DEFAULT_MODELS = {
    "openai": "gpt-4o",
    "anthropic": "claude-sonnet-4-20250514",
    "google": "gemini-2.0-flash",
    "ollama": "llama3",
}

MODES = {
    1: ("standalone", "Standalone Agent — chimera-compliance manages the LLM directly"),
    2: ("integration", "Integration Mode — use with LangChain, LangGraph, CrewAI, etc."),
}

STARTER_CSL_POLICY = '''CONFIG {
  ENFORCEMENT_MODE: BLOCK
}

DOMAIN StarterGuard {
  VARIABLES {
    risk_score: 0..100
    action: {"ALLOW", "DENY"}
  }

  STATE_CONSTRAINT high_risk_block {
    WHEN risk_score > 80
    THEN action == "DENY"
  }
}
'''

STARTER_YAML_POLICY = '''domain: StarterGuard

variables:
  risk_score: "0..100"
  action: "{ALLOW, DENY}"

rules:
  - name: high_risk_block
    when: "risk_score > 80"
    then: BLOCK
    message: "High risk score requires DENY action"
'''

INTEGRATION_FRAMEWORKS = [
    ("langchain", "LangChain — Tool wrapper + callback handler"),
    ("langgraph", "LangGraph — Node guard for state graphs"),
    ("crewai", "CrewAI — Tool wrapper for crew agents"),
    ("llamaindex", "LlamaIndex — Tool spec wrapper"),
    ("autogen", "AutoGen — Function call guard"),
]


@click.command("init")
@click.option("--non-interactive", is_flag=True, help="Use defaults, skip prompts")
@click.option("--mode", type=click.Choice(["standalone", "integration"]),
              default=None, help="Project mode")
@pass_ctx
def init_cmd(ctx: CLIContext, non_interactive: bool, mode: str):
    """Initialize a new chimera-compliance project.

    Creates .chimera/config.yaml and a starter policy file.
    Supports two modes:

    \b
      standalone   — chimera-compliance manages the LLM directly
      integration  — use with LangChain, LangGraph, CrewAI, etc.
    """
    config_dir = Path(ctx.config_dir)
    config_path = Path(ctx.config_path)

    if config_path.exists():
        if not non_interactive:
            if not click.confirm(
                f"  {config_path} already exists. Overwrite?", default=False
            ):
                console.print("[dim]Aborted.[/dim]")
                return
        else:
            console.print(f"[yellow]  Overwriting existing {config_path}[/yellow]")

    show_banner(mini=True)
    console.print()

    # --- Determine mode ---
    if mode is None and not non_interactive:
        from rich.prompt import IntPrompt
        console.print("[bold]How will you use chimera-compliance?[/bold]")
        for num, (_, desc) in MODES.items():
            console.print(f"  [cyan]{num}[/cyan]. {desc}")
        choice = IntPrompt.ask("Choice", default=1)
        choice = max(1, min(len(MODES), choice))
        mode = MODES[choice][0]
    elif mode is None:
        mode = "standalone"

    if non_interactive:
        policy_format, policy_file, audit_dir, retention_days = _defaults_shared()
        if mode == "standalone":
            provider, model, api_key, temperature = _defaults_standalone()
        else:
            provider, model, api_key, temperature = None, None, "", 0.0
            framework = "langchain"
    else:
        policy_format, policy_file, audit_dir, retention_days = _prompt_shared()
        if mode == "standalone":
            provider, model, api_key, temperature = _prompt_standalone()
        else:
            framework = _prompt_integration()
            provider, model, api_key, temperature = None, None, "", 0.0

    # --- Build config ---
    from ..config import save_config
    from ..models import (
        AgentConfig, AgentMetaConfig, LLMConfig,
        PolicyConfig, AuditConfig, OversightConfig,
    )

    if mode == "standalone":
        llm_config = LLMConfig(
            provider=provider, model=model,
            api_key=api_key if api_key else None,
            temperature=temperature,
        )
    else:
        llm_config = LLMConfig(
            provider="none", model="external",
            temperature=0.0,
        )

    config = AgentConfig(
        agent=AgentMetaConfig(name="chimera-compliance", version="0.1.0"),
        llm=llm_config,
        policy=PolicyConfig(file=policy_file),
        audit=AuditConfig(output_dir=audit_dir, retention_days=retention_days),
        oversight=OversightConfig(),
    )

    config_dir.mkdir(parents=True, exist_ok=True)
    Path(audit_dir).mkdir(parents=True, exist_ok=True)
    save_config(config, str(config_path))

    # --- Create starter policy ---
    p = Path(policy_file)
    if not p.exists():
        p.parent.mkdir(parents=True, exist_ok=True)
        if policy_file.endswith((".yaml", ".yml")):
            p.write_text(STARTER_YAML_POLICY, encoding="utf-8")
        else:
            p.write_text(STARTER_CSL_POLICY, encoding="utf-8")

    # --- Next steps ---
    if mode == "standalone":
        steps = [
            f"Edit your policy: [magenta]{policy_file}[/magenta]",
            f"Verify it: [cyan]chimera-compliance verify {policy_file}[/cyan]",
            "Run agent: [cyan]chimera-compliance run[/cyan]",
        ]
    else:
        from rich.markup import escape
        install_cmd = escape(f"pip install chimera-compliance[{framework}]")
        steps = [
            f"Edit your policy: [magenta]{policy_file}[/magenta]",
            f"Test it: [cyan]chimera-compliance test --skip-llm[/cyan]",
            f"Install framework: [cyan]{install_cmd}[/cyan]",
            _integration_snippet(framework, policy_file),
        ]

    display_init_complete(
        config_path=str(config_path),
        policy_file=policy_file,
        steps=steps,
    )


# ============================================================================
# PROMPTS — SHARED (both modes)
# ============================================================================

def _defaults_shared():
    return "yaml", "./policies/starter.yaml", "./audit_logs", 180


def _prompt_shared():
    from rich.prompt import Prompt, IntPrompt

    console.print()
    console.print("[bold]Policy format:[/bold]")
    console.print("  [cyan]1[/cyan]. YAML rules (no extra dependencies)")
    console.print("  [cyan]2[/cyan]. CSL policy (Z3 formal verification, requires csl-core)")
    fmt_choice = IntPrompt.ask("Choice", default=1)
    policy_format = "yaml" if fmt_choice == 1 else "csl"

    default_policy = f"./policies/starter.{policy_format}" if policy_format == "csl" else "./policies/starter.yaml"
    policy_file = Prompt.ask("Policy file path", default=default_policy)
    audit_dir = Prompt.ask("Audit log directory", default="./audit_logs")
    retention_days = IntPrompt.ask("Retention days (Art. 19)", default=180)
    return policy_format, policy_file, audit_dir, retention_days


# ============================================================================
# PROMPTS — STANDALONE MODE
# ============================================================================

def _defaults_standalone():
    return "openai", "gpt-4o", "", 0.7


def _prompt_standalone():
    from rich.prompt import Prompt, IntPrompt, FloatPrompt

    console.print()
    console.print("[bold]Select LLM Provider:[/bold]")
    for i, p in enumerate(PROVIDERS, 1):
        console.print(f"  [cyan]{i}[/cyan]. {p}")
    choice = IntPrompt.ask("Choice", default=1)
    choice = max(1, min(len(PROVIDERS), choice))
    provider = PROVIDERS[choice - 1]

    default_model = DEFAULT_MODELS[provider]
    model = Prompt.ask("Model", default=default_model)

    env_var = f"CHIMERA_{provider.upper()}_API_KEY"
    if provider == "ollama":
        api_key = ""
        console.print(f"[dim]  Ollama runs locally — no API key needed[/dim]")
    else:
        api_key = Prompt.ask(
            f"API Key [dim](or set {env_var})[/dim]",
            default="",
            password=True,
        )
        if api_key:
            console.print(f"[dim]Tip: set {env_var} instead of storing in config[/dim]")

    temperature = FloatPrompt.ask("Temperature", default=0.7)
    return provider, model, api_key, temperature


# ============================================================================
# PROMPTS — INTEGRATION MODE
# ============================================================================

def _prompt_integration():
    from rich.prompt import IntPrompt

    console.print()
    console.print("[bold]Select agent framework:[/bold]")
    for i, (_, desc) in enumerate(INTEGRATION_FRAMEWORKS, 1):
        console.print(f"  [cyan]{i}[/cyan]. {desc}")
    choice = IntPrompt.ask("Choice", default=1)
    choice = max(1, min(len(INTEGRATION_FRAMEWORKS), choice))
    return INTEGRATION_FRAMEWORKS[choice - 1][0]


def _integration_snippet(framework: str, policy_file: str) -> str:
    """Return a code snippet hint for the selected framework."""
    snippets = {
        "langchain": (
            "Use in code: [dim]from chimera_compliance.integrations.langchain import wrap_tools[/dim]"
        ),
        "langgraph": (
            "Use in code: [dim]from chimera_compliance.integrations.langgraph import compliance_node[/dim]"
        ),
        "crewai": (
            "Use in code: [dim]from chimera_compliance.integrations.crewai import wrap_crew_tools[/dim]"
        ),
        "llamaindex": (
            "Use in code: [dim]from chimera_compliance.integrations.llamaindex import wrap_tools[/dim]"
        ),
        "autogen": (
            "Use in code: [dim]from chimera_compliance.integrations.autogen import guard_function_call[/dim]"
        ),
    }
    return snippets.get(framework, "")
