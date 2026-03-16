# Framework Integrations

chimera-compliance plugs into any AI agent framework. Each integration wraps tool/function calls with a compliance guard that evaluates parameters against your policy before execution.

---

## How It Works

All integrations share the same core:

```
Your Agent Tool Call
    │
    ▼
ComplianceGuard.check(action_name, parameters)
    │
    ├── ALLOWED → tool executes normally
    │
    └── BLOCKED → ComplianceError raised (tool does NOT execute)
```

Every call is audited automatically — a `DecisionAuditRecord` is written to disk.

---

## LangChain

```bash
pip install chimera-compliance[langchain]
```

### `wrap_tools()` — Wrap Multiple Tools

The simplest approach. Wraps all tools in-place with compliance checking.

```python
from langchain_core.tools import tool
from chimera_compliance.integrations.langchain import wrap_tools

@tool
def approve_budget(amount: int, department: str) -> str:
    """Approve a budget allocation."""
    return f"Approved ${amount} for {department}"

@tool
def send_payment(amount: int, recipient: str) -> str:
    """Send a payment."""
    return f"Sent ${amount} to {recipient}"

# Wrap all tools — modifies tools in-place, returns same list
guarded_tools = wrap_tools(
    tools=[approve_budget, send_payment],
    policy="./policies/governance.yaml",
    audit_dir="./audit_logs",
)

# Use in your LangChain agent as normal
# agent = create_tool_calling_agent(llm, guarded_tools, prompt)
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `tools` | `List[BaseTool]` | required | LangChain tools to wrap |
| `policy` | `str` | required | Path to `.yaml` or `.csl` policy file |
| `audit_dir` | `str` | `"./audit_logs"` | Audit log directory |
| `param_extractor` | `Callable` | `None` | Custom function to extract params from tool args |

**How parameters are extracted:**
1. If `param_extractor` is provided, it's called with `(args, kwargs)`
2. Otherwise: keyword arguments are used directly
3. If the first positional argument is a JSON string, it's parsed into a dict
4. If the first positional argument is a dict, it's merged into params

### `ChimeraComplianceTool` — Wrap a Single Tool

For fine-grained control over individual tools:

```python
from chimera_compliance.integrations import ComplianceGuard
from chimera_compliance.integrations.langchain import ChimeraComplianceTool

guard = ComplianceGuard(policy="./policies/governance.yaml")

wrapper = ChimeraComplianceTool(
    tool=approve_budget,
    guard=guard,
    param_extractor=lambda args, kwargs: {"amount": kwargs.get("amount", 0)},
)

# The original tool is now guarded (modified in-place)
# approve_budget._run() now checks compliance before executing
```

### `ChimeraCallbackHandler` — Callback Handler

Intercepts tool calls at the callback level:

```python
from chimera_compliance.integrations.langchain import ChimeraCallbackHandler

handler = ChimeraCallbackHandler(
    policy="./policies/governance.yaml",
    audit_dir="./audit_logs",
    on_block="raise",  # or "return"
)

# Get the actual LangChain BaseCallbackHandler
lc_handler = handler.get_handler()

# Use with your LLM or chain
# llm = ChatOpenAI(callbacks=[lc_handler])
```

When `on_block="raise"`, a `ComplianceError` is raised on blocked actions. When `on_block="return"`, the handler logs the block but allows execution to continue.

---

## LangGraph

```bash
pip install chimera-compliance[langgraph]
```

### `compliance_node()` — Graph Node

Creates a node function that gates actions through the compliance guard. Reads parameters from the graph state, evaluates them, and writes the result back.

```python
from langgraph.graph import StateGraph
from chimera_compliance.integrations.langgraph import compliance_node, compliance_edge

# Create the compliance node
check = compliance_node(
    policy="./policies/governance.yaml",
    audit_dir="./audit_logs",
    param_key="parameters",     # state key to read params from
    action_key="action",        # state key to read action name from
    result_key="compliance_result",  # state key to write result to
)

# Create the conditional edge
route = compliance_edge(
    result_key="compliance_result",
    allowed_node="execute",
    blocked_node="report_block",
)

# Build your graph
graph = StateGraph(...)
graph.add_node("agent", agent_node)
graph.add_node("compliance", check)
graph.add_node("execute", execute_node)
graph.add_node("report_block", block_handler_node)

graph.add_edge("agent", "compliance")
graph.add_conditional_edges("compliance", route)
```

**`compliance_node()` parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `policy` | `str` | required | Path to policy file |
| `audit_dir` | `str` | `"./audit_logs"` | Audit directory |
| `param_key` | `str` | `"parameters"` | State key containing parameters to evaluate |
| `action_key` | `str` | `"action"` | State key containing action name |
| `result_key` | `str` | `"compliance_result"` | State key to write result to |

**State output** (written to `result_key`):

```python
{
    "allowed": True,          # bool
    "result": "ALLOWED",      # "ALLOWED" or "BLOCKED"
    "violations": [],         # list of {"constraint": ..., "message": ...}
    "duration_ms": 0.15,      # evaluation time
}
```

### `compliance_edge()` — Conditional Edge

Routes the graph based on the compliance result:

```python
route = compliance_edge(
    result_key="compliance_result",  # state key to check
    allowed_node="execute",          # route here if ALLOWED
    blocked_node="report_block",     # route here if BLOCKED
)
```

---

## CrewAI

```bash
pip install chimera-compliance[crewai]
```

### `wrap_crew_tools()` — Wrap Crew Tools

Wraps CrewAI tools by monkey-patching their `_run()` method:

```python
from crewai.tools import BaseTool
from chimera_compliance.integrations.crewai import wrap_crew_tools

# Your CrewAI tools
class BudgetTool(BaseTool):
    name = "approve_budget"
    description = "Approve budget allocation"

    def _run(self, amount: int, department: str) -> str:
        return f"Approved ${amount} for {department}"

tools = [BudgetTool()]

# Wrap with compliance
guarded_tools = wrap_crew_tools(
    tools=tools,
    policy="./policies/governance.yaml",
    audit_dir="./audit_logs",
)

# Use in your Crew
# crew = Crew(agents=[agent], tasks=[task], tools=guarded_tools)
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `tools` | `List[BaseTool]` | required | CrewAI tools to wrap |
| `policy` | `str` | required | Path to policy file |
| `audit_dir` | `str` | `"./audit_logs"` | Audit directory |
| `param_extractor` | `Callable` | `None` | Custom param extractor |

Tools are modified in-place. If a tool call is blocked, `ComplianceError` is raised.

---

## LlamaIndex

```bash
pip install chimera-compliance[llamaindex]
```

### `wrap_tools()` — Wrap LlamaIndex Tools

Creates new `FunctionTool` wrappers that check compliance before calling the original:

```python
from llama_index.core.tools import FunctionTool
from chimera_compliance.integrations.llamaindex import wrap_tools

def approve_budget(amount: int, department: str) -> str:
    """Approve budget allocation."""
    return f"Approved ${amount} for {department}"

tool = FunctionTool.from_defaults(fn=approve_budget)

# Wrap tools — returns NEW tool instances (not in-place)
guarded_tools = wrap_tools(
    tools=[tool],
    policy="./policies/governance.yaml",
    audit_dir="./audit_logs",
)

# Use guarded_tools in your LlamaIndex agent
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `tools` | `List[BaseTool]` | required | LlamaIndex tools |
| `policy` | `str` | required | Path to policy file |
| `audit_dir` | `str` | `"./audit_logs"` | Audit directory |
| `param_extractor` | `Callable` | `None` | Custom param extractor |

**Important:** Unlike LangChain and CrewAI, LlamaIndex wrapping returns **new** tool instances. Use the returned list, not the originals.

### `wrap_tool()` — Wrap Single Tool

```python
from chimera_compliance.integrations import ComplianceGuard
from chimera_compliance.integrations.llamaindex import wrap_tool

guard = ComplianceGuard(policy="./policies/governance.yaml")
guarded = wrap_tool(tool, guard)
```

---

## AutoGen

```bash
pip install chimera-compliance[autogen]
```

### `guard_function_call()` — Decorator

The simplest way to add compliance to AutoGen function calls:

```python
from chimera_compliance.integrations.autogen import guard_function_call

@guard_function_call(policy="./policies/governance.yaml")
def transfer_funds(amount: int, destination: str) -> str:
    """Transfer funds to a destination account."""
    return f"Transferred ${amount} to {destination}"

# Works with AutoGen's function calling:
# transfer_funds(amount=500000, destination="vendor_abc")
# → ComplianceError if blocked by policy
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `policy` | `str` | required | Path to policy file |
| `audit_dir` | `str` | `"./audit_logs"` | Audit directory |
| `param_mapping` | `Dict[str, str]` | `None` | Map function params to policy variable names |

**`param_mapping` example:**

```python
@guard_function_call(
    policy="./policies/governance.yaml",
    param_mapping={"amt": "amount", "dest": "destination"},
)
def send_money(amt: int, dest: str) -> str:
    return f"Sent ${amt} to {dest}"
```

This maps the function's `amt` parameter to the policy's `amount` variable, and `dest` to `destination`.

### `ChimeraComplianceAgent` — Agent Wrapper

Wraps an AutoGen agent's entire function map:

```python
from chimera_compliance.integrations.autogen import ChimeraComplianceAgent

# Your AutoGen agent
# agent = AssistantAgent(name="finance_bot", ...)

compliant_agent = ChimeraComplianceAgent(
    agent=agent,
    policy="./policies/governance.yaml",
    audit_dir="./audit_logs",
)

# All function calls on the agent are now compliance-checked
# Attribute access is proxied to the underlying agent
```

When a function call is blocked, instead of raising an error, `ChimeraComplianceAgent` returns a message string: `"[BLOCKED by chimera-compliance] violation details..."`. This keeps the AutoGen conversation flowing.

---

## ComplianceGuard — Core API

All integrations use `ComplianceGuard` internally. You can use it directly for custom integrations:

```python
from chimera_compliance.integrations import ComplianceGuard

guard = ComplianceGuard(
    policy="./policies/governance.yaml",
    audit_dir="./audit_logs",
    dry_run=False,
    auto_verify=True,
)

# Check an action
evaluation = guard.check(
    action_name="approve_budget",
    parameters={"amount": 500000, "role": "MANAGER"},
    context={"session_id": "abc123"},
)

print(evaluation.result)      # "ALLOWED" or "BLOCKED"
print(evaluation.violations)  # List[Violation]
print(evaluation.duration_ms) # Evaluation time

# Access the underlying PolicyManager
pm = guard.policy_manager
print(pm.domain_name)
print(pm.constraint_count)
print(pm.backend)  # "csl-core" or "yaml-rule-engine"
```

---

## ComplianceError

All integrations raise `ComplianceError` when an action is blocked:

```python
from chimera_compliance.integrations.base import ComplianceError

try:
    guarded_tool.run(amount=999999, role="ANALYST")
except ComplianceError as e:
    print(e)                    # "Action BLOCKED: Analysts cannot approve any spend"
    print(e.evaluation)         # PolicyEvaluation object
    print(e.evaluation.result)  # "BLOCKED"
    for v in e.evaluation.violations:
        print(f"  {v.constraint}: {v.explanation}")
```

---

## Custom Integration

To build your own integration for a framework not listed above:

```python
from chimera_compliance.integrations import ComplianceGuard
from chimera_compliance.integrations.base import ComplianceError

class MyFrameworkGuard:
    def __init__(self, policy: str, audit_dir: str = "./audit_logs"):
        self._guard = ComplianceGuard(policy=policy, audit_dir=audit_dir)

    def before_action(self, action_name: str, params: dict):
        evaluation = self._guard.check(action_name, params)
        if evaluation.result == "BLOCKED":
            raise ComplianceError(evaluation)
        return evaluation
```

The `ComplianceGuard.check()` method handles:
- Policy hot-reload
- Policy evaluation
- Audit record creation and persistence
- All in a single call
