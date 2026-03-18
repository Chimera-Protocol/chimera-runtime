"""
chimera-runtime — HTML Audit Report Generator

Generates a self-contained HTML report from a DecisionAuditRecord.
No external dependencies — uses Python f-strings for templating.

The report includes:
  - Decision summary (result, action, parameters)
  - Agent information
  - Full reasoning trace (all attempts, candidates, evaluations)
  - Policy compliance details
  - Art. 86 "Right to Explanation" section
  - Performance metrics
  - Human oversight record (if present)

Spec §2.4 format. Self-contained: all CSS is inline.
"""

from __future__ import annotations

import html
import json
from typing import Any

from ..models import DecisionAuditRecord


def _esc(text: Any) -> str:
    """HTML-escape a value."""
    return html.escape(str(text))


def _result_badge(result: str) -> str:
    """Generate a colored badge for the result."""
    colors = {
        "ALLOWED": "#22c55e",
        "BLOCKED": "#ef4444",
        "HUMAN_OVERRIDE": "#f59e0b",
        "INTERRUPTED": "#6b7280",
    }
    color = colors.get(result, "#6b7280")
    return f'<span style="background:{color};color:#fff;padding:4px 12px;border-radius:4px;font-weight:700;font-size:14px;">{_esc(result)}</span>'


def generate_html(record: DecisionAuditRecord) -> str:
    """
    Generate a self-contained HTML audit report.

    Args:
        record: The DecisionAuditRecord to render

    Returns:
        Complete HTML string (ready to write to file)
    """
    d = record.decision
    a = record.agent
    inp = record.input
    r = record.reasoning
    perf = record.performance
    comp = record.compliance

    # Build candidates HTML
    candidates_html = ""
    for attempt in r.attempts:
        candidates_html += f'<h3>Attempt {attempt.attempt_number} — {_esc(attempt.outcome)}</h3>'
        if attempt.note:
            candidates_html += f'<p class="note">{_esc(attempt.note)}</p>'

        for c in attempt.candidates:
            is_selected = c.candidate_id == r.selected_candidate
            border_color = "#22c55e" if is_selected else "#e5e7eb"
            label = ' <span style="color:#22c55e;font-weight:700;">★ SELECTED</span>' if is_selected else ""

            eval_html = ""
            if c.policy_evaluation:
                pe = c.policy_evaluation
                eval_color = "#22c55e" if pe.result == "ALLOWED" else "#ef4444"
                eval_html = f'<div style="margin-top:8px;"><strong>Policy:</strong> <span style="color:{eval_color};font-weight:700;">{_esc(pe.result)}</span> ({pe.duration_ms:.3f}ms)</div>'

                if pe.violations:
                    eval_html += '<div style="margin-top:4px;"><strong>Violations:</strong><ul style="margin:4px 0;">'
                    for v in pe.violations:
                        eval_html += f'<li><code>{_esc(v.constraint)}</code>: {_esc(v.explanation)}</li>'
                    eval_html += '</ul></div>'

            params_json = json.dumps(c.parameters, indent=2, ensure_ascii=False)

            candidates_html += f'''
            <div style="border:2px solid {border_color};border-radius:8px;padding:16px;margin:8px 0;background:#fafafa;">
                <div style="display:flex;justify-content:space-between;align-items:center;">
                    <strong>{_esc(c.candidate_id)}: {_esc(c.strategy)}</strong>{label}
                </div>
                <div style="margin-top:8px;color:#666;font-size:13px;">Confidence: {c.llm_confidence:.0%}</div>
                <div style="margin-top:8px;"><strong>Reasoning:</strong> {_esc(c.llm_reasoning[:500])}</div>
                <details style="margin-top:8px;">
                    <summary>Parameters</summary>
                    <pre style="background:#f1f5f9;padding:8px;border-radius:4px;font-size:12px;overflow-x:auto;">{_esc(params_json)}</pre>
                </details>
                {eval_html}
            </div>'''

    # Human oversight section
    oversight_html = ""
    if record.human_oversight_record:
        hor = record.human_oversight_record
        oversight_html = f'''
        <div class="section">
            <h2>🧑 Human Oversight</h2>
            <table>
                <tr><td><strong>Action</strong></td><td>{_esc(hor.action)}</td></tr>
                <tr><td><strong>Reason</strong></td><td>{_esc(hor.reason)}</td></tr>
                <tr><td><strong>Override Decision</strong></td><td>{_esc(hor.override_decision)}</td></tr>
                <tr><td><strong>Timestamp</strong></td><td>{_esc(hor.timestamp)}</td></tr>
            </table>
        </div>'''

    # Compliance items
    eu_items = ""
    for key, val in comp.eu_ai_act.items():
        icon = "✅" if val else "❌"
        eu_items += f"<tr><td>{icon}</td><td>{_esc(key)}</td></tr>"

    fv_items = ""
    for key, val in comp.formal_verification.items():
        fv_items += f"<tr><td><strong>{_esc(key)}</strong></td><td>{_esc(val)}</td></tr>"

    # Full parameters JSON
    final_params_json = json.dumps(d.final_parameters, indent=2, ensure_ascii=False)

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Audit Report — {_esc(record.decision_id)}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #f8fafc; color: #1e293b; line-height: 1.6; padding: 24px; }}
        .container {{ max-width: 900px; margin: 0 auto; }}
        .header {{ background: #0f172a; color: #fff; padding: 24px 32px; border-radius: 12px 12px 0 0; }}
        .header h1 {{ font-size: 20px; margin-bottom: 8px; }}
        .header .meta {{ font-size: 13px; color: #94a3b8; }}
        .body {{ background: #fff; padding: 32px; border-radius: 0 0 12px 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
        .section {{ margin-bottom: 32px; }}
        .section h2 {{ font-size: 16px; margin-bottom: 12px; padding-bottom: 8px; border-bottom: 2px solid #e2e8f0; }}
        table {{ width: 100%; border-collapse: collapse; font-size: 14px; }}
        td {{ padding: 8px 12px; border-bottom: 1px solid #f1f5f9; vertical-align: top; }}
        td:first-child {{ width: 220px; color: #64748b; }}
        pre {{ background: #f1f5f9; padding: 12px; border-radius: 6px; font-size: 12px; overflow-x: auto; }}
        .note {{ color: #64748b; font-size: 13px; font-style: italic; margin: 4px 0; }}
        h3 {{ font-size: 14px; margin: 16px 0 8px; color: #475569; }}
        details > summary {{ cursor: pointer; color: #3b82f6; font-size: 13px; }}
        .explanation {{ background: #eff6ff; border-left: 4px solid #3b82f6; padding: 16px; border-radius: 0 8px 8px 0; margin: 12px 0; }}
        footer {{ text-align: center; margin-top: 24px; font-size: 12px; color: #94a3b8; }}
    </style>
</head>
<body>
<div class="container">
    <div class="header">
        <h1>🛡️ chimera-runtime Audit Report</h1>
        <div class="meta">
            Decision ID: <strong>{_esc(record.decision_id)}</strong> &nbsp;|&nbsp;
            Schema: {_esc(record.schema_version)} &nbsp;|&nbsp;
            {_esc(record.timestamp)}
        </div>
    </div>
    <div class="body">

        <!-- Decision Summary -->
        <div class="section">
            <h2>📋 Decision Summary</h2>
            <table>
                <tr><td><strong>Result</strong></td><td>{_result_badge(d.result)}</td></tr>
                <tr><td><strong>Action</strong></td><td>{_esc(d.action_taken)}</td></tr>
                <tr><td><strong>Policy File</strong></td><td><code>{_esc(d.policy_file)}</code></td></tr>
                <tr><td><strong>Policy Hash</strong></td><td><code style="font-size:11px;">{_esc(d.policy_hash)}</code></td></tr>
            </table>
            <details style="margin-top:12px;">
                <summary>Final Parameters</summary>
                <pre>{_esc(final_params_json)}</pre>
            </details>
        </div>

        <!-- Art. 86 — Right to Explanation -->
        <div class="section">
            <h2>📖 Right to Explanation (Art. 86)</h2>
            <div class="explanation">
                <p><strong>Why this decision was made:</strong></p>
                <p>{_esc(r.selection_reasoning)}</p>
                <p style="margin-top:8px;"><strong>Selected candidate:</strong> {_esc(r.selected_candidate or "None (all blocked)")}</p>
                <p><strong>Total candidates evaluated:</strong> {r.total_candidates} across {r.total_attempts} attempt(s)</p>
            </div>
        </div>

        <!-- Agent Info -->
        <div class="section">
            <h2>🤖 Agent Info</h2>
            <table>
                <tr><td><strong>Name</strong></td><td>{_esc(a.name)}</td></tr>
                <tr><td><strong>Version</strong></td><td>{_esc(a.version)}</td></tr>
                <tr><td><strong>CSL-Core Version</strong></td><td>{_esc(a.csl_core_version)}</td></tr>
                <tr><td><strong>Model</strong></td><td>{_esc(a.model_provider)} / {_esc(a.model)}</td></tr>
                <tr><td><strong>Temperature</strong></td><td>{a.temperature}</td></tr>
            </table>
        </div>

        <!-- Input -->
        <div class="section">
            <h2>📥 Input</h2>
            <table>
                <tr><td><strong>Request</strong></td><td>{_esc(inp.raw_request)}</td></tr>
            </table>
        </div>

        <!-- Reasoning Trace -->
        <div class="section">
            <h2>🧠 Reasoning Trace</h2>
            {candidates_html}
        </div>

        <!-- Compliance -->
        <div class="section">
            <h2>⚖️ EU AI Act Compliance</h2>
            <table>{eu_items}</table>
            <h3>Formal Verification</h3>
            <table>{fv_items}</table>
        </div>

        <!-- Performance -->
        <div class="section">
            <h2>⏱️ Performance</h2>
            <table>
                <tr><td><strong>Total Duration</strong></td><td>{perf.total_duration_ms:.3f} ms</td></tr>
                <tr><td><strong>LLM Duration</strong></td><td>{perf.llm_duration_ms:.3f} ms</td></tr>
                <tr><td><strong>Policy Evaluation</strong></td><td>{perf.policy_evaluation_ms:.3f} ms</td></tr>
                <tr><td><strong>Audit Generation</strong></td><td>{perf.audit_generation_ms:.3f} ms</td></tr>
            </table>
        </div>

        {oversight_html}

    </div>
    <footer>
        Generated by chimera-runtime v{_esc(a.version)} &nbsp;|&nbsp; Schema {_esc(record.schema_version)} &nbsp;|&nbsp; Powered by CSL-Core + Z3
    </footer>
</div>
</body>
</html>'''
