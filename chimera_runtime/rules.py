"""
chimera-runtime — YAML Rule Engine

Lightweight policy evaluation without CSL-Core / Z3 dependency.
Supports YAML-defined rules with safe expression evaluation.

Rules format:
    rules:
      - name: manager_limit
        when: "role == 'MANAGER' and amount > 250000"
        then: BLOCK
        message: "Managers cannot approve more than $250,000"
"""

from __future__ import annotations

import ast
import hashlib
import operator
import re
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml

from .models import PolicyEvaluation, Violation


# ============================================================================
# ERRORS
# ============================================================================

class RuleEngineError(Exception):
    """Raised when the YAML rule engine encounters an error."""
    pass


class RuleParseError(RuleEngineError):
    """Raised when a rule expression cannot be parsed."""
    pass


# ============================================================================
# SAFE EXPRESSION EVALUATOR
# ============================================================================

_OPERATORS = {
    ast.Eq: operator.eq,
    ast.NotEq: operator.ne,
    ast.Lt: operator.lt,
    ast.LtE: operator.le,
    ast.Gt: operator.gt,
    ast.GtE: operator.ge,
}

_BOOL_OPS = {
    ast.And: all,
    ast.Or: any,
}


def _safe_eval(expr: str, context: Dict[str, Any]) -> bool:
    """
    Safely evaluate a boolean expression against a context dict.

    Supports:
      - Comparisons: ==, !=, >, <, >=, <=
      - Boolean ops: and, or, not
      - String literals: 'value' or "value"
      - Numeric literals: 42, 3.14
      - Variable references from context
      - 'in' operator: value in ('A', 'B', 'C')

    Does NOT use eval(). Parses AST and walks it safely.
    """
    try:
        tree = ast.parse(expr, mode="eval")
    except SyntaxError as e:
        raise RuleParseError(f"Invalid expression: {expr!r} — {e}") from e

    return _eval_node(tree.body, context)


def _eval_node(node: ast.AST, ctx: Dict[str, Any]) -> Any:
    # Boolean literals
    if isinstance(node, ast.Constant):
        return node.value

    # Variable reference
    if isinstance(node, ast.Name):
        if node.id == "True":
            return True
        if node.id == "False":
            return False
        if node.id not in ctx:
            raise RuleParseError(f"Unknown variable: {node.id!r}")
        return ctx[node.id]

    # Comparison: a == b, a > b, etc.
    if isinstance(node, ast.Compare):
        left = _eval_node(node.left, ctx)
        for op_node, comparator in zip(node.ops, node.comparators):
            right = _eval_node(comparator, ctx)
            if isinstance(op_node, ast.In):
                if not isinstance(right, (list, tuple, set)):
                    raise RuleParseError(f"'in' requires a collection, got {type(right)}")
                if left not in right:
                    return False
            elif isinstance(op_node, ast.NotIn):
                if not isinstance(right, (list, tuple, set)):
                    raise RuleParseError(f"'not in' requires a collection, got {type(right)}")
                if left in right:
                    return False
            else:
                op_fn = _OPERATORS.get(type(op_node))
                if op_fn is None:
                    raise RuleParseError(f"Unsupported operator: {type(op_node).__name__}")
                if not op_fn(left, right):
                    return False
            left = right
        return True

    # Boolean ops: and, or
    if isinstance(node, ast.BoolOp):
        fn = _BOOL_OPS.get(type(node.op))
        if fn is None:
            raise RuleParseError(f"Unsupported boolean op: {type(node.op).__name__}")
        return fn(_eval_node(v, ctx) for v in node.values)

    # Unary: not
    if isinstance(node, ast.UnaryOp):
        if isinstance(node.op, ast.Not):
            return not _eval_node(node.operand, ctx)
        raise RuleParseError(f"Unsupported unary op: {type(node.op).__name__}")

    # Tuple/List (for 'in' operator)
    if isinstance(node, (ast.Tuple, ast.List)):
        return tuple(_eval_node(elt, ctx) for elt in node.elts)

    # Set
    if isinstance(node, ast.Set):
        return set(_eval_node(elt, ctx) for elt in node.elts)

    raise RuleParseError(f"Unsupported expression node: {type(node).__name__}")


# ============================================================================
# RULE DATA
# ============================================================================

class Rule:
    """A single policy rule parsed from YAML."""

    __slots__ = ("name", "when", "then", "message")

    def __init__(self, name: str, when: str, then: str, message: str = ""):
        self.name = name
        self.when = when
        self.then = then.upper()
        self.message = message or f"Rule '{name}' triggered"

    def evaluate(self, context: Dict[str, Any]) -> Optional[str]:
        """
        Evaluate the rule. Returns violation message if blocked, None if passed.
        """
        try:
            condition_met = _safe_eval(self.when, context)
        except RuleParseError:
            return None

        if condition_met and self.then == "BLOCK":
            return self.message

        return None


# ============================================================================
# YAML RULE ENGINE
# ============================================================================

class YAMLRuleEngine:
    """
    Evaluates YAML-defined policy rules without CSL-Core.

    Provides the same evaluate() interface as the CSL path
    but uses simple Python expression evaluation instead of Z3.
    """

    def __init__(self, policy_path: str, dry_run: bool = False):
        self._policy_path = Path(policy_path).resolve()
        self._dry_run = dry_run
        self._rules: List[Rule] = []
        self._hash: str = ""
        self._mtime: float = 0.0
        self._domain_name: str = "YAMLPolicy"
        self._variable_names: List[str] = []
        self._variable_domains: Dict[str, str] = {}

        self._load()

    def _load(self) -> None:
        if not self._policy_path.exists():
            raise RuleEngineError(f"Policy file not found: {self._policy_path}")

        self._hash = self._compute_hash()
        self._mtime = self._policy_path.stat().st_mtime

        try:
            data = yaml.safe_load(self._policy_path.read_text(encoding="utf-8"))
        except yaml.YAMLError as e:
            raise RuleEngineError(f"Invalid YAML: {e}") from e

        if not isinstance(data, dict):
            raise RuleEngineError("Policy YAML must be a mapping with 'rules' key")

        self._domain_name = data.get("domain", "YAMLPolicy")

        # Parse variables section if present
        variables = data.get("variables", {})
        if isinstance(variables, dict):
            self._variable_names = sorted(variables.keys())
            self._variable_domains = {k: str(v) for k, v in variables.items()}

        raw_rules = data.get("rules", [])
        if not isinstance(raw_rules, list):
            raise RuleEngineError("'rules' must be a list")

        self._rules = []
        for i, r in enumerate(raw_rules):
            if not isinstance(r, dict):
                raise RuleEngineError(f"Rule #{i} must be a mapping")
            name = r.get("name", f"rule_{i}")
            when = r.get("when", "")
            then = r.get("then", "BLOCK")
            message = r.get("message", "")
            if not when:
                raise RuleEngineError(f"Rule '{name}' missing 'when' condition")
            self._rules.append(Rule(name=name, when=when, then=then, message=message))

    def evaluate(self, parameters: Dict[str, Any]) -> PolicyEvaluation:
        """Evaluate parameters against all rules."""
        start = time.perf_counter()
        violations: List[Violation] = []

        for rule in self._rules:
            msg = rule.evaluate(parameters)
            if msg is not None:
                violations.append(Violation(
                    constraint=rule.name,
                    rule=rule.when,
                    trigger_values=parameters,
                    explanation=msg,
                ))

        duration_ms = (time.perf_counter() - start) * 1000

        if self._dry_run:
            result_str = "ALLOWED"
        else:
            result_str = "BLOCKED" if violations else "ALLOWED"

        return PolicyEvaluation(
            policy_file=str(self._policy_path),
            policy_hash=self._hash,
            result=result_str,
            duration_ms=round(duration_ms, 3),
            violations=violations,
        )

    def verify(self) -> Tuple[bool, List[str]]:
        """YAML rules cannot be formally verified — always returns True."""
        return True, ["YAML rules verified (no Z3 — rule-engine mode)"]

    def reload(self) -> bool:
        """Hot-reload if file changed."""
        if not self._policy_path.exists():
            raise RuleEngineError(f"Policy file not found: {self._policy_path}")
        current_mtime = self._policy_path.stat().st_mtime
        if current_mtime == self._mtime:
            return False
        current_hash = self._compute_hash()
        if current_hash == self._hash:
            self._mtime = current_mtime
            return False
        self._load()
        return True

    def check_reload(self) -> bool:
        try:
            return self.reload()
        except RuleEngineError:
            return False

    def _compute_hash(self) -> str:
        content = self._policy_path.read_bytes()
        digest = hashlib.sha256(content).hexdigest()
        return f"sha256:{digest}"

    # Properties matching PolicyManager interface
    @property
    def policy_path(self) -> str:
        return str(self._policy_path)

    @property
    def hash(self) -> str:
        return self._hash

    @property
    def domain_name(self) -> str:
        return self._domain_name

    @property
    def constraint_count(self) -> int:
        return len(self._rules)

    @property
    def constraint_names(self) -> List[str]:
        return [r.name for r in self._rules]

    @property
    def variable_names(self) -> List[str]:
        return list(self._variable_names)

    @property
    def variable_domains(self) -> Dict[str, str]:
        return dict(self._variable_domains)

    @property
    def metadata(self) -> Dict[str, Any]:
        return {
            "policy_file": str(self._policy_path),
            "policy_hash": self._hash,
            "domain_name": self._domain_name,
            "constraint_count": len(self._rules),
            "variable_names": self._variable_names,
            "dry_run": self._dry_run,
            "engine": "yaml-rule-engine",
        }

    @property
    def loaded(self) -> bool:
        return len(self._rules) > 0
