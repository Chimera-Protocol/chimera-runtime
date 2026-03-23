"""
Audit Uploader — async upload of audit records to Chimera Runtime Dashboard.

Uses stdlib only (urllib.request) to avoid adding dependencies.
Runs in a daemon thread so it never blocks the main pipeline.
Pro+ tier only — free tier users should not initialize this.
"""

from __future__ import annotations

import json
import logging
import queue
import threading
import time
from typing import Optional
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

logger = logging.getLogger("chimera_runtime.audit.uploader")


class AuditUploader:
    """Background uploader for audit records to the Chimera Runtime Dashboard.

    Usage:
        uploader = AuditUploader(api_key="chm_xxx", dashboard_url="https://api-runtime.chimera-protocol.com/api/v1")
        uploader.start()
        uploader.enqueue(record.to_dict())  # non-blocking
        # ... on shutdown:
        uploader.stop()
    """

    def __init__(
        self,
        api_key: str,
        dashboard_url: str,
        max_retries: int = 3,
        batch_size: int = 10,
        flush_interval: float = 5.0,
        queue_size: int = 1000,
    ):
        self._api_key = api_key
        self._base_url = dashboard_url.rstrip("/")
        self._max_retries = max_retries
        self._batch_size = batch_size
        self._flush_interval = flush_interval
        self._queue: queue.Queue = queue.Queue(maxsize=queue_size)
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._started = False

    def start(self) -> None:
        """Start the background upload thread."""
        if self._started:
            return
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._worker,
            name="chimera-audit-uploader",
            daemon=True,
        )
        self._thread.start()
        self._started = True
        logger.debug("Audit uploader started → %s", self._base_url)

    def stop(self, timeout: float = 10.0) -> None:
        """Stop the upload thread, flushing remaining records."""
        if not self._started:
            return
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=timeout)
        self._started = False
        logger.debug("Audit uploader stopped")

    def enqueue(self, record_dict: dict) -> bool:
        """Add a record to the upload queue. Non-blocking, returns False if queue full."""
        try:
            self._queue.put_nowait(record_dict)
            return True
        except queue.Full:
            logger.warning("Upload queue full, dropping record %s", record_dict.get("decision_id", "?"))
            return False

    def _worker(self) -> None:
        """Background worker: batches records and uploads them."""
        batch = []
        last_flush = time.time()

        while not self._stop_event.is_set():
            # Collect records into batch
            try:
                record = self._queue.get(timeout=1.0)
                batch.append(record)
            except queue.Empty:
                pass

            # Flush when batch is full or interval elapsed
            now = time.time()
            should_flush = (
                len(batch) >= self._batch_size
                or (batch and now - last_flush >= self._flush_interval)
            )

            if should_flush:
                self._flush(batch)
                batch = []
                last_flush = now

        # Final flush on shutdown
        while not self._queue.empty():
            try:
                batch.append(self._queue.get_nowait())
            except queue.Empty:
                break
        if batch:
            self._flush(batch)

    def _flush(self, batch: list) -> None:
        """Upload a batch of records."""
        if not batch:
            return

        if len(batch) == 1:
            self._upload_single(batch[0])
        else:
            self._upload_batch(batch)

    def _upload_single(self, record: dict) -> bool:
        """Upload a single record with retries."""
        url = f"{self._base_url}/ingest/"
        data = json.dumps(record, default=str).encode("utf-8")

        for attempt in range(self._max_retries):
            try:
                req = Request(
                    url,
                    data=data,
                    headers={
                        "Content-Type": "application/json",
                        "X-API-Key": self._api_key,
                    },
                    method="POST",
                )
                with urlopen(req, timeout=30) as resp:
                    if resp.status in (200, 201):
                        logger.debug("Uploaded %s", record.get("decision_id", "?"))
                        return True
            except HTTPError as e:
                if e.code == 429:
                    # Rate limited — back off longer
                    wait = min(30, 2 ** (attempt + 2))
                    logger.warning("Rate limited, waiting %ds", wait)
                    time.sleep(wait)
                elif e.code in (401, 403):
                    logger.error("Auth error %d: %s", e.code, e.read().decode()[:200])
                    return False  # Don't retry auth errors
                else:
                    logger.warning("Upload error %d (attempt %d/%d)", e.code, attempt + 1, self._max_retries)
            except (URLError, OSError) as e:
                logger.warning("Network error (attempt %d/%d): %s", attempt + 1, self._max_retries, e)

            # Exponential backoff: 1s, 2s, 4s
            if attempt < self._max_retries - 1:
                time.sleep(2 ** attempt)

        logger.error("Failed to upload %s after %d attempts", record.get("decision_id", "?"), self._max_retries)
        return False

    def _upload_batch(self, records: list) -> bool:
        """Upload a batch of records with retries."""
        url = f"{self._base_url}/ingest/batch/"
        data = json.dumps({"records": records}, default=str).encode("utf-8")

        for attempt in range(self._max_retries):
            try:
                req = Request(
                    url,
                    data=data,
                    headers={
                        "Content-Type": "application/json",
                        "X-API-Key": self._api_key,
                    },
                    method="POST",
                )
                with urlopen(req, timeout=60) as resp:
                    if resp.status in (200, 201):
                        result = json.loads(resp.read().decode("utf-8"))
                        logger.debug("Batch uploaded: %d ingested, %d errors", result.get("ingested", 0), len(result.get("errors", [])))
                        return True
            except HTTPError as e:
                if e.code in (401, 403):
                    logger.error("Auth error %d", e.code)
                    return False
                logger.warning("Batch upload error %d (attempt %d/%d)", e.code, attempt + 1, self._max_retries)
            except (URLError, OSError) as e:
                logger.warning("Network error (attempt %d/%d): %s", attempt + 1, self._max_retries, e)

            if attempt < self._max_retries - 1:
                time.sleep(2 ** attempt)

        # Fallback: try one by one
        logger.warning("Batch upload failed, trying individual uploads")
        for record in records:
            self._upload_single(record)
        return False


# Module-level singleton
_uploader: Optional[AuditUploader] = None


def get_uploader() -> Optional[AuditUploader]:
    """Get the global uploader instance (if configured)."""
    return _uploader


def init_uploader(api_key: str, dashboard_url: str) -> AuditUploader:
    """Initialize and start the global uploader."""
    global _uploader
    if _uploader is not None:
        _uploader.stop()
    _uploader = AuditUploader(api_key=api_key, dashboard_url=dashboard_url)
    _uploader.start()
    return _uploader


def shutdown_uploader() -> None:
    """Stop the global uploader."""
    global _uploader
    if _uploader is not None:
        _uploader.stop()
        _uploader = None
