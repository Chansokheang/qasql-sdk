"""
QA-SQL Command Line Interface

Usage:
    qasql setup --db-uri sqlite:///path/to/db.sqlite
    qasql query --question "Show all customers"
    qasql query --question "Show sales" --hint "sales = sum(amount)"
"""

import argparse
import json
import sys


def cmd_setup(args):
    """Run setup command."""
    from qasql import QASQLEngine

    print("=" * 60)
    print("QA-SQL Setup")
    print("=" * 60)

    engine = QASQLEngine(
        db_uri=args.db_uri,
        llm_provider=args.provider,
        llm_model=args.model,
        llm_base_url=args.ollama_url,
        readable_names=args.readable_names,
        output_dir=args.output_dir,
        config_file=args.config,
    )

    print(f"Database: {args.db_uri or 'from config'}")
    print(f"Provider: {args.provider}")
    print(f"Model: {args.model}")
    print("-" * 60)

    result = engine.setup(force=args.force)

    print(f"\nStatus: {'SUCCESS' if result.success else 'FAILED'}")
    print(f"Database: {result.database_name}")
    print(f"Tables: {result.tables_found}")
    print(f"Schema: {result.schema_path}")
    print(f"Descriptions: {result.descriptions_path}")

    if result.errors:
        print("\nMessages:")
        for err in result.errors:
            print(f"  - {err}")

    print("=" * 60)
    return 0 if result.success else 1


def cmd_query(args):
    """Run query command."""
    from qasql import QASQLEngine

    engine = QASQLEngine(
        db_uri=args.db_uri,
        llm_provider=args.provider,
        llm_model=args.model,
        llm_base_url=args.ollama_url,
        output_dir=args.output_dir,
        config_file=args.config,
    )

    setup_result = engine.setup()
    if not setup_result.success:
        print(f"Setup failed: {setup_result.errors}")
        return 1

    print("=" * 60)
    print("QA-SQL Query")
    print("=" * 60)
    print(f"Question: {args.question}")
    if args.hint:
        print(f"Hint: {args.hint}")
    print("-" * 60)

    result = engine.query(question=args.question, hint=args.hint)

    print(f"\nGenerated SQL:")
    print("-" * 40)
    print(result.sql)
    print("-" * 40)
    print(f"\nConfidence: {result.confidence:.2f}")
    print(f"Candidates: {result.successful_candidates}/{result.total_candidates}")
    print(f"Reasoning: {result.reasoning}")

    if args.verbose:
        print(f"\nTimings:")
        for stage, ms in result.metadata.get("timings", {}).items():
            print(f"  {stage}: {ms:.0f}ms")

    if args.execute:
        print(f"\nExecution Result:")
        print("-" * 40)
        try:
            rows, columns = engine.execute_sql(result.sql)
            if columns:
                print(" | ".join(columns))
                print("-" * len(" | ".join(columns)))
            for row in rows[:20]:
                print(" | ".join(str(v) for v in row))
            if len(rows) > 20:
                print(f"... ({len(rows)} total rows)")
        except Exception as e:
            print(f"Error: {e}")

    print("=" * 60)

    if args.json:
        print(json.dumps(result.to_dict(), indent=2))

    return 0


def cmd_tables(args):
    """List tables command."""
    from qasql import QASQLEngine

    engine = QASQLEngine(
        db_uri=args.db_uri,
        output_dir=args.output_dir,
        config_file=args.config,
    )

    result = engine.setup()
    if not result.success:
        print(f"Setup failed: {result.errors}")
        return 1

    print("Database Tables:")
    print("-" * 40)

    schema = engine.get_schema()
    for table_name, table_info in schema.items():
        cols = len(table_info.get("columns", []))
        rows = table_info.get("row_count", "?")
        print(f"  {table_name}: {cols} columns, {rows} rows")

    return 0


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="QA-SQL: Local Text-to-SQL Engine",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  qasql setup --db-uri sqlite:///mydb.sqlite
  qasql query --question "Show all customers"
  qasql query --question "Show sales" --hint "sales = sum(amount)"
  qasql query --question "List orders" --execute
  qasql tables --db-uri sqlite:///mydb.sqlite
        """
    )

    parser.add_argument("--config", "-c", help="Path to config file")
    parser.add_argument("--db-uri", help="Database URI")
    parser.add_argument("--provider", default="ollama", choices=["ollama", "anthropic", "openai"])
    parser.add_argument("--model", default="llama3.2", help="LLM model")
    parser.add_argument("--ollama-url", default="http://localhost:11434")
    parser.add_argument("--output-dir", "-o", default="./qasql_output")

    subparsers = parser.add_subparsers(dest="command")

    # Setup
    setup_p = subparsers.add_parser("setup", help="Setup database")
    setup_p.add_argument("--readable-names", help="Readable names file")
    setup_p.add_argument("--force", "-f", action="store_true")

    # Query
    query_p = subparsers.add_parser("query", help="Generate SQL")
    query_p.add_argument("--question", "-q", required=True)
    query_p.add_argument("--hint", help="SME hint")
    query_p.add_argument("--execute", "-e", action="store_true")
    query_p.add_argument("--verbose", "-v", action="store_true")
    query_p.add_argument("--json", action="store_true")

    # Tables
    subparsers.add_parser("tables", help="List tables")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    if args.command == "setup":
        return cmd_setup(args)
    elif args.command == "query":
        return cmd_query(args)
    elif args.command == "tables":
        return cmd_tables(args)

    return 0


if __name__ == "__main__":
    sys.exit(main())
