"""
SQL Executor

Executes SQL candidates with retry and refinement logic.
"""

import re
from dataclasses import dataclass
from typing import Any, Optional

from qasql.core.prompts import REFINEMENT_PROMPT, LAST_RESORT_PROMPT
from qasql.core.generator import SQLCandidate


@dataclass
class ExecutionResult:
    """Result of SQL execution."""
    candidate_id: int
    sql: str
    success: bool
    error: Optional[str] = None
    rows: list[tuple] = None
    columns: list[str] = None
    iterations: int = 1


class SQLExecutor:
    """
    Executes SQL candidates with retry loop.

    Features:
    - Retry up to max_iterations on failure
    - LLM-based SQL refinement on errors
    - Last resort generation if all candidates fail
    """

    def __init__(
        self,
        db_connector: Any,
        llm_client: Any,
        max_iterations: int = 3,
        query_timeout: float = 30.0
    ):
        self.db_connector = db_connector
        self.llm_client = llm_client
        self.max_iterations = max_iterations
        self.query_timeout = query_timeout

    def execute_all_candidates(
        self,
        candidates: list[SQLCandidate],
        nl_query: str,
        schema_str: str
    ) -> list[ExecutionResult]:
        """
        Execute all candidates with retry loops.

        Args:
            candidates: SQL candidates to execute
            nl_query: Original natural language query
            schema_str: Schema string for refinement

        Returns:
            List of execution results
        """
        results = []

        for candidate in candidates:
            result = self._execute_with_retry(
                candidate, nl_query, schema_str
            )
            results.append(result)

        return results

    def _execute_with_retry(
        self,
        candidate: SQLCandidate,
        nl_query: str,
        schema_str: str
    ) -> ExecutionResult:
        """Execute a single candidate with retry loop."""
        sql = candidate.sql
        last_error = None

        for iteration in range(1, self.max_iterations + 1):
            if not sql:
                return ExecutionResult(
                    candidate_id=candidate.candidate_id,
                    sql="",
                    success=False,
                    error="Empty SQL",
                    iterations=iteration
                )

            try:
                self.db_connector.connect()
                rows, columns = self.db_connector.execute(sql, timeout=self.query_timeout)

                return ExecutionResult(
                    candidate_id=candidate.candidate_id,
                    sql=sql,
                    success=True,
                    rows=rows,
                    columns=columns,
                    iterations=iteration
                )

            except Exception as e:
                last_error = str(e)

                # Try refinement if not last iteration
                if iteration < self.max_iterations:
                    refined_sql = self._refine_sql(sql, last_error, schema_str, nl_query)
                    if refined_sql and refined_sql != sql:
                        sql = refined_sql
                    else:
                        break  # No improvement possible

            finally:
                self.db_connector.disconnect()

        return ExecutionResult(
            candidate_id=candidate.candidate_id,
            sql=sql,
            success=False,
            error=last_error,
            iterations=self.max_iterations
        )

    def _refine_sql(
        self,
        sql: str,
        error: str,
        schema_str: str,
        nl_query: str
    ) -> str:
        """Use LLM to refine SQL based on error."""
        prompt = REFINEMENT_PROMPT["user_template"].format(
            sql=sql,
            error=error,
            schema=schema_str,
            question=nl_query
        )

        try:
            response = self.llm_client.complete(
                prompt=prompt,
                system_prompt=REFINEMENT_PROMPT["system"],
                max_tokens=1024
            )
            return self._extract_sql(response)
        except:
            return sql

    def last_resort(
        self,
        results: list[ExecutionResult],
        nl_query: str,
        schema_str: str,
        hint: str = ""
    ) -> Optional[ExecutionResult]:
        """
        Generate last resort SQL when all candidates fail.

        Args:
            results: Failed execution results
            nl_query: Original query
            schema_str: Schema string
            hint: Optional SME hint

        Returns:
            ExecutionResult if successful, None otherwise
        """
        # Collect errors
        errors = []
        for r in results:
            if not r.success and r.error:
                errors.append(f"- {r.error}")

        hint_section = f"Hint: {hint}" if hint else ""
        errors_str = "\n".join(errors[:5])  # Limit to 5 errors

        prompt = LAST_RESORT_PROMPT["user_template"].format(
            schema=schema_str,
            question=nl_query,
            hint_section=hint_section,
            errors=errors_str
        )

        try:
            response = self.llm_client.complete(
                prompt=prompt,
                system_prompt=LAST_RESORT_PROMPT["system"],
                max_tokens=2048
            )
            sql = self._extract_sql(response)

            if not sql:
                return None

            # Try to execute
            self.db_connector.connect()
            rows, columns = self.db_connector.execute(sql, timeout=self.query_timeout)
            self.db_connector.disconnect()

            return ExecutionResult(
                candidate_id=0,
                sql=sql,
                success=True,
                rows=rows,
                columns=columns,
                iterations=1
            )

        except Exception as e:
            return ExecutionResult(
                candidate_id=0,
                sql=sql if 'sql' in dir() else "",
                success=False,
                error=str(e),
                iterations=1
            )

    def filter_successful(self, results: list[ExecutionResult]) -> list[ExecutionResult]:
        """Filter to only successful results."""
        return [r for r in results if r.success]

    def _extract_sql(self, response: str) -> str:
        """Extract SQL from LLM response."""
        sql_match = re.search(r'```(?:sql)?\s*([\s\S]*?)\s*```', response, re.IGNORECASE)
        if sql_match:
            return sql_match.group(1).strip()

        select_match = re.search(r'(SELECT[\s\S]+?)(?:;|$)', response, re.IGNORECASE)
        if select_match:
            return select_match.group(1).strip()

        return response.strip()
