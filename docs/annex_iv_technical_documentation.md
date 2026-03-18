# EU AI Act — Annex IV Technical Documentation

**System:** chimera-runtime v0.1.0
**Generated:** 2026-03-17T03:24:22.838Z
**Schema Version:** 1.0.0
**Coverage:** 14/19 sections auto-filled

---

## Section 1 — General Description of the AI System

**Article Reference:** Annex IV, Section 1

chimera-runtime is a neuro-symbolic AI compliance framework that combines large language model (LLM) reasoning with Z3 formal policy verification to produce auditable, compliant AI decisions.

| Property | Value |
|----------|-------|
| System Name | chimera-runtime |
| Version | 0.1.0 |
| CSL-Core Version | 0.3.0 |
| Policy Backend | CSL-Core (Chimera Specification Language) |
| Deployment Mode | Standalone (manages LLM directly) |

**Architecture:** Neural (LLM) → Symbolic (CSL Policy Engine + Z3) → Audit Pipeline


The system operates by:
1. Receiving natural language requests
2. Generating candidate strategies via LLM (openai / gpt-4o)
3. Evaluating each candidate against policy constraints (CSL-Core (Chimera Specification Language))
4. Selecting the highest-confidence compliant candidate
5. Producing a complete audit record for every decision


---

## Section 2 — Elements of the AI System and Development Process

**Article Reference:** Annex IV, Section 2


### 2.1 LLM Component (Neural)

| Property | Value |
|----------|-------|
| Provider | openai |
| Model | gpt-4o |
| Temperature | 0.7 |
| Candidates per Attempt | 3 |
| Max Retries | 3 |


### 2.2 Policy Engine (Symbolic)

| Property | Value |
|----------|-------|
| Engine | CSL-Core (Chimera Specification Language) |
| Formal Verifier | Z3 SMT Solver |
| Policy File | ./policies/governance.csl |
| Policy Hash | sha256:3a8dc2bdcec45c482094ba6dea5c57d72d3a11cff0990a6b7234364ccbb43a71 |
| Auto-Verify on Startup | True |
| Domain | GovernanceGuard |
| Variables | 6 |
| Constraints | 7 |
| Verified | True |


### 2.3 Policy Variables

| Variable | Domain |
|----------|--------|
| amount | 0..1000000 |
| channel | {"DIGITAL", "TV", "PRINT", "RADIO", "ALL"} |
| department | {"MARKETING", "ENGINEERING", "FINANCE", "OPERATIONS", "HR"} |
| is_weekend | {"YES", "NO"} |
| role | {"ANALYST", "MANAGER", "DIRECTOR", "VP", "CEO"} |
| urgency | {"LOW", "MEDIUM", "HIGH", "CRITICAL"} |

### 2.4 Policy Constraints


- **analyst_no_spend**

- **manager_approval_limit**

- **director_approval_limit**

- **vp_approval_limit**

- **single_channel_cap**

- **weekend_freeze**

- **absolute_ceiling**


---

## Section 3 — Monitoring, Functioning, and Control

**Article Reference:** Annex IV, Section 3

### 3.1 Decision Pipeline Monitoring

Every decision is monitored through the complete pipeline:

- **LLM Generation:** Each candidate is tracked with strategy, reasoning, confidence
- **Policy Evaluation:** Every candidate evaluated against all constraints; violations recorded
- **Retry Mechanism:** Failed attempts feed rejection context back to LLM (max 3 retries)
- **Selection:** Best compliant candidate selected by confidence score

### 3.2 Audit Configuration

| Property | Value |
|----------|-------|
| Audit Enabled | True |
| Output Directory | ./audit_logs |
| Format | json |
| HTML Reports | True |
| Retention Days | 180 |

### 3.3 Real-time Controls

- **Policy Hot-Reload:** True — policy changes take effect without restart
- **Halt Mechanism:** `agent.halt()` immediately stops all decision-making (Art. 14)
- **Resume:** `agent.resume()` reactivates after halt
- **Consecutive Block Alert:** After 5 consecutive blocks

---

## Section 4 — Appropriateness of Performance Metrics

**Article Reference:** Annex IV, Section 4


### 4.1 Decision Performance (Last 90 Days)

| Metric | Value |
|--------|-------|
| Total Decisions | 24 |
| Allowed | 15 (62.5%) |
| Blocked | 9 (37.5%) |
| Human Overrides | 0 |
| Interrupted | 0 |
| Avg Duration | 654.5 ms |
| Avg Candidates/Decision | 1.4 |
| Avg Attempts/Decision | 1.1 |
| Total Violations | 22 |

### 4.2 Top Constraint Violations

| Constraint | Occurrences |
|------------|-------------|
| single_channel_cap | 8 |
| manager_approval_limit | 3 |
| director_approval_limit | 2 |
| analyst_no_spend | 2 |
| amount_limit | 2 |
| admin_required | 2 |
| limit_large_transfers | 2 |
| absolute_ceiling | 1 |



---

## Section 5 — Risk Management System

**Article Reference:** Annex IV, Section 5


### 5.1 Formal Verification (Z3)

All policy constraints are formally verified using the Z3 SMT solver before deployment:

1. **Syntax Validation** — CSL parser validates grammar
2. **Semantic Validation** — Type checking, scope analysis
3. **Z3 Logic Verification** — Reachability, consistency, conflict detection
4. **IR Compilation** — Generates runtime guard

**Verification Status:** ✅ Policy verified — constraints are provably consistent


### 5.2 Risk Mitigation Through Policy Constraints

The system mitigates risks through deterministic policy enforcement:

- All LLM outputs are validated against policy constraints before execution
- No action can bypass policy evaluation
- Violations are recorded with full context for investigation

- **22 violations** have been caught and prevented in the current period


### 5.3 Adversarial Resilience (Art. 15)

- LLM outputs are treated as **untrusted** — every candidate must pass policy verification
- Policy constraints are deterministic and cannot be influenced by external inputs
- The CSL-Core (Chimera Specification Language) operates independently of the neural component
- Z3 proves policy consistency — no logical bypass possible


---

## Section 6 — Description of Changes Throughout Lifecycle

**Article Reference:** Annex IV, Section 6


System changes are tracked through the audit pipeline:

- **Policy Hash:** Each decision records the exact policy hash at decision time
- **Current Policy Hash:** `sha256:3a8dc2bdcec45c482094ba6dea5c57d72d3a11cff0990a6b7234364ccbb43a71`
- **Decision Count:** 24 decisions recorded
- **Period:** 2026-02-26T07:41:35.946Z to 2026-03-08T11:27:55.226Z

All changes to policy files trigger re-verification via Z3.


---

## Section 7 — Harmonised Standards Applied

**Article Reference:** Annex IV, Section 7

> ⚠️ **MANUAL INPUT REQUIRED**
>
> List the harmonised standards applied in the development of this AI system.
> This section must be completed by the deploying organisation.
>
> Examples:
> - ISO/IEC 42001:2023 (AI Management Systems)
> - ISO/IEC 23894:2023 (AI Risk Management)
> - EN 301 549 (Accessibility)

---

## Section 8 — Description of Data Used

**Article Reference:** Annex IV, Section 8

> ⚠️ **MANUAL INPUT REQUIRED**
>
> The LLM component (openai / gpt-4o) is a pre-trained
> external model. Training data documentation is the responsibility of the
> model provider.
>
> Describe any fine-tuning data, if applicable:
> - Training datasets used
> - Data collection methodology
> - Data preprocessing steps
> - Bias assessment results

---

## Section 9 — Human Oversight Measures

**Article Reference:** Annex IV, Section 9 (Art. 14)

### 9.1 Oversight Configuration

| Measure | Status |
|---------|--------|
| Active Mode | auto — Automatic approval — no human in the loop (override available) |
| Confirmation Required | False |
| Override Allowed | True |
| Policy Human-Editable | Yes (CSL text files) |
| Stop Mechanism | `agent.halt()` — immediate cessation |
| Consecutive Block Alert | After 5 blocks |

### 9.2 Available Oversight Modes

| Mode | Description |
|------|-------------|
| **Interactive** | Blocks on stdin; human must approve each decision |
| **SDK/Callback** | Programmatic approval via callback function |
| **Auto** | No human in loop (for batch/testing) |

**Currently Active:** `auto`

### 9.3 Override Capabilities

- **CONFIRM:** Human approves the proposed action
- **OVERRIDE:** Human changes the decision (recorded in audit trail)
- **STOP:** Human halts the agent entirely

All human oversight actions are recorded in the `human_oversight_record` field
of the DecisionAuditRecord.

---

## Section 10 — Pre-determined Changes

**Article Reference:** Annex IV, Section 10

> ⚠️ **MANUAL INPUT REQUIRED**
>
> Describe any pre-determined changes to the system that have been assessed
> at the time of initial conformity assessment.
>
> Relevant change types for this system:
> - Policy file updates (automatically re-verified via Z3)
> - LLM model upgrades
> - Configuration parameter adjustments

---

## Section 11 — Validation and Testing Procedures

**Article Reference:** Annex IV, Section 11


### 11.1 Formal Verification (Z3)

Every CSL policy undergoes four-stage verification before deployment:

1. **Syntax Validation** — Parser checks grammar
2. **Semantic Validation** — Scope, types, function whitelist
3. **Z3 Logic Verification** — Reachability, consistency, conflicts
4. **IR Compilation** — Generates runtime guard


### 11.2 Runtime Validation

- Each candidate is evaluated against the compiled policy at runtime
- Policy evaluation results include: ALLOWED / BLOCKED + violation details
- All evaluations are recorded in the audit trail

---

## Section 12 — Cybersecurity Measures

**Article Reference:** Annex IV, Section 12 (Art. 15)

### 12.1 Adversarial Resilience

- **LLM Output Sandboxing:** All LLM outputs pass through deterministic policy gate
- **Formal Verification:** Z3 proves policy consistency — no logical bypass possible
- **Input Validation:** Candidate parameters are validated against policy variable domains
- **No Direct Execution:** LLM cannot execute actions; it only proposes candidates


### 12.2 Data Protection

- **API Keys:** Never serialized to disk (excluded from config.to_dict())
- **Audit Records:** Immutable after creation
- **Retention Enforcement:** Automatic cleanup after 180 days


---

## Section 13 — Computing Infrastructure

**Article Reference:** Annex IV, Section 13

| Component | Infrastructure |
|-----------|---------------|
| LLM Provider | openai |
| LLM Model | gpt-4o |
| Policy Engine | CSL-Core (Chimera Specification Language) |
| Formal Verifier | Z3 SMT Solver (local) |
| Audit Storage | Local filesystem (./audit_logs) |
| Runtime | Python 3.12.5 |
| Platform | macOS-26.3-arm64-arm-64bit |

### 13.1 Installed Dependencies

| Package | Version |
|---------|---------|
| chimera-core | 0.3.0 |
| click | 8.2.1 |
| rich | 13.9.4 |
| pyyaml | 6.0.1 |
| jinja2 | 3.1.6 |
| langchain-core | 1.2.14 |
| langgraph | 1.0.9 |
| openai | 2.21.0 |
| anthropic | 0.79.0 |


---

## Section 14 — Description of Input Data

**Article Reference:** Annex IV, Section 14

### 14.1 Decision Input Format


Each decision receives:

| Field | Type | Description |
|-------|------|-------------|
| `request` | string | Natural language request |
| `context` | dict | Session context (role, user_id, etc.) |


### 14.2 Policy Variable Inputs

Candidates generate parameters that map to policy variables:

| Variable | Domain |
|----------|--------|
| amount | 0..1000000 |
| channel | {"DIGITAL", "TV", "PRINT", "RADIO", "ALL"} |
| department | {"MARKETING", "ENGINEERING", "FINANCE", "OPERATIONS", "HR"} |
| is_weekend | {"YES", "NO"} |
| role | {"ANALYST", "MANAGER", "DIRECTOR", "VP", "CEO"} |
| urgency | {"LOW", "MEDIUM", "HIGH", "CRITICAL"} |


---

## Section 15 — Description of Output

**Article Reference:** Annex IV, Section 15


### 15.1 DecisionResult

| Field | Type | Description |
|-------|------|-------------|
| `result` | enum | ALLOWED, BLOCKED, HUMAN_OVERRIDE, INTERRUPTED |
| `action` | string | Selected strategy description |
| `explanation` | string | Human-readable reasoning |
| `parameters` | dict | Final action parameters |
| `audit` | DecisionAuditRecord | Complete audit trail |


### 15.2 DecisionAuditRecord (Spec §2.1)

Full JSON record containing: agent info, input, reasoning trace (all attempts
and candidates), decision, compliance metadata, performance metrics, and
optional human oversight record.

---

## Section 16 — Post-Market Monitoring Plan

**Article Reference:** Annex IV, Section 16

### 16.1 Automated Monitoring

The audit pipeline provides continuous post-market monitoring:

- **AuditQuery.stats():** Aggregate metrics (block rate, violation counts)
- **AuditQuery.top_violations():** Most frequent constraint violations
- **AuditQuery.filter():** Filter by result, time range, policy, action
- **AuditQuery.export():** Export data in JSON, compact, or stats format
- **enforce_retention():** Automatic cleanup per Art. 19

### 16.2 Alerting

- **Consecutive Block Counter:** Tracks sequential blocked decisions
- **Threshold Alert:** Configured at 5 consecutive blocks
- **Decision Counter:** Running total for utilization monitoring


---

## Section 17 — Description of Changes

**Article Reference:** Annex IV, Section 17


All system changes are captured in the audit trail:

- **Policy changes** are detected via hash comparison and trigger re-verification via Z3

- **Configuration changes** are reflected in the agent info section of each audit record
- **Model changes** are captured in the agent info (model, provider, temperature)
- **24 decisions** have been recorded to date


---

## Section 18 — Relevant Information About Datasets

**Article Reference:** Annex IV, Section 18

> ⚠️ **MANUAL INPUT REQUIRED**
>
> Note: The LLM component is externally trained by openai.
> Refer to the model provider's documentation for training data details.
>
> Provide relevant information about the datasets used for training,
> validation, and testing of the AI system.

---

## Section 19 — EU Declaration of Conformity

**Article Reference:** Annex IV, Section 19

> ⚠️ **MANUAL INPUT REQUIRED**
>
> The EU Declaration of Conformity must be drawn up by the provider
> in accordance with Article 47 and Annex V of the EU AI Act.
>
> This declaration must include:
> - Name and address of the provider
> - Statement that the declaration is issued under the provider's sole responsibility
> - Reference to this technical documentation
> - Statement of conformity with the requirements of the EU AI Act
> - Identification of the notified body (if applicable)

---

*Generated by chimera-runtime v0.1.0 — Annex IV Documentation Generator*
*Policy backend: CSL-Core (Chimera Specification Language) | Python 3.12.5 | CSL-Core: 0.3.0*
