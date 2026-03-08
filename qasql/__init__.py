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

__version__ = "1.0.4"
__author__ = "Chansokheang"

__all__ = [
    "QASQLEngine",
    "QASQLConfig",
    "QueryResult",
    "SetupResult",
    "DatabaseConnector",
    "__version__",
]

# Optional TUI import
def run_ui(db_uri: str = None, model: str = "llama3.2:3b"):
    """Launch the interactive Terminal UI."""
    try:
        from qasql.tui import TerminalUI
        tui = TerminalUI()
        tui.run(db_uri=db_uri, model=model)
    except ImportError:
        print("TUI requires 'rich' library. Install with: pip install qasql[ui]")
