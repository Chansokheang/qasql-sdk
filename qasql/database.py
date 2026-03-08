"""
Database Connector Module

Unified interface for SQLite and PostgreSQL databases.
"""

import sqlite3
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Optional

from qasql.config import QASQLConfig


class BaseDatabaseConnector(ABC):
    """Abstract base class for database connectors."""

    @abstractmethod
    def connect(self):
        """Establish database connection."""
        pass

    @abstractmethod
    def disconnect(self):
        """Close database connection."""
        pass

    @abstractmethod
    def execute(self, sql: str, timeout: float = 30.0) -> tuple[list[tuple], list[str]]:
        """Execute SQL query and return results."""
        pass

    @abstractmethod
    def get_tables(self) -> list[str]:
        """Get list of all table names."""
        pass

    @abstractmethod
    def get_table_schema(self, table_name: str) -> dict[str, Any]:
        """Get schema information for a table."""
        pass

    @abstractmethod
    def get_sample_rows(self, table_name: str, limit: int = 5) -> list[tuple]:
        """Get sample rows from a table."""
        pass

    def extract_full_schema(self) -> dict[str, Any]:
        """Extract complete schema from database."""
        tables = self.get_tables()
        schema = {"tables": {}}

        for table_name in tables:
            table_schema = self.get_table_schema(table_name)
            sample_rows = self.get_sample_rows(table_name)
            table_schema["sample_rows"] = sample_rows
            schema["tables"][table_name] = table_schema

        return schema


class SQLiteConnector(BaseDatabaseConnector):
    """SQLite database connector."""

    def __init__(self, db_path: str):
        self.db_path = Path(db_path)
        self.connection: Optional[sqlite3.Connection] = None

        if not self.db_path.exists():
            raise FileNotFoundError(f"Database not found: {self.db_path}")

    def connect(self):
        self.connection = sqlite3.connect(str(self.db_path))
        self.connection.row_factory = sqlite3.Row

    def disconnect(self):
        if self.connection:
            self.connection.close()
            self.connection = None

    def execute(self, sql: str, timeout: float = 30.0) -> tuple[list[tuple], list[str]]:
        if not self.connection:
            self.connect()

        self.connection.execute(f"PRAGMA busy_timeout = {int(timeout * 1000)}")
        cursor = self.connection.cursor()
        cursor.execute(sql)

        rows = cursor.fetchall()
        column_names = [desc[0] for desc in cursor.description] if cursor.description else []

        return [tuple(row) for row in rows], column_names

    def get_tables(self) -> list[str]:
        if not self.connection:
            self.connect()

        cursor = self.connection.cursor()
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
            ORDER BY name
        """)
        return [row[0] for row in cursor.fetchall()]

    def get_table_schema(self, table_name: str) -> dict[str, Any]:
        if not self.connection:
            self.connect()

        cursor = self.connection.cursor()
        cursor.execute(f"PRAGMA table_info('{table_name}')")
        columns_info = cursor.fetchall()

        columns = []
        primary_keys = []

        for col in columns_info:
            col_name = col[1]
            col_type = col[2] or "TEXT"
            is_pk = col[5] == 1

            column_data = {
                "name": col_name,
                "type": col_type.upper(),
                "nullable": col[3] == 0,
                "default": col[4],
            }

            if col_type.upper() in ("TEXT", "VARCHAR", "CHAR"):
                try:
                    cursor.execute(f"""
                        SELECT DISTINCT "{col_name}"
                        FROM "{table_name}"
                        WHERE "{col_name}" IS NOT NULL
                        LIMIT 20
                    """)
                    distinct_values = [row[0] for row in cursor.fetchall()]
                    if len(distinct_values) <= 15:
                        column_data["distinct_values"] = distinct_values
                except:
                    pass

            columns.append(column_data)
            if is_pk:
                primary_keys.append(col_name)

        cursor.execute(f"PRAGMA foreign_key_list('{table_name}')")
        fk_info = cursor.fetchall()

        foreign_keys = [
            {
                "column": fk[3],
                "references_table": fk[2],
                "references_column": fk[4]
            }
            for fk in fk_info
        ]

        cursor.execute(f"SELECT COUNT(*) FROM '{table_name}'")
        row_count = cursor.fetchone()[0]

        return {
            "columns": columns,
            "primary_keys": primary_keys,
            "foreign_keys": foreign_keys,
            "row_count": row_count
        }

    def get_sample_rows(self, table_name: str, limit: int = 5) -> list[tuple]:
        if not self.connection:
            self.connect()

        cursor = self.connection.cursor()
        cursor.execute(f"SELECT * FROM '{table_name}' LIMIT {limit}")
        return [tuple(row) for row in cursor.fetchall()]


class PostgreSQLConnector(BaseDatabaseConnector):
    """PostgreSQL database connector."""

    def __init__(self, host: str, port: int, database: str, user: str, password: str):
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password
        self.connection = None

    def connect(self):
        try:
            import psycopg2
        except ImportError:
            raise ImportError(
                "psycopg2 is required for PostgreSQL. "
                "Install with: pip install qasql[postgres]"
            )

        self.connection = psycopg2.connect(
            host=self.host,
            port=self.port,
            database=self.database,
            user=self.user,
            password=self.password
        )

    def disconnect(self):
        if self.connection:
            self.connection.close()
            self.connection = None

    def execute(self, sql: str, timeout: float = 30.0) -> tuple[list[tuple], list[str]]:
        if not self.connection:
            self.connect()

        cursor = self.connection.cursor()
        cursor.execute(f"SET statement_timeout = {int(timeout * 1000)}")
        cursor.execute(sql)

        rows = cursor.fetchall()
        column_names = [desc[0] for desc in cursor.description] if cursor.description else []
        return list(rows), column_names

    def get_tables(self) -> list[str]:
        if not self.connection:
            self.connect()

        cursor = self.connection.cursor()
        cursor.execute("""
            SELECT table_name FROM information_schema.tables
            WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """)
        return [row[0] for row in cursor.fetchall()]

    def get_table_schema(self, table_name: str) -> dict[str, Any]:
        if not self.connection:
            self.connect()

        cursor = self.connection.cursor()
        cursor.execute(f"""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_name = '{table_name}' AND table_schema = 'public'
            ORDER BY ordinal_position
        """)

        columns = []
        for col in cursor.fetchall():
            column_data = {
                "name": col[0],
                "type": col[1].upper(),
                "nullable": col[2] == "YES",
                "default": col[3],
            }

            if col[1].upper() in ("TEXT", "VARCHAR", "CHARACTER VARYING"):
                try:
                    cursor.execute(f"""
                        SELECT DISTINCT "{col[0]}" FROM "{table_name}"
                        WHERE "{col[0]}" IS NOT NULL LIMIT 20
                    """)
                    distinct_values = [row[0] for row in cursor.fetchall()]
                    if len(distinct_values) <= 15:
                        column_data["distinct_values"] = distinct_values
                except:
                    pass

            columns.append(column_data)

        cursor.execute(f"""
            SELECT a.attname FROM pg_index i
            JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey)
            WHERE i.indrelid = '{table_name}'::regclass AND i.indisprimary
        """)
        primary_keys = [row[0] for row in cursor.fetchall()]

        cursor.execute(f"""
            SELECT kcu.column_name, ccu.table_name, ccu.column_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu ON tc.constraint_name = kcu.constraint_name
            JOIN information_schema.constraint_column_usage ccu ON ccu.constraint_name = tc.constraint_name
            WHERE tc.constraint_type = 'FOREIGN KEY' AND tc.table_name = '{table_name}'
        """)
        foreign_keys = [
            {"column": fk[0], "references_table": fk[1], "references_column": fk[2]}
            for fk in cursor.fetchall()
        ]

        cursor.execute(f"SELECT COUNT(*) FROM \"{table_name}\"")
        row_count = cursor.fetchone()[0]

        return {
            "columns": columns,
            "primary_keys": primary_keys,
            "foreign_keys": foreign_keys,
            "row_count": row_count
        }

    def get_sample_rows(self, table_name: str, limit: int = 5) -> list[tuple]:
        if not self.connection:
            self.connect()

        cursor = self.connection.cursor()
        cursor.execute(f"SELECT * FROM \"{table_name}\" LIMIT {limit}")
        return list(cursor.fetchall())


class DatabaseConnector:
    """Factory class for creating database connectors."""

    @staticmethod
    def from_config(config: QASQLConfig) -> BaseDatabaseConnector:
        """Create database connector from configuration."""
        if config.db_type == "sqlite":
            return SQLiteConnector(config.db_uri)
        elif config.db_type == "postgresql":
            return PostgreSQLConnector(
                host=config.db_host,
                port=config.db_port,
                database=config.db_name,
                user=config.db_user,
                password=config.db_password
            )
        else:
            raise ValueError(f"Unsupported database type: {config.db_type}")

    @staticmethod
    def from_uri(uri: str) -> BaseDatabaseConnector:
        """Create database connector from URI."""
        config = QASQLConfig(db_uri=uri)
        return DatabaseConnector.from_config(config)
