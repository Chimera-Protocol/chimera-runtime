"""
chimera-compliance — LangGraph Integration

Provides:
  - compliance_node(): A graph node that gates actions through the compliance guard
  - compliance_edge(): A conditional edge that routes based on compliance check

Install: pip install chimera-compliance[langgraph]

Usage:
    from chimera_compliance.integrations.langgraph import compliance_node

    # Add compliance check as a node in your graph
    graph.add_node("compliance", compliance_node(policy="./policies/governance.yaml"))
    graph.add_edge("agent", "compliance")
    graph.add_conditional_edges("compliance", route_after_check)
"""

from __future__ import annotations

from typing import Any, Callable, Dict, Optional

from . import ComplianceGuard
from .base import ComplianceError


def compliance_node(
    policy: str,
    audit_dir: str = "./audit_logs",
    param_key: str = "parameters",
    action_key: str = "action",
    result_key: str = "compliance_result",
) -> Callable:
    """
    Create a LangGraph node that performs compliance checking.

    The node reads parameters from the state, evaluates them against
    the policy, and writes the result back to state.

    Args:
        policy: Path to .csl or .yaml policy file
        audit_dir: Directory for audit logs
        param_key: State key containing parameters to evaluate
        action_key: State key containing the action name
        result_key: State key to write compliance result to

    Returns:
        A callable node function compatible with LangGraph
    """
    guard = ComplianceGuard(policy=policy, audit_dir=audit_dir)

    def node_fn(state: Dict[str, Any]) -> Dict[str, Any]:
        parameters = state.get(param_key, {})
        action_name = state.get(action_key, "unknown_action")

        evaluation = guard.check(action_name, parameters)

        return {
            result_key: {
                "allowed": evaluation.result == "ALLOWED",
                "result": evaluation.result,
                "violations": [
                    {
                        "constraint": v.constraint,
                        "message": v.explanation,
                    }
                    for v in evaluation.violations
                ],
                "duration_ms": evaluation.duration_ms,
            }
        }

    return node_fn


def compliance_edge(
    result_key: str = "compliance_result",
    allowed_node: str = "execute",
    blocked_node: str = "blocked",
) -> Callable:
    """
    Create a conditional edge function that routes based on compliance result.

    Usage:
        graph.add_conditional_edges(
            "compliance",
            compliance_edge(allowed_node="execute", blocked_node="report_block"),
        )
    """
    def edge_fn(state: Dict[str, Any]) -> str:
        result = state.get(result_key, {})
        if result.get("allowed", False):
            return allowed_node
        return blocked_node

    return edge_fn
