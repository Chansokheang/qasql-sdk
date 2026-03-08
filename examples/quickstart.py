"""
QA-SQL SDK - Quick Start

A minimal example to get started with QA-SQL.

Prerequisites:
    1. Install Ollama: https://ollama.ai
    2. Start Ollama: ollama serve
    3. Pull model: ollama pull llama3.2
    4. Install SDK: pip install -e ../

Usage:
    python quickstart.py
"""

import os
import sys

# Add parent directory for local development
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from qasql import QASQLEngine


def main():
    # ============================================================
    # CONFIGURATION - Update this path to your database
    # ============================================================

    # Option 1: Use the california_schools database from the project
    DB_PATH = "../../app/california_schools.sqlite"

    # Option 2: Use your own database
    # DB_PATH = "/path/to/your/database.sqlite"

    # ============================================================
    # SETUP
    # ============================================================

    print("=" * 60)
    print("QA-SQL Quick Start")
    print("=" * 60)

    # Initialize engine
    engine = QASQLEngine(
        db_uri=f"sqlite:///{DB_PATH}",
        llm_provider="ollama",      # Use local Ollama
        llm_model="llama3.2",       # Or: mistral, codellama, etc.
        output_dir="./output"
    )

    # Run setup (one-time: extracts schema, generates descriptions)
    print("\n[1] Running setup...")
    setup_result = engine.setup()

    if not setup_result.success:
        print(f"Setup failed: {setup_result.errors}")
        return

    print(f"    Database: {setup_result.database_name}")
    print(f"    Tables: {setup_result.tables_found}")
    print(f"    Schema: {setup_result.schema_path}")

    # ============================================================
    # QUERY WITHOUT HINT (4 candidates)
    # ============================================================

    print("\n[2] Query without hint...")
    print("    Question: 'How many schools are there?'")

    result = engine.query("How many schools are there?")

    print(f"\n    SQL: {result.sql}")
    print(f"    Confidence: {result.confidence:.2f}")
    print(f"    Candidates: {result.successful_candidates}/{result.total_candidates}")

    # Execute the SQL
    try:
        rows, columns = engine.execute_sql(result.sql)
        print(f"    Result: {rows[0] if rows else 'No results'}")
    except Exception as e:
        print(f"    Execution error: {e}")

    # ============================================================
    # QUERY WITH HINT (5 candidates)
    # ============================================================

    print("\n[3] Query with hint...")
    print("    Question: 'What is the average SAT score?'")
    print("    Hint: 'SAT score is in the satscores table'")

    result = engine.query(
        question="What is the average SAT score?",
        hint="SAT score is in the satscores table, column AvgScrMath"
    )

    print(f"\n    SQL: {result.sql}")
    print(f"    Confidence: {result.confidence:.2f}")
    print(f"    Reasoning: {result.reasoning}")

    # ============================================================
    # SHOW TIMING
    # ============================================================

    print("\n[4] Timing breakdown:")
    for stage, ms in result.metadata.get("timings", {}).items():
        print(f"    {stage}: {ms:.0f}ms")

    print("\n" + "=" * 60)
    print("Done!")
    print("=" * 60)


if __name__ == "__main__":
    main()
