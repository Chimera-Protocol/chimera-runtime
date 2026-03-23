"""
Storage Service — abstract storage backend for audit records.

Supports S3 (production) and local filesystem (development/fallback).
All audit data is user-isolated: stored under audits/{user_id}/ prefix.
"""

from __future__ import annotations

import json
import time
import threading
from abc import ABC, abstractmethod
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional


class StorageBackend(ABC):
    """Abstract storage backend for audit records."""

    @abstractmethod
    def save(self, user_id: int, record_dict: dict) -> str:
        """Save an audit record. Returns the storage key."""
        ...

    @abstractmethod
    def load(self, user_id: int, decision_id: str) -> dict:
        """Load a single audit record by decision_id."""
        ...

    @abstractmethod
    def list_records(self, user_id: int) -> List[dict]:
        """List all audit records for a user, newest first."""
        ...

    @abstractmethod
    def delete(self, user_id: int, decision_id: str) -> bool:
        """Delete a single record. Returns True if deleted."""
        ...


class S3StorageBackend(StorageBackend):
    """S3-backed audit storage with per-user isolation and in-memory caching."""

    def __init__(self, bucket: str, region: str = "us-east-1"):
        import boto3
        self._bucket = bucket
        self._s3 = boto3.client("s3", region_name=region)
        # In-memory cache: {user_id: (timestamp, [records])}
        self._cache: Dict[int, tuple] = {}
        self._cache_ttl = 10  # seconds
        self._lock = threading.Lock()

    def save(self, user_id: int, record_dict: dict) -> str:
        decision_id = record_dict.get("decision_id", "unknown")
        key = f"audits/{user_id}/{decision_id}.json"
        self._s3.put_object(
            Bucket=self._bucket,
            Key=key,
            Body=json.dumps(record_dict, default=str),
            ContentType="application/json",
        )
        # Invalidate cache for this user
        with self._lock:
            self._cache.pop(user_id, None)
        return key

    def load(self, user_id: int, decision_id: str) -> dict:
        key = f"audits/{user_id}/{decision_id}.json"
        resp = self._s3.get_object(Bucket=self._bucket, Key=key)
        return json.loads(resp["Body"].read().decode("utf-8"))

    def list_records(self, user_id: int) -> List[dict]:
        # Check cache
        with self._lock:
            cached = self._cache.get(user_id)
            if cached and (time.time() - cached[0]) < self._cache_ttl:
                return cached[1]

        prefix = f"audits/{user_id}/"
        records = []
        paginator = self._s3.get_paginator("list_objects_v2")

        for page in paginator.paginate(Bucket=self._bucket, Prefix=prefix):
            for obj in page.get("Contents", []):
                try:
                    resp = self._s3.get_object(Bucket=self._bucket, Key=obj["Key"])
                    record = json.loads(resp["Body"].read().decode("utf-8"))
                    records.append(record)
                except Exception:
                    continue

        # Sort newest first
        records.sort(key=lambda r: r.get("timestamp", ""), reverse=True)

        # Update cache
        with self._lock:
            self._cache[user_id] = (time.time(), records)

        return records

    def delete(self, user_id: int, decision_id: str) -> bool:
        key = f"audits/{user_id}/{decision_id}.json"
        try:
            self._s3.delete_object(Bucket=self._bucket, Key=key)
            with self._lock:
                self._cache.pop(user_id, None)
            return True
        except Exception:
            return False


class LocalStorageBackend(StorageBackend):
    """Filesystem-backed audit storage for development and fallback.

    Stores records in: {base_dir}/{user_id}/{decision_id}.json
    Also supports an 'admin' mode that reads all records from the flat
    audit_logs/ directory (for backward compatibility / demo).
    """

    def __init__(self, base_dir: str = "./audit_logs"):
        self._base_dir = Path(base_dir)
        self._base_dir.mkdir(parents=True, exist_ok=True)

    def save(self, user_id: int, record_dict: dict) -> str:
        user_dir = self._base_dir / str(user_id)
        user_dir.mkdir(parents=True, exist_ok=True)
        decision_id = record_dict.get("decision_id", "unknown")
        path = user_dir / f"{decision_id}.json"
        path.write_text(json.dumps(record_dict, indent=2, default=str))
        return str(path)

    def load(self, user_id: int, decision_id: str) -> dict:
        # Try user-isolated path first
        user_path = self._base_dir / str(user_id) / f"{decision_id}.json"
        if user_path.exists():
            return json.loads(user_path.read_text())
        # Fallback: flat directory (legacy)
        flat_path = self._base_dir / f"{decision_id}.json"
        if flat_path.exists():
            return json.loads(flat_path.read_text())
        raise FileNotFoundError(f"Record not found: {decision_id}")

    def list_records(self, user_id: int) -> List[dict]:
        records = []

        # User-isolated directory
        user_dir = self._base_dir / str(user_id)
        if user_dir.exists():
            for f in user_dir.glob("dec_*.json"):
                try:
                    records.append(json.loads(f.read_text()))
                except Exception:
                    continue

        # Sort newest first
        records.sort(key=lambda r: r.get("timestamp", ""), reverse=True)
        return records

    def list_all_records(self) -> List[dict]:
        """Admin mode: load ALL records from flat directory (legacy/demo)."""
        records = []
        # Flat files (legacy)
        for f in self._base_dir.glob("dec_*.json"):
            try:
                records.append(json.loads(f.read_text()))
            except Exception:
                continue
        # User-isolated files
        for user_dir in self._base_dir.iterdir():
            if user_dir.is_dir() and user_dir.name.isdigit():
                for f in user_dir.glob("dec_*.json"):
                    try:
                        records.append(json.loads(f.read_text()))
                    except Exception:
                        continue
        records.sort(key=lambda r: r.get("timestamp", ""), reverse=True)
        return records

    def delete(self, user_id: int, decision_id: str) -> bool:
        user_path = self._base_dir / str(user_id) / f"{decision_id}.json"
        if user_path.exists():
            user_path.unlink()
            return True
        return False


def create_storage_backend(backend_type: str, **kwargs) -> StorageBackend:
    """Factory function to create the appropriate storage backend."""
    if backend_type == "s3":
        return S3StorageBackend(
            bucket=kwargs["s3_bucket"],
            region=kwargs.get("s3_region", "us-east-1"),
        )
    else:
        return LocalStorageBackend(
            base_dir=kwargs.get("base_dir", "./audit_logs"),
        )
