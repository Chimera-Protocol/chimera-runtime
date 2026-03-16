"""
chimera-compliance — CrewAI Integration

Provides:
  - wrap_crew_tools(): Wraps CrewAI tools with compliance guard
  - ChimeraCrewTool: Compliance-guarded CrewAI tool

Install: pip install chimera-compliance[crewai]

Usage:
    from chimera_compliance.integrations.crewai import wrap_crew_tools

    guarded_tools = wrap_crew_tools(
        tools=[search_tool, calculator_tool],
        policy="./policies/governance.yaml",
    )
"""

from __future__ import annotations

import json
from typing import Any, Callable, Dict, List, Optional

from . import ComplianceGuard
from .base import ComplianceError

try:
    from crewai.tools import BaseTool as CrewBaseTool
    CREWAI_AVAILABLE = True
except ImportError:
    CREWAI_AVAILABLE = False


def _require_crewai() -> None:
    if not CREWAI_AVAILABLE:
        raise ImportError(
            "CrewAI is required for this integration.\n"
            "Install it with: pip install chimera-compliance[crewai]"
        )


def wrap_crew_tools(
    tools: List[Any],
    policy: str,
    audit_dir: str = "./audit_logs",
    param_extractor: Optional[Callable] = None,
) -> List[Any]:
    """
    Wrap a list of CrewAI tools with compliance guards.

    Each tool's _run method is intercepted to check compliance
    before execution. If blocked, a ComplianceError is raised.

    Args:
        tools: List of CrewAI tool instances
        policy: Path to .csl or .yaml policy file
        audit_dir: Directory for audit logs
        param_extractor: Optional function to extract params

    Returns:
        The same tools list (tools are modified in-place)
    """
    _require_crewai()
    guard = ComplianceGuard(policy=policy, audit_dir=audit_dir)

    for tool in tools:
        _wrap_single_crew_tool(tool, guard, param_extractor)

    return tools


def _wrap_single_crew_tool(
    tool: Any,
    guard: ComplianceGuard,
    param_extractor: Optional[Callable] = None,
) -> None:
    """Wrap a single CrewAI tool by monkey-patching its _run method."""
    original_run = tool._run

    def guarded_run(*args: Any, **kwargs: Any) -> Any:
        # Extract parameters
        params: Dict[str, Any] = dict(kwargs)
        if param_extractor:
            params = param_extractor(args, kwargs)
        elif args:
            try:
                if isinstance(args[0], str):
                    parsed = json.loads(args[0])
                    if isinstance(parsed, dict):
                        params.update(parsed)
                elif isinstance(args[0], dict):
                    params.update(args[0])
            except (json.JSONDecodeError, TypeError):
                pass

        tool_name = getattr(tool, "name", "unknown_tool")
        evaluation = guard.check(tool_name, params)

        if evaluation.result == "BLOCKED":
            raise ComplianceError(evaluation)

        return original_run(*args, **kwargs)

    tool._run = guarded_run
