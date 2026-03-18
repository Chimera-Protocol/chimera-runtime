# CLI Reference

Complete reference for all `chimera-runtime` CLI commands.

---

## Global Options

```bash
chimera-runtime [OPTIONS] COMMAND [ARGS]
```

| Option | Description |
|--------|-------------|
| `--config`, `-c` | Path to config file (default: `.chimera/config.yaml`) |
| `--verbose`, `-v` | Verbose output |
| `--version` | Show version and exit |
| `--help` | Show help and exit |

---

## `init`

Initialize a new chimera-runtime project.

```bash
chimera-runtime init [OPTIONS]
```

| Option | Description |
|--------|-------------|
| `--mode standalone\|integration` | Project mode (prompted if omitted) |
| `--non-interactive` | Use defaults, skip all prompts |

**Standalone mode** prompts for:
- LLM provider (openai, anthropic, google, ollama)
- Model name
- API key
- Temperature

**Integration mode** prompts for:
- Agent framework (LangChain, LangGraph, CrewAI, LlamaIndex, AutoGen)

**Both modes** prompt for:
- Policy format (YAML or CSL)
- Policy file path
- Audit log directory
- Retention days (EU AI Act Art. 19)

**Creates:**
- `.chimera/config.yaml`
- Starter policy file
- Audit log directory

**Examples:**

```bash
# Interactive setup
chimera-runtime init

# Quick setup with defaults
chimera-runtime init --non-interactive

# Integration mode directly
chimera-runtime init --mode integration
```

---

## `run`

Start the agent in interactive or daemon mode. Requires standalone mode configuration with an LLM provider.

```bash
chimera-runtime run [OPTIONS]
```

| Option | Description |
|--------|-------------|
| `--daemon`, `-d` | Run as daemon (reads JSON from stdin, writes results to stdout) |
| `--require-confirmation` | Require human confirmation for each decision |
| `--human-override` | Allow human override of decisions |
| `--dry-run` | Evaluate policies but never block |
| `--model`, `-m` | Override LLM model |
| `--policy`, `-p` | Override policy file path |

**Interactive commands** (during `run`):
- Type a request → agent processes it through the pipeline
- `status` → show agent status
- `halt` → halt the agent (Art. 14 stop mechanism)
- `resume` → resume a halted agent
- `quit` / `exit` → exit
- `--context {"key": "value"}` → append JSON context to request

**Daemon mode** (`--daemon`):
- Reads one JSON object per line from stdin: `{"request": "...", "context": {...}}`
- Writes one JSON result per line to stdout

**Examples:**

```bash
# Interactive mode
chimera-runtime run

# With human confirmation
chimera-runtime run --require-confirmation

# Dry run (shadow mode)
chimera-runtime run --dry-run

# Override model
chimera-runtime run -m claude-sonnet-4-20250514

# Daemon mode
echo '{"request": "Approve $50k for marketing"}' | chimera-runtime run --daemon
```

---

## `stop`

Stop a running daemon agent.

```bash
chimera-runtime stop [OPTIONS]
```

| Option | Description |
|--------|-------------|
| `--force`, `-f` | Force immediate halt |

---

## `test`

Run end-to-end system validation. Tests the entire setup without requiring user interaction.

```bash
chimera-runtime test [OPTIONS]
```

| Option | Description |
|--------|-------------|
| `--skip-llm` | Skip LLM connection test |
| `--policy`, `-p` | Policy file to test (default: from config) |
| `--verbose`, `-v` | Show detailed output |

**Validation steps:**

| Step | What it tests |
|------|---------------|
| Config loading | Parses and validates `.chimera/config.yaml` |
| Policy loading | Loads and compiles the policy file |
| Policy verification | Z3 verification (CSL) or syntax validation (YAML) |
| Policy simulation | Runs sample inputs against the policy |
| LLM connection | Tests LLM provider connectivity (skippable) |
| Audit write | Verifies audit directory is writable |
| Audit read | Loads and validates existing audit records |
| Integrations | Reports which frameworks are installed |

Exit code: `0` if all checks pass, `1` if any fail.

**Examples:**

```bash
# Test everything except LLM
chimera-runtime test --skip-llm

# Test with a specific policy
chimera-runtime test -p policies/governance.yaml --skip-llm
```

---

## `verify`

Verify a policy file. For CSL files, runs the full Z3 verification pipeline (syntax → semantics → Z3 logic → IR compilation). For YAML files, validates syntax and rule structure.

```bash
chimera-runtime verify [POLICY_FILE]
```

If `POLICY_FILE` is omitted, uses the policy from config.

**Examples:**

```bash
# Verify the configured policy
chimera-runtime verify

# Verify a specific file
chimera-runtime verify policies/governance.yaml
chimera-runtime verify policies/governance.csl
```

---

## `policy`

Policy management commands.

### `policy new`

Create a new CSL policy file from a template.

```bash
chimera-runtime policy new NAME [OPTIONS]
```

| Option | Description |
|--------|-------------|
| `--dir`, `-d` | Policy directory (default: `./policies`) |

**Examples:**

```bash
chimera-runtime policy new PaymentGuard
chimera-runtime policy new HRPolicy --dir ./policies/hr
```

### `policy list`

List all policy files and their status.

```bash
chimera-runtime policy list [OPTIONS]
```

| Option | Description |
|--------|-------------|
| `--dir`, `-d` | Policy directory (default: `./policies`) |

Discovers both `.csl` and `.yaml`/`.yml` files. Shows domain name, constraint count, variable count, and validation status.

### `policy simulate`

Simulate a policy against test input.

```bash
chimera-runtime policy simulate POLICY_FILE [CONTEXT_JSON] [OPTIONS]
```

| Option | Description |
|--------|-------------|
| `--input`, `-i` | JSON file with test context (alternative to inline JSON) |
| `--dry-run` | Dry-run mode (evaluate but never block) |

`CONTEXT_JSON` is inline JSON, e.g. `'{"amount": 50000, "role": "MANAGER"}'`.

Supports batch simulation: pass a JSON array of objects via `--input`.

**Examples:**

```bash
# Inline JSON
chimera-runtime policy simulate policies/governance.yaml '{"amount": 50000, "role": "MANAGER"}'

# From file
chimera-runtime policy simulate policies/governance.yaml --input test_cases.json

# Dry run
chimera-runtime policy simulate policies/governance.yaml '{"amount": 999999}' --dry-run
```

---

## `audit`

Query and manage audit records.

```bash
chimera-runtime audit [OPTIONS]
```

| Option | Description |
|--------|-------------|
| `--last`, `-n` | Show last N decisions |
| `--result`, `-r` | Filter by result: `ALLOWED`, `BLOCKED`, `HUMAN_OVERRIDE`, `INTERRUPTED` |
| `--after` | After datetime (ISO format) |
| `--before` | Before datetime (ISO format) |
| `--id` | Show specific decision by ID |
| `--stats` | Show aggregate statistics |
| `--violations` | Show top constraint violations |
| `--export` | Export to file |
| `--format` | Export format: `json`, `compact`, `stats` |
| `--audit-dir` | Override audit directory |

**Examples:**

```bash
# Last 10 decisions
chimera-runtime audit --last 10

# Blocked decisions only
chimera-runtime audit --result BLOCKED

# Decisions in a date range
chimera-runtime audit --after 2026-01-01T00:00:00Z --before 2026-02-01T00:00:00Z

# Specific decision
chimera-runtime audit --id dec_a1b2c3d4e5f6

# Statistics
chimera-runtime audit --stats

# Top violations
chimera-runtime audit --violations

# Export
chimera-runtime audit --export report.json --format compact
```

---

## `explain`

Generate an Art. 86 Right to Explanation report for a specific decision. Produces a self-contained HTML report.

```bash
chimera-runtime explain --id DECISION_ID [OPTIONS]
```

| Option | Description |
|--------|-------------|
| `--id` | Decision ID to explain (required) |
| `--output`, `-o` | Output HTML file path |
| `--audit-dir` | Override audit directory |
| `--open` | Open the report in browser after generating |

**Examples:**

```bash
# Generate explanation
chimera-runtime explain --id dec_a1b2c3d4e5f6

# Generate and open in browser
chimera-runtime explain --id dec_a1b2c3d4e5f6 --open

# Custom output path
chimera-runtime explain --id dec_a1b2c3d4e5f6 --output ./reports/q1_review.html
```

---

## `docs`

Generate EU AI Act Annex IV technical documentation.

```bash
chimera-runtime docs [generate|status|refresh]
```

### `docs generate`

Generate the full Annex IV technical documentation as Markdown.

### `docs status`

Check if documentation exists and its age.

### `docs refresh`

Re-generate documentation from current state.
