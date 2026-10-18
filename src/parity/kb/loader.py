"""Knowledge Base loader and search engine for dialect differences."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional
import yaml


@dataclass
class DifferenceEntry:
    id: str
    title: str
    severity: str
    category: str
    oracle_behavior: str
    postgres_behavior: str
    symptom: str
    remedy: str
    sql_example_oracle: str
    sql_example_postgres: str


class KnowledgeBase:
    """Provides structured access to Oracle -> PostgreSQL differences catalog."""

    def __init__(self, yaml_path: Optional[Path] = None):
        if yaml_path is None:
            yaml_path = Path(__file__).resolve().parent / "dialect_differences.yaml"
        self.yaml_path = yaml_path
        self._entries: List[DifferenceEntry] = []
        self._load()

    def _load(self) -> None:
        if not self.yaml_path.exists():
            return
        with open(self.yaml_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            raw_entries = data.get("differences", [])
            for item in raw_entries:
                self._entries.append(DifferenceEntry(**item))

    def get_all(self) -> List[DifferenceEntry]:
        return self._entries

    def get_by_id(self, diff_id: str) -> Optional[DifferenceEntry]:
        for entry in self._entries:
            if entry.id.lower() == diff_id.lower():
                return entry
        return None

    def search(self, query: str) -> List[DifferenceEntry]:
        q = query.lower()
        results = []
        for entry in self._entries:
            if (
                q in entry.id.lower()
                or q in entry.title.lower()
                or q in entry.symptom.lower()
                or q in entry.remedy.lower()
                or q in entry.oracle_behavior.lower()
            ):
                results.append(entry)
        return results

    def match_diagnostic(self, error_message: str, sql: str) -> List[DifferenceEntry]:
        """Matches database error message or SQL tokens to cataloged dialect differences."""
        matches = []
        err = error_message.lower()
        sql_upper = sql.upper()

        for entry in self._entries:
            # Check for error symptoms
            if entry.id == "ORA_DIFF_004" and ("nvl" in err or "nvl(" in sql.lower()):
                matches.append(entry)
            elif entry.id == "ORA_DIFF_005" and ("decode" in err or "decode(" in sql.lower()):
                matches.append(entry)
            elif entry.id == "ORA_DIFF_006" and ("rownum" in err or "ROWNUM" in sql_upper):
                matches.append(entry)
            elif entry.id == "ORA_DIFF_007" and ("(+)" in sql or "(+)" in err):
                matches.append(entry)
            elif entry.id == "ORA_DIFF_009" and ("sysdate" in err or "SYSDATE" in sql_upper):
                matches.append(entry)
            elif entry.id == "ORA_DIFF_010" and ("trunc" in err or "TRUNC(" in sql_upper):
                matches.append(entry)
            elif entry.id == "ORA_DIFF_015" and ("dual" in err or "FROM DUAL" in sql_upper):
                matches.append(entry)
            elif entry.id == "ORA_DIFF_008" and (".nextval" in err or ".NEXTVAL" in sql_upper):
                matches.append(entry)
            elif entry.id == "ORA_DIFF_002" and "||" in sql and "null" in err:
                matches.append(entry)

        return matches


kb = KnowledgeBase()
