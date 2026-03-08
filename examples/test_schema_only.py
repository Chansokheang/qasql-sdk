"""
Test QA-SQL SDK - Schema Extraction Only (No LLM Required)

This test demonstrates the schema extraction and database connectivity
without requiring an LLM to be running.
"""

import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from qasql.config import QASQLConfig
from qasql.database import DatabaseConnector


def main():
    # Path to california_schools database
    db_path = os.path.join(
        os.path.dirname(__file__),
        "..", "..", "app", "california_schools.sqlite"
    )
    db_path = os.path.abspath(db_path)

    print("=" * 60)
    print("QA-SQL SDK Test - Schema Extraction (No LLM)")
    print("=" * 60)
    print(f"\nDatabase: {db_path}")

    if not os.path.exists(db_path):
        print("ERROR: Database not found!")
        return

    # Create config and connector
    config = QASQLConfig(db_uri=db_path, db_type="sqlite")
    connector = DatabaseConnector.from_config(config)

    # Connect and extract schema
    print("\n[1] Connecting to database...")
    connector.connect()

    print("\n[2] Getting tables...")
    tables = connector.get_tables()
    print(f"    Found {len(tables)} tables: {tables}")

    print("\n[3] Extracting schema for each table...")
    for table_name in tables:
        print(f"\n{'─' * 50}")
        print(f"Table: {table_name}")
        print("─" * 50)

        schema = connector.get_table_schema(table_name)

        print(f"  Columns: {len(schema.get('columns', []))}")
        print(f"  Rows: {schema.get('row_count', '?')}")
        print(f"  Primary Keys: {schema.get('primary_keys', [])}")
        print(f"  Foreign Keys: {len(schema.get('foreign_keys', []))}")

        print("\n  Column Details:")
        for col in schema.get("columns", [])[:10]:  # First 10 columns
            name = col.get("name", "")
            ctype = col.get("type", "TEXT")
            distinct = col.get("distinct_values", [])

            line = f"    - {name} ({ctype})"
            if distinct:
                line += f" → {distinct[:3]}{'...' if len(distinct) > 3 else ''}"
            print(line)

        if len(schema.get("columns", [])) > 10:
            print(f"    ... and {len(schema['columns']) - 10} more columns")

        # Sample rows
        samples = connector.get_sample_rows(table_name, limit=2)
        if samples:
            print(f"\n  Sample Row: {samples[0][:5]}...")

    # Test SQL execution
    print("\n" + "=" * 60)
    print("[4] Testing SQL Execution...")
    print("=" * 60)

    test_queries = [
        "SELECT COUNT(*) as total_schools FROM schools",
        "SELECT AVG(AvgScrMath) as avg_math FROM satscores WHERE AvgScrMath IS NOT NULL",
        "SELECT CDSCode, School, City FROM schools LIMIT 3"
    ]

    for sql in test_queries:
        print(f"\nSQL: {sql}")
        try:
            rows, columns = connector.execute(sql)
            print(f"Columns: {columns}")
            print(f"Result: {rows}")
        except Exception as e:
            print(f"Error: {e}")

    connector.disconnect()

    print("\n" + "=" * 60)
    print("Schema extraction test completed!")
    print("=" * 60)
    print("""
To run full text-to-SQL queries, you need an LLM:

Option 1: Local Ollama (recommended for privacy)
    ollama serve
    ollama pull llama3.2
    python test_california_schools.py

Option 2: Anthropic API
    export ANTHROPIC_API_KEY='your-key'
    # Modify test to use llm_provider="anthropic"

Option 3: OpenAI API
    export OPENAI_API_KEY='your-key'
    # Modify test to use llm_provider="openai"
""")


if __name__ == "__main__":
    main()
