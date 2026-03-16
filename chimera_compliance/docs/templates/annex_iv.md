# EU AI Act — Annex IV Technical Documentation

**System:** {{ agent_name }} v{{ agent_version }}
**Generated:** {{ generated_at }}
**Schema Version:** {{ schema_version }}
**Coverage:** {{ filled_count }}/19 sections auto-filled

---

## Section 1 — General Description of the AI System

**Article Reference:** Annex IV, Section 1

{{ agent_name }} is a {{ system_type }} to produce auditable, compliant AI decisions.

| Property | Value |
|----------|-------|
| System Name | {{ agent_name }} |
| Version | {{ agent_version }} |
{% if has_z3 %}| CSL-Core Version | {{ csl_core_version }} |
{% endif %}| Policy Backend | {{ policy_engine_name }} |
| Deployment Mode | {% if is_standalone %}Standalone (manages LLM directly){% else %}Integration (plug-in for external agent frameworks){% endif %} |

**Architecture:** {{ architecture_desc }}

{% if is_standalone %}
The system operates by:
1. Receiving natural language requests
2. Generating candidate strategies via LLM ({{ llm_provider }} / {{ llm_model }})
3. Evaluating each candidate against policy constraints ({{ policy_engine_name }})
4. Selecting the highest-confidence compliant candidate
5. Producing a complete audit record for every decision
{% else %}
The system operates by:
1. Intercepting actions from external agent frameworks
2. Evaluating each action against policy constraints ({{ policy_engine_name }})
3. Allowing or blocking the action based on policy evaluation
4. Producing a complete audit record for every decision
{% endif %}

---

## Section 2 — Elements of the AI System and Development Process

**Article Reference:** Annex IV, Section 2

{% if is_standalone %}
### 2.1 LLM Component (Neural)

| Property | Value |
|----------|-------|
| Provider | {{ llm_provider }} |
| Model | {{ llm_model }} |
| Temperature | {{ llm_temperature }} |
| Candidates per Attempt | {{ candidates_per_attempt }} |
| Max Retries | {{ max_retries }} |
{% else %}
### 2.1 External Agent Component

| Property | Value |
|----------|-------|
| Mode | Integration — LLM managed by external framework |
| Provider | {{ llm_provider }} |
| Model | {{ llm_model }} |
{% endif %}

### 2.2 Policy Engine (Symbolic)

| Property | Value |
|----------|-------|
| Engine | {{ policy_engine_name }} |
{% if has_z3 %}| Formal Verifier | Z3 SMT Solver |
{% else %}| Verification | {{ verification_method }} |
{% endif %}| Policy File | {{ policy_file }} |
| Policy Hash | {{ policy_hash }} |
| Auto-Verify on Startup | {{ auto_verify }} |
| Domain | {{ policy_domain }} |
| Variables | {{ policy_variable_count }} |
| Constraints | {{ policy_constraint_count }} |
| Verified | {{ policy_verified }} |
{% if policy_verification_errors %}
**Verification Issues:**
{% for err in policy_verification_errors %}
- {{ err }}
{% endfor %}
{% endif %}

### 2.3 Policy Variables

| Variable | Domain |
|----------|--------|
{% for name, domain in policy_variables %}| {{ name }} | {{ domain }} |
{% endfor %}
### 2.4 Policy Constraints

{% for constraint in policy_constraints %}
- **{{ constraint }}**
{% endfor %}

---

## Section 3 — Monitoring, Functioning, and Control

**Article Reference:** Annex IV, Section 3

### 3.1 Decision Pipeline Monitoring

Every decision is monitored through the complete pipeline:

{% if is_standalone %}- **LLM Generation:** Each candidate is tracked with strategy, reasoning, confidence
{% endif %}- **Policy Evaluation:** Every candidate evaluated against all constraints; violations recorded
{% if is_standalone %}- **Retry Mechanism:** Failed attempts feed rejection context back to LLM (max {{ max_retries }} retries)
- **Selection:** Best compliant candidate selected by confidence score
{% endif %}
### 3.2 Audit Configuration

| Property | Value |
|----------|-------|
| Audit Enabled | {{ audit_enabled }} |
| Output Directory | {{ audit_output_dir }} |
| Format | {{ audit_format }} |
| HTML Reports | {{ audit_html_reports }} |
| Retention Days | {{ audit_retention_days }} |

### 3.3 Real-time Controls

- **Policy Hot-Reload:** {{ policy_hot_reload }} — policy changes take effect without restart
{% if is_standalone %}- **Halt Mechanism:** `agent.halt()` immediately stops all decision-making (Art. 14)
- **Resume:** `agent.resume()` reactivates after halt
{% endif %}- **Consecutive Block Alert:** After {{ stop_on_consecutive_blocks }} consecutive blocks

---

## Section 4 — Appropriateness of Performance Metrics

**Article Reference:** Annex IV, Section 4

{% if has_audit_stats %}
### 4.1 Decision Performance (Last {{ stats_period_days }} Days)

| Metric | Value |
|--------|-------|
| Total Decisions | {{ stats_total_decisions }} |
| Allowed | {{ stats_allowed_count }} ({{ stats_allow_rate }}%) |
| Blocked | {{ stats_blocked_count }} ({{ stats_block_rate }}%) |
| Human Overrides | {{ stats_human_override_count }} |
| Interrupted | {{ stats_interrupted_count }} |
| Avg Duration | {{ stats_avg_duration_ms }} ms |
{% if is_standalone %}| Avg Candidates/Decision | {{ stats_avg_candidates }} |
| Avg Attempts/Decision | {{ stats_avg_attempts }} |
{% endif %}| Total Violations | {{ stats_total_violations }} |

### 4.2 Top Constraint Violations

| Constraint | Occurrences |
|------------|-------------|
{% for name, count in top_violations %}| {{ name }} | {{ count }} |
{% endfor %}
{% else %}
> **No audit data available.** Run the agent to generate performance metrics.
{% endif %}

---

## Section 5 — Risk Management System

**Article Reference:** Annex IV, Section 5

{% if has_z3 %}
### 5.1 Formal Verification (Z3)

All policy constraints are formally verified using the Z3 SMT solver before deployment:

1. **Syntax Validation** — CSL parser validates grammar
2. **Semantic Validation** — Type checking, scope analysis
3. **Z3 Logic Verification** — Reachability, consistency, conflict detection
4. **IR Compilation** — Generates runtime guard

**Verification Status:** {% if policy_verified %}✅ Policy verified — constraints are provably consistent{% else %}⚠️ Policy not yet verified{% endif %}
{% else %}
### 5.1 Policy Validation

Policy rules are validated through {{ verification_method }}:

- **Syntax Validation** — YAML structure and expression parsing
- **Expression Safety** — AST-based evaluator (no eval/exec)
- **Rule Completeness** — All referenced variables checked

**Verification Status:** {% if policy_verified %}✅ Policy validation passed{% else %}⚠️ Policy not yet validated{% endif %}
{% endif %}

### 5.2 Risk Mitigation Through Policy Constraints

The system mitigates risks through deterministic policy enforcement:

{% if is_standalone %}- All LLM outputs are validated against policy constraints before execution
{% else %}- All external agent actions are validated against policy constraints before execution
{% endif %}- No action can bypass policy evaluation
- Violations are recorded with full context for investigation
{% if has_audit_stats and stats_total_violations > 0 %}
- **{{ stats_total_violations }} violations** have been caught and prevented in the current period
{% endif %}

### 5.3 Adversarial Resilience (Art. 15)

{% if is_standalone %}- LLM outputs are treated as **untrusted** — every candidate must pass policy verification
{% endif %}- Policy constraints are deterministic and cannot be influenced by external inputs
- The {{ policy_engine_name }} operates independently of the neural component
{% if has_z3 %}- Z3 proves policy consistency — no logical bypass possible
{% endif %}

---

## Section 6 — Description of Changes Throughout Lifecycle

**Article Reference:** Annex IV, Section 6

{% if has_audit_stats %}
System changes are tracked through the audit pipeline:

- **Policy Hash:** Each decision records the exact policy hash at decision time
- **Current Policy Hash:** `{{ policy_hash }}`
- **Decision Count:** {{ stats_total_decisions }} decisions recorded
- **Period:** {{ stats_period_start }} to {{ stats_period_end }}

All changes to policy files trigger re-verification{% if has_z3 %} via Z3{% endif %}.
{% else %}
> **No audit history available.** Deploy the agent to begin tracking changes.
{% endif %}

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
{% if is_standalone %}> The LLM component ({{ llm_provider }} / {{ llm_model }}) is a pre-trained
> external model. Training data documentation is the responsibility of the
> model provider.
{% else %}> This system operates in integration mode — LLM is managed externally.
> Training data documentation is the responsibility of the external agent
> framework and model provider.
{% endif %}>
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
| Active Mode | {{ oversight_mode }} — {{ oversight_mode_desc }} |
| Confirmation Required | {{ require_confirmation }} |
| Override Allowed | {{ allow_override }} |
| Policy Human-Editable | Yes ({% if has_z3 %}CSL{% else %}YAML{% endif %} text files) |
{% if is_standalone %}| Stop Mechanism | `agent.halt()` — immediate cessation |
{% endif %}| Consecutive Block Alert | After {{ stop_on_consecutive_blocks }} blocks |

### 9.2 Available Oversight Modes

| Mode | Description |
|------|-------------|
| **Interactive** | Blocks on stdin; human must approve each decision |
| **SDK/Callback** | Programmatic approval via callback function |
| **Auto** | No human in loop (for batch/testing) |

**Currently Active:** `{{ oversight_mode }}`

### 9.3 Override Capabilities

- **CONFIRM:** Human approves the proposed action
- **OVERRIDE:** Human changes the decision (recorded in audit trail)
{% if is_standalone %}- **STOP:** Human halts the agent entirely
{% endif %}
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
> - Policy file updates (automatically re-verified{% if has_z3 %} via Z3{% endif %})
{% if is_standalone %}> - LLM model upgrades
{% endif %}> - Configuration parameter adjustments

---

## Section 11 — Validation and Testing Procedures

**Article Reference:** Annex IV, Section 11

{% if has_z3 %}
### 11.1 Formal Verification (Z3)

Every CSL policy undergoes four-stage verification before deployment:

1. **Syntax Validation** — Parser checks grammar
2. **Semantic Validation** — Scope, types, function whitelist
3. **Z3 Logic Verification** — Reachability, consistency, conflicts
4. **IR Compilation** — Generates runtime guard
{% else %}
### 11.1 Policy Validation

Every YAML policy undergoes validation before deployment:

1. **Syntax Validation** — YAML structure parsing
2. **Expression Parsing** — AST-based safe expression evaluation
3. **Variable Reference Check** — All rule variables verified
{% endif %}

### 11.2 Runtime Validation

- Each {% if is_standalone %}candidate{% else %}action{% endif %} is evaluated against the {% if has_z3 %}compiled policy{% else %}loaded rules{% endif %} at runtime
- Policy evaluation results include: ALLOWED / BLOCKED + violation details
- All evaluations are recorded in the audit trail

---

## Section 12 — Cybersecurity Measures

**Article Reference:** Annex IV, Section 12 (Art. 15)

### 12.1 Adversarial Resilience

{% if is_standalone %}- **LLM Output Sandboxing:** All LLM outputs pass through deterministic policy gate
{% endif %}{% if has_z3 %}- **Formal Verification:** Z3 proves policy consistency — no logical bypass possible
{% else %}- **Rule-Based Enforcement:** Deterministic policy evaluation — no logical bypass possible
{% endif %}- **Input Validation:** {% if is_standalone %}Candidate{% else %}Action{% endif %} parameters are validated against policy variable domains
{% if is_standalone %}- **No Direct Execution:** LLM cannot execute actions; it only proposes candidates
{% endif %}

### 12.2 Data Protection

- **API Keys:** Never serialized to disk (excluded from config.to_dict())
- **Audit Records:** Immutable after creation
- **Retention Enforcement:** Automatic cleanup after {{ audit_retention_days }} days
{% if not has_z3 %}- **Safe Expression Evaluator:** Uses `ast` module — no `eval()` or `exec()` used
{% endif %}

---

## Section 13 — Computing Infrastructure

**Article Reference:** Annex IV, Section 13

| Component | Infrastructure |
|-----------|---------------|
{% if is_standalone %}| LLM Provider | {{ llm_provider }} |
| LLM Model | {{ llm_model }} |
{% else %}| LLM Provider | External (managed by agent framework) |
{% endif %}| Policy Engine | {{ policy_engine_name }} |
{% if has_z3 %}| Formal Verifier | Z3 SMT Solver (local) |
{% endif %}| Audit Storage | Local filesystem ({{ audit_output_dir }}) |
| Runtime | Python {{ python_version }} |
| Platform | {{ os_platform }} |

### 13.1 Installed Dependencies

| Package | Version |
|---------|---------|
{% for dep in installed_deps %}| {{ dep.name }} | {{ dep.version }} |
{% endfor %}

---

## Section 14 — Description of Input Data

**Article Reference:** Annex IV, Section 14

### 14.1 Decision Input Format

{% if is_standalone %}
Each decision receives:

| Field | Type | Description |
|-------|------|-------------|
| `request` | string | Natural language request |
| `context` | dict | Session context (role, user_id, etc.) |
{% else %}
Each compliance check receives:

| Field | Type | Description |
|-------|------|-------------|
| `action_name` | string | Name of the action to validate |
| `parameters` | dict | Action parameters to evaluate |
| `context` | dict | Optional session context |
{% endif %}

### 14.2 Policy Variable Inputs

{% if is_standalone %}Candidates generate parameters that map to policy variables:{% else %}Action parameters are mapped to policy variables:{% endif %}

| Variable | Domain |
|----------|--------|
{% for name, domain in policy_variables %}| {{ name }} | {{ domain }} |
{% endfor %}

---

## Section 15 — Description of Output

**Article Reference:** Annex IV, Section 15

{% if is_standalone %}
### 15.1 DecisionResult

| Field | Type | Description |
|-------|------|-------------|
| `result` | enum | ALLOWED, BLOCKED, HUMAN_OVERRIDE, INTERRUPTED |
| `action` | string | Selected strategy description |
| `explanation` | string | Human-readable reasoning |
| `parameters` | dict | Final action parameters |
| `audit` | DecisionAuditRecord | Complete audit trail |
{% else %}
### 15.1 PolicyEvaluation

| Field | Type | Description |
|-------|------|-------------|
| `result` | string | ALLOWED or BLOCKED |
| `policy_file` | string | Policy file used |
| `policy_hash` | string | SHA-256 hash of policy at evaluation time |
| `violations` | list | List of constraint violations (if any) |
| `duration_ms` | float | Evaluation time in milliseconds |
{% endif %}

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
- **Threshold Alert:** Configured at {{ stop_on_consecutive_blocks }} consecutive blocks
{% if is_standalone %}- **Decision Counter:** Running total for utilization monitoring
{% endif %}

---

## Section 17 — Description of Changes

**Article Reference:** Annex IV, Section 17

{% if has_audit_stats %}
All system changes are captured in the audit trail:

- **Policy changes** are detected via hash comparison and trigger re-verification{% if has_z3 %} via Z3{% endif %}

- **Configuration changes** are reflected in the agent info section of each audit record
{% if is_standalone %}- **Model changes** are captured in the agent info (model, provider, temperature)
{% endif %}- **{{ stats_total_decisions }} decisions** have been recorded to date
{% else %}
> **No change history available.** Deploy the agent to begin tracking changes.
{% endif %}

---

## Section 18 — Relevant Information About Datasets

**Article Reference:** Annex IV, Section 18

> ⚠️ **MANUAL INPUT REQUIRED**
>
{% if is_standalone %}> Note: The LLM component is externally trained by {{ llm_provider }}.
> Refer to the model provider's documentation for training data details.
{% else %}> Note: This system operates in integration mode. The LLM is managed by
> the external agent framework. Refer to the framework and model provider's
> documentation for training data details.
{% endif %}>
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

*Generated by {{ agent_name }} v{{ agent_version }} — Annex IV Documentation Generator*
*Policy backend: {{ policy_engine_name }} | Python {{ python_version }}{% if has_z3 %} | CSL-Core: {{ csl_core_version }}{% endif %}*
