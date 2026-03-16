# 🐉 chimera-agent — Project Plan
## packages/chimera-agent/ inside project-chimera v2.0

---

## 1. Ürün Nedir?

chimera-agent, her AI kararını formally verified CSL policy'lere karşı denetleyen,
tam audit trail oluşturan ve EU AI Act compliance'ı out-of-the-box sağlayan
bir AI agent framework'üdür.

**One-liner:** `pip install chimera-agent` → LLM kararlarını Z3 ile verify et, her adımı logla.

**Dependency zinciri:**
```
chimera-agent  →  csl-core (>= 0.3.0)  →  z3-solver
     ↑ kullanır          ↑ kullanır
   (LLM APIs)         (parser, compiler, runtime)
```

chimera-agent, csl-core'a **dokunmaz** — onu bir kütüphane olarak kullanır.

---

## 2. Package Yapısı

```
project-chimera/
└── packages/
    └── chimera-agent/
        ├── pyproject.toml                  # Bağımsız pip package
        ├── README.md
        ├── LICENSE                         # Apache 2.0
        │
        ├── chimera_agent/
        │   ├── __init__.py                 # Public API: ChimeraAgent, DecisionResult, ...
        │   │
        │   ├── models.py                   # Tüm dataclass'lar — zero dependency
        │   │   ├── AgentConfig             #   YAML config'in Python karşılığı
        │   │   ├── Candidate               #   LLM'in ürettiği tek bir strateji adayı
        │   │   ├── PolicyEvaluation        #   CSL-Core verify sonucu (per candidate)
        │   │   ├── Attempt                 #   Bir retry turundaki tüm candidate'ler
        │   │   ├── DecisionResult          #   agent.decide() return tipi
        │   │   └── DecisionAuditRecord     #   Tam audit kaydı (spec §2.1 JSON schema)
        │   │
        │   ├── config.py                   # YAML config loader + validator
        │   │   ├── load_config(path)       #   .chimera/config.yaml → AgentConfig
        │   │   ├── save_config(cfg, path)  #   AgentConfig → YAML
        │   │   └── validate_config(cfg)    #   Eksik/hatalı alan kontrolü
        │   │
        │   ├── policy.py                   # CSL-Core wrapper — policy lifecycle
        │   │   ├── PolicyManager           #   Ana sınıf
        │   │   ├──   .load(path)           #     CSL load + Z3 verify → ChimeraGuard
        │   │   ├──   .evaluate(params)     #     guard.verify(params) → PolicyEvaluation
        │   │   ├──   .reload()             #     Hot-reload (policy değişti mi kontrol)
        │   │   ├──   .hash                 #     SHA256 of policy file
        │   │   └──   .metadata             #     domain_name, constraints count, etc.
        │   │
        │   ├── llm/                        # LLM Provider Abstraction
        │   │   ├── __init__.py
        │   │   ├── base.py                 # BaseLLMProvider (ABC)
        │   │   │   ├── generate_candidates(request, context, n, rejection_context?)
        │   │   │   │     → List[Candidate]
        │   │   │   └── provider_info       → dict (model, provider, temperature)
        │   │   │
        │   │   ├── openai_provider.py      # OpenAI: GPT-4o, GPT-4.1
        │   │   ├── anthropic_provider.py   # Anthropic: Claude Sonnet/Opus
        │   │   ├── google_provider.py      # Google: Gemini 2.0
        │   │   └── ollama_provider.py      # Ollama: local models
        │   │
        │   ├── agent.py                    # 🧠 ChimeraAgent — ana orkestratör
        │   │   ├── __init__(config)        #   Config'den veya YAML'den init
        │   │   ├── .decide(request, ctx)   #   ANA METOD — tüm pipeline burada
        │   │   │     1. LLM → N candidates
        │   │   │     2. Her candidate → policy evaluate
        │   │   │     3. All blocked? → retry with rejection context
        │   │   │     4. Select best allowed
        │   │   │     5. Human oversight (if enabled)
        │   │   │     6. Audit record oluştur + yaz
        │   │   │     7. Return DecisionResult
        │   │   ├── .halt(force=False)      #   Stop mechanism (Art. 14)
        │   │   └── .from_config(path)      #   Factory: YAML → ChimeraAgent
        │   │
        │   ├── oversight.py                # 👤 Human Oversight (Art. 14)
        │   │   ├── request_confirmation()  #   Blocker — kullanıcıdan onay bekle
        │   │   ├── apply_override()        #   Deployer kararı override eder
        │   │   └── HumanOversightRecord    #   Override kaydı (audit'e eklenir)
        │   │
        │   ├── audit/                      # 📋 Decision Audit Pipeline
        │   │   ├── __init__.py
        │   │   ├── recorder.py             # DecisionAuditRecord oluşturma
        │   │   │   └── build_audit_record()  # Tüm parçaları birleştir → JSON
        │   │   ├── storage.py              # Dosya I/O
        │   │   │   ├── save_record(record, dir)   # JSON + optional HTML yaz
        │   │   │   ├── load_record(path)          # JSON oku
        │   │   │   └── enforce_retention(dir, days)  # Eski logları temizle
        │   │   ├── query.py                # AuditQuery — filter, export, stats
        │   │   │   ├── filter(result?, after?, before?)
        │   │   │   ├── stats(last_days=30)
        │   │   │   ├── top_violations(n=10)
        │   │   │   └── export(path, format)
        │   │   └── html_report.py          # HTML rapor generator
        │   │       └── generate_html(record) → str  # Self-contained HTML
        │   │
        │   ├── docs/                       # 📄 Annex IV Documentation Generator
        │   │   ├── __init__.py
        │   │   ├── generator.py            # Auto-fill 14/19 Annex IV sections
        │   │   │   ├── generate(config, audit_dir, policy_dir)
        │   │   │   ├── status()            # Coverage report
        │   │   │   └── refresh()           # Update with latest data
        │   │   └── templates/
        │   │       └── annex_iv.md         # Jinja2 template
        │   │
        │   └── cli/                        # 💻 CLI Interface
        │       ├── __init__.py
        │       ├── main.py                 # Click group, entry point
        │       ├── cmd_init.py             # chimera-agent init (interactive wizard)
        │       ├── cmd_run.py              # chimera-agent run (interactive + daemon)
        │       ├── cmd_stop.py             # chimera-agent stop
        │       ├── cmd_verify.py           # chimera-agent verify (csl-core wrapper)
        │       ├── cmd_audit.py            # chimera-agent audit (query + export)
        │       ├── cmd_policy.py           # chimera-agent policy (new/list/simulate)
        │       ├── cmd_explain.py          # chimera-agent explain (Art. 86)
        │       └── cmd_docs.py             # chimera-agent docs (generate/status/refresh)
        │
        ├── policies/                       # Bundled example policies
        │   ├── governance.csl              # Spec'teki ana örnek
        │   └── starter.csl                 # init wizard'ın template'i
        │
        └── tests/
            ├── conftest.py
            ├── test_models.py
            ├── test_config.py
            ├── test_policy.py
            ├── test_agent.py              # Integration: full pipeline test
            ├── test_audit.py
            ├── test_oversight.py
            ├── test_llm_providers.py
            ├── test_docs_generator.py
            └── test_cli/
                ├── test_init.py
                ├── test_run.py
                └── test_audit_cmd.py
```

---

## 3. Build Aşamaları

Aşağıdaki her aşama kendi içinde **complete ve test edilmiş** olacak.
Bir aşama bitmeden sonrakine geçilmez. Her aşamada:
- Kod yazılır
- Test yazılır ve geçer
- `python -m pytest` yeşil olur

### AŞAMA 1: Temel (Foundation)
**Hedef:** Veri yapıları + config + policy wrapper çalışır.

| # | Dosya | Ne Yapılır | Depend |
|---|-------|-----------|--------|
| 1.1 | `models.py` | Tüm dataclass'lar: AgentConfig, Candidate, PolicyEvaluation, Attempt, DecisionResult, DecisionAuditRecord. Spec §2.1'deki JSON schema birebir implement edilir. `to_dict()` ve `from_dict()` serialization. | — |
| 1.2 | `config.py` | YAML ↔ AgentConfig. load_config, save_config, validate_config. Default değerler spec §3.2'deki config.yaml ile birebir. | models |
| 1.3 | `policy.py` | PolicyManager: csl-core'un load_guard/verify wrapper'ı. SHA256 hash, metadata extraction, hot-reload (mtime check). | models, csl-core |
| 1.4 | `__init__.py` | Public API exports. | models, config, policy |
| 1.5 | `pyproject.toml` | Package metadata, dependencies, entry points. | — |

**Aşama 1 Testi:** `PolicyManager` bir `.csl` dosyası yükleyebilir, verify edebilir, `guard.verify()` çağırıp `PolicyEvaluation` dönebilir.

---

### AŞAMA 2: LLM Katmanı
**Hedef:** LLM'ler candidate üretebilir, structured JSON output döner.

| # | Dosya | Ne Yapılır | Depend |
|---|-------|-----------|--------|
| 2.1 | `llm/base.py` | BaseLLMProvider ABC. `generate_candidates()` imzası, `provider_info` property. Candidate döndürme kontratı. | models |
| 2.2 | `llm/openai_provider.py` | OpenAI implementasyonu. Structured output (JSON mode). System prompt: "N strategy candidates üret, her biri parameters dict içersin." Retry/rejection context desteği. | base |
| 2.3 | `llm/anthropic_provider.py` | Anthropic implementasyonu. Aynı kontrat. | base |
| 2.4 | `llm/google_provider.py` | Google Gemini implementasyonu. | base |
| 2.5 | `llm/ollama_provider.py` | Ollama implementasyonu (local). | base |

**Aşama 2 Testi:** Mock LLM ile `generate_candidates()` çağrıldığında `List[Candidate]` döner, her candidate'de `strategy`, `parameters`, `reasoning` var.

---

### AŞAMA 3: Agent Core (Kalp)
**Hedef:** `agent.decide()` çalışır — tam neuro→symbolic→audit pipeline.

| # | Dosya | Ne Yapılır | Depend |
|---|-------|-----------|--------|
| 3.1 | `agent.py` | ChimeraAgent sınıfı. `decide()` metodu: LLM → candidates → policy eval → retry loop → select → return. `from_config()` factory. `halt()` stop mechanism. | models, config, policy, llm |
| 3.2 | `oversight.py` | HumanOversight: `request_confirmation()` (stdin blocker), `apply_override()`. Interactive mode ve SDK mode. | models |

**Aşama 3 Testi:** Mock LLM + gerçek CSL policy ile `agent.decide("Increase budget by 40%")` çağrılır → 3 candidate üretilir → policy evaluate edilir → best allowed seçilir → `DecisionResult` döner.

---

### AŞAMA 4: Audit Pipeline
**Hedef:** Her karar JSON + HTML olarak loglanır, sorgulanabilir.

| # | Dosya | Ne Yapılır | Depend |
|---|-------|-----------|--------|
| 4.1 | `audit/recorder.py` | `build_audit_record()`: Agent state + candidates + evaluations + decision → DecisionAuditRecord. UUID generation, timestamp, policy hash capture. | models |
| 4.2 | `audit/storage.py` | `save_record()`: JSON dosya yazma (decision_id based filename). `load_record()`. `enforce_retention()`: retention_days'den eski dosyaları sil. | models |
| 4.3 | `audit/query.py` | `AuditQuery`: filter(result, after, before), stats(last_days), top_violations(n), export(path, format). Audit dir scan → filter → aggregate. | storage |
| 4.4 | `audit/html_report.py` | `generate_html()`: DecisionAuditRecord → self-contained HTML rapor. Jinja2 template. Spec §2.4'teki format. Art. 86 explanation section. | models |

**Aşama 4 Testi:** Tam pipeline çalıştır → `audit_logs/` dizininde JSON + HTML dosyaları oluşur → `AuditQuery.filter(result="BLOCKED")` çalışır → `stats()` doğru aggregate verir.

---

### AŞAMA 5: Annex IV Documentation Generator
**Hedef:** `chimera-agent docs generate` 14/19 section auto-fill eder.

| # | Dosya | Ne Yapılır | Depend |
|---|-------|-----------|--------|
| 5.1 | `docs/templates/annex_iv.md` | Jinja2 Markdown template — 19 section, her biri conditional. | — |
| 5.2 | `docs/generator.py` | `generate()`: config + audit logs + policy files → template render. `status()`: coverage report. `refresh()`: re-render with latest data. | config, audit, policy |

**Aşama 5 Testi:** Mock config + birkaç audit record + policy dosyası ile `generate()` → Markdown dosyası, 14 section dolu, 5 section TODO.

---

### AŞAMA 6: CLI Interface
**Hedef:** `chimera-agent` komutu çalışır — tüm spec §3 komutları.

| # | Dosya | Ne Yapılır | Depend |
|---|-------|-----------|--------|
| 6.1 | `cli/main.py` | Click group, version, global options. Entry point: `chimera-agent`. | — |
| 6.2 | `cli/cmd_init.py` | Interactive wizard: provider seç, API key, model, policy path, audit config. `.chimera/config.yaml` + starter policy oluştur. | config |
| 6.3 | `cli/cmd_run.py` | Interactive mode (default): prompt loop, real-time reasoning display. `--daemon` mode: background service. `--require-confirmation`, `--human-override`. | agent, oversight |
| 6.4 | `cli/cmd_stop.py` | `chimera-agent stop`: graceful halt. `--force`: immediate, log INTERRUPTED. | agent |
| 6.5 | `cli/cmd_verify.py` | `chimera-agent verify`: csl-core verify wrapper, policy metadata display. | policy |
| 6.6 | `cli/cmd_audit.py` | `chimera-agent audit`: --last, --result, --after, --before, --id, --format, --export, --stats. | audit/query |
| 6.7 | `cli/cmd_policy.py` | `chimera-agent policy new`, `policy list`, `policy simulate`. | policy |
| 6.8 | `cli/cmd_explain.py` | `chimera-agent explain --id <dec_id>`: Art. 86 HTML report generation. | audit/html_report |
| 6.9 | `cli/cmd_docs.py` | `chimera-agent docs generate/status/refresh`. | docs/generator |

**Aşama 6 Testi:** CLI subprocess tests — her komut doğru exit code ve output verir.

---

### AŞAMA 7: Packaging & Polish
**Hedef:** `pip install chimera-agent` çalışır, PyPI-ready.

| # | İş | Detay |
|---|-----|-------|
| 7.1 | `pyproject.toml` finalize | Metadata, classifiers, optional deps, entry points |
| 7.2 | `README.md` | Quickstart, architecture diagram, spec'ten örnekler |
| 7.3 | Example policies | `governance.csl`, `starter.csl` bundled |
| 7.4 | CI/CD | GitHub Actions: lint, test, build, publish |
| 7.5 | Full integration test | End-to-end: init → run → decide → audit → export |

---

## 4. Dependency Matris

```toml
[project]
name = "chimera-agent"
dependencies = [
    "csl-core>=0.3.0",          # Foundation — policy engine
    "pyyaml>=6.0",              # Config dosyası
    "rich>=13.0.0",             # Terminal UI (csl-core zaten depend ediyor)
    "click>=8.0",               # CLI framework
    "jinja2>=3.0",              # HTML report templates
]

[project.optional-dependencies]
openai = ["openai>=1.0"]
anthropic = ["anthropic>=0.40"]
google = ["google-generativeai>=0.5"]
ollama = ["ollama>=0.3"]
all = ["chimera-agent[openai,anthropic,google,ollama]"]
dev = ["pytest>=7.0", "pytest-cov", "ruff", "black", "mypy"]
```

---

## 5. Başarı Kriterleri

Her aşamanın sonunda bu kontrol listesini geçeceğiz:

- [ ] **Zero placeholder:** Tek bir `pass`, `TODO`, `NotImplementedError` yok
- [ ] **Testler yeşil:** `pytest` tüm testleri geçiyor
- [ ] **Type-safe:** Tüm public API'ler type hint'li
- [ ] **Spec uyumu:** Spec'teki JSON schema, CLI output, ve davranış birebir
- [ ] **CSL-Core uyumu:** `load_guard`, `guard.verify`, `GuardResult` doğru kullanılıyor
- [ ] **Audit completeness:** Her karar tam DecisionAuditRecord üretiyor
- [ ] **EU AI Act mapping:** Compliance tablosundaki her article karşılanıyor

---

## 6. Teknik Kararlar

| Karar | Seçim | Neden |
|-------|-------|-------|
| CLI framework | Click | Argparse'tan daha clean, grup/subcommand desteği native |
| Config format | YAML | Human-readable, industry standard |
| Audit format | JSON (per-decision file) | Spec uyumu, grep-friendly, compliance export |
| HTML reports | Jinja2 | Self-contained, no JS dependency |
| LLM abstraction | ABC + providers | Her provider kendi dosyasında, optional dependency |
| ID generation | UUID v4 | `dec_` prefix + UUID, globally unique |
| Hashing | SHA256 | Policy file hash, tamper detection |
| Timestamp | ISO 8601 UTC | `2026-02-25T14:32:07.841Z` format |

---

## 7. Motto

> **"ASLA PLACEHOLDER YOK, ASLA GERİDE KALMAK YOK,
> TÜM ÜRÜNÜ TAM HALDE SHIP EDECEĞİZ, KISA YOL YOK!"**

Her satır production-ready. Her fonksiyon tam implement. Her test gerçek assertion.