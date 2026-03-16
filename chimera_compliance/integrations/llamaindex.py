"""
chimera-compliance — LlamaIndex Integration

Provides:
  - ChimeraToolSpec: Wraps LlamaIndex tool specs with compliance guard
  - wrap_tools(): Convenience function for wrapping tools

Install: pip install chimera-compliance[llamaindex]

Usage:
    from chimera_compliance.integrations.llamaindex import wrap_tools

    guarded_tools = wrap_tools(
        tools=[query_tool, calculator_tool],
        policy="./policies/governance.yaml",
    )
"""

from __future__ import annotations

import json
from typing import Any, Callable, Dict, List, Optional

from . import ComplianceGuard
from .base import ActionGuardMixin, ComplianceError

try:
    from llama_index.core.tools import FunctionTool, BaseTool as LlamaBaseTool
    LLAMAINDEX_AVAILABLE = True
except ImportError:
    LLAMAINDEX_AVAILABLE = False


def _require_llamaindex() -> None:
    if not LLAMAINDEX_AVAILABLE:
        raise ImportError(
            "LlamaIndex is required for this integration.\n"
            "Install it with: pip install chimera-compliance[llamaindex]"
        )


def wrap_tool(
    tool: Any,
    guard: ComplianceGuard,
    param_extractor: Optional[Callable] = None,
) -> Any:
    """
    Wrap a single LlamaIndex tool with compliance guard.

    Returns a new FunctionTool that checks compliance before calling the original.
    """
    _require_llamaindex()

    original_fn = tool.fn if hasattr(tool, "fn") else tool._fn

    def guarded_fn(*args: Any, **kwargs: Any) -> Any:
        # Extract params
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

        tool_name = getattr(tool, "metadata", {})
        if hasattr(tool_name, "name"):
            tool_name = tool_name.name
        elif isinstance(tool_name, dict):
            tool_name = tool_name.get("name", "unknown_tool")
        else:
            tool_name = getattr(tool, "name", "unknown_tool")

        evaluation = guard.check(str(tool_name), params)

        if evaluation.result == "BLOCKED":
            violations = "; ".join(v.explanation for v in evaluation.violations)
            raise ComplianceError(evaluation)

        return original_fn(*args, **kwargs)

    return FunctionTool.from_defaults(
        fn=guarded_fn,
        name=getattr(tool, "metadata", {}).get("name", "guarded_tool")
        if isinstance(getattr(tool, "metadata", None), dict)
        else getattr(getattr(tool, "metadata", None), "name", "guarded_tool"),
        description=getattr(tool, "metadata", {}).get("description", "")
        if isinstance(getattr(tool, "metadata", None), dict)
        else getattr(getattr(tool, "metadata", None), "description", ""),
    )


def wrap_tools(
    tools: List[Any],
    policy: str,
    audit_dir: str = "./audit_logs",
    param_extractor: Optional[Callable] = None,
) -> List[Any]:
    """
    Wrap a list of LlamaIndex tools with compliance guards.

    Args:
        tools: List of LlamaIndex tool instances
        policy: Path to .csl or .yaml policy file
        audit_dir: Directory for audit logs
        param_extractor: Optional function to extract params from tool args

    Returns:
        List of wrapped tools
    """
    _require_llamaindex()
    guard = ComplianceGuard(policy=policy, audit_dir=audit_dir)
    return [wrap_tool(t, guard, param_extractor) for t in tools]
