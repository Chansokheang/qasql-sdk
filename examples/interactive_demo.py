"""
QA-SQL SDK - Interactive Demo

An interactive REPL for testing text-to-SQL queries.

Prerequisites:
    1. Install Ollama and start it
    2. Install SDK: pip install -e ../

Usage:
    python interactive_demo.py --db-uri sqlite:///path/to/db.sqlite
    python interactive_demo.py --db-uri sqlite:///../../app/california_schools.sqlite
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from qasql import QASQLEngine


def print_banner():
    print("""
╔═══════════════════════════════════════════════════════════╗
║                     QA-SQL Interactive                     ║
║              Local Text-to-SQL Engine                      ║
╚═══════════════════════════════════════════════════════════╝

Commands:
  /tables     - List all tables
  /schema <t> - Show schema for table <t>
  /hint <h>   - Set hint for next query
  /execute    - Toggle auto-execute (current: OFF)
  /clear      - Clear hint
  /quit       - Exit

Type a question to generate SQL, or a command to explore the database.
""")


def main():
    parser = argparse.ArgumentParser(description="QA-SQL Interactive Demo")
    parser.add_argument("--db-uri", required=True, help="Database URI")
    parser.add_argument("--provider", default="ollama", help="LLM provider")
    parser.add_argument("--model", default="llama3.2", help="LLM model")
    args = parser.parse_args()

    print_banner()

    # Initialize engine
    print(f"Connecting to: {args.db_uri}")
    print(f"Using: {args.provider}/{args.model}")
    print()

    engine = QASQLEngine(
        db_uri=args.db_uri,
        llm_provider=args.provider,
        llm_model=args.model
    )

    print("Running setup...")
    result = engine.setup()

    if not result.success:
        print(f"Setup failed: {result.errors}")
        return

    print(f"Ready! Found {result.tables_found} tables.\n")

    # State
    current_hint = None
    auto_execute = False

    # REPL loop
    while True:
        try:
            # Prompt
            prompt = "qasql"
            if current_hint:
                prompt += f" [hint: {current_hint[:20]}...]"
            prompt += "> "

            user_input = input(prompt).strip()

            if not user_input:
                continue

            # Commands
            if user_input.lower() in ["/quit", "/exit", "/q"]:
                print("Goodbye!")
                break

            elif user_input.lower() == "/tables":
                tables = engine.get_tables()
                print(f"\nTables ({len(tables)}):")
                for t in tables:
                    schema = engine.get_schema()[t]
                    cols = len(schema.get("columns", []))
                    rows = schema.get("row_count", "?")
                    print(f"  {t}: {cols} columns, {rows} rows")
                print()

            elif user_input.lower().startswith("/schema"):
                parts = user_input.split(maxsplit=1)
                if len(parts) < 2:
                    print("Usage: /schema <table_name>")
                    continue

                table_name = parts[1]
                schema = engine.get_schema()

                if table_name not in schema:
                    print(f"Table not found: {table_name}")
                    print(f"Available: {list(schema.keys())}")
                    continue

                table_info = schema[table_name]
                print(f"\nTable: {table_name}")
                print(f"Rows: {table_info.get('row_count', '?')}")
                print(f"Primary Keys: {table_info.get('primary_keys', [])}")
                print("\nColumns:")
                for col in table_info.get("columns", []):
                    name = col.get("name", "")
                    ctype = col.get("type", "TEXT")
                    print(f"  {name} ({ctype})")
                    if col.get("distinct_values"):
                        vals = col["distinct_values"][:5]
                        print(f"    Values: {vals}")
                print()

            elif user_input.lower().startswith("/hint"):
                parts = user_input.split(maxsplit=1)
                if len(parts) < 2:
                    if current_hint:
                        print(f"Current hint: {current_hint}")
                    else:
                        print("No hint set. Usage: /hint <your hint>")
                else:
                    current_hint = parts[1]
                    print(f"Hint set: {current_hint}")

            elif user_input.lower() == "/clear":
                current_hint = None
                print("Hint cleared.")

            elif user_input.lower() == "/execute":
                auto_execute = not auto_execute
                print(f"Auto-execute: {'ON' if auto_execute else 'OFF'}")

            elif user_input.startswith("/"):
                print(f"Unknown command: {user_input}")
                print("Type /quit to exit, or a question to generate SQL.")

            else:
                # Generate SQL
                print(f"\nGenerating SQL...")
                if current_hint:
                    print(f"Using hint: {current_hint}")

                result = engine.query(
                    question=user_input,
                    hint=current_hint
                )

                print(f"\n{'─' * 50}")
                print(f"SQL: {result.sql}")
                print(f"{'─' * 50}")
                print(f"Confidence: {result.confidence:.2f}")
                print(f"Candidates: {result.successful_candidates}/{result.total_candidates}")
                print(f"Time: {result.metadata.get('timings', {}).get('total_ms', 0):.0f}ms")

                if auto_execute and result.sql:
                    print(f"\n{'─' * 50}")
                    print("Execution Result:")
                    try:
                        rows, columns = engine.execute_sql(result.sql)
                        if columns:
                            print(" | ".join(str(c) for c in columns))
                            print("-" * 40)
                        for row in rows[:10]:
                            print(" | ".join(str(v) for v in row))
                        if len(rows) > 10:
                            print(f"... ({len(rows)} total rows)")
                    except Exception as e:
                        print(f"Error: {e}")

                print()

        except KeyboardInterrupt:
            print("\nUse /quit to exit.")
        except EOFError:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    main()
