"""
QA-SQL: Local-first Text-to-SQL Engine

A privacy-focused Text-to-SQL engine that processes all queries locally,
ensuring sensitive enterprise schemas never leak to third-party AI providers.

Usage:
    from qasql import QASQLEngine

    engine = QASQLEngine(
        db_uri="sqlite:///path/to/database.sqlite",
        llm_provider="ollama",  # Local LLM
        llm_model="llama3.2"
    )
    engine.setup()

    # Query without hint (4 candidates)
    result = engine.query("Show total sales by customer")

    # Query with hint (5 candidates, includes SME strategy)
    result = engine.query(
        question="Show total sales by customer",
        hint="sales = sum(order_amount)"
    )

    print(result.sql)
    print(result.confidence)
"""

from qasql.engine import QASQLEngine
from qasql.config import QASQLConfig
from qasql.result import QueryResult, SetupResult
from qasql.database import DatabaseConnector

__version__ = "1.0.0"
__author__ = "QA-SQL Team"

__all__ = [
    "QASQLEngine",
    "QASQLConfig",
    "QueryResult",
    "SetupResult",
    "DatabaseConnector",
    "__version__",
]
