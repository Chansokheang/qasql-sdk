"""
Configuration Module

Handles configuration for QA-SQL engine.
"""

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Literal


@dataclass
class QASQLConfig:
    """
    Configuration for QA-SQL Engine.

    Attributes:
        db_type: Database type ("sqlite", "postgresql", or "supabase")
        db_uri: Database connection URI or file path
        db_host: PostgreSQL host
        db_port: PostgreSQL port
        db_name: Database name (for PostgreSQL)
        db_user: Database username
        db_password: Database password
        db_sslmode: SSL mode for PostgreSQL (disable, allow, prefer, require, verify-ca, verify-full)
        db_schema: PostgreSQL schema name (default: "public")
        supabase_url: Supabase project URL (e.g., https://xxx.supabase.co)
        supabase_key: Supabase API key (anon or service_role)
        llm_provider: LLM provider ("ollama", "anthropic", "openai")
        llm_model: Model name
        llm_base_url: Base URL for Ollama server
        readable_names_path: Path to readable names mapping file
        output_dir: Directory for generated schema/descriptions
        relevance_threshold: Threshold for table relevance (0.0-1.0)
        query_timeout: SQL query timeout in seconds
        max_workers: Max parallel workers for schema agent
    """

    # Database settings
    db_type: Literal["sqlite", "postgresql", "supabase", "mysql"] = "sqlite"
    db_uri: str = ""
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = ""
    db_user: str = ""
    db_password: str = ""
    db_sslmode: str = "prefer"  # disable, allow, prefer, require, verify-ca, verify-full
    db_schema: str = "public"  # PostgreSQL schema

    # Supabase settings
    supabase_url: str = ""  # e.g., https://xxx.supabase.co
    supabase_key: str = ""  # anon key or service_role key

    # LLM settings (local by default)
    llm_provider: Literal["ollama", "anthropic", "openai"] = "ollama"
    llm_model: str = "llama3.2"
    llm_base_url: str = "http://localhost:11434"
    llm_max_tokens: int = 2048
    llm_temperature: float = 0.0

    # Optional metadata
    readable_names_path: Optional[str] = None

    # Output settings
    output_dir: Path = field(default_factory=lambda: Path("./qasql_output"))

    # Pipeline settings
    relevance_threshold: float = 0.5
    query_timeout: float = 30.0
    max_workers: int = 4
    max_refinement_attempts: int = 3

    def __post_init__(self):
        """Validate and process configuration after initialization."""
        self.output_dir = Path(self.output_dir)
        if self.db_uri:
            self._parse_db_uri()

    def _parse_db_uri(self):
        """Parse database URI into components."""
        uri = self.db_uri

        if uri.startswith("sqlite:///"):
            self.db_type = "sqlite"
            self.db_uri = uri.replace("sqlite:///", "")
        elif uri.endswith(".sqlite") or uri.endswith(".db"):
            self.db_type = "sqlite"
        elif uri.startswith("postgresql://") or uri.startswith("postgres://"):
            self.db_type = "postgresql"
            self._parse_postgres_uri(uri)
        elif uri.startswith("mysql://"):
            self.db_type = "mysql"
            self._parse_mysql_uri(uri)

    def _parse_postgres_uri(self, uri: str):
        """Parse PostgreSQL connection URI."""
        uri = uri.replace("postgresql://", "").replace("postgres://", "")

        if "@" in uri:
            auth, rest = uri.split("@", 1)
            if ":" in auth:
                self.db_user, self.db_password = auth.split(":", 1)
            else:
                self.db_user = auth
        else:
            rest = uri

        if "/" in rest:
            host_port, self.db_name = rest.split("/", 1)
        else:
            host_port = rest

        if ":" in host_port:
            self.db_host, port_str = host_port.split(":", 1)
            self.db_port = int(port_str)
        else:
            self.db_host = host_port

    def _parse_mysql_uri(self, uri: str):
        """Parse MySQL connection URI (mysql://user:pass@host:3306/dbname)."""
        uri = uri.replace("mysql://", "")

        if "@" in uri:
            auth, rest = uri.split("@", 1)
            if ":" in auth:
                self.db_user, self.db_password = auth.split(":", 1)
            else:
                self.db_user = auth
        else:
            rest = uri

        if "/" in rest:
            host_port, self.db_name = rest.split("/", 1)
        else:
            host_port = rest

        if ":" in host_port:
            self.db_host, port_str = host_port.split(":", 1)
            self.db_port = int(port_str)
        else:
            self.db_host = host_port
            self.db_port = 3306

    def get_db_path(self) -> Path:
        """Get SQLite database file path."""
        if self.db_type != "sqlite":
            raise ValueError("get_db_path() only valid for SQLite databases")
        return Path(self.db_uri)

    def get_postgres_params(self) -> dict:
        """Get PostgreSQL connection parameters."""
        if self.db_type != "postgresql":
            raise ValueError("get_postgres_params() only valid for PostgreSQL")
        return {
            "host": self.db_host,
            "port": self.db_port,
            "database": self.db_name,
            "user": self.db_user,
            "password": self.db_password,
            "sslmode": self.db_sslmode,
            "schema": self.db_schema,
        }

    def get_mysql_params(self) -> dict:
        """Get MySQL connection parameters."""
        if self.db_type != "mysql":
            raise ValueError("get_mysql_params() only valid for MySQL")
        return {
            "host": self.db_host,
            "port": self.db_port,
            "database": self.db_name,
            "user": self.db_user,
            "password": self.db_password,
        }

    def get_supabase_params(self) -> dict:
        """Get Supabase connection parameters."""
        if self.db_type != "supabase":
            raise ValueError("get_supabase_params() only valid for Supabase")
        return {
            "url": self.supabase_url,
            "key": self.supabase_key,
            "schema": self.db_schema,
        }

    def get_database_name(self) -> str:
        """Extract database name from configuration."""
        if self.db_type == "sqlite":
            return Path(self.db_uri).stem
        elif self.db_type == "mysql":
            return self.db_name
        elif self.db_type == "supabase":
            # Extract project name from Supabase URL
            if self.supabase_url:
                import re
                match = re.search(r"https://([^.]+)", self.supabase_url)
                if match:
                    return match.group(1)
            return "supabase"
        return self.db_name

    @classmethod
    def from_json(cls, path: str) -> "QASQLConfig":
        """Load configuration from JSON file."""
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        config_dict = {}

        if "database" in data:
            db = data["database"]
            for key in ["uri", "type", "host", "port", "name", "user", "password", "sslmode", "schema"]:
                if key in db:
                    config_dict[f"db_{key}"] = db[key]

        if "supabase" in data:
            sb = data["supabase"]
            if "url" in sb:
                config_dict["supabase_url"] = sb["url"]
            if "key" in sb:
                config_dict["supabase_key"] = sb["key"]
            if "schema" in sb:
                config_dict["db_schema"] = sb["schema"]
            # Auto-set type to supabase
            if "supabase_url" in config_dict:
                config_dict["db_type"] = "supabase"

        if "llm" in data:
            llm = data["llm"]
            if "provider" in llm:
                config_dict["llm_provider"] = llm["provider"]
            if "model" in llm:
                config_dict["llm_model"] = llm["model"]
            if "base_url" in llm:
                config_dict["llm_base_url"] = llm["base_url"]

        if "options" in data:
            opts = data["options"]
            if "readable_names" in opts:
                config_dict["readable_names_path"] = opts["readable_names"]
            if "relevance_threshold" in opts:
                config_dict["relevance_threshold"] = opts["relevance_threshold"]
            if "query_timeout" in opts:
                config_dict["query_timeout"] = opts["query_timeout"]
            if "output_dir" in opts:
                config_dict["output_dir"] = opts["output_dir"]

        return cls(**config_dict)

    def to_json(self, path: str):
        """Save configuration to JSON file."""
        data = {
            "database": {
                "type": self.db_type,
                "uri": self.db_uri,
                "host": self.db_host,
                "port": self.db_port,
                "name": self.db_name,
                "user": self.db_user,
            },
            "llm": {
                "provider": self.llm_provider,
                "model": self.llm_model,
                "base_url": self.llm_base_url
            },
            "options": {
                "readable_names": self.readable_names_path,
                "relevance_threshold": self.relevance_threshold,
                "query_timeout": self.query_timeout,
                "output_dir": str(self.output_dir)
            }
        }

        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    @classmethod
    def from_env(cls) -> "QASQLConfig":
        """Load configuration from environment variables."""
        config_dict = {}

        env_mapping = {
            "QASQL_DB_URI": "db_uri",
            "QASQL_DB_TYPE": "db_type",
            "QASQL_DB_HOST": "db_host",
            "QASQL_DB_NAME": "db_name",
            "QASQL_DB_USER": "db_user",
            "QASQL_DB_PASSWORD": "db_password",
            "QASQL_DB_SSLMODE": "db_sslmode",
            "QASQL_DB_SCHEMA": "db_schema",
            "SUPABASE_URL": "supabase_url",
            "SUPABASE_KEY": "supabase_key",
            "QASQL_LLM_PROVIDER": "llm_provider",
            "QASQL_LLM_MODEL": "llm_model",
            "QASQL_OLLAMA_URL": "llm_base_url",
        }

        for env_var, config_key in env_mapping.items():
            if os.environ.get(env_var):
                config_dict[config_key] = os.environ[env_var]

        if os.environ.get("QASQL_DB_PORT"):
            config_dict["db_port"] = int(os.environ["QASQL_DB_PORT"])

        # Auto-detect Supabase if URL is set
        if os.environ.get("SUPABASE_URL") and not os.environ.get("QASQL_DB_TYPE"):
            config_dict["db_type"] = "supabase"

        return cls(**config_dict)
