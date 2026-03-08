"""
Schema Agent (Map-Reduce)

Decomposes queries and identifies relevant tables/columns.
"""

import json
import re
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import Any


@dataclass
class TableRelevance:
    """Relevance assessment for a table."""
    table_name: str
    relevance_score: float
    relevant_columns: list[str] = field(default_factory=list)
    reason: str = ""


class SchemaAgent:
    """
    Map-Reduce Schema Agent.

    Decomposes NL queries and identifies relevant tables.
    """

    def __init__(self, llm_client: Any, max_workers: int = 4):
        self.llm_client = llm_client
        self.max_workers = max_workers

    def run(
        self,
        nl_query: str,
        schema: dict[str, Any],
        profile: dict[str, Any] = None,
        hint: str = "",
        relevance_threshold: float = 0.5
    ) -> dict[str, Any]:
        """
        Run schema agent to identify relevant tables.

        Args:
            nl_query: Natural language query
            schema: Database schema
            profile: Column descriptions
            hint: Optional SME hint
            relevance_threshold: Minimum score to include table

        Returns:
            Focused schema with only relevant tables
        """
        # Decompose query
        components = self._decompose_query(nl_query)

        # Score tables in parallel
        table_names = list(schema.keys())
        relevances = []

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = []
            for table_name in table_names:
                table_schema = schema[table_name]
                table_profile = profile.get("tables", {}).get(table_name) if profile else None

                future = executor.submit(
                    self._score_table,
                    table_name,
                    table_schema,
                    table_profile,
                    components,
                    nl_query,
                    hint
                )
                futures.append((table_name, future))

            for table_name, future in futures:
                try:
                    relevance = future.result()
                    relevances.append(relevance)
                except Exception as e:
                    relevances.append(TableRelevance(
                        table_name=table_name,
                        relevance_score=0.0,
                        reason=f"Error: {e}"
                    ))

        # Filter by threshold
        relevant_tables = {}
        table_relevances = []

        for rel in relevances:
            table_relevances.append({
                "table_name": rel.table_name,
                "relevance_score": rel.relevance_score,
                "relevant_columns": rel.relevant_columns,
                "reason": rel.reason
            })

            if rel.relevance_score >= relevance_threshold:
                relevant_tables[rel.table_name] = schema[rel.table_name]

        # If no tables pass threshold, include top 3
        if not relevant_tables:
            sorted_rels = sorted(relevances, key=lambda x: x.relevance_score, reverse=True)
            for rel in sorted_rels[:3]:
                relevant_tables[rel.table_name] = schema[rel.table_name]

        return {
            "tables": relevant_tables,
            "table_relevances": table_relevances,
            "metadata": {
                "decomposed_components": components,
                "total_tables_evaluated": len(table_names),
                "relevant_tables_count": len(relevant_tables),
                "relevance_threshold": relevance_threshold
            }
        }

    def _decompose_query(self, nl_query: str) -> list[dict]:
        """Decompose query into semantic components."""
        prompt = f"""Analyze this query and extract key components.

Query: "{nl_query}"

Return JSON with components (entity, filter, aggregation, projection):
{{
    "components": [
        {{"text": "phrase", "type": "entity|filter|aggregation|projection"}}
    ]
}}

Return ONLY valid JSON."""

        try:
            response = self.llm_client.complete(prompt=prompt, max_tokens=512)
            result = self._parse_json(response)
            return result.get("components", [])
        except:
            # Fallback: extract keywords
            return [{"text": nl_query, "type": "entity"}]

    def _score_table(
        self,
        table_name: str,
        table_schema: dict,
        table_profile: dict,
        components: list[dict],
        nl_query: str,
        hint: str
    ) -> TableRelevance:
        """Score table relevance using keyword + LLM matching."""
        # Keyword matching score
        keyword_score = self._keyword_match_score(
            table_name, table_schema, table_profile, components, hint
        )

        # If high keyword score, use it directly
        if keyword_score >= 0.8:
            return TableRelevance(
                table_name=table_name,
                relevance_score=keyword_score,
                relevant_columns=self._get_relevant_columns(table_schema, components),
                reason="High keyword match"
            )

        # LLM semantic scoring for ambiguous cases
        llm_score = self._llm_score(table_name, table_schema, table_profile, nl_query, hint)

        # Combine scores
        final_score = max(keyword_score, llm_score)

        return TableRelevance(
            table_name=table_name,
            relevance_score=final_score,
            relevant_columns=self._get_relevant_columns(table_schema, components),
            reason=f"keyword={keyword_score:.2f}, llm={llm_score:.2f}"
        )

    def _keyword_match_score(
        self,
        table_name: str,
        table_schema: dict,
        table_profile: dict,
        components: list[dict],
        hint: str
    ) -> float:
        """Calculate keyword matching score."""
        score = 0.0
        all_text = table_name.lower()

        # Add column names
        for col in table_schema.get("columns", []):
            all_text += " " + col.get("name", "").lower()
            all_text += " " + col.get("readable_name", "").lower()

        # Add descriptions from profile
        if table_profile:
            for col in table_profile.get("columns", []):
                all_text += " " + col.get("description", "").lower()

        # Check components
        for comp in components:
            text = comp.get("text", "").lower()
            words = text.split()
            matches = sum(1 for w in words if w in all_text)
            if words:
                score += matches / len(words)

        # Check hint
        if hint and table_name.lower() in hint.lower():
            score += 0.5

        # Normalize
        if components:
            score = min(1.0, score / len(components))

        return score

    def _llm_score(
        self,
        table_name: str,
        table_schema: dict,
        table_profile: dict,
        nl_query: str,
        hint: str
    ) -> float:
        """Get LLM semantic relevance score."""
        columns = [c.get("name", "") for c in table_schema.get("columns", [])]

        prompt = f"""Rate how relevant this table is to the query (0.0-1.0).

Table: {table_name}
Columns: {', '.join(columns[:10])}
Query: {nl_query}
{"Hint: " + hint if hint else ""}

Return only a number between 0.0 and 1.0."""

        try:
            response = self.llm_client.complete(prompt=prompt, max_tokens=32)
            score = float(re.search(r'[\d.]+', response).group())
            return min(1.0, max(0.0, score))
        except:
            return 0.3  # Default moderate score

    def _get_relevant_columns(self, table_schema: dict, components: list[dict]) -> list[str]:
        """Get columns relevant to query components."""
        relevant = []
        component_words = set()
        for comp in components:
            component_words.update(comp.get("text", "").lower().split())

        for col in table_schema.get("columns", []):
            col_name = col.get("name", "").lower()
            col_readable = col.get("readable_name", "").lower()

            for word in component_words:
                if word in col_name or word in col_readable:
                    relevant.append(col.get("name", ""))
                    break

        return relevant

    def _parse_json(self, response: str) -> dict:
        """Extract JSON from response."""
        json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', response)
        if json_match:
            response = json_match.group(1)

        json_match = re.search(r'\{[\s\S]*\}', response)
        if json_match:
            response = json_match.group(0)

        return json.loads(response)
