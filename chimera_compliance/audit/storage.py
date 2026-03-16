"""
chimera-compliance — Audit Storage

File-based storage for DecisionAuditRecords.

Each record is stored as a JSON file named by decision_id:
    audit_logs/dec_a1b2c3d4e5f6.json

Provides:
  - save_record(): Write record to disk (JSON)
  - load_record(): Read single record by decision_id
  - load_all_records(): Scan directory, load all records
  - enforce_retention(): Delete records older than N days (Art. 19)
"""

from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import List, Optional

from ..models import DecisionAuditRecord


# ============================================================================
# ERRORS
# ============================================================================

class AuditStorageError(Exception):
    """Raised when audit storage operations fail."""
    pass


# ============================================================================
# DEFAULT PATHS
# ============================================================================

DEFAULT_AUDIT_DIR = "./audit_logs"


# ============================================================================
# SAVE
# ============================================================================

def save_record(
    record: DecisionAuditRecord,
    audit_dir: str = DEFAULT_AUDIT_DIR,
    also_save_html: bool = False,
) -> str:
    """
    Save a DecisionAuditRecord as a JSON file.

    Args:
        record: The audit record to save
        audit_dir: Directory to store audit files
        also_save_html: If True, also generate and save an HTML report

    Returns:
        Path to the saved JSON file

    Raises:
        AuditStorageError: If the file cannot be written
    """
    dir_path = Path(audit_dir)
    try:
        dir_path.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        raise AuditStorageError(f"Cannot create audit directory {audit_dir}: {e}") from e

    filename = f"{record.decision_id}.json"
    filepath = dir_path / filename

    try:
        json_str = record.to_json(indent=2)
        filepath.write_text(json_str, encoding="utf-8")
    except (OSError, TypeError) as e:
        raise AuditStorageError(f"Cannot write audit record to {filepath}: {e}") from e

    # Optionally save HTML report alongside JSON
    if also_save_html:
        try:
            from .html_report import generate_html
            html_content = generate_html(record)
            html_path = dir_path / f"{record.decision_id}.html"
            html_path.write_text(html_content, encoding="utf-8")
        except Exception:
            pass  # HTML generation is best-effort

    return str(filepath)


# ============================================================================
# LOAD
# ============================================================================

def load_record(
    decision_id: str,
    audit_dir: str = DEFAULT_AUDIT_DIR,
) -> DecisionAuditRecord:
    """
    Load a single DecisionAuditRecord by decision_id.

    Args:
        decision_id: The decision ID (e.g. "dec_a1b2c3d4e5f6")
        audit_dir: Directory containing audit files

    Returns:
        Deserialized DecisionAuditRecord

    Raises:
        AuditStorageError: If the file doesn't exist or is corrupt
    """
    filepath = Path(audit_dir) / f"{decision_id}.json"

    if not filepath.exists():
        raise AuditStorageError(
            f"Audit record not found: {filepath}"
        )

    try:
        json_str = filepath.read_text(encoding="utf-8")
        return DecisionAuditRecord.from_json(json_str)
    except json.JSONDecodeError as e:
        raise AuditStorageError(f"Corrupt audit record {filepath}: {e}") from e
    except (KeyError, TypeError) as e:
        raise AuditStorageError(f"Invalid audit record format in {filepath}: {e}") from e


def load_all_records(
    audit_dir: str = DEFAULT_AUDIT_DIR,
) -> List[DecisionAuditRecord]:
    """
    Load all DecisionAuditRecords from the audit directory.

    Skips corrupt files (logs warning to stderr).

    Returns:
        List of records sorted by timestamp (newest first)
    """
    dir_path = Path(audit_dir)
    if not dir_path.exists():
        return []

    records: List[DecisionAuditRecord] = []
    for filepath in sorted(dir_path.glob("dec_*.json")):
        try:
            json_str = filepath.read_text(encoding="utf-8")
            record = DecisionAuditRecord.from_json(json_str)
            records.append(record)
        except Exception:
            # Skip corrupt files — don't crash the query pipeline
            continue

    # Sort newest first
    records.sort(key=lambda r: r.timestamp, reverse=True)
    return records


# ============================================================================
# RETENTION (Art. 19)
# ============================================================================

def enforce_retention(
    audit_dir: str = DEFAULT_AUDIT_DIR,
    retention_days: int = 90,
) -> int:
    """
    Delete audit records older than retention_days.

    EU AI Act Art. 19 requires log retention for a defined period.
    After that period, records should be cleaned up.

    Args:
        audit_dir: Directory containing audit files
        retention_days: Maximum age in days (default: 90)

    Returns:
        Number of records deleted
    """
    dir_path = Path(audit_dir)
    if not dir_path.exists():
        return 0

    # Clamp retention to tier limits
    try:
        from ..licensing import get_license, LicenseTier
        lic = get_license()
        if lic.tier == LicenseTier.FREE:
            retention_days = min(retention_days, 7)
        elif lic.tier == LicenseTier.PRO:
            retention_days = min(retention_days, 90)
        # Enterprise: unlimited (no clamp)
    except Exception:
        pass  # Graceful fallback

    cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)
    deleted = 0

    for filepath in dir_path.glob("dec_*.json"):
        try:
            # Use file modification time as proxy for record age
            mtime = datetime.fromtimestamp(filepath.stat().st_mtime, tz=timezone.utc)
            if mtime < cutoff:
                # Delete JSON and corresponding HTML if it exists
                filepath.unlink()
                html_path = filepath.with_suffix(".html")
                if html_path.exists():
                    html_path.unlink()
                deleted += 1
        except OSError:
            continue

    return deleted
