"""Prompt templates and formatters for semantic SQL repair."""

from typing import Any, Dict, List, Optional
from parity.kb.loader import DifferenceEntry


SYSTEM_REPAIR_PROMPT = """You are Parity's Autonomous SQL Migration & Repair Agent.
Your task is to fix a PostgreSQL query that was transpiled from Oracle SQL, but failed semantic verification against the target database.

CRITICAL INSTRUCTIONS:
1. Output ONLY the repaired PostgreSQL SQL query enclosed in ```sql ... ``` code fence.
2. Do NOT add conversational prose, pleasantries, or explanations.
3. Obey PostgreSQL syntax and semantic rules strictly.
4. Adhere to the provided Oracle-to-PostgreSQL Knowledge Base diagnostic entries.
5. NEVER rely on Oracle proprietary keywords (e.g. NVL, DECODE, (+), SYSDATE, ROWNUM, FROM DUAL).
"""


def build_repair_prompt(
    object_name: str,
    source_oracle_sql: str,
    failed_target_sql: str,
    failed_layer_name: str,
    layer_diagnostics: str,
    diff_details: Optional[Dict[str, Any]] = None,
    kb_entries: Optional[List[DifferenceEntry]] = None,
) -> str:
    """Constructs a structured prompt without leaking any raw table rows."""
    prompt_lines = [
        f"### Migration Repair Request: {object_name}",
        "",
        "#### 1. Original Source (Oracle SQL):",
        "```sql",
        source_oracle_sql.strip(),
        "```",
        "",
        "#### 2. Current Transpiled Candidate (PostgreSQL SQL):",
        "```sql",
        failed_target_sql.strip(),
        "```",
        "",
        f"#### 3. Verification Failure ({failed_layer_name}):",
        f"- Diagnostic Message: {layer_diagnostics}",
    ]

    if diff_details:
        prompt_lines.append("- Diagnostic Details (Aggregates & Schema Only, No Raw Rows):")
        for k, v in diff_details.items():
            prompt_lines.append(f"  * {k}: {v}")

    if kb_entries:
        prompt_lines.append("")
        prompt_lines.append("#### 4. Relevant Dialect Knowledge Base Remedies:")
        for e in kb_entries:
            prompt_lines.append(f"- **[{e.id}] {e.title}** (Severity: {e.severity}):")
            prompt_lines.append(f"  * Oracle Behavior: {e.oracle_behavior}")
            prompt_lines.append(f"  * Postgres Behavior: {e.postgres_behavior}")
            prompt_lines.append(f"  * Recommended Remedy: {e.remedy}")
            prompt_lines.append(f"  * Postgres Example: `{e.sql_example_postgres}`")

    prompt_lines.append("")
    prompt_lines.append("#### 5. Your Goal:")
    prompt_lines.append("Rewrite the candidate PostgreSQL SQL query to resolve the semantic mismatch and pass verification.")
    prompt_lines.append("Return ONLY the final PostgreSQL query in a ```sql ... ``` block.")

    return "\n".join(prompt_lines)


def extract_sql_from_response(response_text: str) -> str:
    """Extracts clean SQL from model output, stripping markdown codeblocks and comments."""
    text = response_text.strip()
    if "```sql" in text:
        parts = text.split("```sql")
        content = parts[1].split("```")[0]
        return content.strip()
    elif "```" in text:
        parts = text.split("```")
        content = parts[1].split("```")[0]
        return content.strip()
    return text
