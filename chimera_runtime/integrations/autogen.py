"""
chimera-runtime — AutoGen Integration

Provides:
  - ChimeraRuntimeAgent: Wraps AutoGen agents with runtime guard
  - guard_function_call(): Decorator for function call compliance checking

Install: pip install chimera-runtime[autogen]

Usage:
    from chimera_runtime.integrations.autogen import guard_function_call

    @guard_function_call(policy="./policies/governance.yaml")
    def transfer_funds(amount: int, destination: str) -> str:
        return f"Transferred ${amount} to {destination}"
"""

from __future__ import annotations

import functools
import json
from typing import Any, Callable, Dict, List, Optional

from . import ComplianceGuard
from .base import ComplianceError


def guard_function_call(
    policy: str,
    audit_dir: str = "./audit_logs",
    param_mapping: Optional[Dict[str, str]] = None,
) -> Callable:
    """
    Decorator that wraps a function with runtime checking.

    Works with AutoGen function calls — the function's keyword arguments
    are evaluated against the policy before execution.

    Args:
        policy: Path to .csl or .yaml policy file
        audit_dir: Directory for audit logs
        param_mapping: Optional mapping from function param names to policy variable names.
                       E.g., {"amt": "amount"} maps function's 'amt' to policy's 'amount'

    Usage:
        @guard_function_call(policy="./policies/governance.yaml")
        def approve_spend(amount: int, role: str) -> str:
            return f"Approved ${amount}"
    """
    guard = ComplianceGuard(policy=policy, audit_dir=audit_dir)

    def decorator(fn: Callable) -> Callable:
        @functools.wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Build parameters dict from kwargs
            params = dict(kwargs)

            # Apply param mapping if provided
            if param_mapping:
                mapped = {}
                for fn_key, policy_key in param_mapping.items():
                    if fn_key in params:
                        mapped[policy_key] = params[fn_key]
                for k, v in params.items():
                    if k not in param_mapping:
                        mapped[k] = v
                params = mapped

            evaluation = guard.check(fn.__name__, params)

            if evaluation.result == "BLOCKED":
                raise ComplianceError(evaluation)

            return fn(*args, **kwargs)

        return wrapper
    return decorator


class ChimeraRuntimeAgent:
    """
    Wraps an AutoGen agent with runtime checking on function calls.

    Usage:
        from autogen_agentchat import AssistantAgent

        agent = AssistantAgent(name="finance_bot", ...)
        compliant_agent = ChimeraRuntimeAgent(
            agent=agent,
            policy="./policies/governance.yaml",
        )
    """

    def __init__(
        self,
        agent: Any,
        policy: str,
        audit_dir: str = "./audit_logs",
    ):
        self._agent = agent
        self._guard = ComplianceGuard(policy=policy, audit_dir=audit_dir)
        self._wrap_function_map()

    def _wrap_function_map(self) -> None:
        """Wrap all registered functions in the agent's function map."""
        func_map = getattr(self._agent, "_function_map", None)
        if func_map is None:
            return

        for name, fn in list(func_map.items()):
            func_map[name] = self._create_guarded_fn(name, fn)

    def _create_guarded_fn(self, name: str, fn: Callable) -> Callable:
        guard = self._guard

        @functools.wraps(fn)
        def guarded(*args: Any, **kwargs: Any) -> Any:
            params = dict(kwargs)
            evaluation = guard.check(name, params)

            if evaluation.result == "BLOCKED":
                violations = "; ".join(v.explanation for v in evaluation.violations)
                return f"[BLOCKED by chimera-runtime] {violations}"

            return fn(*args, **kwargs)

        return guarded

    @property
    def agent(self) -> Any:
        """Access the underlying AutoGen agent."""
        return self._agent

    def __getattr__(self, name: str) -> Any:
        """Proxy attribute access to the underlying agent."""
        return getattr(self._agent, name)
