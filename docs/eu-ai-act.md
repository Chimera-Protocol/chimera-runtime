# EU AI Act Compliance Mapping

How chimera-compliance maps to specific EU AI Act articles and requirements.

---

## Overview

The EU AI Act (Regulation 2024/1689) establishes harmonized rules for AI systems in the European Union. chimera-compliance addresses the requirements for **high-risk AI systems** (Title III, Chapter 2) by providing deterministic policy enforcement, comprehensive audit trails, human oversight mechanisms, and transparency guarantees.

---

## Article-by-Article Mapping

### Article 9 — Risk Management System

> High-risk AI systems shall have a risk management system established, implemented, documented, and maintained.

**chimera-compliance implementation:**

| Requirement | Implementation |
|-------------|---------------|
| Risk identification | Policy rules define risk boundaries (amount limits, role restrictions, action constraints) |
| Risk evaluation | Every action is evaluated against the policy before execution |
| Risk mitigation | BLOCK action prevents execution of non-compliant actions |
| Continuous monitoring | Audit trail tracks all decisions over time; `chimera-compliance audit --stats` provides aggregate risk analysis |
| Documentation | `chimera-compliance docs generate` produces Annex IV documentation |

**How to use:**

```yaml
# Define risk boundaries in your policy
rules:
  - name: high_risk_threshold
    when: "risk_score > 80"
    then: BLOCK
    message: "Action exceeds risk threshold"
```

---

### Article 12 — Record-keeping

> High-risk AI systems shall technically allow for the automatic recording of events (logs) over the lifetime of the system.

**chimera-compliance implementation:**

| Requirement | Implementation |
|-------------|---------------|
| Art. 12(1) — Automatic recording | Every `decide()` and `ComplianceGuard.check()` call automatically writes a `DecisionAuditRecord` to disk |
| Art. 12(2a) — Identification of risk situations | Violations are recorded with constraint name, rule text, trigger values, and explanation |
| Art. 12(2b) — Input data | `InputInfo` section captures raw request, structured parameters, and context |
| Art. 12(3) — Proportionate logging | Two formats: full JSON (with reasoning trace) and compact JSON (essentials only) |

**Audit record structure (8 sections):**

```
DecisionAuditRecord
├── schema_version    # Record format version
├── decision_id       # Unique identifier (dec_<uuid>)
├── timestamp         # ISO 8601 UTC with milliseconds
├── agent             # Agent identity snapshot
├── input             # Request and parameters
├── reasoning         # All attempts, all candidates
├── decision          # Final action taken
├── compliance        # EU AI Act checklist
└── performance       # Timing metrics
```

**CLI commands:**

```bash
# View recent decisions
chimera-compliance audit --last 20

# Filter by result
chimera-compliance audit --result BLOCKED

# Aggregate statistics
chimera-compliance audit --stats

# Export for external analysis
chimera-compliance audit --export report.json --format compact
```

---

### Article 13 — Transparency

> High-risk AI systems shall be designed and developed in such a way as to ensure that their operation is sufficiently transparent to enable deployers to interpret the system's output and use it appropriately.

**chimera-compliance implementation:**

| Requirement | Implementation |
|-------------|---------------|
| System output interpretation | `DecisionResult` provides `.result`, `.action`, `.explanation`, and `.parameters` |
| Reasoning transparency | `ReasoningTrace` records all candidates, all attempts, selection reasoning |
| Policy transparency | Policy files (YAML/CSL) are human-readable, version-controlled, and auditable |
| Agent identity | `AgentInfo` records model, provider, version, temperature for each decision |

**Every decision result includes:**

```python
result = agent.decide("Increase marketing spend")

result.result       # "ALLOWED" / "BLOCKED"
result.action       # What action was selected
result.explanation  # Human-readable explanation of WHY
result.parameters   # Exact parameters of the action
result.audit        # Full audit record with reasoning trace
```

---

### Article 14 — Human Oversight

> High-risk AI systems shall be designed and developed in such a way as to enable effective human oversight during the period of use.

**chimera-compliance implementation:**

| Requirement | Implementation |
|-------------|---------------|
| Art. 14(1) — Oversight capability | `HumanOversight` class with three modes: `auto`, `interactive`, `sdk` |
| Art. 14(3a) — Understanding capabilities | Policy files are human-readable; `chimera-compliance explain` generates explanation reports |
| Art. 14(3b) — Remaining aware of automation bias | All decisions show violations and reasoning, even when ALLOWED |
| Art. 14(3c) — Correctly interpret output | `DecisionResult` provides structured, interpretable output |
| Art. 14(3d) — Override/reverse | `apply_override()` method; `--require-confirmation` CLI flag |
| Art. 14(3e) — Stop mechanism | `agent.halt()` / `agent.resume()`; `AgentHalted` exception on halted agents |

**Oversight modes:**

```python
from chimera_compliance import ChimeraAgent, HumanOversight

# Auto mode (testing/batch)
agent = ChimeraAgent(oversight=HumanOversight(mode="auto"))

# Interactive mode (CLI) — blocks on stdin
agent = ChimeraAgent(oversight=HumanOversight(mode="interactive"))

# SDK mode (programmatic)
def my_approval(candidate, evaluation):
    return candidate.llm_confidence > 0.9

agent = ChimeraAgent(
    oversight=HumanOversight(mode="sdk", confirm_callback=my_approval)
)
```

**Stop mechanism:**

```python
agent.halt(reason="Risk review triggered")
# All subsequent decide() calls raise AgentHalted

agent.resume()
# Agent resumes normal operation
```

**CLI:**

```bash
# Require confirmation for each decision
chimera-compliance run --require-confirmation

# During interactive session, type "halt" to stop
```

---

### Article 15 — Accuracy, Robustness, and Cybersecurity

> High-risk AI systems shall be designed and developed in such a way that they achieve an appropriate level of accuracy, robustness, and cybersecurity.

**chimera-compliance implementation:**

| Requirement | Implementation |
|-------------|---------------|
| Accuracy | Formal verification via Z3 proves policy correctness; YAML rules use AST-based safe evaluation (no `eval()`) |
| Robustness | Retry loop with rejection context; policy hot-reload; graceful error handling |
| Cybersecurity | YAML engine uses AST-based safe evaluation; API keys never serialized to audit logs; policy files are deterministic |

**Safe expression evaluation:**

The YAML rule engine parses expressions using Python's `ast` module and walks the AST tree safely. It supports only whitelisted operations (comparisons, boolean operators, literals, variable references). No arbitrary code execution is possible.

**Z3 formal verification** (CSL backend):

```bash
chimera-compliance verify policies/governance.csl
```

Verification pipeline:
1. Syntax validation
2. Semantic validation (scope, types, function whitelist)
3. Z3 logic verification (reachability, consistency, conflicts)
4. IR compilation

---

### Article 19 — Automatic Log Retention

> The logs referred to in Article 12 shall be kept for a period that is appropriate in the light of the intended purpose of the high-risk AI system, of at least six months.

**chimera-compliance implementation:**

| Requirement | Implementation |
|-------------|---------------|
| Minimum 6-month retention | Default: 180 days (configurable via `audit.retention_days`) |
| Automatic enforcement | `enforce_retention()` function removes records older than configured period |
| Configurable period | Set in `.chimera/config.yaml` under `audit.retention_days` |

```yaml
# .chimera/config.yaml
audit:
  enabled: true
  output_dir: ./audit_logs
  retention_days: 180  # Minimum per Art. 19
```

```python
from chimera_compliance import enforce_retention

# Remove records older than configured retention period
# Note: enforce_retention() defaults to 90 days if retention_days is not specified.
# Pass your config's retention_days explicitly to match Art. 19 requirements.
enforce_retention(audit_dir="./audit_logs", retention_days=180)
```

---

### Article 86 — Right to Explanation

> Any affected person subject to a decision which is taken by the deployer on the basis of the output from a high-risk AI system shall have the right to obtain clear and meaningful explanations of the role of the AI system in the decision-making procedure and the main elements of the decision taken.

**chimera-compliance implementation:**

| Requirement | Implementation |
|-------------|---------------|
| Clear explanation | `DecisionResult.explanation` provides human-readable reasoning |
| Meaningful details | Full reasoning trace: all candidates, all violations, selection reasoning |
| Self-contained report | `chimera-compliance explain --id <id>` generates HTML report |
| Accessible format | HTML reports viewable in any browser; JSON for programmatic access |

**Generate explanation report:**

```bash
chimera-compliance explain --id dec_a1b2c3d4e5f6 --open
```

The HTML report includes:
- Decision outcome (ALLOWED/BLOCKED)
- Action taken and parameters
- All candidates generated and why each was selected/rejected
- Policy violations with constraint names and explanations
- Policy file and hash at decision time
- Agent configuration snapshot
- Performance metrics

---

### Annex IV — Technical Documentation

> The technical documentation shall contain, as a minimum, the following information:
> (a) A general description of the AI system
> (b) A detailed description of the elements and development process
> ...

**chimera-compliance implementation:**

```bash
chimera-compliance docs generate
```

Generates Annex IV compliant technical documentation including:
- System description
- Policy specification
- Data flow description
- Risk management measures
- Testing and validation procedures
- Performance metrics

---

## Compliance Checklist

Every `DecisionAuditRecord` includes a compliance section:

```json
{
  "compliance": {
    "eu_ai_act": {
      "article_12_record_keeping": true,
      "article_13_transparency": true,
      "article_14_human_oversight": true,
      "article_15_adversarial_resilience": true,
      "article_19_auto_logs": true,
      "article_86_right_to_explanation": true
    },
    "formal_verification": {
      "policy_verified": true,
      "verification_engine": "Z3",
      "verification_result": "SAT"
    },
    "human_oversight": {
      "override_available": true,
      "stop_mechanism": true,
      "policy_human_editable": true
    }
  }
}
```

---

## Summary

| EU AI Act Article | chimera-compliance Feature |
|-------------------|---------------------------|
| Art. 9 — Risk Management | Policy rules define risk boundaries; continuous audit |
| Art. 12 — Record-keeping | Automatic `DecisionAuditRecord` for every decision |
| Art. 13 — Transparency | Human-readable policies, reasoning traces, explanation reports |
| Art. 14 — Human Oversight | Three oversight modes, halt/resume, override capability |
| Art. 15 — Accuracy/Robustness | Z3 formal verification, AST-based safe eval, retry loop |
| Art. 19 — Log Retention | Configurable retention with 180-day default |
| Art. 86 — Right to Explanation | Self-contained HTML explanation reports |
| Annex IV — Documentation | Auto-generated technical documentation |
