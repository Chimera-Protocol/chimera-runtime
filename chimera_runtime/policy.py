"""
chimera-runtime — Policy Manager

Unified interface for policy evaluation supporting two backends:
  1. CSL-Core (optional) — Z3 formal verification via .csl files
  2. YAML Rule Engine (built-in) — lightweight rule evaluation via .yaml files

Install CSL-Core for Z3 support: pip install chimera-runtime[csl]
"""

from __future__ import annotations

import hashlib
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .models import PolicyEvaluation, Violation

# --- CSL-Core optional import ---
try:
    from chimera_core import load_guard, RuntimeConfig
    from chimera_core.runtime import ChimeraGuard, GuardResult
    CSL_CORE_AVAILABLE = True
except ImportError:
    CSL_CORE_AVAILABLE = False


# ============================================================================
# ERRORS
# ============================================================================

class PolicyError(Exception):
    """Raised when a policy cannot be loaded, verified, or evaluated."""
    pass


class PolicyFileNotFoundError(PolicyError):
    """Raised when the policy file does not exist."""
    pass


class PolicyVerificationError(PolicyError):
    """Raised when Z3 verification fails."""
    pass


# ============================================================================
# POLICY MANAGER
# ============================================================================

class PolicyManager:
    """
    Manages the lifecycle of a policy for chimera-runtime.

    Automatically selects the backend based on file extension:
      - .csl → CSL-Core with Z3 formal verification (requires csl-core)
      - .yaml / .yml → Built-in YAML rule engine

    Usage:
        pm = PolicyManager("./policies/governance.csl")
        eval_result = pm.evaluate({"amount": 240000, "role": "MANAGER"})

        pm = PolicyManager("./policies/rules.yaml")
        eval_result = pm.evaluate({"amount": 240000, "role": "MANAGER"})
    """

    def __init__(
        self,
        policy_path: str,
        auto_verify: bool = True,
        dry_run: bool = False,
    ):
        self._policy_path = Path(policy_path).resolve()
        self._auto_verify = auto_verify
        self._dry_run = dry_run
        self._engine: Optional[Any] = None
        self._backend: str = "unknown"

        # CSL-Core backend state
        self._guard: Optional[Any] = None
        self._hash: str = ""
        self._mtime: float = 0.0
        self._domain_name: str = ""
        self._constraint_count: int = 0
        self._constraint_names: List[str] = []
        self._variable_names: List[str] = []
        self._variable_domains: Dict[str, str] = {}

        self._load()

    # ========================================================================
    # PUBLIC API
    # ========================================================================

    def evaluate(self, parameters: Dict[str, Any]) -> PolicyEvaluation:
        """
        Evaluate candidate parameters against the loaded policy.

        Works identically regardless of backend (CSL or YAML).
        """
        if self._backend == "yaml":
            if self._engine is None:
                raise PolicyError("No policy loaded")
            return self._engine.evaluate(parameters)

        if self._backend == "csl":
            return self._evaluate_csl(parameters)

        raise PolicyError("No policy loaded")

    def verify(self) -> Tuple[bool, List[str]]:
        """
        Run verification on the loaded policy.

        CSL backend: Z3 formal verification
        YAML backend: syntax validation (always passes)
        """
        if self._backend == "yaml":
            return self._engine.verify()

        if not CSL_CORE_AVAILABLE:
            return True, ["CSL-Core not installed — skipping Z3 verification"]

        try:
            _ = load_guard(str(self._policy_path))
            return True, []
        except Exception as e:
            return False, [str(e)]

    def reload(self) -> bool:
        """
        Hot-reload policy if the file has changed on disk.
        Returns True if reloaded, False if unchanged.
        """
        if self._backend == "yaml":
            return self._engine.reload()

        if not self._policy_path.exists():
            raise PolicyFileNotFoundError(
                f"Policy file no longer exists: {self._policy_path}"
            )

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
        """Non-throwing reload. Returns True if reloaded, False otherwise.

        Hot-reload requires PRO tier. Free tier must restart to pick up changes.
        """
        from .licensing import check_tier
        if not check_tier("pro"):
            return False  # Free tier: no hot-reload, restart required
        try:
            return self.reload()
        except (PolicyError, Exception):
            return False

    # ========================================================================
    # PROPERTIES
    # ========================================================================

    @property
    def policy_path(self) -> str:
        return str(self._policy_path)

    @property
    def hash(self) -> str:
        if self._backend == "yaml":
            return self._engine.hash
        return self._hash

    @property
    def domain_name(self) -> str:
        if self._backend == "yaml":
            return self._engine.domain_name
        return self._domain_name

    @property
    def constraint_count(self) -> int:
        if self._backend == "yaml":
            return self._engine.constraint_count
        return self._constraint_count

    @property
    def constraint_names(self) -> List[str]:
        if self._backend == "yaml":
            return self._engine.constraint_names
        return list(self._constraint_names)

    @property
    def variable_names(self) -> List[str]:
        if self._backend == "yaml":
            return self._engine.variable_names
        return list(self._variable_names)

    @property
    def variable_domains(self) -> Dict[str, str]:
        if self._backend == "yaml":
            return self._engine.variable_domains
        return dict(self._variable_domains)

    @property
    def metadata(self) -> Dict[str, Any]:
        if self._backend == "yaml":
            return self._engine.metadata
        return {
            "policy_file": str(self._policy_path),
            "policy_hash": self._hash,
            "domain_name": self._domain_name,
            "constraint_count": self._constraint_count,
            "variable_names": self._variable_names,
            "dry_run": self._dry_run,
            "engine": "csl-core",
        }

    @property
    def loaded(self) -> bool:
        if self._backend == "yaml":
            return self._engine.loaded
        return self._guard is not None

    @property
    def backend(self) -> str:
        """Returns 'csl-core' or 'yaml-rule-engine'."""
        return "csl-core" if self._backend == "csl" else "yaml-rule-engine"

    # ========================================================================
    # INTERNAL — LOADING
    # ========================================================================

    def _load(self) -> None:
        if not self._policy_path.exists():
            raise PolicyFileNotFoundError(
                f"Policy file not found: {self._policy_path}"
            )

        suffix = self._policy_path.suffix.lower()

        if suffix in (".yaml", ".yml"):
            self._load_yaml()
        elif suffix == ".csl":
            self._load_csl()
        else:
            raise PolicyError(
                f"Unsupported policy format: {suffix}. Use .csl or .yaml"
            )

    def _load_yaml(self) -> None:
        from .rules import YAMLRuleEngine, RuleEngineError
        try:
            self._engine = YAMLRuleEngine(
                str(self._policy_path), dry_run=self._dry_run
            )
            self._backend = "yaml"
        except RuleEngineError as e:
            raise PolicyError(f"Failed to load YAML policy: {e}") from e

    def _load_csl(self) -> None:
        if not CSL_CORE_AVAILABLE:
            raise PolicyError(
                f"CSL-Core is required for .csl policies but is not installed.\n"
                f"Install it with: pip install chimera-runtime[csl]"
            )

        self._hash = self._compute_hash()
        self._mtime = self._policy_path.stat().st_mtime

        runtime_config = RuntimeConfig(
            raise_on_block=False,
            collect_all_violations=True,
            dry_run=self._dry_run,
        )

        try:
            self._guard = load_guard(str(self._policy_path), config=runtime_config)
        except Exception as e:
            raise PolicyError(
                f"Failed to load policy {self._policy_path}: {e}"
            ) from e

        self._backend = "csl"
        self._extract_metadata()

    # ========================================================================
    # INTERNAL — CSL-CORE SPECIFICS
    # ========================================================================

    def _evaluate_csl(self, parameters: Dict[str, Any]) -> PolicyEvaluation:
        if self._guard is None:
            raise PolicyError("No CSL policy loaded")

        try:
            start = time.perf_counter()
            guard_result = self._guard.verify(parameters)
            duration_ms = (time.perf_counter() - start) * 1000
        except Exception as e:
            raise PolicyError(f"Policy evaluation failed: {e}") from e

        violations = self._map_violations(guard_result, parameters)
        result_str = "ALLOWED" if guard_result.allowed else "BLOCKED"

        return PolicyEvaluation(
            policy_file=str(self._policy_path),
            policy_hash=self._hash,
            result=result_str,
            duration_ms=round(duration_ms, 3),
            violations=violations,
        )

    def _extract_metadata(self) -> None:
        if self._guard is None:
            return

        cc = getattr(self._guard, "constitution", None) or \
             getattr(self._guard, "compiled", None) or \
             getattr(self._guard, "compiled_constitution", None) or \
             getattr(self._guard, "_compiled", None)

        if cc is not None:
            self._domain_name = getattr(cc, "domain_name", "Unknown")
            constraints = getattr(cc, "constraints", [])
            self._constraint_count = len(constraints)
            self._constraint_names = [
                getattr(c, "name", f"constraint_{i}")
                for i, c in enumerate(constraints)
            ]
            var_domains = getattr(cc, "variable_domains", {})
            self._variable_names = sorted(var_domains.keys())
            self._variable_domains = {k: str(v) for k, v in var_domains.items()}
        else:
            self._domain_name = getattr(self._guard, "domain_name", "Unknown")
            self._constraint_count = 0
            self._constraint_names = []
            self._variable_names = []
            self._variable_domains = {}

    def _compute_hash(self) -> str:
        try:
            content = self._policy_path.read_bytes()
            digest = hashlib.sha256(content).hexdigest()
            return f"sha256:{digest}"
        except OSError as e:
            raise PolicyError(f"Cannot read policy file for hashing: {e}") from e

    def _map_violations(
        self, guard_result: Any, parameters: Dict[str, Any]
    ) -> List[Violation]:
        violations: List[Violation] = []
        raw_violations = guard_result.violations or []
        triggered_rules = guard_result.triggered_rule_ids or []

        for i, raw_msg in enumerate(raw_violations):
            constraint_name = self._parse_constraint_name(raw_msg, triggered_rules, i)
            violations.append(Violation(
                constraint=constraint_name,
                rule=raw_msg,
                trigger_values=parameters,
                explanation=raw_msg,
            ))

        return violations

    def _parse_constraint_name(
        self, raw_msg: str, triggered_rules: List[str], index: int
    ) -> str:
        if index < len(triggered_rules):
            return triggered_rules[index]

        if "Constraint '" in raw_msg:
            start = raw_msg.index("Constraint '") + len("Constraint '")
            end = raw_msg.index("'", start)
            return raw_msg[start:end]

        return f"constraint_{index}"
