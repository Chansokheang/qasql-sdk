"""
QA-SQL SDK - Basic Usage Examples

This file demonstrates how to use the QA-SQL SDK for text-to-SQL generation.

Prerequisites:
    1. Install the SDK:
       pip install -e ../  (from this directory)
       OR
       pip install qasql   (from PyPI after publish)

    2. For local LLM (recommended for privacy):
       - Install Ollama: https://ollama.ai
       - Start server: ollama serve
       - Pull model: ollama pull llama3.2

    3. For cloud LLMs:
       - Anthropic: export ANTHROPIC_API_KEY='your-key'
       - OpenAI: export OPENAI_API_KEY='your-key'

Usage:
    python basic_usage.py
"""

import os
import sys

# Add parent directory to path for local development
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from qasql import QASQLEngine, QueryResult


def example_sqlite_ollama():
    """Example: SQLite database with local Ollama LLM."""
    print("\n" + "=" * 60)
    print("Example 1: SQLite + Ollama (Local)")
    print("=" * 60)

    # Initialize engine with SQLite and local Ollama
    engine = QASQLEngine(
        db_uri="sqlite:///path/to/your/database.sqlite",  # Change this path
        llm_provider="ollama",
        llm_model="llama3.2",
        output_dir="./qasql_output"
    )

    # One-time setup: extracts schema and generates descriptions
    print("\nRunning setup...")
    setup_result = engine.setup()

    print(f"Status: {'SUCCESS' if setup_result.success else 'FAILED'}")
    print(f"Database: {setup_result.database_name}")
    print(f"Tables found: {setup_result.tables_found}")

    if not setup_result.success:
        print(f"Errors: {setup_result.errors}")
        return

    # Query without hint (generates 4 candidates)
    print("\n--- Query without hint (4 candidates) ---")
    result = engine.query("Show all customers")

    print(f"SQL: {result.sql}")
    print(f"Confidence: {result.confidence:.2f}")
    print(f"Candidates: {result.successful_candidates}/{result.total_candidates}")

    # Query with hint (generates 5 candidates, includes SME strategy)
    print("\n--- Query with hint (5 candidates) ---")
    result = engine.query(
        question="Show total sales by customer",
        hint="sales = sum(order_amount) from orders table"
    )

    print(f"SQL: {result.sql}")
    print(f"Confidence: {result.confidence:.2f}")
    print(f"Reasoning: {result.reasoning}")


def example_postgresql():
    """Example: PostgreSQL database."""
    print("\n" + "=" * 60)
    print("Example 2: PostgreSQL")
    print("=" * 60)

    engine = QASQLEngine(
        db_uri="postgresql://user:password@localhost:5432/mydb",
        llm_provider="ollama",
        llm_model="llama3.2"
    )

    setup_result = engine.setup()
    print(f"Tables: {setup_result.tables_found}")

    result = engine.query("List all orders from last month")
    print(f"SQL: {result.sql}")


def example_with_readable_names():
    """Example: Using readable names mapping for cryptic column names."""
    print("\n" + "=" * 60)
    print("Example 3: With Readable Names Mapping")
    print("=" * 60)

    # Create a readable names mapping file
    import json

    readable_names = {
        "tbl_cust_01": {
            "table_readable_name": "Customers",
            "columns": {
                "col_a": "Customer Name",
                "col_b": "Email Address",
                "col_c": "Registration Date"
            }
        },
        "tbl_ord_02": {
            "table_readable_name": "Orders",
            "columns": {
                "ord_id": "Order ID",
                "cust_ref": "Customer Reference",
                "amt_val": "Order Amount"
            }
        }
    }

    # Save to file
    os.makedirs("./temp", exist_ok=True)
    with open("./temp/readable_names.json", "w") as f:
        json.dump(readable_names, f, indent=2)

    # Use with engine
    engine = QASQLEngine(
        db_uri="sqlite:///path/to/cryptic_db.sqlite",
        llm_provider="ollama",
        readable_names="./temp/readable_names.json"
    )

    # Now the engine understands that col_a means "Customer Name"


def example_execute_sql():
    """Example: Execute generated SQL and get results."""
    print("\n" + "=" * 60)
    print("Example 4: Execute SQL")
    print("=" * 60)

    engine = QASQLEngine(
        db_uri="sqlite:///path/to/database.sqlite",
        llm_provider="ollama"
    )

    engine.setup()

    # Generate SQL
    result = engine.query("Count customers by country")
    print(f"Generated SQL: {result.sql}")

    # Execute the SQL
    try:
        rows, columns = engine.execute_sql(result.sql)

        print(f"\nResults ({len(rows)} rows):")
        print(" | ".join(columns))
        print("-" * 40)
        for row in rows[:10]:  # Show first 10 rows
            print(" | ".join(str(v) for v in row))

    except Exception as e:
        print(f"Execution error: {e}")


def example_config_file():
    """Example: Using a configuration file."""
    print("\n" + "=" * 60)
    print("Example 5: Config File")
    print("=" * 60)

    import json

    # Create config file
    config = {
        "database": {
            "type": "sqlite",
            "uri": "./mydb.sqlite"
        },
        "llm": {
            "provider": "ollama",
            "model": "llama3.2",
            "base_url": "http://localhost:11434"
        },
        "options": {
            "readable_names": None,
            "relevance_threshold": 0.5,
            "query_timeout": 30,
            "output_dir": "./output"
        }
    }

    os.makedirs("./temp", exist_ok=True)
    with open("./temp/qasql.config.json", "w") as f:
        json.dump(config, f, indent=2)

    # Use config file
    engine = QASQLEngine(config_file="./temp/qasql.config.json")


def example_cloud_providers():
    """Example: Using cloud LLM providers (Anthropic, OpenAI)."""
    print("\n" + "=" * 60)
    print("Example 6: Cloud Providers")
    print("=" * 60)

    # Anthropic Claude
    # Requires: export ANTHROPIC_API_KEY='your-key'
    # engine = QASQLEngine(
    #     db_uri="sqlite:///mydb.sqlite",
    #     llm_provider="anthropic",
    #     llm_model="claude-sonnet-4-5-20250929"
    # )

    # OpenAI GPT
    # Requires: export OPENAI_API_KEY='your-key'
    # engine = QASQLEngine(
    #     db_uri="sqlite:///mydb.sqlite",
    #     llm_provider="openai",
    #     llm_model="gpt-4o-mini"
    # )

    print("Uncomment the code above to use cloud providers.")
    print("Make sure to set the appropriate API key environment variable.")


def example_inspect_results():
    """Example: Inspecting detailed query results."""
    print("\n" + "=" * 60)
    print("Example 7: Detailed Results Inspection")
    print("=" * 60)

    engine = QASQLEngine(
        db_uri="sqlite:///path/to/database.sqlite",
        llm_provider="ollama"
    )

    engine.setup()

    result = engine.query(
        question="What are the top 5 products by revenue?",
        hint="revenue = price * quantity"
    )

    # Access all result fields
    print(f"Generated SQL: {result.sql}")
    print(f"Confidence: {result.confidence:.2f}")
    print(f"Question: {result.question}")
    print(f"Hint: {result.hint}")
    print(f"Reasoning: {result.reasoning}")

    # Candidate details
    print(f"\nCandidates ({result.successful_candidates}/{result.total_candidates} successful):")
    for candidate in result.candidates:
        status = "✓" if candidate.success else "✗"
        print(f"  {status} [{candidate.strategy}] {candidate.sql[:50]}...")
        if candidate.error:
            print(f"      Error: {candidate.error}")

    # Timing information
    print(f"\nTimings:")
    for stage, ms in result.metadata.get("timings", {}).items():
        print(f"  {stage}: {ms:.0f}ms")

    # Convert to dict (for JSON serialization)
    result_dict = result.to_dict()
    print(f"\nResult as dict keys: {list(result_dict.keys())}")


def example_schema_inspection():
    """Example: Inspecting extracted schema."""
    print("\n" + "=" * 60)
    print("Example 8: Schema Inspection")
    print("=" * 60)

    engine = QASQLEngine(
        db_uri="sqlite:///path/to/database.sqlite",
        llm_provider="ollama"
    )

    engine.setup()

    # Get table list
    tables = engine.get_tables()
    print(f"Tables: {tables}")

    # Get full schema
    schema = engine.get_schema()
    for table_name, table_info in schema.items():
        print(f"\nTable: {table_name}")
        print(f"  Columns: {len(table_info.get('columns', []))}")
        print(f"  Rows: {table_info.get('row_count', '?')}")
        print(f"  Primary Keys: {table_info.get('primary_keys', [])}")

        # Show columns
        for col in table_info.get("columns", [])[:5]:  # First 5
            print(f"    - {col['name']} ({col.get('type', 'TEXT')})")

    # Get column descriptions
    profile = engine.get_profile()
    print("\nColumn Descriptions:")
    for table_name, table_profile in profile.get("tables", {}).items():
        print(f"\n{table_name}:")
        for col in table_profile.get("columns", [])[:3]:  # First 3
            print(f"  {col['name']}: {col.get('description', 'N/A')}")


# ============================================================
# Main
# ============================================================

def main():
    """Run examples."""
    print("=" * 60)
    print("QA-SQL SDK Examples")
    print("=" * 60)
    print("""
Available examples:
  1. SQLite + Ollama (Local)
  2. PostgreSQL
  3. With Readable Names
  4. Execute SQL
  5. Config File
  6. Cloud Providers
  7. Detailed Results
  8. Schema Inspection

Note: Most examples require a real database path.
      Update the db_uri in each example before running.
""")

    # Uncomment the example you want to run:

    # example_sqlite_ollama()
    # example_postgresql()
    # example_with_readable_names()
    # example_execute_sql()
    # example_config_file()
    # example_cloud_providers()
    # example_inspect_results()
    # example_schema_inspection()

    print("\nUncomment an example in main() to run it.")


if __name__ == "__main__":
    main()
