# Policy Guide

How to write compliance policies for chimera-runtime.

chimera-runtime supports two policy formats:
- **YAML rules** (built-in, no extra dependencies)
- **CSL policies** (optional, requires `pip install chimera-runtime[csl]`)

Both formats produce the same `PolicyEvaluation` result and can be used interchangeably with any integration.

---

## YAML Rules

The recommended starting point. No additional dependencies required.

### Structure

```yaml
domain: MyDomain

variables:
  variable_name: "range_or_enum"
  amount: "0..1000000"
  role: "{ANALYST, MANAGER, DIRECTOR}"

rules:
  - name: rule_name
    when: "boolean expression"
    then: BLOCK
    message: "Human-readable explanation"
```

### Fields

| Field | Required | Description |
|-------|----------|-------------|
| `domain` | No | Domain name (defaults to `YAMLPolicy`) |
| `variables` | No | Variable declarations with ranges/enums (for documentation and testing) |
| `rules` | Yes | List of rule objects |

Each rule:

| Field | Required | Description |
|-------|----------|-------------|
| `name` | No | Rule identifier (defaults to `rule_0`, `rule_1`, ...) |
| `when` | Yes | Boolean expression that triggers the rule |
| `then` | No | Action when triggered: `BLOCK` (default) |
| `message` | No | Human-readable violation message |

### Expression Syntax

The `when` field uses a safe expression evaluator (AST-based, no `eval()`).

**Supported operators:**

| Operator | Example |
|----------|---------|
| `==` | `role == 'MANAGER'` |
| `!=` | `status != 'ACTIVE'` |
| `>` | `amount > 10000` |
| `<` | `risk_score < 50` |
| `>=` | `age >= 18` |
| `<=` | `count <= 100` |
| `and` | `role == 'MANAGER' and amount > 50000` |
| `or` | `priority == 'HIGH' or urgency == 'CRITICAL'` |
| `not` | `not is_approved` |
| `in` | `role in ('ADMIN', 'SUPERADMIN')` |
| `not in` | `status not in ('BANNED', 'SUSPENDED')` |

**Literal types:**
- Strings: `'value'` or `"value"`
- Integers: `42`, `0`, `1000000`
- Floats: `0.5`, `3.14`
- Booleans: `True`, `False`

### Variable Declarations

The `variables` section documents what variables your rules use. This is used by the `chimera-runtime test` command to generate sample inputs.

```yaml
variables:
  # Integer range — midpoint used for test simulation
  amount: "0..1000000"
  risk_score: "0..100"

  # Enum — first value used for test simulation
  role: "{ANALYST, MANAGER, DIRECTOR, VP, CEO}"
  action: "{APPROVE, DENY, ESCALATE}"
```

### Complete Example

```yaml
domain: GovernanceGuard

variables:
  amount: "0..1000000"
  role: "{ANALYST, MANAGER, DIRECTOR, VP, CEO}"
  channel: "{DIGITAL, TV, PRINT, RADIO, ALL}"
  is_weekend: "{YES, NO}"
  urgency: "{LOW, MEDIUM, HIGH, CRITICAL}"

rules:
  - name: analyst_no_spend
    when: "role == 'ANALYST' and amount > 0"
    then: BLOCK
    message: "Analysts cannot approve any spend"

  - name: manager_approval_limit
    when: "role == 'MANAGER' and amount > 250000"
    then: BLOCK
    message: "Managers cannot approve more than $250,000"

  - name: director_approval_limit
    when: "role == 'DIRECTOR' and amount > 500000"
    then: BLOCK
    message: "Directors cannot approve more than $500,000"

  - name: vp_approval_limit
    when: "role == 'VP' and amount > 750000"
    then: BLOCK
    message: "VPs cannot approve more than $750,000"

  - name: single_channel_cap
    when: "channel != 'ALL' and amount > 300000"
    then: BLOCK
    message: "Single channel budget capped at $300,000"

  - name: weekend_freeze
    when: "is_weekend == 'YES' and urgency != 'CRITICAL'"
    then: BLOCK
    message: "No budget changes on weekends unless critical"

  - name: absolute_ceiling
    when: "amount > 1000000"
    then: BLOCK
    message: "Absolute ceiling: no single decision exceeds $1,000,000"
```

### Evaluation Behavior

- All rules are evaluated against the input parameters
- If **any** rule's `when` condition is true and its `then` is `BLOCK`, the result is `BLOCKED`
- If **no** rules trigger, the result is `ALLOWED`
- Multiple violations can be reported simultaneously

---

## CSL Policies

CSL (Constraint Specification Language) provides mathematically provable policy enforcement via Z3 formal verification.

```bash
pip install chimera-runtime[csl]
```

### Structure

```csl
CONFIG {
  ENFORCEMENT_MODE: BLOCK
}

DOMAIN DomainName {
  VARIABLES {
    variable_name: range_or_enum
  }

  STATE_CONSTRAINT constraint_name {
    WHEN condition
    THEN consequence
  }
}
```

### Syntax

**CONFIG block:**
```csl
CONFIG {
  ENFORCEMENT_MODE: BLOCK
}
```

**VARIABLES block:**
```csl
VARIABLES {
  amount: 0..1000000          // Integer range
  role: {"ADMIN", "USER"}     // String enum
  score: 0..1                 // Numeric range (can include float)
}
```

**STATE_CONSTRAINT block:**
```csl
STATE_CONSTRAINT manager_limit {
  WHEN amount > 250000
  THEN role == "DIRECTOR"
}
```

This means: "When amount exceeds 250,000, then role MUST be DIRECTOR." If the condition is true but the consequence is false, the action is BLOCKED.

### Complete Example

```csl
CONFIG {
  ENFORCEMENT_MODE: BLOCK
}

DOMAIN GovernanceGuard {
  VARIABLES {
    amount: 0..1000000
    role: {"ANALYST", "MANAGER", "DIRECTOR", "VP", "CEO"}
    channel: {"DIGITAL", "TV", "PRINT", "RADIO", "ALL"}
    is_weekend: {"YES", "NO"}
    urgency: {"LOW", "MEDIUM", "HIGH", "CRITICAL"}
  }

  STATE_CONSTRAINT analyst_no_spend {
    WHEN role == "ANALYST"
    THEN amount == 0
  }

  STATE_CONSTRAINT manager_limit {
    WHEN role == "MANAGER"
    THEN amount <= 250000
  }

  STATE_CONSTRAINT director_limit {
    WHEN role == "DIRECTOR"
    THEN amount <= 500000
  }

  STATE_CONSTRAINT weekend_freeze {
    WHEN is_weekend == "YES"
    THEN urgency == "CRITICAL"
  }
}
```

### Z3 Verification

When a `.csl` policy is loaded, CSL-Core runs the full Z3 verification pipeline:

1. **Syntax validation** — CSL parser
2. **Semantic validation** — scope checking, type checking, function whitelist
3. **Z3 logic verification** — reachability, internal consistency, pairwise conflicts, policy-wide conflicts
4. **IR compilation** — compiled to runtime guard

This ensures:
- Every constraint is reachable (can actually trigger)
- No two constraints contradict each other
- The policy is internally consistent

Use `chimera-runtime verify` to run verification manually:

```bash
chimera-runtime verify policies/governance.csl
```

---

## YAML vs CSL: When to Use Which

| Factor | YAML Rules | CSL + Z3 |
|--------|-----------|----------|
| Dependencies | None (built-in) | Requires `csl-core` |
| Verification | Syntax only | Full Z3 formal verification |
| Expressiveness | Boolean expressions | Constraint logic |
| Setup complexity | Simple | Moderate |
| Performance | Fast (~0.1ms) | Fast (~0.5ms) |
| Guarantees | Runtime enforcement | Mathematical proof + runtime |
| Best for | Getting started, simple rules | Regulated industries, complex policies |

**Recommendation:** Start with YAML rules. Move to CSL when you need formal guarantees or when your policies become complex enough to benefit from Z3 consistency checking.

---

## Testing Policies

### CLI Simulation

```bash
# Single test case
chimera-runtime policy simulate policies/governance.yaml '{"amount": 50000, "role": "MANAGER"}'

# Multiple test cases from file
chimera-runtime policy simulate policies/governance.yaml --input test_cases.json

# Dry run (evaluates but never blocks)
chimera-runtime policy simulate policies/governance.yaml '{"amount": 999999}' --dry-run
```

### Programmatic Testing

```python
from chimera_runtime import PolicyManager

pm = PolicyManager("./policies/governance.yaml")

# Test ALLOWED case
result = pm.evaluate({"amount": 50000, "role": "MANAGER"})
assert result.result == "ALLOWED"

# Test BLOCKED case
result = pm.evaluate({"amount": 500000, "role": "MANAGER"})
assert result.result == "BLOCKED"
assert len(result.violations) > 0
assert result.violations[0].constraint == "manager_approval_limit"
```

### Batch Testing (JSON file)

Create `test_cases.json`:

```json
[
  {"amount": 50000, "role": "MANAGER"},
  {"amount": 500000, "role": "MANAGER"},
  {"amount": 100, "role": "ANALYST"},
  {"amount": 800000, "role": "VP"},
  {"amount": 200000, "role": "DIRECTOR", "channel": "DIGITAL"}
]
```

```bash
chimera-runtime policy simulate policies/governance.yaml --input test_cases.json
```

---

## Hot Reload

Policies are hot-reloaded automatically when the file changes. No restart required.

The `PolicyManager` checks the file's modification time and SHA-256 hash before each evaluation. If the file has changed on disk, it reloads automatically.

Enable in config:

```yaml
oversight:
  policy_hot_reload: true
```

Or programmatically:

```python
pm = PolicyManager("./policies/governance.yaml")

# Check and reload if changed
reloaded = pm.reload()  # Returns True if reloaded

# Non-throwing version
pm.check_reload()  # Returns True/False, never raises
```

---

## Dry Run Mode

Evaluate policies without blocking. Useful for shadow testing a new policy in production.

```bash
# CLI
chimera-runtime policy simulate policies/new_policy.yaml '{"amount": 999999}' --dry-run

# Or via agent
chimera-runtime run --dry-run
```

```python
# Programmatic
pm = PolicyManager("./policies/governance.yaml", dry_run=True)
result = pm.evaluate({"amount": 999999, "role": "ANALYST"})
# result.result → "ALLOWED" (even though violations exist)
# result.violations → [Violation(...)]  (violations still reported)
```

In dry run mode:
- The `result` is always `"ALLOWED"`
- Violations are still detected and reported
- Audit records still show what *would have been* blocked
