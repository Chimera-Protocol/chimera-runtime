# I Generated EU AI Act Annex IV Documentation for My AI Agent With a Single Command

*The EU AI Act requires 19 sections of technical documentation for high-risk AI systems. I automated 14 of them.*

---

If you're building AI agents for enterprise use, you've probably heard about the EU AI Act. What you might not know is that **Annex IV** — the technical documentation requirement — is one of the most labour-intensive compliance obligations in the entire regulation.

Every high-risk AI system must produce detailed technical documentation covering 19 sections: system architecture, risk management, human oversight measures, validation procedures, cybersecurity, performance metrics, post-market monitoring, and more.

For most companies, this means weeks of work. Lawyers drafting. Engineers reviewing. Compliance teams cross-referencing. Version after version of Word documents passed around in email chains.

I took a different approach.

```bash
chimera-runtime docs generate
```

One command. 14 of 19 sections auto-filled. A complete, structured Markdown document ready for review.

<!-- [IMAGE: screenshot of the terminal output below — use a tool like carbon.sh or terminal screenshot] -->

```
╭──────────────────── 📄 Annex IV Documentation Generated ─────────────────────╮
│                                                                              │
│  Output:   docs/annex_iv_technical_documentation.md                          │
│  Coverage: 14/19 sections auto-filled                                        │
│  Manual:   5 sections require manual input                                   │
│                                                                              │
╰──────────────────────────────────────────────────────────────────────────────╯

  ✏️  Manual sections to complete:
     Section 7: Harmonised Standards Applied
     Section 8: Description of Data Used
     Section 10: Pre-determined Changes
     Section 18: Relevant Information About Datasets
     Section 19: EU Declaration of Conformity
```

Here's how I built it, what it generates, and why this matters for anyone deploying AI agents in production.

---

## What Is Annex IV, and Why Should You Care?

The EU AI Act (Regulation 2024/1689) classifies AI systems by risk level. If your system falls into the **high-risk** category — think finance, healthcare, HR, legal, critical infrastructure — you need to comply with Articles 9 through 15, plus produce the technical documentation specified in **Annex IV**.

Annex IV lists 19 sections that must be documented:

1. General description of the AI system
2. Elements and development process
3. Monitoring, functioning, and control
4. Performance metrics
5. Risk management system
6. Changes throughout lifecycle
7. Harmonised standards applied
8. Description of data used
9. Human oversight measures
10. Pre-determined changes
11. Validation and testing procedures
12. Cybersecurity measures
13. Computing infrastructure
14. Input data description
15. Output description
16. Post-market monitoring plan
17. Description of changes
18. Dataset information
19. EU Declaration of Conformity

Most of these require specific technical details: what model you're using, what safety constraints exist, how decisions are audited, what your oversight mechanisms look like.

If you're already running a compliance-aware agent, **this information already exists in your system**. It's in your config files, your policy definitions, your audit logs, and your runtime metadata.

The question is: why are humans rewriting it into a Word document?

---

## The Architecture Behind One-Click Generation

I built an `AnnexIVGenerator` class inside **chimera-runtime** that pulls data from three sources:

### Source 1: Agent Configuration

The `.chimera/config.yaml` file contains your agent's identity — name, version, LLM provider, model, temperature, retry settings, audit configuration, and oversight mode.

```yaml
agent:
  name: chimera-runtime
  version: 0.1.0

llm:
  provider: openai
  model: gpt-4o
  temperature: 0.7
  candidates_per_attempt: 3
  max_retries: 3

audit:
  enabled: true
  output_dir: ./audit_logs
  retention_days: 180

oversight:
  require_confirmation: false
  allow_override: true
```

This feeds into Sections 1 (General Description), 2 (Development Process), 3 (Monitoring & Control), 9 (Human Oversight), 12 (Cybersecurity), and 13 (Computing Infrastructure).

### Source 2: Policy Files

chimera-runtime enforces deterministic policy constraints — either YAML rules or CSL (Chimera Specification Language) policies verified by the Z3 theorem prover.

```
DOMAIN GovernanceGuard {
  VARIABLES {
    amount: 0..1000000
    role: {"ANALYST", "MANAGER", "DIRECTOR", "VP", "CEO"}
    urgency: {"LOW", "MEDIUM", "HIGH", "CRITICAL"}
  }

  STATE_CONSTRAINT manager_approval_limit {
    WHEN role == "MANAGER"
    THEN amount <= 250000
  }

  STATE_CONSTRAINT weekend_freeze {
    WHEN is_weekend == "YES"
    THEN urgency == "CRITICAL"
  }
}
```

The generator extracts: domain name, variable definitions with their types and ranges, constraint names, policy hash (SHA-256), and verification status.

This feeds into Sections 2 (Policy Engine details), 5 (Risk Management), 11 (Validation & Testing), and 14 (Input Data Description).

Here's what it looks like when you verify a policy — the Z3 theorem prover checks mathematical consistency:

<!-- [IMAGE: screenshot of the terminal output below] -->

```
⚡ Verifying: policies/governance.csl

⚙️  Compiling Domain: GovernanceGuard
   • Validating Syntax... ✅ OK
   ├── Verifying Logic Model (Z3 Engine)... ✅ Mathematically Consistent
   • Generating IR... ✅ OK
✅ Policy Verified
├── 📋 Metadata
│   ├── Domain:      GovernanceGuard
│   ├── Hash:        sha256:3a8dc2bdcec45c482094ba6dea5c57d72d3a11cff0990a6b7234364ccbb43a71
│   ├── Constraints: 7
│   └── Variables:   6
├── ⚡ Constraints
│   ├── analyst_no_spend
│   ├── manager_approval_limit
│   ├── director_approval_limit
│   ├── vp_approval_limit
│   ├── single_channel_cap
│   ├── weekend_freeze
│   └── absolute_ceiling
└── 📊 Variables
    ├── amount: 0..1000000
    ├── channel: {"DIGITAL", "TV", "PRINT", "RADIO", "ALL"}
    ├── department: {"MARKETING", "ENGINEERING", "FINANCE", "OPERATIONS", "HR"}
    ├── is_weekend: {"YES", "NO"}
    ├── role: {"ANALYST", "MANAGER", "DIRECTOR", "VP", "CEO"}
    └── urgency: {"LOW", "MEDIUM", "HIGH", "CRITICAL"}
```

All of this metadata — the domain, hash, variables, constraints, verification status — is automatically extracted and injected into the Annex IV document.

### Source 3: Audit Logs

Every decision chimera-runtime makes produces an immutable JSON audit record — the `DecisionAuditRecord`. These records contain timestamps, reasoning traces, policy evaluation results, violations, performance metrics, and human oversight actions.

The generator aggregates these into real statistics:

- Total decisions, block rate, allow rate
- Top constraint violations by frequency
- Average decision duration
- Candidates per decision, retry counts
- Period covered

This feeds into Sections 4 (Performance Metrics), 6 (Lifecycle Changes), 16 (Post-Market Monitoring), and 17 (Change Description).

Here's a real `chimera-runtime audit --stats` output from my system:

<!-- [IMAGE: screenshot of the terminal output below] -->

```
╭──────────────────────────── 📊 Audit Statistics ─────────────────────────────╮
│                                                                              │
│    Metric                                Value                               │
│   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━       │
│    Total Decisions                          24   ████████████████            │
│    ✅ Allowed                       15 (62.5%)                               │
│    🚫 Blocked                        9 (37.5%)                               │
│    🧑 Human Override                         0                               │
│    ⏸️  Interrupted                            0                               │
│                                                                              │
│    Avg Duration                        654.5ms                               │
│    Avg Candidates                          1.4                               │
│    Total Violations                         22                               │
│    Period              2026-02-26 → 2026-03-08                               │
│                                                                              │
╰──────────────────────────────────────────────────────────────────────────────╯
```

24 decisions, 9 blocked, 22 violations caught. All of this flows directly into the Annex IV document — no manual data entry.

---

## What Gets Generated

Here's what the output actually looks like. Running `chimera-runtime docs generate` produces a structured Markdown document with every section properly formatted:

**Section 1** includes a system overview table with name, version, architecture type, and deployment mode — automatically determined based on whether you're running standalone or as a plug-in to LangChain/LangGraph/CrewAI.

**Section 2** breaks down your system into its neural (LLM) and symbolic (policy engine) components. If you're using CSL with Z3, it notes the formal verifier. It lists every policy variable with its domain and every constraint by name.

**Section 4** pulls real performance data from your audit logs — total decisions, block/allow rates, average duration, and the top constraint violations with occurrence counts.

**Section 5** details your risk management approach. If Z3 is enabled, it documents the four-stage formal verification pipeline (syntax, semantic, Z3 logic, IR compilation). It reports how many violations have been caught and prevented.

**Section 9** documents your human oversight configuration — which mode is active (interactive, SDK callback, or auto), whether confirmation is required, whether override is allowed, and all available oversight actions (CONFIRM, OVERRIDE, STOP).

**Section 12** covers cybersecurity: LLM output sandboxing, formal verification guarantees, input validation against policy domains, API key protection, and data retention enforcement.

The remaining auto-filled sections (3, 6, 11, 13, 14, 15, 16, 17) follow the same pattern — pulling real data from your running system.

**5 sections** (7, 8, 10, 18, 19) are marked as "Manual Input Required" with clear guidance on what to fill in. These are organisation-specific — harmonised standards, training data descriptions, pre-determined changes, dataset details, and the EU Declaration of Conformity.

---

## The Full CLI Experience

Let me walk you through the complete workflow — every command, every output, exactly as it appears in the terminal.

### Step 1: Check Your Policies

Before generating documentation, verify your policies are valid. The Z3 theorem prover checks mathematical consistency:

<!-- [IMAGE: screenshot of the terminal output below] -->

```
$ chimera-runtime policy list

                         📜 Policies in ./policies
╭──────────────────┬─────────────────┬─────────────┬───────────┬──────────╮
│ File             │ Domain          │ Constraints │ Variables │ Status   │
├──────────────────┼─────────────────┼─────────────┼───────────┼──────────┤
│ governance.csl   │ GovernanceGuard │      7      │     6     │ ✅ Valid │
│ paymentguard.csl │ PaymentGuard    │      0      │     0     │ ✅ Valid │
│ starter.csl      │ HelloWorld      │      1      │     2     │ ✅ Valid │
│ governance.yaml  │ GovernanceGuard │      7      │     6     │ ✅ Valid │
│ starter.yaml     │ StarterGuard    │      1      │     2     │ ✅ Valid │
╰──────────────────┴─────────────────┴─────────────┴───────────┴──────────╯
```

### Step 2: Simulate a Policy (Optional)

You can test your policy against specific inputs before deployment. Here's a manager trying to approve $500K — and getting blocked by two constraints:

<!-- [IMAGE: screenshot of the terminal output below] -->

```
$ chimera-runtime policy simulate policies/governance.csl \
    '{"amount": 500000, "role": "MANAGER", "channel": "DIGITAL",
      "department": "MARKETING", "is_weekend": "NO", "urgency": "HIGH"}'

╭────────────────────────────  Case 1  🚫 BLOCKED  ────────────────────────────╮
│  Input         {"amount": 500000, "role": "MANAGER", "channel": "DIGITAL",…  │
│  Duration      0.040ms                                                       │
│  Violation     manager_approval_limit: Violation 'manager_approval_limit':   │
│                amount=500000 must be <= 250000.                              │
│  Violation     single_channel_cap: Violation 'single_channel_cap':           │
│                amount=500000 must be <= 300000.                              │
╰──────────────────────────────────────────────────────────────────────────────╯
```

The same manager with $100K? Passes cleanly:

```
$ chimera-runtime policy simulate policies/governance.csl \
    '{"amount": 100000, "role": "MANAGER", "channel": "DIGITAL",
      "department": "MARKETING", "is_weekend": "NO", "urgency": "HIGH"}'

╭────────────────────────────  Case 1  ✅ ALLOWED  ────────────────────────────╮
│  Input         {"amount": 100000, "role": "MANAGER", "channel": "DIGITAL",…  │
│  Duration      0.030ms                                                       │
╰──────────────────────────────────────────────────────────────────────────────╯
```

### Step 3: Review Audit Trail

After running your agent in production, check what happened:

<!-- [IMAGE: screenshot of the terminal output below] -->

```
$ chimera-runtime audit --last 5

                                📋 Audit Records
╭──────────────────────────┬───────────────┬┬──────────┬───────────────────────╮
│ Decision ID              │ Result        ││ Duration │ Timestamp             │
├──────────────────────────┼───────────────┼┼──────────┼───────────────────────┤
│ dec_17a533a0366b4ffba1c0 │ 🚫 BLOCKED    ││    0.2ms │ 2026-03-08T11:27:55.2 │
│ dec_3ec8bb443e69471f8150 │ ✅ ALLOWED    ││    0.1ms │ 2026-03-08T11:27:55.1 │
│ dec_54bca9db05e0474290cb │ 🚫 BLOCKED    ││    0.1ms │ 2026-03-08T11:27:55.1 │
│ dec_57fa1911ff95484b8de6 │ ✅ ALLOWED    ││    0.1ms │ 2026-03-08T11:27:55.1 │
│ dec_e5fd7678062747f3a072 │ ✅ ALLOWED    ││    0.1ms │ 2026-03-08T11:27:55.0 │
╰──────────────────────────┴───────────────┴┴──────────┴───────────────────────╯
  Total: 5 records
```

And see which constraints are firing most often:

<!-- [IMAGE: screenshot of the terminal output below] -->

```
$ chimera-runtime audit --violations

                  ⚠️  Top Constraint Violations
╭──────┬─────────────────────────┬───────┬──────────────────────╮
│    # │ Constraint              │ Count │                      │
├──────┼─────────────────────────┼───────┼──────────────────────┤
│    1 │ single_channel_cap      │     8 │ ████████████████     │
│    2 │ manager_approval_limit  │     3 │ ██████               │
│    3 │ director_approval_limit │     2 │ ████                 │
│    4 │ analyst_no_spend        │     2 │ ████                 │
│    5 │ amount_limit            │     2 │ ████                 │
│    6 │ admin_required          │     2 │ ████                 │
│    7 │ limit_large_transfers   │     2 │ ████                 │
│    8 │ absolute_ceiling        │     1 │ ██                   │
╰──────┴─────────────────────────┴───────┴──────────────────────╯
```

### Step 4: Generate the Documentation

Now the main event — one command:

<!-- [IMAGE: screenshot of the terminal output below — this is the hero image for the article] -->

```
$ chimera-runtime docs generate

⚙️  Compiling Domain: GovernanceGuard
   • Validating Syntax... ✅ OK
   ├── Verifying Logic Model (Z3 Engine)... ✅ Mathematically Consistent
   • Generating IR... ✅ OK

╭──────────────────── 📄 Annex IV Documentation Generated ─────────────────────╮
│                                                                              │
│  Output:   docs/annex_iv_technical_documentation.md                          │
│  Coverage: 14/19 sections auto-filled                                        │
│  Manual:   5 sections require manual input                                   │
│                                                                              │
╰──────────────────────────────────────────────────────────────────────────────╯

  ✏️  Manual sections to complete:
     Section 7: Harmonised Standards Applied
     Section 8: Description of Data Used
     Section 10: Pre-determined Changes
     Section 18: Relevant Information About Datasets
     Section 19: EU Declaration of Conformity
```

### Step 5: Check Coverage Anytime

Want to see where you stand without regenerating?

<!-- [IMAGE: screenshot of the terminal output below] -->

```
$ chimera-runtime docs status

📄 Annex IV Documentation Status
├── ██████████████░░░░░  14/19 (74%)
├── 📡 Data Sources
│   ├── ✅ Audit data
│   └── ✅ Policy data
├── ✅ Auto-filled (14)
│   ├── Section 1: General Description of the AI System
│   ├── Section 2: Elements of the AI System and Development Process
│   ├── Section 3: Monitoring, Functioning, and Control
│   ├── Section 4: Appropriateness of Performance Metrics
│   ├── Section 5: Risk Management System
│   ├── Section 6: Description of Changes Throughout Lifecycle
│   ├── Section 9: Human Oversight Measures
│   ├── Section 11: Validation and Testing Procedures
│   ├── Section 12: Cybersecurity Measures
│   ├── Section 13: Computing Infrastructure
│   ├── Section 14: Description of Input Data
│   ├── Section 15: Description of Output
│   ├── Section 16: Post-Market Monitoring Plan
│   └── Section 17: Description of Changes
└── ✏️  Manual Required (5)
    ├── Section 7: Harmonised Standards Applied
    ├── Section 8: Description of Data Used
    ├── Section 10: Pre-determined Changes
    ├── Section 18: Relevant Information About Datasets
    └── Section 19: EU Declaration of Conformity
```

That progress bar — `██████████████░░░░░ 14/19 (74%)` — tells you exactly where you stand.

As your agent runs and produces more audit data, just run `chimera-runtime docs refresh` to update the document with the latest statistics.

---

## Smart Template Logic

The generator isn't a simple find-and-replace. The Jinja2 template adapts based on your actual configuration:

**Standalone vs. Integration mode:** If you're using `ChimeraAgent` directly (standalone), the document describes candidate generation, retry loops, and selection logic. If you're wrapping LangChain or CrewAI tools (integration mode), it describes action interception and validation.

**CSL vs. YAML:** If your policy uses CSL with Z3, the document references formal verification, SMT solving, and mathematical consistency proofs. If you're using YAML rules, it describes rule-based validation with AST-based safe expression evaluation.

**With vs. without audit data:** Performance sections only appear when you have actual decision history. Without audit logs, those sections show a clear message: "No audit data available. Run the agent to generate performance metrics."

This means the document is always accurate — it reflects what your system actually does, not what a template assumes.

---

## From Generation to Submission

The generated document covers the technical core. Here's how a realistic workflow looks:

1. **Run your agent** in production (or staging) for a meaningful period
2. **Generate:** `chimera-runtime docs generate`
3. **Review** the 14 auto-filled sections — verify accuracy
4. **Complete** the 5 manual sections with your organisation's specifics
5. **Export** to your preferred format (the Markdown converts cleanly to PDF or DOCX)
6. **Submit** as part of your conformity assessment

The key insight: **steps 1 and 2 take seconds**. The document writes itself from your system's actual state. Your compliance team spends their time on the 5 sections that genuinely require human judgment — not retyping your config into a spreadsheet.

---

## Why This Matters Now

The EU AI Act enforcement begins in **August 2026**. That's not a distant deadline — it's a few months away.

If you're deploying AI agents in finance, healthcare, HR, or legal — or if your agents make decisions that affect EU citizens — you will need this documentation.

Most teams don't even know Annex IV exists yet. The ones who do are staring at 19 sections wondering where to start.

The answer: start by making your agent auditable. Once your system has policy constraints, audit trails, and human oversight mechanisms, the documentation writes itself.

chimera-runtime handles all of this:

- **Deterministic policy guards** (YAML or Z3-verified CSL)
- **Complete audit trails** for every decision (Article 12)
- **Human oversight** with confirm, override, and stop (Article 14)
- **Right to explanation** with one-click HTML reports (Article 86)
- **Annex IV documentation** auto-generated from your live system

```bash
pip install chimera-runtime

chimera-runtime init
chimera-runtime docs generate
```

Two commands from zero to a 14/19 Annex IV document.

---

## Try It Yourself

The code is open-source under Apache 2.0:

- **GitHub:** [github.com/Chimera-Protocol/chimera-runtime](https://github.com/Chimera-Protocol/chimera-runtime)
- **Dashboard:** [runtime.chimera-protocol.com](https://runtime.chimera-protocol.com)
- **PyPI:** `pip install chimera-runtime`

Works with LangChain, LangGraph, CrewAI, LlamaIndex, AutoGen — or standalone with OpenAI, Anthropic, Google, and Ollama.

The EU AI Act deadline is coming. Your documentation doesn't have to be painful.

---

*Built by [Aytug Akarlar](https://github.com/akarlaraytu). If you're working on AI compliance, I'd love to hear from you — open an issue on GitHub or reach out through the [dashboard](https://runtime.chimera-protocol.com).*

---

**Tags:** `#EUAIAct` `#AnnexIV` `#AICompliance` `#AIGovernance` `#OpenSource` `#Python` `#AIAgents` `#LangChain` `#FormalVerification` `#TechnicalDocumentation`
