"""
Test QA-SQL SDK with California Schools Database

This test uses the existing california_schools.sqlite database.
"""

import os
import sys

# Add paths
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from qasql import QASQLEngine


def main():
    # Path to california_schools database
    db_path = os.path.join(
        os.path.dirname(__file__),
        "..", "..", "app", "california_schools.sqlite"
    )
    db_path = os.path.abspath(db_path)

    print("=" * 60)
    print("QA-SQL SDK Test - California Schools Database")
    print("=" * 60)
    print(f"\nDatabase: {db_path}")
    print(f"Exists: {os.path.exists(db_path)}")

    if not os.path.exists(db_path):
        print("ERROR: Database not found!")
        return

    # Initialize engine (using Ollama for local processing)
    print("\n[1] Initializing engine...")

    try:
        engine = QASQLEngine(
            db_uri=f"sqlite:///{db_path}",
            llm_provider="ollama",
            llm_model="llama3.2:3b",
            output_dir="./test_output"
        )
    except Exception as e:
        print(f"ERROR: Failed to initialize engine: {e}")
        print("\nMake sure Ollama is running:")
        print("  1. ollama serve")
        print("  2. ollama pull llama3.2")
        return

    # Setup
    print("\n[2] Running setup (extracting schema)...")
    try:
        setup_result = engine.setup()  # Uses cache if available

        print(f"    Status: {'SUCCESS' if setup_result.success else 'FAILED'}")
        print(f"    Database: {setup_result.database_name}")
        print(f"    Tables: {setup_result.tables_found}")

        if setup_result.errors:
            for err in setup_result.errors:
                print(f"    Warning: {err}")

    except Exception as e:
        print(f"ERROR: Setup failed: {e}")
        return

    # Show tables
    print("\n[3] Tables found:")
    tables = engine.get_tables()
    schema = engine.get_schema()
    for table in tables:
        info = schema[table]
        cols = len(info.get("columns", []))
        rows = info.get("row_count", "?")
        print(f"    - {table}: {cols} columns, {rows} rows")

    # Test queries
    test_queries = [
        {
            "question": "How many schools are there in total?",
            "hint": None
        },
        {
            "question": "What is the average SAT math score?",
            "hint": "SAT scores are in satscores table, math score is AvgScrMath"
        },
        {
            "question": "List the top 5 schools by enrollment",
            "hint": None
        }
    ]

    print("\n[4] Running test queries...")

    for i, test in enumerate(test_queries, 1):
        print(f"\n{'─' * 60}")
        print(f"Query {i}: {test['question']}")
        if test['hint']:
            print(f"Hint: {test['hint']}")
        print("─" * 60)

        try:
            result = engine.query(
                question=test['question'],
                hint=test['hint']
            )

            print(f"\nGenerated SQL:")
            print(f"  {result.sql}")
            print(f"\nConfidence: {result.confidence:.2f}")
            print(f"Candidates: {result.successful_candidates}/{result.total_candidates}")
            print(f"Time: {result.metadata.get('timings', {}).get('total_ms', 0):.0f}ms")

            # Try to execute
            if result.sql:
                try:
                    rows, columns = engine.execute_sql(result.sql)
                    print(f"\nExecution Result ({len(rows)} rows):")
                    if columns:
                        print(f"  Columns: {columns}")
                    for row in rows[:5]:
                        print(f"  {row}")
                    if len(rows) > 5:
                        print(f"  ... and {len(rows) - 5} more rows")
                except Exception as e:
                    print(f"\nExecution Error: {e}")

        except Exception as e:
            print(f"\nERROR: {e}")

    print("\n" + "=" * 60)
    print("Test completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
