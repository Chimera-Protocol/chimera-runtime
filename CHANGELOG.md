# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [3.0.0] — 2026-03-05

### Changed

- **REBRAND** — Package renamed from `chimera-agent` to `chimera-compliance`
  - `pip install chimera-compliance` replaces `pip install chimera-agent`
  - CLI command is now `chimera-compliance` (was `chimera-agent`)
  - Python package is now `chimera_compliance` (was `chimera_agent`)
- **CSL-Core is now optional** — Install with `pip install chimera-compliance[csl]` for Z3 formal verification. Without it, YAML rules provide lightweight policy evaluation.

### Added

- **YAML Rule Engine** — Define policies in YAML without CSL-Core dependency
- **Agent Framework Integrations** — LangChain, LangGraph, LlamaIndex, CrewAI, AutoGen
  - `chimera_compliance.integrations.langchain` — Tool wrapper + callback handler
  - `chimera_compliance.integrations.langgraph` — Node guard + state checkpoint
  - `chimera_compliance.integrations.llamaindex` — Tool spec + callback handler
  - `chimera_compliance.integrations.crewai` — Tool wrapper for crews
  - `chimera_compliance.integrations.autogen` — Agent wrapper
- **E2E Test Command** — `chimera-compliance test [--skip-llm]` validates entire pipeline

### Fixed

- CSL syntax in templates and examples now uses correct braced syntax

## [2.0.0] — 2026-02-26

### Added

- **Core Agent Pipeline** — `ChimeraAgent.decide()` with multi-candidate LLM generation,
  CSL policy verification, retry loop with rejection context, and automatic candidate selection
- **Multi-Provider LLM Layer** — OpenAI, Anthropic, Google Gemini, and Ollama support
  with unified `BaseLLMProvider` interface and automatic variable spec injection
- **Policy Engine** — `PolicyManager` wrapping CSL-Core with hot-reload, dry-run mode,
  variable domain extraction, and constraint name introspection
- **Audit Pipeline** (Art. 12) — Complete `DecisionAuditRecord` for every decision:
  `build_audit_record()`, `save_record()`, `load_record()`, `enforce_retention()`
- **Audit Query** — `AuditQuery.filter()`, `.stats()`, `.top_violations()`, `.export()`
  with support for JSON/compact/stats export formats
- **HTML Explanation Reports** (Art. 86) — Self-contained HTML reports via `generate_html()`
  with reasoning trace, policy details, and compliance timeline
- **Human Oversight** (Art. 14) — `HumanOversight` supporting interactive, SDK callback,
  and auto modes with full override/confirm/halt capabilities
- **Annex IV Documentation Generator** — `AnnexIVGenerator` auto-fills 14/19 sections
  from config, audit logs, and policy metadata using Jinja2 templates
- **Rich CLI** — Beautiful terminal interface powered by Click + Rich:
  `init`, `run`, `stop`, `verify`, `audit`, `policy`, `explain`, `docs`
- **Configuration** — YAML-based `AgentConfig` with `load_config()` / `save_config()`
  and full validation
- **284+ tests** across all modules with comprehensive coverage

### Technical

- CSL-Core ≥0.3.0 with Z3 formal verification
- Policy hash tracking (SHA-256) for change detection
- Deterministic policy gate — mathematical, not probabilistic
- Full type hints (Python 3.10+)
- Apache 2.0 license

## [1.7.0] — 2026-01-15

### Changed

- "Great Unification" — Migrated from SymbolicGuardian to CSL-Core `load_guard`
- Unified policy engine across all agent components

## [1.0.0] — 2025-11-01

### Added

- Initial release with basic agent pipeline
- Single-provider (OpenAI) support
- Simple policy evaluation
- Basic audit logging
