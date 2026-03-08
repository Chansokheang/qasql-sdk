"""
SQL Candidate Generator

Generates SQL candidates using multiple context strategies.
"""

import re
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Any

from qasql.core.prompts import PROMPTS, ContextStrategy


@dataclass
class SQLCandidate:
    """A generated SQL candidate."""
    candidate_id: int
    sql: str
    strategy: ContextStrategy
    strategy_name: str


class CandidateGenerator:
    """
    Generates SQL candidates using multiple strategies.

    Strategies:
    - full_schema: Complete database schema
    - sme_metadata: Schema with domain expert hints (SKIPPED if no hint)
    - minimal_profile: Column names only
    - focused_schema: Filtered relevant tables
    - full_profile: Schema with descriptions
    """

    def __init__(self, llm_client: Any):
        self.llm_client = llm_client

    def generate_all_candidates(
        self,
        nl_query: str,
        schema: dict[str, Any],
        focused_schema: dict[str, Any],
        profile: dict[str, Any],
        hint: str = "",
        parallel: bool = True
    ) -> list[SQLCandidate]:
        """
        Generate SQL candidates using all applicable strategies.

        If hint is not provided, SME strategy is skipped (4 candidates).
        If hint is provided, all 5 strategies are used.

        Args:
            nl_query: Natural language query
            schema: Full database schema
            focused_schema: Filtered schema from schema agent
            profile: Column descriptions
            hint: Optional SME hint
            parallel: Whether to generate in parallel

        Returns:
            List of SQL candidates
        """
        # Determine which strategies to use
        if hint:
            strategies = [
                ContextStrategy.FULL_SCHEMA,
                ContextStrategy.SME_METADATA,
                ContextStrategy.MINIMAL_PROFILE,
                ContextStrategy.FOCUSED_SCHEMA,
                ContextStrategy.FULL_PROFILE,
            ]
        else:
            # Skip SME when no hint
            strategies = [
                ContextStrategy.FULL_SCHEMA,
                ContextStrategy.MINIMAL_PROFILE,
                ContextStrategy.FOCUSED_SCHEMA,
                ContextStrategy.FULL_PROFILE,
            ]

        if parallel:
            return self._generate_parallel(
                strategies, nl_query, schema, focused_schema, profile, hint
            )
        else:
            return self._generate_sequential(
                strategies, nl_query, schema, focused_schema, profile, hint
            )

    def _generate_parallel(
        self,
        strategies: list[ContextStrategy],
        nl_query: str,
        schema: dict,
        focused_schema: dict,
        profile: dict,
        hint: str
    ) -> list[SQLCandidate]:
        """Generate candidates in parallel."""
        candidates = []

        def generate_one(args):
            idx, strategy = args
            return self._generate_candidate(
                idx + 1, strategy, nl_query, schema, focused_schema, profile, hint
            )

        with ThreadPoolExecutor(max_workers=len(strategies)) as executor:
            candidates = list(executor.map(generate_one, enumerate(strategies)))

        return candidates

    def _generate_sequential(
        self,
        strategies: list[ContextStrategy],
        nl_query: str,
        schema: dict,
        focused_schema: dict,
        profile: dict,
        hint: str
    ) -> list[SQLCandidate]:
        """Generate candidates sequentially."""
        candidates = []
        for idx, strategy in enumerate(strategies):
            candidate = self._generate_candidate(
                idx + 1, strategy, nl_query, schema, focused_schema, profile, hint
            )
            candidates.append(candidate)
        return candidates

    def _generate_candidate(
        self,
        candidate_id: int,
        strategy: ContextStrategy,
        nl_query: str,
        schema: dict,
        focused_schema: dict,
        profile: dict,
        hint: str
    ) -> SQLCandidate:
        """Generate a single SQL candidate."""
        prompt_config = PROMPTS[strategy]

        # Build schema string based on strategy
        if strategy == ContextStrategy.FOCUSED_SCHEMA:
            schema_str = self._format_schema(focused_schema.get("tables", schema))
        elif strategy == ContextStrategy.MINIMAL_PROFILE:
            schema_str = self._format_minimal(schema)
        elif strategy == ContextStrategy.FULL_PROFILE:
            schema_str = self._format_with_profile(schema, profile)
        else:
            schema_str = self._format_schema(schema)

        # Build user prompt
        user_prompt = prompt_config["user_template"].format(
            schema=schema_str,
            question=nl_query,
            hint=hint
        )

        try:
            response = self.llm_client.complete(
                prompt=user_prompt,
                system_prompt=prompt_config["system"],
                max_tokens=2048,
                temperature=0.0
            )
            sql = self._extract_sql(response)
        except Exception as e:
            sql = ""

        return SQLCandidate(
            candidate_id=candidate_id,
            sql=sql,
            strategy=strategy,
            strategy_name=prompt_config["name"]
        )

    def _format_schema(self, schema: dict) -> str:
        """Format schema for prompt."""
        lines = []
        for table_name, table_info in schema.items():
            columns = []
            for col in table_info.get("columns", []):
                col_str = f"{col['name']} ({col.get('type', 'TEXT')})"
                columns.append(col_str)

            pk = table_info.get("primary_keys", [])
            fk = table_info.get("foreign_keys", [])

            lines.append(f"Table: {table_name}")
            lines.append(f"  Columns: {', '.join(columns)}")
            if pk:
                lines.append(f"  Primary Key: {', '.join(pk)}")
            if fk:
                fk_strs = [f"{f['column']} -> {f['references_table']}.{f['references_column']}" for f in fk]
                lines.append(f"  Foreign Keys: {', '.join(fk_strs)}")
            lines.append("")

        return "\n".join(lines)

    def _format_minimal(self, schema: dict) -> str:
        """Format minimal schema (columns only)."""
        lines = []
        for table_name, table_info in schema.items():
            columns = [col["name"] for col in table_info.get("columns", [])]
            lines.append(f"{table_name}: {', '.join(columns)}")
        return "\n".join(lines)

    def _format_with_profile(self, schema: dict, profile: dict) -> str:
        """Format schema with descriptions."""
        lines = []
        profile_tables = profile.get("tables", {})

        for table_name, table_info in schema.items():
            table_profile = profile_tables.get(table_name, {})
            profile_cols = {c["name"]: c for c in table_profile.get("columns", [])}

            lines.append(f"Table: {table_name}")

            for col in table_info.get("columns", []):
                col_name = col["name"]
                col_type = col.get("type", "TEXT")
                desc = profile_cols.get(col_name, {}).get("description", "")

                if desc:
                    lines.append(f"  {col_name} ({col_type}): {desc}")
                else:
                    lines.append(f"  {col_name} ({col_type})")

            lines.append("")

        return "\n".join(lines)

    def _extract_sql(self, response: str) -> str:
        """Extract SQL from LLM response."""
        # Try code blocks
        sql_match = re.search(r'```(?:sql)?\s*([\s\S]*?)\s*```', response, re.IGNORECASE)
        if sql_match:
            return sql_match.group(1).strip()

        # Try SELECT statement
        select_match = re.search(r'(SELECT[\s\S]+?)(?:;|$)', response, re.IGNORECASE)
        if select_match:
            return select_match.group(1).strip()

        return response.strip()
