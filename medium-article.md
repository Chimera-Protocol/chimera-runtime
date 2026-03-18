# I Built an Open-Source Compliance Layer for AI Agents — Here's Why Every Agent Needs a Policy Guard

*The EU AI Act takes effect in August 2026. Your AI agents aren't ready. Mine weren't either — so I built Chimera Runtime.*

---

AI agents are everywhere. They approve expenses, write code, send emails, make hiring decisions. But here's the uncomfortable truth:

**Nobody is auditing what they do.**

Not the tool calls. Not the reasoning. Not the decisions that get blocked — or worse, the ones that don't. When the EU AI Act enforcement begins in August 2026, every high-risk AI system will need:

- A complete audit trail for every decision
- Deterministic safety constraints (not vibes-based guardrails)
- Human oversight mechanisms
- Right to explanation for affected individuals

I spent the last several months building **chimera-runtime** — an open-source compliance layer that plugs into any AI agent framework and enforces policy guards before every action executes.

Today, I'm releasing it publicly.

---

## The Problem: AI Agents Are Ungoverned

Consider a typical LangChain agent that handles financial operations. It can:

- Approve budget allocations
- Transfer funds between departments
- Generate compliance reports

Without guardrails, a single hallucination or prompt injection could trigger a $500K transfer that nobody reviewed. The agent's "reasoning" lives in a chat log that nobody audits.

**Current solutions fall short:**

- **Prompt-based guardrails** — "Please don't approve amounts over $100K" is not a safety mechanism. It's a suggestion.
- **Output filters** — Catching bad outputs after execution is too late. The action already happened.
- **Manual review queues** — Don't scale. Agents make thousands of decisions per hour.

What's needed is a **deterministic gate** that sits between the agent's intent and the action's execution. A gate that cannot be prompt-injected, cannot be reasoned around, and produces an immutable audit record every single time.

---

## The Solution: Deterministic Policy Guards

**chimera-runtime** intercepts every agent action and evaluates it against a policy before execution. The result is always one of three outcomes:

- **ALLOW** — Action proceeds, audit record created
- **BLOCK** — Action stopped, violation recorded with explanation
- **ASK_HUMAN** — Action paused, human confirmation required

```
Agent Intent → Policy Guard → ALLOW / BLOCK / ASK_HUMAN → Audit Record
```

The key insight: **policies are not AI-generated.** They're deterministic rules — either YAML-based or formally verified using Z3 theorem prover via CSL (Chimera Specification Language).

This means a policy constraint like "Managers cannot approve more than $250,000" is mathematically guaranteed to be enforced. No prompt can override it. No chain-of-thought can reason around it.

### A Simple Policy in YAML

```yaml
rules:
  - name: manager_limit
    when: "role == 'MANAGER' and amount > 250000"
    then: BLOCK
    message: "Managers cannot approve more than $250,000"

  - name: weekend_freeze
    when: "is_weekend == 'YES' and urgency != 'CRITICAL'"
    then: BLOCK
    message: "No changes on weekends unless critical"
```

### The Same Policy with Z3 Formal Verification (CSL)

```
DOMAIN GovernanceGuard {
  VARIABLES {
    amount: 0..1000000
    role: {"ANALYST", "MANAGER", "DIRECTOR", "VP", "CEO"}
  }

  STATE_CONSTRAINT manager_approval_limit {
    WHEN role == "MANAGER"
    THEN amount <= 250000
  }
}
```

When you verify a CSL policy, the Z3 theorem prover checks it for:

- **Reachability** — Can each constraint actually trigger?
- **Internal consistency** — Do constraints contradict each other?
- **Pairwise conflicts** — Can two rules create a deadlock?
- **Policy-wide satisfiability** — Is the entire policy logically sound?

This is not a linter. It's formal verification — the same technique used to verify hardware circuits and flight control systems.

---

## What the Dashboard Looks Like

chimera-runtime ships with a full compliance dashboard. Here's what you get:

### Real-Time Decision Monitoring

<!-- [INSERT: dashboard.png] -->

Every agent decision appears in real-time — ALLOWED, BLOCKED, or ESCALATED. The EU AI Act compliance score (top right) tracks coverage across all six articles. Top violations surface the constraints that fire most often.

### Policy Management with Formal Verification

<!-- [INSERT: policy.png] -->

Create, edit, and verify policies directly in the dashboard. Each policy shows its constraints, variables, and Z3 verification status. A green "Z3 SAT" badge means the policy is formally verified — logically consistent and free of contradictions.

### Analytics — Decision Trends & Heatmaps

<!-- [INSERT: analytics.png] -->

The analytics view shows decision trends over time, block rate heatmaps by hour/day, and violation frequency across all agents. This is critical for compliance reporting — you can see exactly when and why decisions were blocked.

### Connect Any Framework in 4 Steps

<!-- [INSERT: framework.png] -->

The Connect Agent wizard generates integration code for LangChain, LangGraph, CrewAI, LlamaIndex, or AutoGen. Select your framework, pick a policy, and get copy-paste code.

---

## Framework Integrations

chimera-runtime works with every major agent framework. Here's how integration looks:

### LangChain — 3 Lines

```python
from chimera_runtime.integrations.langchain import wrap_tools

guarded_tools = wrap_tools(
    your_tools,
    policy="./policies/governance.yaml"
)
# Use guarded_tools instead of your_tools — done.
```

### LangGraph — Add a Compliance Node

```python
from chimera_runtime.integrations.langgraph import compliance_node

graph.add_node(
    "compliance_check",
    compliance_node(policy="./policies/governance.yaml")
)
```

### Direct Usage (No Framework)

```python
from chimera_runtime import ChimeraAgent

agent = ChimeraAgent(
    model="gpt-4o",
    api_key="sk-...",
    policy="./policies/governance.csl",
)

result = agent.decide(
    "Approve $200k marketing spend for Q3",
    context={"role": "MANAGER", "department": "MARKETING"},
)

print(result.result)  # "ALLOWED"
```

Also supports **CrewAI**, **LlamaIndex**, **AutoGen**, and any raw LLM provider (OpenAI, Anthropic, Google, Ollama).

---

## EU AI Act Coverage

The EU AI Act is not optional. It applies to any AI system operating in or affecting EU citizens. Here's what chimera-runtime covers:

| Article | What It Requires | How Chimera Handles It |
|---------|-----------------|----------------------|
| **Art. 9** | Risk management system | Z3 formal verification of all policy constraints |
| **Art. 12** | Record-keeping | Complete audit record for every single decision |
| **Art. 13** | Transparency | Query any decision, get full reasoning chain |
| **Art. 14** | Human oversight | Halt, resume, or override any agent at any time |
| **Art. 86** | Right to explanation | One-click HTML reports per decision |
| **Annex IV** | Technical documentation | Auto-generated documentation (14/19 sections) |

The compliance dashboard tracks your coverage score across all articles in real-time.

---

## How It Works Under the Hood

The architecture is intentionally simple:

1. **Agent makes a decision** — Any framework, any LLM provider
2. **Policy Guard intercepts** — Before the action executes
3. **Constraints evaluated** — YAML rules or Z3 SAT solving
4. **Result: ALLOW, BLOCK, or ASK_HUMAN**
5. **Audit record created** — Immutable, timestamped, with full context
6. **Action executes (or doesn't)** — Based on policy result

Key design decisions:

- **No network dependency for enforcement** — Policies evaluate locally. Your agent doesn't slow down waiting for an API call.
- **Deterministic, not probabilistic** — A blocked action is always blocked. Not "95% likely to be blocked."
- **Framework agnostic** — The compliance layer doesn't care if you're using LangChain or a bash script calling curl. If it makes decisions, it can be guarded.
- **Audit records are append-only** — Once written, they cannot be modified or deleted.

---

## Getting Started

```bash
pip install chimera-runtime

chimera-runtime init
chimera-runtime test --skip-llm  # verify everything works
chimera-runtime run              # start the agent
```

The dashboard is live at [runtime.chimera-protocol.com](https://runtime.chimera-protocol.com).

The code is open-source: [github.com/Chimera-Protocol/chimera-runtime](https://github.com/Chimera-Protocol/chimera-runtime)

---

## What's Next

The EU AI Act deadline is **August 2026**. That's not far away. If you're building AI agents for enterprise use — especially in finance, healthcare, HR, or legal — compliance is not a nice-to-have. It's a legal requirement.

chimera-runtime is the foundation. The policy guard that sits between your agent and the real world. The audit trail that proves your system is governed. The formal verification that guarantees your constraints hold.

**Try it. Break it. Tell me what's missing.**

```bash
pip install chimera-runtime
```

---

*chimera-runtime is open-source under the Apache 2.0 license. Built by [Aytug Akarlar](https://github.com/akarlaraytu).*

*If you're working on AI governance, I'd love to hear from you — reach out through the [dashboard contact form](https://runtime.chimera-protocol.com/contact) or open an issue on GitHub.*

---

**Tags:** `#AI` `#ArtificialIntelligence` `#EUAIAct` `#Compliance` `#OpenSource` `#LangChain` `#AIAgents` `#FormalVerification` `#Python` `#AIGovernance`
