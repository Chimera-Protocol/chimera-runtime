"""
Docs API Router — /api/v1/docs/*

Serves markdown documentation files from the repo docs/ folder.
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException

from ..services.docs_service import DocsService

router = APIRouter(prefix="/docs", tags=["docs"])

_service: Optional[DocsService] = None


def init_service(docs_dir: str) -> None:
    global _service
    _service = DocsService(docs_dir)


def get_service() -> DocsService:
    if _service is None:
        raise HTTPException(500, "Docs service not initialized")
    return _service


@router.get("")
async def list_docs():
    """List all documentation files with metadata."""
    svc = get_service()
    return {"docs": svc.list_docs()}


@router.get("/{slug}")
async def get_doc(slug: str):
    """Get a single document's full markdown content."""
    svc = get_service()
    try:
        return svc.get_doc(slug)
    except FileNotFoundError as e:
        raise HTTPException(404, str(e))
