# Architecture

How chimera-runtime works, from request to audited decision.

---

## Overview

chimera-runtime operates as a **deterministic execution layer** between AI agents and the actions they take. It enforces policies before actions execute and records every decision for auditability.

There are two operating modes:

1. **Integration mode** — chimera-runtime wraps tool calls in an external agent framework (LangChain, LangGraph, etc.)
2. **Standalone mode** — chimera-runtime orchestrates the full neural-symbolic pipeline including LLM interaction

---

## Integration Mode Pipeline

When used with an agent framework, the pipeline is:

```
Agent Framework (LangChain, etc.)
    │
    ▼
Tool Call Intercepted
    │
    ▼
┌─────────────────────────┐
│   ComplianceGuard       │
│                         │
│  1. Extract parameters  │
│  2. PolicyManager       │
│     .evaluate(params)   │
│  3. ALLOWED / BLOCKED   │
│  4. Record audit log    │
└─────────────────────────┘
    │
    ├─── ALLOWED ──→ Tool executes normally
    │
    └─── BLOCKED ──→ ComplianceError raised
```

### ComplianceGuard

`ComplianceGuard` (`chimera_runtime.integrations.ComplianceGuard`) is the core class used by all integrations. It combines:

- **PolicyManager** — loads and evaluates the policy file
- **Audit recording** — writes a `DecisionAuditRecord` for every check
- **Hot-reload** — detects policy file changes without restart

```python
guard = ComplianceGuard(
    policy="./policies/governance.yaml",
    audit_dir="./audit_logs",
)

evaluation = guard.check(
    action_name="approve_budget",
    parameters={"amount": 500000, "role": "MANAGER"},
)
# evaluation.result → "BLOCKED"
# evaluation.violations → [Violation(...)]
```

Every call to `guard.check()` produces:
- A `PolicyEvaluation` returned to the caller
- A `DecisionAuditRecord` persisted to disk

---

## Standalone Mode Pipeline

When chimera-runtime manages the LLM directly via `ChimeraAgent`:

```
Natural Language Request
    │
    ▼
┌──────────────────────────────────────────────┐
│              ChimeraAgent.decide()           │
│                                              │
│  ┌─── Retry Loop (max_retries) ───────────┐ │
│  │                                         │ │
│  │  Step 1: LLM generates N candidates    │ │
│  │          (diverse strategies)           │ │
│  │                                         │ │
│  │  Step 2: PolicyManager evaluates each   │ │
│  │          candidate against CSL/YAML     │ │
│  │                                         │ │
│  │  Step 3: If any ALLOWED → select best   │ │
│  │          (highest confidence)           │ │
│  │                                         │ │
│  │  Step 4: If ALL BLOCKED → build         │ │
│  │          rejection context → retry      │ │
│  │                                         │ │
│  └─────────────────────────────────────────┘ │
│                                              │
│  Step 5: Human oversight check (if enabled)  │
│                                              │
│  Step 6: Build DecisionAuditRecord           │
│                                              │
│  Step 7: Persist audit to disk               │
│                                              │
│  Return DecisionResult                       │
└──────────────────────────────────────────────┘
```

### Key Concepts

**Candidate generation**: The LLM generates `candidates_per_attempt` (default: 3) diverse strategy candidates per attempt. Each candidate includes a strategy description, confidence score, reasoning, and structured parameters.

**Policy gate**: Each candidate's parameters are evaluated against the loaded policy. Only candidates that pass all rules are considered.

**Retry with rejection context**: If all candidates are blocked, chimera-runtime feeds the violation details back to the LLM as rejection context, asking it to generate new candidates that avoid the violated constraints. This continues for `max_retries` (default: 3) attempts.

**Best-candidate selection**: Among allowed candidates, the one with the highest LLM confidence score is selected.

---

## Policy Engine

`PolicyManager` (`chimera_runtime.policy.PolicyManager`) automatically selects the evaluation backend based on file extension:

| File Extension | Backend | Verification | Dependency |
|---------------|---------|-------------|------------|
| `.yaml` / `.yml` | YAMLRuleEngine | Syntax validation | None (built-in) |
| `.csl` | CSL-Core + Z3 | Formal verification (Z3 SAT) | `pip install chimera-runtime[csl]` |

### YAML Rule Engine

Built-in lightweight engine. Evaluates rules using an AST-based safe expression evaluator (no `eval()`). Supports comparisons (`==`, `!=`, `>`, `<`, `>=`, `<=`), boolean operators (`and`, `or`, `not`), `in` operator, string/numeric literals, and variable references.

```yaml
rules:
  - name: manager_limit
    when: "role == 'MANAGER' and amount > 250000"
    then: BLOCK
    message: "Managers cannot approve more than $250,000"
```

### CSL-Core + Z3

Optional backend providing mathematically provable policy enforcement. Policies are written in CSL (Constraint Specification Language) and compiled to Z3 constraints.

```
pip install chimera-runtime[csl]
```

CSL provides:
- Z3 SAT verification (prove policy is internally consistent)
- Reachability analysis (prove every constraint can trigger)
- Pairwise conflict detection
- Formal guarantees about policy behavior

---

## Audit Pipeline

Every decision produces a `DecisionAuditRecord` — an immutable JSON document with 8 sections:

```json
{
  "schema_version": "1.0.0",
  "decision_id": "dec_a1b2c3d4e5f6...",
  "timestamp": "2026-03-05T10:30:00.123Z",
  "agent": { ... },
  "input": { ... },
  "reasoning": { ... },
  "decision": { ... },
  "compliance": { ... },
  "performance": { ... }
}
```

| Section | Contents | EU AI Act |
|---------|----------|-----------|
| `agent` | Agent name, version, model, provider, temperature | Art. 13 |
| `input` | Raw request, structured params, context | Art. 12 |
| `reasoning` | All attempts, all candidates, selection reasoning | Art. 86 |
| `decision` | Action taken, result, final parameters, policy hash | Art. 12 |
| `compliance` | EU AI Act checklist, verification engine, oversight status | Art. 9, 15 |
| `performance` | Total duration, LLM time, policy eval time, audit time | Art. 15 |
| `human_oversight_record` | (optional) Human confirmation, override, or stop | Art. 14 |

Records are stored as individual JSON files in the audit directory (default: `./audit_logs/`). File naming: `{decision_id}.json`.

### Retention

EU AI Act Article 19 requires minimum record retention. Default: 180 days. Configurable via `audit.retention_days` in config. The `enforce_retention()` function removes records older than the configured period.

---

## Human Oversight (Art. 14)

Three modes:

| Mode | Behavior | Use Case |
|------|----------|----------|
| `auto` | Always approves (no human in loop) | Testing, batch processing |
| `interactive` | Blocks on stdin for confirmation | CLI / REPL usage |
| `sdk` | Calls a callback function | Programmatic integration |

Humans can:
- **Confirm** — approve the proposed action
- **Override** — change the decision (e.g., force-block an allowed action)
- **Stop** — halt the agent entirely (`agent.halt()`)

A halted agent raises `AgentHalted` on every subsequent `decide()` call until `agent.resume()` is called.

---

## Hot Reload

Both the YAML and CSL backends support hot-reload. When `policy_hot_reload: true` in config, the `PolicyManager` checks the file's modification time and SHA-256 hash before each evaluation. If the file has changed, it reloads automatically — no restart needed.

```yaml
# .chimera/config.yaml
oversight:
  policy_hot_reload: true
```

---

## Configuration

Configuration is loaded from `.chimera/config.yaml` with environment variable overrides:

| Env Variable | Config Path | Description |
|-------------|-------------|-------------|
| `CHIMERA_API_KEY` | `llm.api_key` | LLM API key |
| `CHIMERA_MODEL` | `llm.model` | LLM model name |
| `CHIMERA_PROVIDER` | `llm.provider` | LLM provider |
| `CHIMERA_POLICY_FILE` | `policy.file` | Policy file path |
| `CHIMERA_AUDIT_DIR` | `audit.output_dir` | Audit log directory |

Resolution order: YAML file → environment variables → dataclass defaults.

---

## Project Structure

```
your-project/
├── .chimera/
│   └── config.yaml          # Project configuration
├── policies/
│   ├── starter.yaml          # YAML rules (default)
│   └── governance.csl        # CSL policy (optional)
├── audit_logs/
│   ├── dec_a1b2c3d4e5f6.json # Audit records
│   └── ...
└── your_code.py
```
