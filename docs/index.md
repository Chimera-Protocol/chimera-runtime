# chimera-compliance Documentation

**EU AI Act Compliant Agent Compliance Layer**

Every AI decision formally verified. Every step logged. Every action auditable.

---

## What is chimera-compliance?

chimera-compliance is a plug-in compliance layer for AI agents. It sits between your AI agent framework and the actions your agents take, providing:

- **Deterministic policy enforcement** — BLOCK, ALLOW, or ASK_HUMAN before every action
- **Full audit trail** — every decision recorded per EU AI Act requirements
- **Framework agnostic** — works with LangChain, LangGraph, LlamaIndex, CrewAI, AutoGen, or standalone
- **Two policy engines** — lightweight YAML rules (built-in) or CSL + Z3 formal verification (optional)

```
pip install chimera-compliance
```

---

## Documentation

| Guide | Description |
|-------|-------------|
| [Quickstart](quickstart.md) | Get up and running in 5 minutes |
| [Architecture](architecture.md) | How the pipeline works: Neural → Symbolic → Audit |
| [CLI Reference](cli-reference.md) | All CLI commands with examples |
| [Policy Guide](policy-guide.md) | Writing YAML rules and CSL policies |
| [Integrations](integrations.md) | LangChain, LangGraph, LlamaIndex, CrewAI, AutoGen |
| [EU AI Act Compliance](eu-ai-act.md) | Article-by-article compliance mapping |
| [API Reference](api-reference.md) | Full Python SDK reference |

---

## Quick Links

- **Install**: `pip install chimera-compliance`
- **Initialize**: `chimera-compliance init`
- **Test setup**: `chimera-compliance test --skip-llm`
- **Verify policy**: `chimera-compliance verify policies/governance.yaml`
- **Simulate**: `chimera-compliance policy simulate policies/governance.yaml '{"amount": 50000, "role": "MANAGER"}'`

---

## Requirements

- Python 3.10+
- Core dependencies: `pyyaml`, `rich`, `click`, `jinja2` (installed automatically)

### Optional Dependencies

```bash
# Z3 formal verification
pip install chimera-compliance[csl]

# LLM providers
pip install chimera-compliance[openai]
pip install chimera-compliance[anthropic]
pip install chimera-compliance[google]
pip install chimera-compliance[ollama]

# Agent frameworks
pip install chimera-compliance[langchain]
pip install chimera-compliance[langgraph]
pip install chimera-compliance[llamaindex]
pip install chimera-compliance[crewai]
pip install chimera-compliance[autogen]

# Everything
pip install chimera-compliance[all]
```
