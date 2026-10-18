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

    kb_html = ""
    if report.applied_kb_entries:
        kb_badges = "".join(f'<span class="badge" style="background:#3b82f622; color:#60a5fa; border:1px solid #3b82f644; margin-right:6px;">{html.escape(k)}</span>' for k in report.applied_kb_entries)
        kb_html = f"""
        <div class="card" style="margin-bottom: 24px;">
            <div class="card-title">Applied Knowledge Base Context</div>
            <div>{kb_badges}</div>
        </div>
        """

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
        .stats-bar {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 16px;
            margin-bottom: 24px;
        }}
        .stat-card {{
            background: var(--surface);
            border: 1px solid var(--surface-border);
            border-radius: 10px;
            padding: 16px;
        }}
        .stat-label {{
            font-size: 12px;
            color: var(--text-secondary);
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 4px;
        }}
        .stat-value {{
            font-size: 20px;
            font-weight: 700;
            color: var(--text-primary);
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

        <div class="stats-bar">
            <div class="stat-card">
                <div class="stat-label">Verification Status</div>
                <div class="stat-value" style="color: {status_color}; font-size: 16px;">{status_badge}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Repair Attempts</div>
                <div class="stat-value">{report.attempts}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Total Cost</div>
                <div class="stat-value">${report.cost_usd:.5f}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Duration</div>
                <div class="stat-value">{report.total_duration_ms:.1f}ms</div>
            </div>
        </div>

        {kb_html}

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


def generate_summary_report_html(
    reports: List[VerificationReport],
    output_path: Optional[Path] = None,
    title: str = "Parity Migration Summary Dashboard",
) -> str:
    """Generates an HTML summary dashboard across all verified objects."""
    total_objects = len(reports)
    passed_count = sum(1 for r in reports if r.overall_passed)
    pass_rate = (passed_count / total_objects * 100.0) if total_objects > 0 else 0.0
    total_cost = sum(r.cost_usd for r in reports)
    total_duration = sum(r.total_duration_ms for r in reports)

    rate_color = "#10b981" if pass_rate >= 80 else ("#f59e0b" if pass_rate >= 50 else "#ef4444")

    rows_html = ""
    for r in reports:
        status_color = "#10b981" if r.overall_passed else "#ef4444"
        status_text = "PASS" if r.overall_passed else "FAIL"

        l_badges = []
        for l_num in range(1, 6):
            layer = r.get_layer(l_num)
            if layer:
                bg = "#10b981" if layer.passed else "#ef4444"
                text = f"L{l_num}"
            else:
                bg = "#6b7280"
                text = f"L{l_num}"
            l_badges.append(f'<span class="badge" style="background:{bg}22; color:{bg}; border:1px solid {bg}55; margin-right:3px;">{text}</span>')

        layers_summary = "".join(l_badges)
        detail_link = f"{r.query_name}_evidence.html"

        rows_html += f"""
        <tr>
            <td><strong>{html.escape(r.query_name)}</strong></td>
            <td><span class="badge" style="background:{status_color}22; color:{status_color}; border:1px solid {status_color}55;">{status_text}</span></td>
            <td>{layers_summary}</td>
            <td>{r.attempts}</td>
            <td>${r.cost_usd:.5f}</td>
            <td>{r.total_duration_ms:.1f}ms</td>
            <td><a href="{detail_link}" class="report-link">View Evidence</a></td>
        </tr>
        """

    summary_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{html.escape(title)}</title>
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
            max-width: 1200px;
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
        .stats-bar {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 16px;
            margin-bottom: 24px;
        }}
        .stat-card {{
            background: var(--surface);
            border: 1px solid var(--surface-border);
            border-radius: 10px;
            padding: 20px;
        }}
        .stat-label {{
            font-size: 12px;
            color: var(--text-secondary);
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 6px;
        }}
        .stat-value {{
            font-size: 26px;
            font-weight: 700;
            color: var(--text-primary);
        }}
        .card {{
            background: var(--surface);
            border: 1px solid var(--surface-border);
            border-radius: 12px;
            padding: 24px;
            overflow-x: auto;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 14px;
            text-align: left;
        }}
        th {{
            color: var(--text-secondary);
            font-weight: 600;
            padding: 12px 14px;
            border-bottom: 1px solid var(--surface-border);
            text-transform: uppercase;
            font-size: 12px;
            letter-spacing: 0.05em;
        }}
        td {{
            padding: 14px;
            border-bottom: 1px solid #1a2233;
            color: #d1d5db;
        }}
        tr:hover td {{
            background: #141d2f;
        }}
        .badge {{
            padding: 3px 8px;
            border-radius: 6px;
            font-size: 11px;
            font-weight: 600;
            display: inline-block;
        }}
        .report-link {{
            color: #38bdf8;
            text-decoration: none;
            font-weight: 600;
        }}
        .report-link:hover {{
            text-decoration: underline;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div>
                <h1 style="margin: 0 0 6px 0; font-size: 24px;">{html.escape(title)}</h1>
                <div style="color: var(--text-secondary); font-size: 14px;">5-Layer Semantic Verification Audit Trail • Generated: {time.strftime("%Y-%m-%d %H:%M:%S")}</div>
            </div>
        </div>

        <div class="stats-bar">
            <div class="stat-card">
                <div class="stat-label">Total SQL Objects</div>
                <div class="stat-value">{total_objects}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Verified Pass Rate</div>
                <div class="stat-value" style="color: {rate_color};">{pass_rate:.1f}% ({passed_count}/{total_objects})</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Total LLM Spend</div>
                <div class="stat-value">${total_cost:.5f}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Total Execution Time</div>
                <div class="stat-value">{total_duration:.1f}ms</div>
            </div>
        </div>

        <div class="card">
            <table>
                <thead>
                    <tr>
                        <th>Object Name</th>
                        <th>Status</th>
                        <th>Verification Layers</th>
                        <th>Attempts</th>
                        <th>Cost</th>
                        <th>Duration</th>
                        <th>Report</th>
                    </tr>
                </thead>
                <tbody>
                    {rows_html}
                </tbody>
            </table>
        </div>
    </div>
</body>
</html>
"""
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(summary_html, encoding="utf-8")

    return summary_html

