"""chimera-compliance — Audit Pipeline

Complete audit trail for every AI decision:
  - recorder: Build audit records from agent state
  - storage: Persist/load records as JSON files
  - query: Filter, aggregate, and export audit data
  - html_report: Generate self-contained HTML reports
"""

from .recorder import build_audit_record
from .storage import (
    save_record,
    load_record,
    load_all_records,
    enforce_retention,
    AuditStorageError,
)
from .query import AuditQuery, AuditStats
from .html_report import generate_html

__all__ = [
    "build_audit_record",
    "save_record",
    "load_record",
    "load_all_records",
    "enforce_retention",
    "AuditStorageError",
    "AuditQuery",
    "AuditStats",
    "generate_html",
]
