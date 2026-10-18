"""PL/SQL to PL/pgSQL transpiler for functions and basic procedures."""

import re
from typing import Optional, Tuple
from parity.plsql.models import PLSQLConstructType, PLSQLTranspileResult, UnsupportedConstruct
from parity.plsql.unsupported import detect_unsupported_constructs


TYPE_MAP = [
    (re.compile(r"\bVARCHAR2\b", re.IGNORECASE), "VARCHAR"),
    (re.compile(r"\bNVARCHAR2\b", re.IGNORECASE), "VARCHAR"),
    (re.compile(r"\bNUMBER\((\d+)\s*,\s*(\d+)\)", re.IGNORECASE), r"NUMERIC(\1, \2)"),
    (re.compile(r"\bNUMBER\((\d+)\)", re.IGNORECASE), r"NUMERIC(\1)"),
    (re.compile(r"\bNUMBER\b", re.IGNORECASE), "NUMERIC"),
    (re.compile(r"\bPLS_INTEGER\b", re.IGNORECASE), "INTEGER"),
    (re.compile(r"\bBINARY_INTEGER\b", re.IGNORECASE), "INTEGER"),
    (re.compile(r"\bDATE\b", re.IGNORECASE), "TIMESTAMP WITHOUT TIME ZONE"),
    (re.compile(r"\bCLOB\b", re.IGNORECASE), "TEXT"),
    (re.compile(r"\bBLOB\b", re.IGNORECASE), "BYTEA"),
]


def convert_datatype(datatype_str: str) -> str:
    """Maps Oracle datatypes to PostgreSQL equivalents."""
    res = datatype_str.strip()
    for pattern, repl in TYPE_MAP:
        res = pattern.sub(repl, res)
    return res


def convert_body_statements(body_code: str) -> str:
    """Converts standard Oracle builtin calls to PostgreSQL PL/pgSQL equivalents."""
    converted = body_code

    # DBMS_OUTPUT.PUT_LINE(x) -> RAISE NOTICE '%', x;
    converted = re.sub(
        r"DBMS_OUTPUT\.PUT_LINE\s*\((.*?)\)\s*;",
        r"RAISE NOTICE '%', \1;",
        converted,
        flags=re.IGNORECASE,
    )

    # RAISE_APPLICATION_ERROR(-20001, 'msg') -> RAISE EXCEPTION '%', 'msg';
    converted = re.sub(
        r"RAISE_APPLICATION_ERROR\s*\(\s*[^,]+,\s*(.*?)\s*\)\s*;",
        r"RAISE EXCEPTION '%', \1;",
        converted,
        flags=re.IGNORECASE,
    )

    # SYSDATE -> CURRENT_TIMESTAMP
    converted = re.sub(r"\bSYSDATE\b", "CURRENT_TIMESTAMP", converted, flags=re.IGNORECASE)

    # NVL(a, b) -> COALESCE(a, b)
    converted = re.sub(r"\bNVL\s*\(", "COALESCE(", converted, flags=re.IGNORECASE)

    # TRUNC(d, 'MM') -> DATE_TRUNC('month', d)
    converted = re.sub(
        r"\bTRUNC\s*\(\s*([^,]+?)\s*,\s*'MM'\s*\)",
        r"DATE_TRUNC('month', \1)",
        converted,
        flags=re.IGNORECASE,
    )

    return converted


class PLSQLConverter:
    """Converts simple Oracle PL/SQL functions and procedures to PostgreSQL PL/pgSQL."""

    FUNCTION_REGEX = re.compile(
        r"CREATE\s+(?:OR\s+REPLACE\s+)?FUNCTION\s+([a-zA-Z0-9_]+)\s*(?:\((.*?)\))?\s+RETURN\s+([a-zA-Z0-9_\(\)%]+)\s+(?:IS|AS)\b(.*)",
        re.IGNORECASE | re.DOTALL,
    )

    PROCEDURE_REGEX = re.compile(
        r"CREATE\s+(?:OR\s+REPLACE\s+)?PROCEDURE\s+([a-zA-Z0-9_]+)\s*(?:\((.*?)\))?\s+(?:IS|AS)\b(.*)",
        re.IGNORECASE | re.DOTALL,
    )

    def convert(self, oracle_sql: str) -> PLSQLTranspileResult:
        """Converts Oracle PL/SQL into PostgreSQL PL/pgSQL, or flags unsupported constructs."""
        raw_code = oracle_sql.strip()

        # Step 1: Detect explicit unsupported constructs
        unsupported = detect_unsupported_constructs(raw_code)
        if unsupported:
            return PLSQLTranspileResult(
                object_name="unknown",
                object_type=PLSQLConstructType.ANONYMOUS_BLOCK,
                source_code=raw_code,
                target_code="",
                success=False,
                unsupported_constructs=unsupported,
                warnings=[f"Unsupported construct: {u.name} (Line {u.line_number})" for u in unsupported],
            )

        # Step 2: Try parsing as Function
        func_match = self.FUNCTION_REGEX.search(raw_code)
        if func_match:
            return self._convert_function(raw_code, func_match)

        # Step 3: Try parsing as Procedure
        proc_match = self.PROCEDURE_REGEX.search(raw_code)
        if proc_match:
            return self._convert_procedure(raw_code, proc_match)

        # If not recognizable as standard function/procedure
        return PLSQLTranspileResult(
            object_name="unknown",
            object_type=PLSQLConstructType.ANONYMOUS_BLOCK,
            source_code=raw_code,
            target_code="",
            success=False,
            unsupported_constructs=[
                UnsupportedConstruct(
                    name="UNRECOGNIZED_PLSQL_BLOCK",
                    line_number=1,
                    description="Code is not a standard CREATE FUNCTION or CREATE PROCEDURE statement.",
                    remedy="Ensure code starts with CREATE [OR REPLACE] FUNCTION/PROCEDURE.",
                )
            ],
            warnings=["Only CREATE OR REPLACE FUNCTION and CREATE OR REPLACE PROCEDURE are currently supported."],
        )

    def _convert_function(self, raw_code: str, match: re.Match) -> PLSQLTranspileResult:
        func_name = match.group(1).lower()
        raw_params = match.group(2) or ""
        raw_return = match.group(3)
        rest = match.group(4)

        target_params = self._convert_parameters(raw_params)
        target_return = convert_datatype(raw_return)

        declarations, body, exceptions = self._extract_blocks(rest, func_name)

        decl_section = f"DECLARE\n{declarations}\n" if declarations.strip() else ""
        exc_section = f"\nEXCEPTION\n{exceptions}" if exceptions.strip() else ""

        converted_body = convert_body_statements(body.strip())

        target_code = (
            f"CREATE OR REPLACE FUNCTION {func_name}({target_params})\n"
            f"RETURNS {target_return}\n"
            f"LANGUAGE plpgsql\n"
            f"AS $$\n"
            f"{decl_section}"
            f"BEGIN\n"
            f"    {converted_body}\n"
            f"{exc_section}"
            f"END;\n"
            f"$$;"
        )

        return PLSQLTranspileResult(
            object_name=func_name,
            object_type=PLSQLConstructType.FUNCTION,
            source_code=raw_code,
            target_code=target_code,
            success=True,
        )

    def _convert_procedure(self, raw_code: str, match: re.Match) -> PLSQLTranspileResult:
        proc_name = match.group(1).lower()
        raw_params = match.group(2) or ""
        rest = match.group(3)

        target_params = self._convert_parameters(raw_params)
        declarations, body, exceptions = self._extract_blocks(rest, proc_name)

        decl_section = f"DECLARE\n{declarations}\n" if declarations.strip() else ""
        exc_section = f"\nEXCEPTION\n{exceptions}" if exceptions.strip() else ""

        converted_body = convert_body_statements(body.strip())

        target_code = (
            f"CREATE OR REPLACE PROCEDURE {proc_name}({target_params})\n"
            f"LANGUAGE plpgsql\n"
            f"AS $$\n"
            f"{decl_section}"
            f"BEGIN\n"
            f"    {converted_body}\n"
            f"{exc_section}"
            f"END;\n"
            f"$$;"
        )

        return PLSQLTranspileResult(
            object_name=proc_name,
            object_type=PLSQLConstructType.PROCEDURE,
            source_code=raw_code,
            target_code=target_code,
            success=True,
        )

    def _convert_parameters(self, raw_params: str) -> str:
        if not raw_params.strip():
            return ""

        parts = [p.strip() for p in raw_params.split(",") if p.strip()]
        converted_parts = []
        for p in parts:
            # e.g. p_emp_id IN NUMBER := 0
            # Remove default or IN
            # IN is optional in Postgres
            tokens = p.split()
            if len(tokens) >= 2:
                name = tokens[0]
                type_tokens = tokens[1:]
                # Check for IN / OUT / IN OUT
                mode = ""
                if type_tokens[0].upper() == "IN" and len(type_tokens) > 1 and type_tokens[1].upper() == "OUT":
                    mode = "INOUT "
                    type_tokens = type_tokens[2:]
                elif type_tokens[0].upper() in ("IN", "OUT"):
                    if type_tokens[0].upper() == "OUT":
                        mode = "OUT "
                    type_tokens = type_tokens[1:]

                dtype = " ".join(type_tokens)
                converted_parts.append(f"{mode}{name} {convert_datatype(dtype)}")
            else:
                converted_parts.append(convert_datatype(p))

        return ", ".join(converted_parts)

    def _extract_blocks(self, rest: str, obj_name: str) -> Tuple[str, str, str]:
        """Extracts declarations, body, and exceptions from the remainder of a function/procedure."""
        # Find BEGIN
        begin_match = re.search(r"\bBEGIN\b", rest, re.IGNORECASE)
        if not begin_match:
            return ("", rest, "")

        declarations = rest[:begin_match.start()].strip()
        body_and_rest = rest[begin_match.end():].strip()

        # Clean trailing END [name];
        # Strip trailing END obj_name; or END;
        body_clean = re.sub(rf"\bEND(?:\s+{obj_name})?\s*;\s*$", "", body_and_rest, flags=re.IGNORECASE).strip()

        # Check for EXCEPTION block
        exc_match = re.search(r"\bEXCEPTION\b", body_clean, re.IGNORECASE)
        if exc_match:
            body = body_clean[:exc_match.start()].strip()
            exceptions = body_clean[exc_match.end():].strip()
        else:
            body = body_clean
            exceptions = ""

        # Map datatypes in declarations
        decl_lines = []
        for line in declarations.splitlines():
            line_str = line.strip()
            if line_str:
                decl_lines.append("    " + convert_datatype(line_str))
        formatted_declarations = "\n".join(decl_lines)

        return formatted_declarations, body, exceptions
