# API Reference

Complete Python SDK reference for chimera-runtime v3.0.0.

---

## Core Classes

### `ChimeraAgent`

The central orchestrator for standalone mode. Manages the full neural → symbolic → audit pipeline.

```python
from chimera_runtime import ChimeraAgent
```

**Constructor:**

```python
ChimeraAgent(
    model: str = "gpt-4o",
    api_key: Optional[str] = None,
    policy: str = "./policies/governance.csl",
    provider: str = "openai",
    temperature: float = 0.7,
    max_retries: int = 3,
    candidates_per_attempt: int = 3,
    dry_run: bool = False,
    oversight: Optional[HumanOversight] = None,
    llm_provider: Optional[BaseLLMProvider] = None,
    policy_manager: Optional[PolicyManager] = None,
    agent_name: str = "chimera-runtime",
    audit_dir: Optional[str] = None,
)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `model` | `str` | `"gpt-4o"` | LLM model identifier |
| `api_key` | `str\|None` | `None` | API key for LLM provider |
| `policy` | `str` | `"./policies/governance.csl"` | Path to policy file (.csl or .yaml) |
| `provider` | `str` | `"openai"` | LLM provider: `"openai"`, `"anthropic"`, `"google"`, `"ollama"` |
| `temperature` | `float` | `0.7` | LLM sampling temperature |
| `max_retries` | `int` | `3` | Max retry attempts when all candidates blocked |
| `candidates_per_attempt` | `int` | `3` | Number of candidates generated per attempt |
| `dry_run` | `bool` | `False` | If True, policy never blocks (shadow mode) |
| `oversight` | `HumanOversight\|None` | `None` | Human oversight controller (defaults to auto-approve) |
| `llm_provider` | `BaseLLMProvider\|None` | `None` | Pre-configured LLM provider (overrides model/api_key/provider) |
| `policy_manager` | `PolicyManager\|None` | `None` | Pre-configured PolicyManager (overrides policy path) |
| `agent_name` | `str` | `"chimera-runtime"` | Name for audit records |
| `audit_dir` | `str\|None` | `None` | Directory to persist audit records (`None` = no auto-save) |

**Methods:**

#### `decide(request, context) → DecisionResult`

Execute the full neuro → symbolic → audit pipeline.

```python
result = agent.decide(
    request="Increase marketing spend by 40%",
    context={"role": "MANAGER", "department": "MARKETING"},
)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `request` | `str` | required | Natural language request |
| `context` | `Dict[str, Any]\|None` | `None` | Additional context (role, session_id, etc.) |

**Returns:** `DecisionResult`

**Raises:**
- `AgentHalted` — if agent has been halted via `halt()`
- `ChimeraAgentError` — if pipeline fails unrecoverably

#### `from_config(config, config_path, **overrides) → ChimeraAgent` (classmethod)

Create from an `AgentConfig` or YAML config file.

```python
agent = ChimeraAgent.from_config(config_path=".chimera/config.yaml")
agent = ChimeraAgent.from_config(config=my_config, model="gpt-4o-mini")
```

#### `halt(reason) → None`

Halt the agent. All subsequent `decide()` calls raise `AgentHalted`. Art. 14 stop mechanism.

#### `resume() → None`

Resume a halted agent.

**Properties:**

| Property | Type | Description |
|----------|------|-------------|
| `is_halted` | `bool` | Whether the agent is halted |
| `decision_count` | `int` | Total decisions made |
| `consecutive_blocks` | `int` | Consecutive blocked decisions |

---

### `PolicyManager`

Unified interface for policy evaluation. Auto-selects backend based on file extension.

```python
from chimera_runtime import PolicyManager
```

**Constructor:**

```python
PolicyManager(
    policy_path: str,
    auto_verify: bool = True,
    dry_run: bool = False,
)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `policy_path` | `str` | required | Path to `.csl`, `.yaml`, or `.yml` file |
| `auto_verify` | `bool` | `True` | Run verification on load |
| `dry_run` | `bool` | `False` | If True, result is always ALLOWED (violations still reported) |

**Methods:**

#### `evaluate(parameters) → PolicyEvaluation`

Evaluate parameters against the policy.

```python
result = pm.evaluate({"amount": 500000, "role": "MANAGER"})
print(result.result)      # "ALLOWED" or "BLOCKED"
print(result.violations)  # List[Violation]
print(result.duration_ms) # float
```

#### `verify() → Tuple[bool, List[str]]`

Run verification. Returns `(success, error_messages)`.

- CSL backend: Z3 formal verification
- YAML backend: syntax validation (always passes)

#### `reload() → bool`

Hot-reload policy if file changed. Returns `True` if reloaded.

**Raises:** `PolicyFileNotFoundError` if file deleted.

#### `check_reload() → bool`

Non-throwing reload. Returns `True` if reloaded, `False` otherwise. Never raises.

**Properties:**

| Property | Type | Description |
|----------|------|-------------|
| `policy_path` | `str` | Absolute path to policy file |
| `hash` | `str` | SHA-256 hash (format: `sha256:<hex>`) |
| `domain_name` | `str` | Policy domain name |
| `constraint_count` | `int` | Number of constraints/rules |
| `constraint_names` | `List[str]` | Names of all constraints/rules |
| `variable_names` | `List[str]` | Sorted list of variable names |
| `variable_domains` | `Dict[str, str]` | Variable name → domain string |
| `metadata` | `Dict[str, Any]` | Full metadata dict |
| `loaded` | `bool` | Whether a policy is loaded |
| `backend` | `str` | `"csl-core"` or `"yaml-rule-engine"` |

---

### `YAMLRuleEngine`

Built-in YAML rule evaluation engine. Used by `PolicyManager` for `.yaml`/`.yml` files.

```python
from chimera_runtime import YAMLRuleEngine
```

**Constructor:**

```python
YAMLRuleEngine(policy_path: str, dry_run: bool = False)
```

**Methods:** Same interface as `PolicyManager` — `evaluate()`, `verify()`, `reload()`, `check_reload()`.

**Properties:** Same as `PolicyManager` — `policy_path`, `hash`, `domain_name`, `constraint_count`, `constraint_names`, `variable_names`, `variable_domains`, `metadata`, `loaded`.

---

### `HumanOversight`

EU AI Act Article 14 compliance: humans can confirm, override, or stop decisions.

```python
from chimera_runtime import HumanOversight
```

**Constructor:**

```python
HumanOversight(
    mode: str = "auto",
    confirm_callback: Optional[Callable] = None,
)
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `mode` | `str` | `"auto"` | `"auto"`, `"interactive"`, or `"sdk"` |
| `confirm_callback` | `Callable\|None` | `None` | Required for `"sdk"` mode. Signature: `(candidate, evaluation) → bool` |

**Modes:**

| Mode | Behavior |
|------|----------|
| `"auto"` | Always approves (no human in loop) |
| `"interactive"` | Blocks on stdin for confirmation |
| `"sdk"` | Calls `confirm_callback` function |

**Methods:**

#### `request_confirmation(candidate, evaluation) → bool`

Ask human for confirmation. Returns `True` if approved.

#### `apply_override(action, reason) → HumanOversightRecord`

Create a human override record. `action` must be `"CONFIRM"`, `"OVERRIDE"`, or `"STOP"`.

---

## Data Models

All models are `@dataclass` with `to_dict()` and `from_dict()` methods.

### `DecisionResult`

Return type from `ChimeraAgent.decide()`.

```python
from chimera_runtime import DecisionResult
```

| Field | Type | Description |
|-------|------|-------------|
| `result` | `str` | `"ALLOWED"`, `"BLOCKED"`, `"HUMAN_OVERRIDE"`, `"INTERRUPTED"` |
| `action` | `str` | Action taken or `"BLOCKED"` |
| `explanation` | `str` | Human-readable explanation |
| `parameters` | `Dict[str, Any]` | Final action parameters (empty if blocked) |
| `audit` | `DecisionAuditRecord` | Full audit record |

**Properties:**

| Property | Type | Description |
|----------|------|-------------|
| `allowed` | `bool` | `result == "ALLOWED"` |
| `blocked` | `bool` | `result == "BLOCKED"` |
| `decision_id` | `str` | From audit record |

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `to_dict()` | `Dict` | Serialize to JSON-ready dict |

---

### `DecisionAuditRecord`

The atomic, immutable audit unit. 8 sections per EU AI Act requirements.

```python
from chimera_runtime import DecisionAuditRecord
```

| Field | Type | Description |
|-------|------|-------------|
| `schema_version` | `str` | Record format version (`"1.0.0"`) |
| `decision_id` | `str` | Unique ID (`dec_<uuid>`) |
| `timestamp` | `str` | ISO 8601 UTC with milliseconds |
| `agent` | `AgentInfo` | Agent identity snapshot |
| `input` | `InputInfo` | Request and parameters |
| `reasoning` | `ReasoningTrace` | All attempts and candidates |
| `decision` | `DecisionInfo` | Final decision details |
| `compliance` | `ComplianceInfo` | EU AI Act compliance checklist |
| `performance` | `PerformanceInfo` | Timing metrics |
| `human_oversight_record` | `HumanOversightRecord\|None` | Human intervention record |

**Methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `to_dict()` | `Dict` | Full JSON-ready dict |
| `to_json(indent=2)` | `str` | Formatted JSON string |
| `to_compact()` | `Dict` | Compact format (essentials only) |
| `to_compact_json()` | `str` | Compact JSON string |
| `from_dict(d)` | `DecisionAuditRecord` | Deserialize from dict |
| `from_json(s)` | `DecisionAuditRecord` | Deserialize from JSON string |

---

### `PolicyEvaluation`

Result of evaluating parameters against a policy.

```python
from chimera_runtime import PolicyEvaluation
```

| Field | Type | Description |
|-------|------|-------------|
| `policy_file` | `str` | Path to policy file |
| `policy_hash` | `str` | SHA-256 hash |
| `result` | `str` | `"ALLOWED"` or `"BLOCKED"` |
| `duration_ms` | `float` | Evaluation time in milliseconds |
| `violations` | `List[Violation]` | List of violations (empty if allowed) |

---

### `Violation`

A single policy violation.

```python
from chimera_runtime import Violation
```

| Field | Type | Description |
|-------|------|-------------|
| `constraint` | `str` | Constraint/rule name |
| `rule` | `str` | Rule expression text |
| `trigger_values` | `Dict[str, Any]` | Values that triggered the violation |
| `explanation` | `str` | Human-readable explanation |

---

### `Candidate`

A single strategy candidate from the LLM.

```python
from chimera_runtime import Candidate
```

| Field | Type | Description |
|-------|------|-------------|
| `candidate_id` | `str` | e.g., `"cand_001"` |
| `strategy` | `str` | Strategy description |
| `llm_reasoning` | `str` | LLM's reasoning |
| `llm_confidence` | `float` | Confidence [0, 1] |
| `parameters` | `Dict[str, Any]` | Structured parameters |
| `policy_evaluation` | `PolicyEvaluation\|None` | Filled after evaluation |

---

### `Attempt`

A single attempt round in the retry loop.

```python
from chimera_runtime import Attempt
```

| Field | Type | Description |
|-------|------|-------------|
| `attempt_number` | `int` | 1-indexed attempt number |
| `candidates` | `List[Candidate]` | Candidates in this round |
| `outcome` | `str` | `"ALL_PASSED"`, `"PARTIAL"`, `"ALL_BLOCKED"` |
| `note` | `str` | Optional explanation |

---

### Config Models

#### `AgentConfig`

Complete agent configuration. Maps to `.chimera/config.yaml`.

```python
from chimera_runtime import AgentConfig
```

| Field | Type | Description |
|-------|------|-------------|
| `agent` | `AgentMetaConfig` | Agent identity (name, version) |
| `llm` | `LLMConfig` | LLM provider settings |
| `policy` | `PolicyConfig` | Policy file path and auto-verify |
| `audit` | `AuditConfig` | Audit output settings |
| `oversight` | `OversightConfig` | Human oversight settings |

#### `LLMConfig`

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `provider` | `str` | `"openai"` | Provider name |
| `model` | `str` | `"gpt-4o"` | Model identifier |
| `temperature` | `float` | `0.7` | Sampling temperature |
| `max_retries` | `int` | `3` | Max retry attempts |
| `candidates_per_attempt` | `int` | `3` | Candidates per attempt |
| `api_key` | `str\|None` | `None` | API key (never serialized to disk) |

#### `PolicyConfig`

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `file` | `str` | `"./policies/governance.csl"` | Policy file path |
| `auto_verify` | `bool` | `True` | Z3/syntax verification on startup |

#### `AuditConfig`

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `enabled` | `bool` | `True` | Enable audit logging |
| `output_dir` | `str` | `"./audit_logs"` | Output directory |
| `format` | `str` | `"json"` | Format: `"json"`, `"compact"`, `"both"` |
| `html_reports` | `bool` | `True` | Generate HTML reports |
| `retention_days` | `int` | `180` | Record retention (Art. 19 minimum) |

#### `OversightConfig`

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `require_confirmation` | `bool` | `False` | Require human confirmation |
| `allow_override` | `bool` | `True` | Allow human override |
| `policy_hot_reload` | `bool` | `True` | Auto-reload policy on change |
| `stop_on_consecutive_blocks` | `int` | `5` | Auto-halt after N consecutive blocks |

---

### Info Models (Audit Sections)

#### `AgentInfo`

| Field | Type | Description |
|-------|------|-------------|
| `name` | `str` | Agent name |
| `version` | `str` | Agent version |
| `csl_core_version` | `str` | CSL-Core version or `"not-installed"` |
| `model` | `str` | LLM model used |
| `model_provider` | `str` | LLM provider |
| `temperature` | `float` | Temperature used |

#### `InputInfo`

| Field | Type | Description |
|-------|------|-------------|
| `raw_request` | `str` | Original request |
| `structured_params` | `Dict[str, Any]` | Parsed parameters |
| `context` | `Dict[str, Any]` | Session/environment context |

#### `ReasoningTrace`

| Field | Type | Description |
|-------|------|-------------|
| `total_candidates` | `int` | Total candidates across all attempts |
| `total_attempts` | `int` | Number of attempts |
| `attempts` | `List[Attempt]` | All attempt rounds |
| `selected_candidate` | `str\|None` | ID of selected candidate |
| `selection_reasoning` | `str` | Why this candidate was chosen |

#### `DecisionInfo`

| Field | Type | Description |
|-------|------|-------------|
| `action_taken` | `str` | Action name |
| `result` | `str` | Decision result |
| `final_parameters` | `Dict[str, Any]` | Parameters of executed action |
| `policy_file` | `str` | Policy file path |
| `policy_hash` | `str` | Policy hash at decision time |

#### `ComplianceInfo`

| Field | Type | Description |
|-------|------|-------------|
| `eu_ai_act` | `Dict[str, bool]` | Article compliance checklist |
| `formal_verification` | `Dict[str, Any]` | Verification engine and result |
| `human_oversight` | `Dict[str, bool]` | Oversight capabilities |

#### `PerformanceInfo`

| Field | Type | Description |
|-------|------|-------------|
| `total_duration_ms` | `float` | Total pipeline time |
| `llm_duration_ms` | `float` | LLM generation time |
| `policy_evaluation_ms` | `float` | Policy evaluation time |
| `audit_generation_ms` | `float` | Audit record build time |

#### `HumanOversightRecord`

| Field | Type | Description |
|-------|------|-------------|
| `action` | `str` | `"CONFIRM"`, `"OVERRIDE"`, `"STOP"` |
| `reason` | `str` | Human's stated reason |
| `override_decision` | `str` | What the human decided |
| `timestamp` | `str` | When the human acted |

---

## Enums

### `DecisionResultType`

```python
from chimera_runtime import DecisionResultType

DecisionResultType.ALLOWED        # "ALLOWED"
DecisionResultType.BLOCKED        # "BLOCKED"
DecisionResultType.HUMAN_OVERRIDE # "HUMAN_OVERRIDE"
DecisionResultType.INTERRUPTED    # "INTERRUPTED"
```

### `AttemptOutcome`

```python
from chimera_runtime import AttemptOutcome

AttemptOutcome.ALL_PASSED  # "ALL_PASSED"
AttemptOutcome.PARTIAL     # "PARTIAL"
AttemptOutcome.ALL_BLOCKED # "ALL_BLOCKED"
```

### `EnforcementType`

```python
from chimera_runtime import EnforcementType

EnforcementType.ACTIVE   # "ACTIVE"
EnforcementType.DRY_RUN  # "DRY_RUN"
```

---

## Integration Classes

### `ComplianceGuard`

Core guard shared by all integrations.

```python
from chimera_runtime.integrations import ComplianceGuard
```

**Constructor:**

```python
ComplianceGuard(
    policy: str,
    audit_dir: str = "./audit_logs",
    dry_run: bool = False,
    auto_verify: bool = True,
)
```

**Methods:**

#### `check(action_name, parameters, context) → PolicyEvaluation`

Evaluate an action against the policy. Automatically records audit.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `action_name` | `str` | required | Name of tool/action |
| `parameters` | `Dict[str, Any]` | required | Parameters to evaluate |
| `context` | `Dict[str, Any]\|None` | `None` | Additional context |

**Properties:**

| Property | Type | Description |
|----------|------|-------------|
| `policy_manager` | `PolicyManager` | Underlying policy manager |

### `ComplianceError`

Exception raised when an action is blocked.

```python
from chimera_runtime.integrations.base import ComplianceError
```

| Attribute | Type | Description |
|-----------|------|-------------|
| `evaluation` | `PolicyEvaluation` | The evaluation that caused the block |

---

## Audit Functions

```python
from chimera_runtime import (
    build_audit_record,
    save_record,
    load_record,
    load_all_records,
    enforce_retention,
    AuditQuery,
    AuditStats,
    generate_html,
)
```

### `save_record(record, audit_dir) → str`

Persist a `DecisionAuditRecord` to disk. Returns the file path.

### `load_record(decision_id, audit_dir) → DecisionAuditRecord`

Load a specific record by ID. Raises `AuditStorageError` if not found.

### `load_all_records(audit_dir) → List[DecisionAuditRecord]`

Load all records from the audit directory.

### `enforce_retention(audit_dir, retention_days=90) → int`

Remove records older than `retention_days` (default: 90). Returns count of removed records. Note: `AuditConfig.retention_days` defaults to 180 in config; pass it explicitly to match your config.

### `generate_html(record) → str`

Generate a self-contained HTML explanation report from a `DecisionAuditRecord`.

### `AuditQuery`

Query and filter audit records.

```python
query = AuditQuery(audit_dir="./audit_logs")

# Filter records
records = query.filter(result="BLOCKED", after="2026-01-01T00:00:00Z")

# Aggregate stats
stats = query.stats()  # → AuditStats

# Top violations
top = query.top_violations(n=20)

# Export
query.export("report.json", format="compact")
```

**Methods:**

| Method | Parameters | Returns |
|--------|-----------|---------|
| `filter()` | `result`, `after`, `before`, `policy_file`, `action` (all optional) | `List[DecisionAuditRecord]` |
| `stats()` | `last_days` (optional int), `records` (optional list) | `AuditStats` |
| `top_violations()` | `n` (default 10), `records` (optional list) | `List[Tuple[str, int]]` |
| `export()` | `path`, `format` (`"json"`/`"compact"`/`"stats"`), `records` (optional) | `str` (file path) |
| `refresh()` | — | `None` (force reload from disk) |

---

## Config Functions

```python
from chimera_runtime import load_config, save_config, validate_config
```

### `load_config(config_path) → AgentConfig`

Load config from YAML file. Returns `AgentConfig`.

### `save_config(config, config_path) → Path`

Save `AgentConfig` to YAML file. Returns the `Path` to the written config file.

### `validate_config(config) → None`

Validate config. Raises `ConfigError` on invalid config.

---

## Helper Functions

```python
from chimera_runtime import generate_decision_id, generate_candidate_id, utc_now_iso
```

### `generate_decision_id() → str`

Generate unique decision ID: `dec_<20-char-hex>`.

### `generate_candidate_id(index) → str`

Generate candidate ID: `cand_001`, `cand_002`, etc.

### `utc_now_iso() → str`

ISO 8601 UTC timestamp with millisecond precision.

---

## Exceptions

| Exception | Module | Description |
|-----------|--------|-------------|
| `ChimeraAgentError` | `chimera_runtime.agent` | Base agent error |
| `AgentHalted` | `chimera_runtime.agent` | Agent has been halted (Art. 14) |
| `PolicyError` | `chimera_runtime.policy` | Policy load/eval/verify error |
| `PolicyFileNotFoundError` | `chimera_runtime.policy` | Policy file does not exist |
| `PolicyVerificationError` | `chimera_runtime.policy` | Z3 verification failed |
| `RuleEngineError` | `chimera_runtime.rules` | YAML rule engine error |
| `RuleParseError` | `chimera_runtime.rules` | Expression parse error |
| `ComplianceError` | `chimera_runtime.integrations.base` | Action blocked by policy |
| `OversightError` | `chimera_runtime.oversight` | Oversight operation error |
| `OversightTimeoutError` | `chimera_runtime.oversight` | Human confirmation timeout |
| `ConfigError` | `chimera_runtime.config` | Config load/validate error |
| `AuditStorageError` | `chimera_runtime.audit.storage` | Audit I/O error |
| `LLMError` | `chimera_runtime.llm` | LLM provider error |
| `LLMAuthenticationError` | `chimera_runtime.llm` | Invalid API key |
| `LLMRateLimitError` | `chimera_runtime.llm` | Rate limit exceeded |
| `LLMTimeoutError` | `chimera_runtime.llm` | LLM request timeout |
| `LLMResponseParseError` | `chimera_runtime.llm` | Cannot parse LLM response |
| `DocsGeneratorError` | `chimera_runtime.docs` | Documentation generation error |

---

## Constants

| Constant | Value | Description |
|----------|-------|-------------|
| `__version__` | `"3.0.0"` | Package version |
| `CSL_CORE_AVAILABLE` | `bool` | Whether `csl-core` is installed |
| `SCHEMA_VERSION` | `"1.0.0"` | Audit record schema version |
