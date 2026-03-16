# Quickstart

Get chimera-compliance running in under 5 minutes.

---

## Installation

```bash
pip install chimera-compliance
```

## Initialize a Project

chimera-compliance supports two modes:

### Integration Mode (recommended for most teams)

Use this when you already have an AI agent framework (LangChain, LangGraph, CrewAI, etc.) and want to add compliance.

```bash
chimera-compliance init --mode integration
```

The wizard will ask you to:
1. Select your agent framework (LangChain, LangGraph, CrewAI, LlamaIndex, AutoGen)
2. Choose a policy format (YAML or CSL)
3. Set policy file path
4. Set audit log directory and retention period

This creates:
```
.chimera/config.yaml     # Project configuration
policies/starter.yaml    # Starter policy (your rules go here)
audit_logs/              # Audit log directory
```

### Standalone Mode

Use this when chimera-compliance manages the LLM directly (no external framework).

```bash
chimera-compliance init --mode standalone
```

Additional prompts:
- LLM provider (OpenAI, Anthropic, Google, Ollama)
- Model name
- API key (or set via `CHIMERA_API_KEY` env var)
- Temperature

### Non-Interactive

```bash
chimera-compliance init --non-interactive
```

Uses defaults: standalone mode, YAML policy format, `./policies/starter.yaml`, `./audit_logs/`, 180-day retention.

---

## Verify Your Setup

```bash
chimera-compliance test --skip-llm
```

This runs 8 validation steps:
1. Config loading
2. Policy loading
3. Policy verification
4. Policy simulation (with sample inputs)
5. LLM connection (skipped with `--skip-llm`)
6. Audit write test
7. Audit read test
8. Integration availability check

---

## Write Your First Policy

Edit `policies/starter.yaml`:

```yaml
domain: MyAppGuard

variables:
  amount: "0..1000000"
  role: "{ANALYST, MANAGER, DIRECTOR}"
  action: "{APPROVE, DENY}"

rules:
  - name: analyst_no_spend
    when: "role == 'ANALYST' and amount > 0"
    then: BLOCK
    message: "Analysts cannot approve any spend"

  - name: manager_limit
    when: "role == 'MANAGER' and amount > 250000"
    then: BLOCK
    message: "Managers cannot approve more than $250,000"
```

### Test the Policy

```bash
# Should be ALLOWED — Manager with $50,000
chimera-compliance policy simulate policies/starter.yaml '{"amount": 50000, "role": "MANAGER"}'

# Should be BLOCKED — Manager with $500,000
chimera-compliance policy simulate policies/starter.yaml '{"amount": 500000, "role": "MANAGER"}'

# Should be BLOCKED — Analyst with any amount
chimera-compliance policy simulate policies/starter.yaml '{"amount": 100, "role": "ANALYST"}'
```

---

## Use with Your Agent Framework

### LangChain

```bash
pip install chimera-compliance[langchain]
```

```python
from langchain_core.tools import tool
from chimera_compliance.integrations.langchain import wrap_tools

@tool
def approve_budget(amount: int, department: str) -> str:
    """Approve a budget allocation."""
    return f"Approved ${amount} for {department}"

# Wrap tools with compliance guard
guarded_tools = wrap_tools(
    tools=[approve_budget],
    policy="./policies/starter.yaml",
)

# Use guarded_tools in your LangChain agent as normal.
# Every tool call is now checked against the policy and audited.
```

### LangGraph

```bash
pip install chimera-compliance[langgraph]
```

```python
from chimera_compliance.integrations.langgraph import compliance_node, compliance_edge

# Add a compliance gate node to your graph
check = compliance_node(policy="./policies/starter.yaml")
route = compliance_edge(allowed_node="execute", blocked_node="report_block")

graph.add_node("compliance", check)
graph.add_edge("agent", "compliance")
graph.add_conditional_edges("compliance", route)
```

### CrewAI

```bash
pip install chimera-compliance[crewai]
```

```python
from chimera_compliance.integrations.crewai import wrap_crew_tools

guarded_tools = wrap_crew_tools(
    tools=[my_crew_tool],
    policy="./policies/starter.yaml",
)
```

### AutoGen

```bash
pip install chimera-compliance[autogen]
```

```python
from chimera_compliance.integrations.autogen import guard_function_call

@guard_function_call(policy="./policies/starter.yaml")
def transfer_funds(amount: int, destination: str) -> str:
    return f"Transferred ${amount} to {destination}"
```

### Standalone (Direct LLM)

```bash
export CHIMERA_API_KEY=sk-...
chimera-compliance run
```

Or programmatically:

```python
from chimera_compliance import ChimeraAgent

agent = ChimeraAgent(
    model="gpt-4o",
    api_key="sk-...",
    policy="./policies/starter.yaml",
)

result = agent.decide(
    "Increase marketing spend by 40%",
    context={"role": "MANAGER"},
)

print(result.result)       # "ALLOWED" or "BLOCKED"
print(result.action)       # Action description
print(result.explanation)  # Why this decision was made
print(result.audit)        # Full DecisionAuditRecord
```

---

## View Audit Logs

```bash
# Last 10 decisions
chimera-compliance audit --last 10

# Only blocked decisions
chimera-compliance audit --result BLOCKED

# Aggregate statistics
chimera-compliance audit --stats

# Generate Art. 86 explanation report
chimera-compliance explain --id dec_abc123 --open
```

---

## Next Steps

- [Policy Guide](policy-guide.md) — Learn YAML rules and CSL policy syntax
- [Integrations](integrations.md) — Deep dive into each framework integration
- [CLI Reference](cli-reference.md) — All commands and options
- [Architecture](architecture.md) — How the pipeline works under the hood
