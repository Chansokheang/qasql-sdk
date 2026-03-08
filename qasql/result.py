"""
Result Module

Data structures for query and setup results.
"""

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class CandidateSQL:
    """A single SQL candidate from generation."""
    candidate_id: int
    sql: str
    strategy: str
    success: bool = False
    error: Optional[str] = None
    execution_time_ms: float = 0.0


@dataclass
class QueryResult:
    """
    Result of a text-to-SQL query.

    Attributes:
        sql: The generated SQL query (best candidate)
        confidence: Confidence score (0.0 - 1.0)
        question: Original natural language question
        hint: SME hint if provided
        reasoning: Judge's reasoning for selection
        candidates: All generated candidates
        successful_candidates: Number of successful candidates
        total_candidates: Total number of candidates
        metadata: Additional metadata (timings, etc.)
    """
    sql: str
    confidence: float
    question: str
    hint: Optional[str] = None
    reasoning: str = ""
    candidates: list[CandidateSQL] = field(default_factory=list)
    successful_candidates: int = 0
    total_candidates: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:
        return (
            f"QueryResult(\n"
            f"  sql={self.sql!r},\n"
            f"  confidence={self.confidence:.2f},\n"
            f"  candidates={self.successful_candidates}/{self.total_candidates}\n"
            f")"
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert result to dictionary."""
        return {
            "sql": self.sql,
            "confidence": self.confidence,
            "question": self.question,
            "hint": self.hint,
            "reasoning": self.reasoning,
            "successful_candidates": self.successful_candidates,
            "total_candidates": self.total_candidates,
            "candidates": [
                {
                    "id": c.candidate_id,
                    "sql": c.sql,
                    "strategy": c.strategy,
                    "success": c.success,
                    "error": c.error
                }
                for c in self.candidates
            ],
            "metadata": self.metadata
        }


@dataclass
class SetupResult:
    """
    Result of engine setup.

    Attributes:
        success: Whether setup completed successfully
        database_name: Name of the database
        tables_found: Number of tables found
        schema_path: Path to generated schema file
        descriptions_path: Path to generated descriptions file
        errors: List of any errors encountered
    """
    success: bool
    database_name: str
    tables_found: int = 0
    schema_path: Optional[str] = None
    descriptions_path: Optional[str] = None
    errors: list[str] = field(default_factory=list)

    def __str__(self) -> str:
        status = "SUCCESS" if self.success else "FAILED"
        return (
            f"SetupResult({status})\n"
            f"  Database: {self.database_name}\n"
            f"  Tables: {self.tables_found}\n"
            f"  Schema: {self.schema_path}\n"
            f"  Descriptions: {self.descriptions_path}"
        )
