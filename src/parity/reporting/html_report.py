"""Evidence Report generator producing modern, reviewer-friendly HTML audit artifacts."""

import html
from pathlib import Path
import time
from typing import Any, Dict, List, Optional
from parity.verifier.models import VerificationReport


def generate_object_report_html(report: VerificationReport, output_path: Optional[Path] = None) -> str:
    """Generates an HTML evidence report for a single verified SQL query."""
    status_color = "#10b981" if report.overall_passed else "#ef4444"
    status_badge = "VERIFIED PASS" if report.overall_passed else "VERIFICATION FAILED"

    layers_html = ""
    for l in report.layers:
        l_color = "#10b981" if l.passed else ("#ef4444" if l.status.value == "FAILED" else "#f59e0b")
        layers_html += f"""
        <div class="layer-card">
            <div class="layer-header">
                <span class="layer-title">Layer {l.layer_number}: {html.escape(l.name)}</span>
                <span class="badge" style="background: {l_color}22; color: {l_color}; border: 1px solid {l_color}44;">
                    {l.status.value}
                </span>
            </div>
            <div class="layer-msg">{html.escape(l.message)}</div>
            {f'<div class="layer-meta">Execution: {l.duration_ms:.2f}ms</div>' if l.duration_ms else ''}
        </div>
        """

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Parity Evidence Report: {html.escape(report.query_name)}</title>
    <style>
        :root {{
            --bg: #090d16;
            --surface: #111827;
            --surface-border: #1f2937;
            --text-primary: #f3f4f6;
            --text-secondary: #9ca3af;
            --accent: #3b82f6;
            --font-mono: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
        }}
        body {{
            margin: 0;
            padding: 30px;
            background-color: var(--bg);
            color: var(--text-primary);
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            line-height: 1.5;
        }}
        .container {{
            max-width: 1100px;
            margin: 0 auto;
        }}
        .header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 24px;
            background: var(--surface);
            border: 1px solid var(--surface-border);
            border-radius: 12px;
            margin-bottom: 24px;
        }}
        .title-group h1 {{
            margin: 0 0 6px 0;
            font-size: 24px;
            letter-spacing: -0.02em;
        }}
        .subtitle {{
            color: var(--text-secondary);
            font-size: 14px;
        }}
        .status-pill {{
            padding: 8px 16px;
            border-radius: 9999px;
            font-weight: 700;
            font-size: 13px;
            letter-spacing: 0.05em;
            background: {status_color}22;
            color: {status_color};
            border: 1px solid {status_color}55;
        }}
        .grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-bottom: 24px;
        }}
        .card {{
            background: var(--surface);
            border: 1px solid var(--surface-border);
            border-radius: 12px;
            padding: 20px;
        }}
        .card-title {{
            font-size: 14px;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: var(--text-secondary);
            margin-bottom: 12px;
            font-weight: 600;
        }}
        pre {{
            margin: 0;
            padding: 16px;
            background: #06090e;
            border: 1px solid var(--surface-border);
            border-radius: 8px;
            font-family: var(--font-mono);
            font-size: 13px;
            color: #e5e7eb;
            overflow-x: auto;
            white-space: pre-wrap;
        }}
        .layer-stack {{
            display: flex;
            flex-direction: column;
            gap: 12px;
        }}
        .layer-card {{
            background: #0d131f;
            border: 1px solid var(--surface-border);
            border-radius: 8px;
            padding: 14px 18px;
        }}
        .layer-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 6px;
        }}
        .layer-title {{
            font-weight: 600;
            font-size: 14px;
        }}
        .layer-msg {{
            font-size: 13px;
            color: var(--text-secondary);
        }}
        .layer-meta {{
            font-size: 11px;
            color: #6b7280;
            margin-top: 4px;
        }}
        .badge {{
            padding: 3px 8px;
            border-radius: 6px;
            font-size: 11px;
            font-weight: 600;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="title-group">
                <h1>Parity Verification Evidence</h1>
                <div class="subtitle">Query Object: <strong>{html.escape(report.query_name)}</strong> • Generated: {time.strftime("%Y-%m-%d %H:%M:%S")}</div>
            </div>
            <div class="status-pill">{status_badge}</div>
        </div>

        <div class="grid">
            <div class="card">
                <div class="card-title">Source: Oracle SQL</div>
                <pre>{html.escape(report.source_sql)}</pre>
            </div>
            <div class="card">
                <div class="card-title">Target: PostgreSQL SQL</div>
                <pre>{html.escape(report.target_sql)}</pre>
            </div>
        </div>

        <div class="card">
            <div class="card-title">Multi-Layer Semantic Verification Stack</div>
            <div class="layer-stack">
                {layers_html}
            </div>
        </div>
    </div>
</body>
</html>
"""
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(html_content, encoding="utf-8")

    return html_content
