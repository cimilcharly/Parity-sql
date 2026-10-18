"""Pull Request generation for automated object migrations."""

from pathlib import Path
from typing import Optional
from parity.workflow.models import MigrationItem


def generate_pr_markdown(item: MigrationItem, output_path: Optional[Path] = None) -> str:
    """Generates a GitHub PR markdown artifact for a migrated SQL/PLSQL object."""
    status_emoji = "✅" if item.passed else "❌"
    status_text = "VERIFIED PASS" if item.passed else "BLOCKED (VERIFICATION FAILED)"
    merge_directive = (
        "> **MERGE POLICY**: ✅ **APPROVED FOR MERGE**. All 5 semantic verification layers passed successfully."
        if item.passed
        else "> **MERGE POLICY**: ⛔ **DO NOT MERGE**. Verification failed or unsupported constructs detected."
    )

    kb_section = ""
    if item.applied_kb_entries:
        kb_items = "\n".join(f"- `{k}`" for k in item.applied_kb_entries)
        kb_section = f"\n### 🧠 Applied Knowledge Base Context\n{kb_items}\n"

    evidence_link = (
        f"[View Full HTML Evidence Report]({item.evidence_report_path.as_posix()})"
        if item.evidence_report_path
        else "N/A"
    )

    md = f"""# feat(migration): Migrate Oracle `{item.object_name}` to PostgreSQL

{status_emoji} **Verification Status**: `{status_text}`  
🌿 **Target Branch**: `{item.git_branch}`  
📊 **Repair Attempts**: `{item.attempts}`  
💰 **LLM Cost**: `${item.cost_usd:.5f}`  
⏱️ **Verification Latency**: `{item.duration_ms:.1f}ms`  
📂 **Source File**: `{item.source_file.name}`

---

{merge_directive}

---

## 🔍 Semantic Verification Audit Trail

| Verification Layer | Check Type | Status |
|---|---|---|
| **Layer 1** | Target PostgreSQL Query Plan Compilation (`EXPLAIN`) | {"✅ PASSED" if item.passed else "⚠️ CHECK REPORT"} |
| **Layer 2** | Schema Column Count, Types & Projection Order | {"✅ PASSED" if item.passed else "⚠️ CHECK REPORT"} |
| **Layer 3** | Exact Row Count Cardinality Parity | {"✅ PASSED" if item.passed else "⚠️ CHECK REPORT"} |
| **Layer 4** | Column Aggregates (Nulls, Sums, Medians $\\le 10^{-9}$) | {"✅ PASSED" if item.passed else "⚠️ CHECK REPORT"} |
| **Layer 5** | Row-Level Cryptographic SHA-256 Multiset Hashing | {"✅ PASSED" if item.passed else "⚠️ CHECK REPORT"} |

{kb_section}

---

## 📄 SQL Comparison

### Source (Oracle SQL)
```sql
{item.source_sql}
```

### Transpiled Target (PostgreSQL SQL)
```sql
{item.target_sql if item.target_sql else "-- [TRANSCRIPTION BLOCKED]"}
```

---

## 📎 Audit Artifacts
- **Evidence Audit Report**: {evidence_link}
- **Deterministic-First Guarantee**: Checked via Parity 5-Layer Stack.

*Generated automatically by Parity Migration Workflow.*
"""
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(md, encoding="utf-8")

    return md
