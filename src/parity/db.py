"""Database connectors for Oracle and PostgreSQL with read-only enforcement."""

from contextlib import contextmanager
import time
from typing import Any, Dict, Generator, List, Optional, Tuple

from parity.config import settings
from parity.security.redactor import Redactor


class DatabaseError(Exception):
    """Raised for database connectivity or execution errors."""
    pass


class QueryResult:
    """Holds column metadata and rows from a database execution."""
    def __init__(self, columns: List[str], rows: List[Tuple[Any, ...]]):
        self.columns = columns
        self.rows = rows

    @property
    def row_count(self) -> int:
        return len(self.rows)

    def to_dicts(self) -> List[Dict[str, Any]]:
        return [dict(zip(self.columns, row)) for row in self.rows]


class DatabaseManager:
    """Manages connections and safe read-only queries against Oracle and PostgreSQL."""

    def __init__(self):
        self.cfg = settings
        self._oracle_online: Optional[bool] = None
        self._postgres_online: Optional[bool] = None

    def check_oracle_health(self) -> bool:
        """Fast check if Oracle container/server is reachable."""
        if self._oracle_online is not None:
            return self._oracle_online
        try:
            import oracledb
            dsn = f"{self.cfg.oracle.host}:{self.cfg.oracle.port}/{self.cfg.oracle.database}"
            conn = oracledb.connect(
                user=self.cfg.oracle.user,
                password=self.cfg.oracle.password,
                dsn=dsn,
                tcp_connect_timeout=1.0,
            )
            conn.close()
            self._oracle_online = True
            return True
        except Exception:
            self._oracle_online = False
            return False

    def check_postgres_health(self) -> bool:
        """Fast check if PostgreSQL container/server is reachable."""
        if self._postgres_online is not None:
            return self._postgres_online
        try:
            conn = self._get_pg_connection(timeout=1)
            conn.close()
            self._postgres_online = True
            return True
        except Exception:
            self._postgres_online = False
            return False

    def execute_oracle(self, sql: str, params: Optional[Dict[str, Any]] = None) -> QueryResult:
        """Executes a read-only query against the Oracle database."""
        if self.cfg.read_only_guard:
            Redactor.assert_read_only(sql)

        try:
            import oracledb
        except ImportError:
            raise DatabaseError("oracledb package is not installed. Install via pip install oracledb.")

        try:
            dsn = f"{self.cfg.oracle.host}:{self.cfg.oracle.port}/{self.cfg.oracle.database}"
            with oracledb.connect(
                user=self.cfg.oracle.user,
                password=self.cfg.oracle.password,
                dsn=dsn,
                tcp_connect_timeout=2.0,
            ) as connection:
                with connection.cursor() as cursor:
                    if self.cfg.oracle.schema:
                        cursor.execute(f"ALTER SESSION SET CURRENT_SCHEMA = {self.cfg.oracle.schema}")
                    cursor.execute(sql, params or {})
                    columns = [desc[0].lower() for desc in cursor.description] if cursor.description else []
                    rows = cursor.fetchall()
                    return QueryResult(columns=columns, rows=rows)
        except Exception as e:
            raise DatabaseError(f"Oracle Execution Error: {e}") from e

    def _get_pg_connection(self, timeout: int = 2):
        """Returns a PostgreSQL connection using psycopg (v3) or psycopg2."""
        try:
            import psycopg
            conn_info = (
                f"host={self.cfg.postgres.host} "
                f"port={self.cfg.postgres.port} "
                f"dbname={self.cfg.postgres.database} "
                f"user={self.cfg.postgres.user} "
                f"password={self.cfg.postgres.password} "
                f"connect_timeout={timeout}"
            )
            return psycopg.connect(conn_info)
        except ImportError:
            pass

        try:
            import psycopg2
            return psycopg2.connect(
                host=self.cfg.postgres.host,
                port=self.cfg.postgres.port,
                dbname=self.cfg.postgres.database,
                user=self.cfg.postgres.user,
                password=self.cfg.postgres.password,
                connect_timeout=timeout,
            )
        except ImportError:
            raise DatabaseError("Neither psycopg nor psycopg2 is installed. Install via pip install psycopg2-binary or psycopg.")

    def execute_postgres(self, sql: str, params: Optional[Tuple[Any, ...]] = None) -> QueryResult:
        """Executes a read-only query against the PostgreSQL database."""
        if self.cfg.read_only_guard:
            Redactor.assert_read_only(sql)

        try:
            with self._get_pg_connection() as conn:
                with conn.cursor() as cursor:
                    if self.cfg.postgres.schema:
                        cursor.execute(f"SET search_path TO {self.cfg.postgres.schema}, public")
                    cursor.execute(sql, params)
                    columns = [desc[0].lower() if hasattr(desc, '__getitem__') else desc.name.lower() for desc in cursor.description] if cursor.description else []
                    rows = cursor.fetchall()
                    return QueryResult(columns=columns, rows=rows)
        except Exception as e:
            raise DatabaseError(f"PostgreSQL Execution Error: {e}") from e

    def explain_postgres(self, sql: str) -> bool:
        """Validates query compilation on PostgreSQL without executing side effects using EXPLAIN."""
        if self.cfg.read_only_guard:
            Redactor.assert_read_only(sql)

        try:
            with self._get_pg_connection() as conn:
                with conn.cursor() as cursor:
                    if self.cfg.postgres.schema:
                        cursor.execute(f"SET search_path TO {self.cfg.postgres.schema}, public")
                    cursor.execute(f"EXPLAIN {sql}")
                    cursor.fetchall()
                    return True
        except Exception as e:
            raise DatabaseError(f"Postgres EXPLAIN validation failed: {e}") from e


db = DatabaseManager()
