"""
Docs Service — reads markdown files from the repo docs/ folder for the blog/docs section.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Optional


# Category mapping for each doc file
CATEGORIES = {
    "index": "Overview",
    "quickstart": "Getting Started",
    "architecture": "Architecture",
    "policy-guide": "Policy",
    "cli-reference": "CLI",
    "api-reference": "API",
    "integrations": "Integrations",
    "eu-ai-act": "EU AI Act",
    "annex_iv_technical_documentation": "EU AI Act",
}

# Display order
DOC_ORDER = [
    "index",
    "quickstart",
    "architecture",
    "policy-guide",
    "cli-reference",
    "api-reference",
    "integrations",
    "eu-ai-act",
    "annex_iv_technical_documentation",
]


class DocsService:
    """Reads and serves markdown documentation files."""

    def __init__(self, docs_dir: str):
        self._docs_dir = Path(docs_dir)

    def list_docs(self) -> List[Dict[str, Any]]:
        """List all documentation files with metadata."""
        if not self._docs_dir.exists():
            return []

        docs = []
        seen_slugs = set()

        # First pass: add docs in defined order
        for slug in DOC_ORDER:
            filepath = self._docs_dir / f"{slug}.md"
            if filepath.exists() and slug not in seen_slugs:
                seen_slugs.add(slug)
                docs.append(self._extract_metadata(filepath, slug))

        # Second pass: any remaining .md files not in DOC_ORDER
        for filepath in sorted(self._docs_dir.glob("*.md")):
            slug = filepath.stem
            if slug not in seen_slugs:
                seen_slugs.add(slug)
                docs.append(self._extract_metadata(filepath, slug))

        return docs

    def get_doc(self, slug: str) -> Dict[str, Any]:
        """Get a single document's full content."""
        filepath = self._docs_dir / f"{slug}.md"
        if not filepath.exists():
            # Try with underscores
            filepath = self._docs_dir / f"{slug.replace('-', '_')}.md"
        if not filepath.exists():
            raise FileNotFoundError(f"Document not found: {slug}")

        content = filepath.read_text(encoding="utf-8")
        title = self._extract_title(content)
        actual_slug = filepath.stem
        category = CATEGORIES.get(actual_slug, "General")

        return {
            "title": title,
            "slug": actual_slug,
            "category": category,
            "content": content,
        }

    def _extract_metadata(self, filepath: Path, slug: str) -> Dict[str, Any]:
        """Extract title, excerpt, and category from a markdown file."""
        content = filepath.read_text(encoding="utf-8")
        title = self._extract_title(content)
        excerpt = self._extract_excerpt(content)
        category = CATEGORIES.get(slug, "General")

        return {
            "title": title,
            "slug": slug,
            "category": category,
            "excerpt": excerpt,
            "filename": filepath.name,
        }

    @staticmethod
    def _extract_title(content: str) -> str:
        """Extract the first # heading as title."""
        for line in content.split("\n"):
            line = line.strip()
            if line.startswith("# "):
                return line[2:].strip()
        return "Untitled"

    @staticmethod
    def _extract_excerpt(content: str, max_length: int = 200) -> str:
        """Extract the first paragraph after the title as excerpt."""
        lines = content.split("\n")
        in_paragraph = False
        paragraph_lines = []

        for line in lines:
            stripped = line.strip()
            # Skip title and empty lines before first paragraph
            if stripped.startswith("#"):
                in_paragraph = False
                paragraph_lines = []
                continue
            if not stripped and not in_paragraph:
                continue
            if stripped and not stripped.startswith(("```", "---", "|", ">")):
                in_paragraph = True
                paragraph_lines.append(stripped)
            elif in_paragraph and not stripped:
                break  # End of first paragraph

        text = " ".join(paragraph_lines)
        # Remove markdown formatting
        text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)  # links
        text = re.sub(r"[*_`]", "", text)  # bold/italic/code
        if len(text) > max_length:
            text = text[:max_length].rsplit(" ", 1)[0] + "..."
        return text
