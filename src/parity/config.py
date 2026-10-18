"""Configuration loader for Parity."""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class DatabaseConfig:
    host: str
    port: int
    user: str
    password: str
    database: str
    schema: Optional[str] = None


@dataclass
class Settings:
    oracle: DatabaseConfig
    postgres: DatabaseConfig
    numeric_tolerance: float = 1e-9
    max_row_sample: int = 10000
    read_only_guard: bool = True
    project_root: Path = Path(__file__).resolve().parent.parent.parent

    @classmethod
    def load(cls) -> "Settings":
        # Check for .env file and load it if python-dotenv is available
        try:
            from dotenv import load_dotenv
            load_dotenv()
        except ImportError:
            pass

        oracle_cfg = DatabaseConfig(
            host=os.getenv("ORACLE_HOST", "localhost"),
            port=int(os.getenv("ORACLE_PORT", "1521")),
            user=os.getenv("ORACLE_USER", "hr"),
            password=os.getenv("ORACLE_PASSWORD", "hr_password"),
            database=os.getenv("ORACLE_SERVICE", "FREEPDB1"),
            schema=os.getenv("ORACLE_SCHEMA", "HR"),
        )

        postgres_cfg = DatabaseConfig(
            host=os.getenv("POSTGRES_HOST", "localhost"),
            port=int(os.getenv("POSTGRES_PORT", "5432")),
            user=os.getenv("POSTGRES_USER", "parity"),
            password=os.getenv("POSTGRES_PASSWORD", "parity_secret"),
            database=os.getenv("POSTGRES_DB", "parity_db"),
            schema=os.getenv("POSTGRES_SCHEMA", "hr"),
        )

        return cls(
            oracle=oracle_cfg,
            postgres=postgres_cfg,
            numeric_tolerance=float(os.getenv("PARITY_NUMERIC_TOLERANCE", "1e-9")),
            max_row_sample=int(os.getenv("PARITY_MAX_ROW_SAMPLE", "10000")),
            read_only_guard=os.getenv("PARITY_READ_ONLY_GUARD", "true").lower() == "true",
        )


settings = Settings.load()
