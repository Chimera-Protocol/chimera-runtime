# chimera-runtime Documentation

**EU AI Act Compliant Deterministic Runtime**

Every AI decision formally verified. Every step logged. Every action auditable.

---

## What is chimera-runtime?

chimera-runtime is a plug-in deterministic runtime for AI agents. It sits between your AI agent framework and the actions your agents take, providing:

- **Deterministic policy enforcement** — BLOCK, ALLOW, or ASK_HUMAN before every action
- **Full audit trail** — every decision recorded per EU AI Act requirements
- **Framework agnostic** — works with LangChain, LangGraph, LlamaIndex, CrewAI, AutoGen, or standalone
- **Two policy engines** — lightweight YAML rules (built-in) or CSL + Z3 formal verification (optional)

```
pip install chimera-runtime
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

- **Install**: `pip install chimera-runtime`
- **Initialize**: `chimera-runtime init`
- **Test setup**: `chimera-runtime test --skip-llm`
- **Verify policy**: `chimera-runtime verify policies/governance.yaml`
- **Simulate**: `chimera-runtime policy simulate policies/governance.yaml '{"amount": 50000, "role": "MANAGER"}'`

---

## Requirements

- Python 3.10+
- Core dependencies: `pyyaml`, `rich`, `click`, `jinja2` (installed automatically)

### Optional Dependencies

```bash
# Z3 formal verification
pip install chimera-runtime[csl]

# LLM providers
pip install chimera-runtime[openai]
pip install chimera-runtime[anthropic]
pip install chimera-runtime[google]
pip install chimera-runtime[ollama]

# Agent frameworks
pip install chimera-runtime[langchain]
pip install chimera-runtime[langgraph]
pip install chimera-runtime[llamaindex]
pip install chimera-runtime[crewai]
pip install chimera-runtime[autogen]

# Everything
pip install chimera-runtime[all]
```
