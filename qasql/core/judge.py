"""
SQL Judge

Selects the best SQL candidate using LLM-as-a-Judge.
"""

import json
import re
from dataclasses import dataclass
from typing import Any

from qasql.core.prompts import JUDGE_PROMPT
from qasql.core.generator import SQLCandidate
from qasql.core.executor import ExecutionResult


@dataclass
class JudgmentResult:
    """Result of judge selection."""
    selected_id: int
    selected_sql: str
    confidence: float
    reasoning: str
    total_candidates: int
    successful_candidates: int


class SQLJudge:
    """
    LLM-as-a-Judge for selecting best SQL candidate.

    Evaluates candidates based on:
    - Execution success
    - Correctness to query intent
    - SQL quality
    """

    def __init__(self, llm_client: Any):
        self.llm_client = llm_client

    def judge(
        self,
        candidates: list[SQLCandidate],
        execution_results: list[ExecutionResult],
        nl_query: str,
        hint: str = ""
    ) -> JudgmentResult:
        """
        Select the best SQL candidate.

        Args:
            candidates: All generated candidates
            execution_results: Execution results for each candidate
            nl_query: Original natural language query
            hint: Optional SME hint

        Returns:
            JudgmentResult with selected candidate
        """
        # Map execution results by candidate ID
        exec_map = {r.candidate_id: r for r in execution_results}

        # Filter to successful candidates
        successful = []
        for c in candidates:
            exec_result = exec_map.get(c.candidate_id)
            if exec_result and exec_result.success:
                successful.append((c, exec_result))

        total_candidates = len(candidates)
        successful_count = len(successful)

        # If no successful candidates, return empty result
        if not successful:
            # Try to return the last attempted SQL
            if execution_results:
                last_result = execution_results[-1]
                return JudgmentResult(
                    selected_id=last_result.candidate_id,
                    selected_sql=last_result.sql,
                    confidence=0.0,
                    reasoning="All candidates failed execution",
                    total_candidates=total_candidates,
                    successful_candidates=0
                )

            return JudgmentResult(
                selected_id=-1,
                selected_sql="",
                confidence=0.0,
                reasoning="No candidates generated",
                total_candidates=total_candidates,
                successful_candidates=0
            )

        # If only one successful, return it
        if len(successful) == 1:
            candidate, exec_result = successful[0]
            return JudgmentResult(
                selected_id=candidate.candidate_id,
                selected_sql=exec_result.sql,
                confidence=0.8,
                reasoning=f"Only successful candidate (strategy: {candidate.strategy_name})",
                total_candidates=total_candidates,
                successful_candidates=1
            )

        # Multiple successful - use LLM judge
        return self._llm_judge(successful, nl_query, hint, total_candidates)

    def _llm_judge(
        self,
        successful: list[tuple[SQLCandidate, ExecutionResult]],
        nl_query: str,
        hint: str,
        total_candidates: int
    ) -> JudgmentResult:
        """Use LLM to judge between multiple successful candidates."""
        # Build candidates section
        candidates_text = []
        for candidate, exec_result in successful:
            candidates_text.append(
                f"Option {candidate.candidate_id} ({candidate.strategy_name}):\n"
                f"{exec_result.sql}"
            )

        hint_section = f"Hint: {hint}" if hint else ""

        prompt = JUDGE_PROMPT["user_template"].format(
            question=nl_query,
            hint_section=hint_section,
            candidates="\n\n".join(candidates_text)
        )

        try:
            response = self.llm_client.complete(
                prompt=prompt,
                system_prompt=JUDGE_PROMPT["system"],
                max_tokens=512
            )

            result = self._parse_judgment(response)

            # Find selected candidate
            selected_id = result.get("selected_id", successful[0][0].candidate_id)
            selected_sql = ""

            for candidate, exec_result in successful:
                if candidate.candidate_id == selected_id:
                    selected_sql = exec_result.sql
                    break

            # If not found, use first
            if not selected_sql:
                selected_id = successful[0][0].candidate_id
                selected_sql = successful[0][1].sql

            return JudgmentResult(
                selected_id=selected_id,
                selected_sql=selected_sql,
                confidence=result.get("confidence", 0.7),
                reasoning=result.get("reasoning", "Selected by LLM judge"),
                total_candidates=total_candidates,
                successful_candidates=len(successful)
            )

        except Exception as e:
            # Fallback: return first successful
            candidate, exec_result = successful[0]
            return JudgmentResult(
                selected_id=candidate.candidate_id,
                selected_sql=exec_result.sql,
                confidence=0.6,
                reasoning=f"Judge failed ({e}), using first successful",
                total_candidates=total_candidates,
                successful_candidates=len(successful)
            )

    def _parse_judgment(self, response: str) -> dict:
        """Parse JSON judgment from response."""
        # Try to find JSON
        json_match = re.search(r'\{[\s\S]*\}', response)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except:
                pass

        # Try to extract fields manually
        result = {}

        id_match = re.search(r'selected_id["\s:]+(\d+)', response)
        if id_match:
            result["selected_id"] = int(id_match.group(1))

        conf_match = re.search(r'confidence["\s:]+(\d*\.?\d+)', response)
        if conf_match:
            result["confidence"] = float(conf_match.group(1))

        reason_match = re.search(r'reasoning["\s:]+["\']?([^"\'}\n]+)', response)
        if reason_match:
            result["reasoning"] = reason_match.group(1).strip()

        return result
