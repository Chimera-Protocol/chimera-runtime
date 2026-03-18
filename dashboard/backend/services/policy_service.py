"""
Policy Service — wraps chimera_runtime.policy.PolicyManager for the dashboard.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from chimera_runtime.policy import PolicyManager, PolicyError, CSL_CORE_AVAILABLE


class PolicyService:
    """Wraps PolicyManager for the dashboard API."""

    def __init__(self, policies_dir: str = "./policies"):
        self._policies_dir = Path(policies_dir)
        self._managers: Dict[str, PolicyManager] = {}

    # ========================================================================
    # LIST ALL POLICIES
    # ========================================================================

    def list_policies(self) -> List[Dict[str, Any]]:
        """List all policy files in the policies directory."""
        if not self._policies_dir.exists():
            return []

        policies = []
        for f in sorted(self._policies_dir.iterdir()):
            if f.suffix.lower() in (".csl", ".yaml", ".yml"):
                try:
                    pm = self._get_manager(f.name)
                    policies.append({
                        "filename": f.name,
                        "domain_name": pm.domain_name,
                        "constraint_count": pm.constraint_count,
                        "backend": pm.backend,
                        "hash": pm.hash,
                        "loaded": pm.loaded,
                    })
                except PolicyError:
                    policies.append({
                        "filename": f.name,
                        "domain_name": "Error",
                        "constraint_count": 0,
                        "backend": "unknown",
                        "hash": "",
                        "loaded": False,
                        "error": True,
                    })
        return policies

    # ========================================================================
    # SINGLE POLICY DETAIL
    # ========================================================================

    def get_policy(self, filename: str) -> Dict[str, Any]:
        """Get detailed policy information."""
        pm = self._get_manager(filename)
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
        }

    # ========================================================================
    # VERIFY
    # ========================================================================

    def verify_policy(self, filename: str) -> Dict[str, Any]:
        """Run verification (Z3 for CSL, syntax for YAML) with real Z3 per-constraint analysis."""
        import time

        pm = self._get_manager(filename)
        is_csl = pm.backend == "csl-core"
        engine = "z3" if is_csl else "syntax"

        if is_csl and CSL_CORE_AVAILABLE:
            return self._verify_csl_z3(filename, pm)

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

    def _verify_csl_z3(self, filename: str, pm) -> Dict[str, Any]:
        """Run real Z3 verification with per-constraint reachability analysis."""
        import time
        from chimera_core.language.parser import CSLParser
        from chimera_core.engines.z3_engine.verifier import LogicVerifier

        filepath = self._policies_dir / filename
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

        # Extract per-constraint reachability from Z3 issues
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

        # Build per-constraint results from real Z3 data
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
        self, filename: str, parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Evaluate parameters against a policy."""
        pm = self._get_manager(filename)
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
    # CREATE / RAW CONTENT (Feature 2 — Policy Editor)
    # ========================================================================

    def create_policy(self, filename: str, content: str) -> Dict[str, Any]:
        """Create a new policy file. Validates filename, writes to disk."""
        # Security: prevent path traversal
        if "/" in filename or "\\" in filename or ".." in filename:
            raise PolicyError("Invalid filename: path traversal not allowed")

        # Ensure correct extension
        if not any(filename.endswith(ext) for ext in (".csl", ".yaml", ".yml")):
            raise PolicyError("Filename must end with .csl, .yaml, or .yml")

        filepath = self._policies_dir / filename
        if filepath.exists():
            raise PolicyError(f"Policy file already exists: {filename}")

        # Write file
        filepath.write_text(content, encoding="utf-8")

        # Invalidate cache
        self._managers.pop(filename, None)

        # Try to load and validate
        try:
            pm = self._get_manager(filename)
            return {
                "filename": filename,
                "status": "created",
                "message": f"Policy '{pm.domain_name}' created with {pm.constraint_count} constraints",
            }
        except PolicyError as e:
            # File was written but has errors — still return success with warning
            return {
                "filename": filename,
                "status": "created_with_warnings",
                "message": f"Policy file saved but has validation issues: {e}",
            }

    def get_policy_content(self, filename: str) -> Dict[str, str]:
        """Get raw policy file content."""
        if "/" in filename or "\\" in filename or ".." in filename:
            raise PolicyError("Invalid filename")

        filepath = self._policies_dir / filename
        if not filepath.exists():
            raise PolicyError(f"Policy file not found: {filename}")

        return {
            "filename": filename,
            "content": filepath.read_text(encoding="utf-8"),
        }

    # ========================================================================
    # INTERNAL
    # ========================================================================

    def _get_manager(self, filename: str) -> PolicyManager:
        """Get or create a PolicyManager for a policy file."""
        if filename not in self._managers:
            filepath = self._policies_dir / filename
            if not filepath.exists():
                raise PolicyError(f"Policy file not found: {filename}")
            self._managers[filename] = PolicyManager(str(filepath), auto_verify=False)
        return self._managers[filename]
