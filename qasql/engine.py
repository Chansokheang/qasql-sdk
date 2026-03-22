"""
QA-SQL Engine

Main entry point for the QA-SQL SDK.
"""

import json
import time
import decimal
import datetime
from pathlib import Path
from typing import Literal, Optional


class _JSONEncoder(json.JSONEncoder):
    """JSON encoder that handles datetime, date, time, and Decimal types."""
    def default(self, obj):
        if isinstance(obj, (datetime.datetime, datetime.date, datetime.time)):
            return obj.isoformat()
        if isinstance(obj, decimal.Decimal):
            return float(obj)
        if isinstance(obj, bytes):
            return obj.decode("utf-8", errors="replace")
        return super().default(obj)

from qasql.config import QASQLConfig
from qasql.database import DatabaseConnector, BaseDatabaseConnector
from qasql.result import QueryResult, SetupResult, CandidateSQL
from qasql.llm import create_llm_client, BaseLLMClient
from qasql.core import SchemaAgent, CandidateGenerator, SQLExecutor, SQLJudge


class QASQLEngine:
    """
    QA-SQL Engine for local text-to-SQL generation.

    All processing happens locally when using Ollama provider.
    Sensitive schemas never leave your network.

    Usage:
        engine = QASQLEngine(
            db_uri="sqlite:///path/to/database.sqlite",
            llm_provider="ollama",
            llm_model="llama3.2"
        )
        engine.setup()

        result = engine.query("Show total sales by customer")
        print(result.sql)
    """

    def __init__(
        self,
        db_uri: str = None,
        db_type: Literal["sqlite", "postgresql", "supabase", "mysql"] = None,
        db_host: str = "localhost",
        db_port: int = 5432,
        db_name: str = None,
        db_user: str = None,
        db_password: str = None,
        db_sslmode: str = "prefer",
        db_schema: str = "public",
        supabase_url: str = None,
        supabase_key: str = None,
        llm_provider: Literal["ollama", "anthropic", "openai"] = "ollama",
        llm_model: str = None,
        llm_base_url: str = "http://localhost:11434",
        readable_names: str = None,
        output_dir: str = "./qasql_output",
        config: QASQLConfig = None,
        config_file: str = None,
    ):
        """
        Initialize the QA-SQL Engine.

        Args:
            db_uri: Database connection URI
            db_type: Database type ("sqlite", "postgresql", or "supabase")
            db_host: PostgreSQL host
            db_port: PostgreSQL port
            db_name: Database name
            db_user: Database username
            db_password: Database password
            db_sslmode: SSL mode for PostgreSQL (disable, allow, prefer, require)
            db_schema: PostgreSQL/Supabase schema (default: "public")
            supabase_url: Supabase project URL (e.g., https://xxx.supabase.co)
            supabase_key: Supabase API key (anon or service_role)
            llm_provider: LLM provider ("ollama", "anthropic", "openai")
            llm_model: LLM model name
            llm_base_url: Ollama server URL
            readable_names: Path to readable names file
            output_dir: Directory for generated files
            config: Pre-built QASQLConfig
            config_file: Path to JSON config file
        """
        if config_file:
            self.config = QASQLConfig.from_json(config_file)
        elif config:
            self.config = config
        else:
            # Auto-detect Supabase if URL is provided
            effective_db_type = db_type
            if supabase_url and not db_type:
                effective_db_type = "supabase"

            self.config = QASQLConfig(
                db_uri=db_uri or "",
                db_type=effective_db_type or "sqlite",
                db_host=db_host,
                db_port=db_port,
                db_name=db_name or "",
                db_user=db_user or "",
                db_password=db_password or "",
                db_sslmode=db_sslmode,
                db_schema=db_schema,
                supabase_url=supabase_url or "",
                supabase_key=supabase_key or "",
                llm_provider=llm_provider,
                llm_model=llm_model or ("llama3.2" if llm_provider == "ollama" else "claude-sonnet-4-5-20250929"),
                llm_base_url=llm_base_url,
                readable_names_path=readable_names,
                output_dir=Path(output_dir),
            )

        self._llm_client: Optional[BaseLLMClient] = None
        self._db_connector: Optional[BaseDatabaseConnector] = None
        self._schema: Optional[dict] = None
        self._profile: Optional[dict] = None
        self._database_name: Optional[str] = None
        self._initialized = False

    def _create_llm_client(self) -> BaseLLMClient:
        """Create LLM client based on configuration."""
        return create_llm_client(
            provider=self.config.llm_provider,
            model=self.config.llm_model,
            base_url=self.config.llm_base_url
        )

    def _create_db_connector(self) -> BaseDatabaseConnector:
        """Create database connector based on configuration."""
        return DatabaseConnector.from_config(self.config)

    def setup(self, force: bool = False) -> SetupResult:
        """
        Run one-time setup: extract schema and generate descriptions.

        Args:
            force: If True, regenerate even if files exist

        Returns:
            SetupResult with status and file paths
        """
        self._database_name = self.config.get_database_name()
        output_dir = Path(self.config.output_dir)

        schema_dir = output_dir / "schemas"
        descriptions_dir = output_dir / "descriptions"

        schema_path = schema_dir / f"{self._database_name}_schema.json"
        descriptions_path = descriptions_dir / f"{self._database_name}_descriptions.json"

        # Check existing setup
        if not force and schema_path.exists() and descriptions_path.exists():
            with open(schema_path, "r", encoding="utf-8") as f:
                self._schema = json.load(f).get("tables", {})
            with open(descriptions_path, "r", encoding="utf-8") as f:
                self._profile = json.load(f)

            self._initialized = True

            return SetupResult(
                success=True,
                database_name=self._database_name,
                tables_found=len(self._schema),
                schema_path=str(schema_path),
                descriptions_path=str(descriptions_path),
                errors=["Using existing setup (use force=True to regenerate)"]
            )

        # Create directories
        schema_dir.mkdir(parents=True, exist_ok=True)
        descriptions_dir.mkdir(parents=True, exist_ok=True)

        errors = []

        # Load readable names if provided
        readable_names = {}
        if self.config.readable_names_path:
            try:
                readable_names = self._load_readable_names(self.config.readable_names_path)
            except Exception as e:
                errors.append(f"Failed to load readable names: {e}")

        # Extract schema
        try:
            connector = self._create_db_connector()
            connector.connect()
            schema_data = connector.extract_full_schema()
            connector.disconnect()

            # Apply readable names
            for table_name, table_info in schema_data.get("tables", {}).items():
                if table_name in readable_names:
                    mapping = readable_names[table_name]
                    table_info["table_readable_name"] = mapping.get("table_readable_name", table_name)
                    col_mapping = mapping.get("columns", {})
                    for col in table_info.get("columns", []):
                        if col["name"] in col_mapping:
                            col["readable_name"] = col_mapping[col["name"]]

            self._schema = schema_data.get("tables", {})

        except Exception as e:
            return SetupResult(
                success=False,
                database_name=self._database_name,
                errors=[f"Schema extraction failed: {e}"]
            )

        # Save schema
        schema_data["database"] = self._database_name
        with open(schema_path, "w", encoding="utf-8") as f:
            json.dump(schema_data, f, indent=2, ensure_ascii=False, cls=_JSONEncoder)

        # Generate descriptions
        try:
            self._llm_client = self._create_llm_client()
            self._profile = self._generate_descriptions(self._schema)
        except Exception as e:
            errors.append(f"Description generation failed: {e}")
            # Create basic profile without LLM
            self._profile = self._create_basic_profile(self._schema)

        # Save descriptions
        self._profile["database"] = self._database_name
        with open(descriptions_path, "w", encoding="utf-8") as f:
            json.dump(self._profile, f, indent=2, ensure_ascii=False, cls=_JSONEncoder)

        self._initialized = True

        return SetupResult(
            success=True,
            database_name=self._database_name,
            tables_found=len(self._schema),
            schema_path=str(schema_path),
            descriptions_path=str(descriptions_path),
            errors=errors
        )

    def _load_readable_names(self, path: str) -> dict:
        """Load readable names from JSON or CSV."""
        path = Path(path)
        if path.suffix == ".json":
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        elif path.suffix == ".csv":
            import csv
            result = {}
            with open(path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    table = row.get("table", "")
                    if table not in result:
                        result[table] = {"columns": {}}
                    if row.get("column"):
                        result[table]["columns"][row["column"]] = row.get("readable_name", "")
                    elif row.get("readable_name"):
                        result[table]["table_readable_name"] = row["readable_name"]
            return result
        return {}

    def _generate_descriptions(self, schema: dict) -> dict:
        """Generate column descriptions using LLM."""
        profile = {"tables": {}}

        for table_name, table_info in schema.items():
            table_profile = {
                "table_readable_name": table_info.get("table_readable_name", table_name),
                "columns": []
            }

            for col in table_info.get("columns", []):
                col_name = col.get("name", "")
                col_type = col.get("type", "TEXT")
                readable = col.get("readable_name", col_name)

                # Generate description
                desc = self._generate_column_desc(table_name, col_name, col_type, readable)

                col_profile = {
                    "name": col_name,
                    "readable_name": readable,
                    "type": col_type,
                    "description": desc
                }

                if col.get("distinct_values"):
                    col_profile["distinct_values"] = col["distinct_values"]

                table_profile["columns"].append(col_profile)

            profile["tables"][table_name] = table_profile

        return profile

    def _generate_column_desc(self, table: str, col: str, col_type: str, readable: str) -> str:
        """Generate description for a single column."""
        prompt = f"""Write a brief (10-20 words) description for this database column:
Table: {table}
Column: {col}
Type: {col_type}
{"Readable name: " + readable if readable != col else ""}

Write ONLY the description."""

        try:
            return self.llm_client.complete(prompt=prompt, max_tokens=100).strip()
        except:
            return readable if readable != col else f"The {col} field"

    def _create_basic_profile(self, schema: dict) -> dict:
        """Create basic profile without LLM."""
        profile = {"tables": {}}
        for table_name, table_info in schema.items():
            table_profile = {
                "table_readable_name": table_info.get("table_readable_name", table_name),
                "columns": []
            }
            for col in table_info.get("columns", []):
                col_profile = {
                    "name": col.get("name", ""),
                    "readable_name": col.get("readable_name", col.get("name", "")),
                    "type": col.get("type", "TEXT"),
                    "description": col.get("readable_name", col.get("name", ""))
                }
                if col.get("distinct_values"):
                    col_profile["distinct_values"] = col["distinct_values"]
                table_profile["columns"].append(col_profile)
            profile["tables"][table_name] = table_profile
        return profile

    def _ensure_initialized(self):
        """Ensure engine is initialized."""
        if not self._initialized:
            raise RuntimeError(
                "Engine not initialized. Call setup() first.\n"
                "Example:\n"
                "  engine = QASQLEngine(db_uri='...')\n"
                "  engine.setup()\n"
                "  result = engine.query('...')"
            )

    @property
    def llm_client(self) -> BaseLLMClient:
        """Get or create LLM client."""
        if self._llm_client is None:
            self._llm_client = self._create_llm_client()
        return self._llm_client

    @property
    def db_connector(self) -> BaseDatabaseConnector:
        """Get or create database connector."""
        if self._db_connector is None:
            self._db_connector = self._create_db_connector()
        return self._db_connector

    def query(self, question: str, hint: str = None) -> QueryResult:
        """
        Generate SQL from natural language question.

        Args:
            question: Natural language question
            hint: Optional SME hint (e.g., "sales = sum(order_amount)")

        Returns:
            QueryResult with generated SQL and metadata

        Note:
            If hint is not provided, SME strategy is skipped (4 candidates).
            If hint is provided, all 5 strategies are used.
        """
        self._ensure_initialized()

        start_time = time.perf_counter()
        metadata = {"timings": {}}

        # Stage 1: Schema Agent
        t0 = time.perf_counter()
        schema_agent = SchemaAgent(self.llm_client, self.config.max_workers)
        focused_schema = schema_agent.run(
            nl_query=question,
            schema=self._schema,
            profile=self._profile,
            hint=hint or "",
            relevance_threshold=self.config.relevance_threshold
        )
        metadata["timings"]["schema_agent_ms"] = (time.perf_counter() - t0) * 1000

        # Stage 2: Generate Candidates
        t0 = time.perf_counter()
        generator = CandidateGenerator(self.llm_client)
        candidates = generator.generate_all_candidates(
            nl_query=question,
            schema=self._schema,
            focused_schema=focused_schema,
            profile=self._profile,
            hint=hint or "",
            parallel=True
        )
        metadata["timings"]["generation_ms"] = (time.perf_counter() - t0) * 1000

        # Stage 3: Execute Candidates
        t0 = time.perf_counter()
        executor = SQLExecutor(
            db_connector=self.db_connector,
            llm_client=self.llm_client,
            max_iterations=self.config.max_refinement_attempts,
            query_timeout=self.config.query_timeout
        )

        schema_str = self._format_schema_str()
        execution_results = executor.execute_all_candidates(
            candidates=candidates,
            nl_query=question,
            schema_str=schema_str
        )
        metadata["timings"]["execution_ms"] = (time.perf_counter() - t0) * 1000

        # Stage 3b: Last Resort
        successful = executor.filter_successful(execution_results)
        if not successful:
            t0 = time.perf_counter()
            last_resort = executor.last_resort(
                results=execution_results,
                nl_query=question,
                schema_str=schema_str,
                hint=hint or ""
            )
            if last_resort and last_resort.success:
                execution_results.append(last_resort)
                from qasql.core.generator import SQLCandidate
                from qasql.core.prompts import ContextStrategy
                candidates.append(SQLCandidate(
                    candidate_id=0,
                    sql=last_resort.sql,
                    strategy=ContextStrategy.FULL_SCHEMA,
                    strategy_name="last_resort"
                ))
                metadata["last_resort_used"] = True
            metadata["timings"]["last_resort_ms"] = (time.perf_counter() - t0) * 1000

        # Stage 4: Judge
        t0 = time.perf_counter()
        judge = SQLJudge(self.llm_client)
        judgment = judge.judge(
            candidates=candidates,
            execution_results=execution_results,
            nl_query=question,
            hint=hint or ""
        )
        metadata["timings"]["judge_ms"] = (time.perf_counter() - t0) * 1000
        metadata["timings"]["total_ms"] = (time.perf_counter() - start_time) * 1000

        # Build result
        exec_map = {r.candidate_id: r for r in execution_results}
        result_candidates = []
        for c in candidates:
            exec_r = exec_map.get(c.candidate_id)
            result_candidates.append(CandidateSQL(
                candidate_id=c.candidate_id,
                sql=exec_r.sql if exec_r else c.sql,
                strategy=c.strategy_name,
                success=exec_r.success if exec_r else False,
                error=exec_r.error if exec_r and not exec_r.success else None
            ))

        return QueryResult(
            sql=judgment.selected_sql,
            confidence=judgment.confidence,
            question=question,
            hint=hint,
            reasoning=judgment.reasoning,
            candidates=result_candidates,
            successful_candidates=judgment.successful_candidates,
            total_candidates=judgment.total_candidates,
            metadata=metadata
        )

    def _format_schema_str(self) -> str:
        """Format schema as string for prompts."""
        lines = []
        for table_name, table_info in self._schema.items():
            cols = [f"{c['name']} ({c.get('type', 'TEXT')})" for c in table_info.get("columns", [])]
            lines.append(f"Table {table_name}: {', '.join(cols)}")
        return "\n".join(lines)

    def execute_sql(self, sql: str) -> tuple[list[tuple], list[str]]:
        """Execute SQL query directly."""
        self._ensure_initialized()
        connector = self._create_db_connector()
        connector.connect()
        try:
            return connector.execute(sql, timeout=self.config.query_timeout)
        finally:
            connector.disconnect()

    def get_schema(self) -> dict:
        """Get extracted database schema."""
        self._ensure_initialized()
        return self._schema

    def get_profile(self) -> dict:
        """Get generated column descriptions."""
        self._ensure_initialized()
        return self._profile

    def get_tables(self) -> list[str]:
        """Get list of table names."""
        self._ensure_initialized()
        return list(self._schema.keys())
