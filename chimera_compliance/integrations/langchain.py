"""
chimera-compliance — LangChain Integration

Provides:
  - ChimeraComplianceTool: Wraps any LangChain tool with compliance guard
  - ChimeraCallbackHandler: Intercepts tool calls as a callback handler
  - wrap_tools(): Convenience function to wrap multiple tools

Install: pip install chimera-compliance[langchain]

Usage:
    from chimera_compliance.integrations.langchain import wrap_tools

    guarded_tools = wrap_tools(
        tools=[search_tool, calculator_tool],
        policy="./policies/governance.yaml",
    )
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, Type, Union

from . import ComplianceGuard
from .base import ActionGuardMixin, ComplianceError

try:
    from langchain_core.tools import BaseTool, ToolException
    from langchain_core.callbacks import BaseCallbackHandler
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False


def _require_langchain() -> None:
    if not LANGCHAIN_AVAILABLE:
        raise ImportError(
            "LangChain is required for this integration.\n"
            "Install it with: pip install chimera-compliance[langchain]"
        )


class ChimeraComplianceTool(ActionGuardMixin):
    """
    Wraps a LangChain BaseTool with a compliance guard.

    The wrapped tool's _run() method is intercepted:
    1. Parameters are extracted and evaluated against the policy
    2. If ALLOWED, the original tool executes normally
    3. If BLOCKED, a ToolException is raised with violation details
    """

    def __init__(
        self,
        tool: Any,  # BaseTool
        guard: ComplianceGuard,
        param_extractor: Optional[Any] = None,
    ):
        _require_langchain()
        self._original_tool = tool
        self._guard = guard
        self._param_extractor = param_extractor

        # Monkey-patch the tool's _run method
        original_run = tool._run

        def guarded_run(*args: Any, **kwargs: Any) -> Any:
            # Extract parameters for policy evaluation
            params = self._extract_params(args, kwargs)
            evaluation = self._check_compliance(
                action_name=tool.name,
                parameters=params,
                on_block="return",
            )
            if evaluation.result == "BLOCKED":
                violations = "; ".join(v.explanation for v in evaluation.violations)
                raise ToolException(
                    f"[chimera-compliance] Tool '{tool.name}' BLOCKED: {violations}"
                )
            return original_run(*args, **kwargs)

        tool._run = guarded_run

    def _extract_params(self, args: tuple, kwargs: dict) -> Dict[str, Any]:
        """Extract parameters from tool call for policy evaluation."""
        if self._param_extractor:
            return self._param_extractor(args, kwargs)

        params: Dict[str, Any] = dict(kwargs)
        if args:
            # Try to parse first arg as JSON
            try:
                if isinstance(args[0], str):
                    parsed = json.loads(args[0])
                    if isinstance(parsed, dict):
                        params.update(parsed)
                    else:
                        params["input"] = args[0]
                elif isinstance(args[0], dict):
                    params.update(args[0])
                else:
                    params["input"] = str(args[0])
            except (json.JSONDecodeError, TypeError):
                params["input"] = str(args[0])

        return params

    @property
    def tool(self) -> Any:
        return self._original_tool


class ChimeraCallbackHandler:
    """
    LangChain callback handler that intercepts tool calls for compliance checking.

    Usage:
        handler = ChimeraCallbackHandler(policy="./policies/governance.yaml")
        llm = ChatOpenAI(callbacks=[handler])
    """

    def __init__(
        self,
        policy: str,
        audit_dir: str = "./audit_logs",
        on_block: str = "raise",
        **kwargs: Any,
    ):
        _require_langchain()
        self._guard = ComplianceGuard(policy=policy, audit_dir=audit_dir)
        self._on_block = on_block
        # We need to be a proper callback handler
        self._handler = _create_callback_handler(self._guard, on_block)

    def get_handler(self) -> Any:
        """Returns the actual LangChain BaseCallbackHandler instance."""
        return self._handler


def _create_callback_handler(guard: ComplianceGuard, on_block: str) -> Any:
    """Factory to create the actual callback handler (avoids class-level import issues)."""
    _require_langchain()

    class _Handler(BaseCallbackHandler):
        def on_tool_start(
            self,
            serialized: Dict[str, Any],
            input_str: str,
            **kwargs: Any,
        ) -> None:
            tool_name = serialized.get("name", "unknown_tool")

            # Try to parse input as dict for evaluation
            params: Dict[str, Any] = {}
            try:
                parsed = json.loads(input_str)
                if isinstance(parsed, dict):
                    params = parsed
                else:
                    params = {"input": input_str}
            except (json.JSONDecodeError, TypeError):
                params = {"input": input_str}

            evaluation = guard.check(tool_name, params)

            if evaluation.result == "BLOCKED" and on_block == "raise":
                violations = "; ".join(v.explanation for v in evaluation.violations)
                raise ComplianceError(evaluation)

    return _Handler()


def wrap_tools(
    tools: List[Any],
    policy: str,
    audit_dir: str = "./audit_logs",
    param_extractor: Optional[Any] = None,
) -> List[Any]:
    """
    Wrap a list of LangChain tools with compliance guards.

    Args:
        tools: List of LangChain BaseTool instances
        policy: Path to .csl or .yaml policy file
        audit_dir: Directory for audit logs
        param_extractor: Optional function to extract params from tool args

    Returns:
        The same tools list (tools are modified in-place)
    """
    _require_langchain()
    guard = ComplianceGuard(policy=policy, audit_dir=audit_dir)

    for tool in tools:
        ChimeraComplianceTool(tool, guard, param_extractor)

    return tools
