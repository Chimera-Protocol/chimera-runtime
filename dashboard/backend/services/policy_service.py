"""
Policy Service — wraps chimera_runtime.policy.PolicyManager for the dashboard.

Hybrid model:
  - Global policies: shared read-only templates in the main policies_dir
  - User policies: per-user policies in policies_dir/{user_id}/

Users see both global (as templates) and their own policies.
Create/edit only writes to user's directory.
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional

from chimera_runtime.policy import PolicyManager, PolicyError, CSL_CORE_AVAILABLE


class PolicyService:
    """Wraps PolicyManager for the dashboard API."""

    def __init__(self, policies_dir: str = "./policies"):
        self._policies_dir = Path(policies_dir)
        self._managers: Dict[str, PolicyManager] = {}

    # ========================================================================
    # USER DIR HELPERS
    # ========================================================================

    def _user_dir(self, user_id: int) -> Path:
        """Get/create user-specific policy directory."""
        d = self._policies_dir / str(user_id)
        d.mkdir(parents=True, exist_ok=True)
        return d

    def _resolve_policy_path(self, filename: str, user_id: Optional[int] = None) -> Path:
        """Resolve policy file path: user dir first, then global."""
        if user_id is not None:
            user_path = self._user_dir(user_id) / filename
            if user_path.exists():
                return user_path

        global_path = self._policies_dir / filename
        if global_path.exists():
            return global_path

        raise PolicyError(f"Policy file not found: {filename}")

    def _is_global(self, filepath: Path) -> bool:
        """Check if a policy file is in the global directory (not user-specific)."""
        return filepath.parent == self._policies_dir

    # ========================================================================
    # LIST ALL POLICIES (global + user)
    # ========================================================================

    def list_policies(self, user_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """List policies: global templates + user's own policies."""
        policies = []
        seen_filenames = set()

        # User policies first (take priority)
        if user_id is not None:
            user_dir = self._user_dir(user_id)
            for f in sorted(user_dir.iterdir()):
                if f.suffix.lower() in (".csl", ".yaml", ".yml"):
                    seen_filenames.add(f.name)
                    policies.append(self._policy_summary(f, is_global=False))

        # Global policies (skip if user has same filename)
        if self._policies_dir.exists():
            for f in sorted(self._policies_dir.iterdir()):
                if f.is_file() and f.suffix.lower() in (".csl", ".yaml", ".yml"):
                    if f.name not in seen_filenames:
                        policies.append(self._policy_summary(f, is_global=True))

        return policies

    def _policy_summary(self, filepath: Path, is_global: bool = False) -> Dict[str, Any]:
        """Build summary dict for a policy file."""
        try:
            pm = self._get_manager_from_path(filepath)
            return {
                "filename": filepath.name,
                "domain_name": pm.domain_name,
                "constraint_count": pm.constraint_count,
                "backend": pm.backend,
                "hash": pm.hash,
                "loaded": pm.loaded,
                "is_global": is_global,
            }
        except (PolicyError, Exception):
            return {
                "filename": filepath.name,
                "domain_name": "Error",
                "constraint_count": 0,
                "backend": "unknown",
                "hash": "",
                "loaded": False,
                "is_global": is_global,
                "error": True,
            }

    # ========================================================================
    # SINGLE POLICY DETAIL
    # ========================================================================

    def get_policy(self, filename: str, user_id: Optional[int] = None) -> Dict[str, Any]:
        """Get detailed policy information."""
        filepath = self._resolve_policy_path(filename, user_id)
        pm = self._get_manager_from_path(filepath)
        return {
            "filename": filename,
            "domain_name": pm.domain_name,
            "constraint_count": pm.constraint_count,
            "constraint_names": pm.constraint_names,
            "variable_names": pm.variable_names,
            "variable_domains": pm.variable_domains,
            "backend": pm.backend,
            "hash": pm.hash,
            "csl_core_available": CSL_CORE_AVAILABLE,
            "metadata": pm.metadata,
            "is_global": self._is_global(filepath),
        }

    # ========================================================================
    # VERIFY
    # ========================================================================

    def verify_policy(self, filename: str, user_id: Optional[int] = None) -> Dict[str, Any]:
        """Run verification (Z3 for CSL, syntax for YAML)."""
        import time

        filepath = self._resolve_policy_path(filename, user_id)
        pm = self._get_manager_from_path(filepath)
        is_csl = pm.backend == "csl-core"
        engine = "z3" if is_csl else "syntax"

        if is_csl and CSL_CORE_AVAILABLE:
            return self._verify_csl_z3(filename, pm, filepath)

        # YAML fallback — syntax check only
        start = time.perf_counter()
        ok, messages = pm.verify()
        elapsed_ms = round((time.perf_counter() - start) * 1000, 2)

        constraint_results = [
            {"name": cname, "reachable": True, "status": "SAT" if ok else "UNKNOWN"}
            for cname in pm.constraint_names
        ]

        return {
            "filename": filename,
            "verified": ok,
            "messages": messages,
            "backend": pm.backend,
            "verification_engine": engine,
            "verification_time_ms": elapsed_ms,
            "constraint_results": constraint_results,
            "csl_core_available": CSL_CORE_AVAILABLE,
        }

    def _verify_csl_z3(self, filename: str, pm, filepath: Path) -> Dict[str, Any]:
        """Run real Z3 verification with per-constraint reachability analysis."""
        import time
        from chimera_core.language.parser import CSLParser
        from chimera_core.engines.z3_engine.verifier import LogicVerifier

        source = filepath.read_text(encoding="utf-8")

        start = time.perf_counter()
        try:
            parser = CSLParser()
            ast = parser.parse(source)
            verifier = LogicVerifier()
            ok, issues = verifier.verify(ast)
        except Exception as e:
            elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
            return {
                "filename": filename,
                "verified": False,
                "messages": [str(e)],
                "backend": pm.backend,
                "verification_engine": "z3",
                "verification_time_ms": elapsed_ms,
                "constraint_results": [],
                "csl_core_available": True,
            }
        elapsed_ms = round((time.perf_counter() - start) * 1000, 2)

        unreachable_rules = set()
        inconsistent_rules = set()
        messages = []
        coverage_meta = {}

        for issue in issues:
            kind = issue.get("kind", "")
            msg = issue.get("message", "")
            rules = issue.get("rules", [])
            severity = issue.get("severity", "info")

            if kind == "UNREACHABLE":
                unreachable_rules.update(rules)
                messages.append(msg)
            elif kind == "INTERNAL_INCONSISTENCY":
                inconsistent_rules.update(rules)
                messages.append(msg)
            elif kind == "PAIRWISE_CONFLICT":
                messages.append(msg)
            elif kind == "COVERAGE":
                coverage_meta = issue.get("meta", {})
            elif kind == "UNSUPPORTED":
                messages.append(msg)
            elif severity in ("error", "warning") and msg:
                messages.append(msg)

        constraint_results = []
        for cname in pm.constraint_names:
            if cname in inconsistent_rules:
                constraint_results.append({"name": cname, "reachable": False, "status": "INCONSISTENT"})
            elif cname in unreachable_rules:
                constraint_results.append({"name": cname, "reachable": False, "status": "UNREACHABLE"})
            else:
                constraint_results.append({"name": cname, "reachable": True, "status": "SAT"})

        return {
            "filename": filename,
            "verified": ok,
            "messages": messages,
            "backend": pm.backend,
            "verification_engine": "z3",
            "verification_time_ms": elapsed_ms,
            "constraint_results": constraint_results,
            "csl_core_available": True,
        }

    # ========================================================================
    # SIMULATE
    # ========================================================================

    def simulate_policy(
        self, filename: str, parameters: Dict[str, Any], user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Evaluate parameters against a policy."""
        filepath = self._resolve_policy_path(filename, user_id)
        pm = self._get_manager_from_path(filepath)
        result = pm.evaluate(parameters)
        return {
            "filename": filename,
            "result": result.result,
            "duration_ms": result.duration_ms,
            "violations": [
                {
                    "constraint": v.constraint,
                    "rule": v.rule,
                    "trigger_values": v.trigger_values,
                    "explanation": v.explanation,
                }
                for v in result.violations
            ],
            "policy_hash": result.policy_hash,
        }

    # ========================================================================
    # CREATE / RAW CONTENT
    # ========================================================================

    def create_policy(self, filename: str, content: str, user_id: Optional[int] = None) -> Dict[str, Any]:
        """Create a new policy file in user's directory."""
        if "/" in filename or "\\" in filename or ".." in filename:
            raise PolicyError("Invalid filename: path traversal not allowed")

        if not any(filename.endswith(ext) for ext in (".csl", ".yaml", ".yml")):
            raise PolicyError("Filename must end with .csl, .yaml, or .yml")

        # Always write to user directory
        if user_id is not None:
            target_dir = self._user_dir(user_id)
        else:
            target_dir = self._policies_dir

        filepath = target_dir / filename
        if filepath.exists():
            raise PolicyError(f"Policy file already exists: {filename}")

        filepath.write_text(content, encoding="utf-8")

        # Invalidate cache
        cache_key = str(filepath)
        self._managers.pop(cache_key, None)

        try:
            pm = self._get_manager_from_path(filepath)
            return {
                "filename": filename,
                "status": "created",
                "message": f"Policy '{pm.domain_name}' created with {pm.constraint_count} constraints",
            }
        except PolicyError as e:
            return {
                "filename": filename,
                "status": "created_with_warnings",
                "message": f"Policy file saved but has validation issues: {e}",
            }

    def get_policy_content(self, filename: str, user_id: Optional[int] = None) -> Dict[str, str]:
        """Get raw policy file content."""
        if "/" in filename or "\\" in filename or ".." in filename:
            raise PolicyError("Invalid filename")

        filepath = self._resolve_policy_path(filename, user_id)
        return {
            "filename": filename,
            "content": filepath.read_text(encoding="utf-8"),
            "is_global": self._is_global(filepath),
        }

    def copy_global_to_user(self, filename: str, user_id: int) -> Dict[str, str]:
        """Copy a global policy to user's directory for customization."""
        global_path = self._policies_dir / filename
        if not global_path.exists():
            raise PolicyError(f"Global policy not found: {filename}")

        user_dir = self._user_dir(user_id)
        user_path = user_dir / filename
        if user_path.exists():
            raise PolicyError(f"You already have a custom version of: {filename}")

        shutil.copy2(global_path, user_path)

        # Invalidate cache
        cache_key = str(user_path)
        self._managers.pop(cache_key, None)

        return {
            "filename": filename,
            "status": "copied",
            "message": f"Global policy '{filename}' copied to your workspace for customization",
        }

    def delete_user_policy(self, filename: str, user_id: int) -> Dict[str, str]:
        """Delete a user's custom policy. Cannot delete global policies."""
        user_path = self._user_dir(user_id) / filename
        if not user_path.exists():
            raise PolicyError(f"Policy not found in your workspace: {filename}")

        user_path.unlink()
        cache_key = str(user_path)
        self._managers.pop(cache_key, None)

        return {"filename": filename, "status": "deleted"}

    # ========================================================================
    # INTERNAL
    # ========================================================================

    def _get_manager(self, filename: str, user_id: Optional[int] = None) -> PolicyManager:
        """Get or create a PolicyManager by filename (resolves path)."""
        filepath = self._resolve_policy_path(filename, user_id)
        return self._get_manager_from_path(filepath)

    def _get_manager_from_path(self, filepath: Path) -> PolicyManager:
        """Get or create a PolicyManager from an absolute path."""
        cache_key = str(filepath)
        if cache_key not in self._managers:
            if not filepath.exists():
                raise PolicyError(f"Policy file not found: {filepath.name}")
            self._managers[cache_key] = PolicyManager(str(filepath), auto_verify=False)
        return self._managers[cache_key]
