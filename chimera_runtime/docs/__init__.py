"""chimera-runtime — Documentation Generator

EU AI Act Annex IV technical documentation auto-generation.
"""

from .generator import (
    AnnexIVGenerator,
    DocsGeneratorError,
    AUTO_SECTIONS,
    MANUAL_SECTIONS,
    SECTION_TITLES,
)

__all__ = [
    "AnnexIVGenerator",
    "DocsGeneratorError",
    "AUTO_SECTIONS",
    "MANUAL_SECTIONS",
    "SECTION_TITLES",
]
