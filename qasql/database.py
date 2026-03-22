"""
Database Connector Module

Unified interface for SQLite, PostgreSQL, and Supabase databases.
"""

import sqlite3
import re
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
    """PostgreSQL database connector with SSL support for Supabase and cloud databases."""

    def __init__(
        self,
        host: str,
        port: int,
        database: str,
        user: str,
        password: str,
        sslmode: str = "prefer",
        schema: str = "public"
    ):
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password
        self.sslmode = sslmode
        self.schema = schema
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
            password=self.password,
            sslmode=self.sslmode
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
            WHERE table_schema = %s AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """, (self.schema,))
        return [row[0] for row in cursor.fetchall()]

    def get_table_schema(self, table_name: str) -> dict[str, Any]:
        if not self.connection:
            self.connect()

        cursor = self.connection.cursor()
        cursor.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_name = %s AND table_schema = %s
            ORDER BY ordinal_position
        """, (table_name, self.schema))

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


class SupabaseConnector(BaseDatabaseConnector):
    """
    Supabase database connector using the official supabase-py client.

    Uses the Supabase Python SDK for schema extraction and queries.
    Requires SUPABASE_URL and SUPABASE_KEY (anon or service_role).

    Install: pip install supabase

    Note: For complex SQL queries, you need to create an 'exec_sql' RPC function
    in Supabase, or use PostgreSQLConnector with direct database connection.
    """

    def __init__(
        self,
        url: str,
        key: str,
        schema: str = "public"
    ):
        """
        Initialize Supabase connector.

        Args:
            url: Supabase project URL (e.g., https://xxx.supabase.co)
            key: API key (anon key or service_role key)
            schema: Database schema to use (default: "public")
        """
        self.url = url.rstrip("/")
        self.key = key
        self.schema = schema
        self.client = None
        self._tables_cache: Optional[list[str]] = None

    def connect(self):
        """Initialize Supabase client connection."""
        try:
            from supabase import create_client, Client
        except ImportError:
            raise ImportError(
                "supabase is required for Supabase connections. "
                "Install with: pip install supabase"
            )

        self.client: Client = create_client(self.url, self.key)

    def disconnect(self):
        """Clear client connection."""
        self.client = None
        self._tables_cache = None

    def get_tables(self) -> list[str]:
        """Get list of all table names from Supabase."""
        if not self.client:
            self.connect()

        if self._tables_cache is not None:
            return self._tables_cache

        try:
            # Try to get tables via RPC function (if created)
            result = self.client.rpc(
                "get_tables",
                {"schema_name": self.schema}
            ).execute()
            if result.data:
                self._tables_cache = [row["table_name"] for row in result.data]
                return self._tables_cache
        except Exception:
            pass

        # Fallback: Try to query information_schema via RPC
        try:
            result = self.client.rpc(
                "exec_sql",
                {"query": f"""
                    SELECT table_name FROM information_schema.tables
                    WHERE table_schema = '{self.schema}' AND table_type = 'BASE TABLE'
                    ORDER BY table_name
                """}
            ).execute()
            if result.data:
                self._tables_cache = [row["table_name"] for row in result.data]
                return self._tables_cache
        except Exception:
            pass

        # Last fallback: empty list with warning
        print("Warning: Could not retrieve tables. Create 'get_tables' or 'exec_sql' RPC function.")
        self._tables_cache = []
        return self._tables_cache

    def get_table_schema(self, table_name: str) -> dict[str, Any]:
        """Get schema information for a table."""
        if not self.client:
            self.connect()

        columns = []
        primary_keys = []
        foreign_keys = []
        row_count = 0

        # Try to get columns via RPC
        try:
            result = self.client.rpc(
                "exec_sql",
                {"query": f"""
                    SELECT column_name, data_type, is_nullable, column_default
                    FROM information_schema.columns
                    WHERE table_name = '{table_name}' AND table_schema = '{self.schema}'
                    ORDER BY ordinal_position
                """}
            ).execute()
            if result.data:
                for col in result.data:
                    columns.append({
                        "name": col.get("column_name"),
                        "type": col.get("data_type", "").upper(),
                        "nullable": col.get("is_nullable") == "YES",
                        "default": col.get("column_default"),
                    })
        except Exception:
            # Fallback: infer schema from sample data
            try:
                result = self.client.table(table_name).select("*").limit(1).execute()
                if result.data and len(result.data) > 0:
                    for key, value in result.data[0].items():
                        col_type = "TEXT"
                        if isinstance(value, bool):
                            col_type = "BOOLEAN"
                        elif isinstance(value, int):
                            col_type = "INTEGER"
                        elif isinstance(value, float):
                            col_type = "NUMERIC"
                        columns.append({
                            "name": key,
                            "type": col_type,
                            "nullable": True,
                            "default": None,
                        })
            except Exception:
                pass

        # Try to get row count
        try:
            result = self.client.table(table_name).select("*", count="exact").limit(0).execute()
            row_count = result.count or 0
        except Exception:
            pass

        return {
            "columns": columns,
            "primary_keys": primary_keys,
            "foreign_keys": foreign_keys,
            "row_count": row_count
        }

    def get_sample_rows(self, table_name: str, limit: int = 5) -> list[tuple]:
        """Get sample rows from a table."""
        if not self.client:
            self.connect()

        try:
            result = self.client.table(table_name).select("*").limit(limit).execute()
            if result.data:
                return [tuple(row.values()) for row in result.data]
        except Exception:
            pass
        return []

    def execute(self, sql: str, timeout: float = 30.0) -> tuple[list[tuple], list[str]]:
        """
        Execute SQL query via Supabase RPC.

        Requires a database function 'exec_sql' to be created in Supabase.
        Run this SQL in the Supabase SQL Editor:

        CREATE OR REPLACE FUNCTION exec_sql(query text)
        RETURNS json
        LANGUAGE plpgsql
        SECURITY DEFINER
        AS $$
        DECLARE
            result json;
        BEGIN
            EXECUTE 'SELECT json_agg(row_to_json(t)) FROM (' || query || ') t'
            INTO result;
            RETURN COALESCE(result, '[]'::json);
        END;
        $$;

        If this function doesn't exist, falls back to simple table queries.
        """
        if not self.client:
            self.connect()

        # Try RPC execution first
        try:
            result = self.client.rpc("exec_sql", {"query": sql}).execute()
            if result.data:
                if isinstance(result.data, list) and len(result.data) > 0:
                    columns = list(result.data[0].keys())
                    rows = [tuple(row.values()) for row in result.data]
                    return rows, columns
            return [], []
        except Exception as rpc_error:
            pass

        # Fallback: Parse simple SELECT and use table API
        select_match = re.match(
            r"SELECT\s+(.+?)\s+FROM\s+[\"']?(\w+)[\"']?(?:\s+LIMIT\s+(\d+))?",
            sql.strip(),
            re.IGNORECASE | re.DOTALL
        )

        if select_match:
            columns_str, table_name, limit = select_match.groups()

            try:
                # Handle COUNT(*)
                if "COUNT(*)" in columns_str.upper():
                    result = self.client.table(table_name).select("*", count="exact").limit(0).execute()
                    return [(result.count or 0,)], ["count"]

                # Handle SELECT columns
                if columns_str.strip() == "*":
                    select_cols = "*"
                else:
                    select_cols = columns_str.strip()

                query = self.client.table(table_name).select(select_cols)
                if limit:
                    query = query.limit(int(limit))

                result = query.execute()
                if result.data:
                    columns = list(result.data[0].keys()) if result.data else []
                    rows = [tuple(row.values()) for row in result.data]
                    return rows, columns
            except Exception:
                pass

        raise NotImplementedError(
            f"Complex SQL execution requires the 'exec_sql' RPC function in Supabase.\n"
            f"Create it in the Supabase SQL Editor:\n\n"
            f"CREATE OR REPLACE FUNCTION exec_sql(query text)\n"
            f"RETURNS json LANGUAGE plpgsql SECURITY DEFINER AS $$\n"
            f"DECLARE result json;\n"
            f"BEGIN\n"
            f"  EXECUTE 'SELECT json_agg(row_to_json(t)) FROM (' || query || ') t' INTO result;\n"
            f"  RETURN COALESCE(result, '[]'::json);\n"
            f"END;\n"
            f"$$;\n\n"
            f"Or use PostgreSQLConnector for direct database access."
        )


class MySQLConnector(BaseDatabaseConnector):
    """MySQL database connector."""

    def __init__(
        self,
        host: str,
        port: int,
        database: str,
        user: str,
        password: str,
        charset: str = "utf8mb4"
    ):
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password
        self.charset = charset
        self.connection = None

    def connect(self):
        try:
            import mysql.connector
            self.connection = mysql.connector.connect(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password,
                charset=self.charset,
                use_pure=True
            )
        except ImportError:
            try:
                import pymysql
                self.connection = pymysql.connect(
                    host=self.host,
                    port=self.port,
                    database=self.database,
                    user=self.user,
                    password=self.password,
                    charset=self.charset,
                    cursorclass=pymysql.cursors.Cursor
                )
            except ImportError:
                raise ImportError(
                    "MySQL driver not found. "
                    "Install with: pip install qasql[mysql]"
                )

    def disconnect(self):
        if self.connection:
            self.connection.close()
            self.connection = None

    def execute(self, sql: str, timeout: float = 30.0) -> tuple[list[tuple], list[str]]:
        if not self.connection:
            self.connect()

        cursor = self.connection.cursor()
        try:
            cursor.execute(f"SET SESSION max_execution_time = {int(timeout * 1000)}")
        except Exception:
            pass  # Older MySQL versions may not support this

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
            WHERE table_schema = %s AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """, (self.database,))
        return [row[0] for row in cursor.fetchall()]

    def get_table_schema(self, table_name: str) -> dict[str, Any]:
        if not self.connection:
            self.connect()

        cursor = self.connection.cursor()
        cursor.execute("""
            SELECT column_name, data_type, is_nullable, column_default, column_key
            FROM information_schema.columns
            WHERE table_name = %s AND table_schema = %s
            ORDER BY ordinal_position
        """, (table_name, self.database))

        columns = []
        primary_keys = []

        for col in cursor.fetchall():
            col_name, col_type, is_nullable, col_default, col_key = col
            column_data = {
                "name": col_name,
                "type": col_type.upper(),
                "nullable": is_nullable == "YES",
                "default": col_default,
            }

            if col_type.upper() in ("TEXT", "VARCHAR", "CHAR", "ENUM"):
                try:
                    cursor.execute(f"""
                        SELECT DISTINCT `{col_name}` FROM `{table_name}`
                        WHERE `{col_name}` IS NOT NULL LIMIT 20
                    """)
                    distinct_values = [row[0] for row in cursor.fetchall()]
                    if len(distinct_values) <= 15:
                        column_data["distinct_values"] = distinct_values
                except Exception:
                    pass

            columns.append(column_data)
            if col_key == "PRI":
                primary_keys.append(col_name)

        cursor.execute("""
            SELECT kcu.column_name, kcu.referenced_table_name, kcu.referenced_column_name
            FROM information_schema.key_column_usage kcu
            JOIN information_schema.referential_constraints rc
                ON kcu.constraint_name = rc.constraint_name
                AND kcu.constraint_schema = rc.constraint_schema
            WHERE kcu.table_name = %s AND kcu.table_schema = %s
                AND kcu.referenced_table_name IS NOT NULL
        """, (table_name, self.database))
        foreign_keys = [
            {"column": fk[0], "references_table": fk[1], "references_column": fk[2]}
            for fk in cursor.fetchall()
        ]

        cursor.execute(f"SELECT COUNT(*) FROM `{table_name}`")
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
        cursor.execute(f"SELECT * FROM `{table_name}` LIMIT {limit}")
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
                password=config.db_password,
                sslmode=config.db_sslmode,
                schema=config.db_schema
            )
        elif config.db_type == "supabase":
            return SupabaseConnector(
                url=config.supabase_url,
                key=config.supabase_key,
                schema=config.db_schema
            )
        elif config.db_type == "mysql":
            return MySQLConnector(
                host=config.db_host,
                port=config.db_port,
                database=config.db_name,
                user=config.db_user,
                password=config.db_password,
            )
        else:
            raise ValueError(f"Unsupported database type: {config.db_type}")

    @staticmethod
    def from_uri(uri: str) -> BaseDatabaseConnector:
        """Create database connector from URI."""
        config = QASQLConfig(db_uri=uri)
        return DatabaseConnector.from_config(config)
