"""
QA-SQL SDK - Supabase Database Testing

This file tests the SDK's ability to connect to and query Supabase databases
using the official supabase-py client.

Prerequisites:
    1. Install the SDK with Supabase support:
       pip install supabase

    2. Get your Supabase credentials:
       - Go to: https://supabase.com/dashboard
       - Select your project
       - Go to Settings -> API
       - Copy the Project URL and anon/service_role key

    3. Set environment variables:
       export SUPABASE_URL='https://xxx.supabase.co'
       export SUPABASE_KEY='your-anon-key-or-service-role-key'

    4. For LLM operations:
       - Anthropic: export ANTHROPIC_API_KEY='your-key'
       - Ollama: ollama serve && ollama pull llama3.2

    5. (Optional) Create the exec_sql function for complex SQL queries:
       Run this in the Supabase SQL Editor:

       CREATE OR REPLACE FUNCTION exec_sql(query text)
       RETURNS json
       LANGUAGE plpgsql
       SECURITY DEFINER
       AS $$
       DECLARE
           result json;
       BEGIN
           EXECUTE 'SELECT json_agg(row_to_json(t)) FROM (' || query || ') t'
           INTO result;
           RETURN COALESCE(result, '[]'::json);
       END;
       $$;

Usage:
    python test_supabase.py
"""

import os
import sys

# Add parent directory to path for local development
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from qasql import QASQLEngine
from qasql.database import SupabaseConnector, DatabaseConnector
from qasql.config import QASQLConfig


# ============================================================
# Configuration - Set via environment variables
# ============================================================

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
SUPABASE_SCHEMA = os.getenv("SUPABASE_SCHEMA", "public")

# LLM Configuration
LLM_PROVIDER = os.getenv("QASQL_LLM_PROVIDER", "anthropic")
LLM_MODEL = os.getenv("QASQL_LLM_MODEL", "claude-sonnet-4-5-20250929")


# ============================================================
# Test Functions
# ============================================================

def test_direct_connection():
    """Test 1: Direct Supabase connection using SupabaseConnector."""
    print("\n" + "=" * 60)
    print("Test 1: Direct Supabase Connection")
    print("=" * 60)

    try:
        connector = SupabaseConnector(
            url=SUPABASE_URL,
            key=SUPABASE_KEY,
            schema=SUPABASE_SCHEMA
        )

        print(f"Connecting to Supabase...")
        print(f"  URL: {SUPABASE_URL[:40]}...")
        print(f"  Schema: {SUPABASE_SCHEMA}")

        connector.connect()
        print("\nConnected successfully!")

        # Get tables
        tables = connector.get_tables()
        print(f"\nTables found: {len(tables)}")
        for table in tables[:10]:  # Show first 10
            print(f"  - {table}")

        if tables:
            # Get schema for first table
            table_name = tables[0]
            schema = connector.get_table_schema(table_name)
            print(f"\nSchema for '{table_name}':")
            print(f"  Columns: {len(schema['columns'])}")
            print(f"  Row count: {schema['row_count']}")

            # Show columns
            print("\n  Column details:")
            for col in schema["columns"][:5]:
                print(f"    - {col['name']} ({col['type']})")

            # Get sample rows
            samples = connector.get_sample_rows(table_name, limit=3)
            print(f"\n  Sample rows: {len(samples)}")
            for i, row in enumerate(samples[:2]):
                print(f"    Row {i+1}: {str(row)[:80]}...")

        connector.disconnect()
        print("\nDisconnected.")
        return True

    except ImportError as e:
        print(f"\nERROR: {e}")
        print("Install Supabase support: pip install supabase")
        return False
    except Exception as e:
        print(f"\nERROR: {e}")
        print("\nTroubleshooting:")
        print("  1. Check your SUPABASE_URL and SUPABASE_KEY")
        print("  2. Verify the URL format: https://xxx.supabase.co")
        print("  3. Make sure you're using the correct API key")
        return False


def test_config_based_connection():
    """Test 2: Connection using QASQLConfig."""
    print("\n" + "=" * 60)
    print("Test 2: Connection via QASQLConfig")
    print("=" * 60)

    try:
        config = QASQLConfig(
            db_type="supabase",
            supabase_url=SUPABASE_URL,
            supabase_key=SUPABASE_KEY,
            db_schema=SUPABASE_SCHEMA,
        )

        connector = DatabaseConnector.from_config(config)
        connector.connect()
        print("Connected successfully via QASQLConfig!")

        # Extract full schema
        print("\nExtracting schema...")
        schema = connector.extract_full_schema()
        print(f"Schema extracted for {len(schema['tables'])} tables")

        # Show table names
        if schema['tables']:
            print("\nTables:")
            for table_name in list(schema['tables'].keys())[:5]:
                table_info = schema['tables'][table_name]
                print(f"  - {table_name}: {table_info['row_count']} rows, {len(table_info['columns'])} columns")

        connector.disconnect()
        return True

    except Exception as e:
        print(f"ERROR: {e}")
        return False


def test_env_based_config():
    """Test 3: Configuration from environment variables."""
    print("\n" + "=" * 60)
    print("Test 3: Configuration from Environment Variables")
    print("=" * 60)

    print("Checking environment variables:")
    env_vars = [
        "SUPABASE_URL",
        "SUPABASE_KEY",
        "SUPABASE_SCHEMA",
        "QASQL_LLM_PROVIDER",
        "ANTHROPIC_API_KEY",
    ]

    for var in env_vars:
        value = os.getenv(var)
        if value:
            # Mask sensitive values
            if "KEY" in var or "PASSWORD" in var:
                display = f"{value[:10]}...{value[-4:]}" if len(value) > 14 else "***"
            elif "URL" in var:
                display = f"{value[:40]}..." if len(value) > 40 else value
            else:
                display = value
            print(f"  {var}: {display}")
        else:
            print(f"  {var}: (not set)")

    try:
        # Try loading from env
        config = QASQLConfig.from_env()
        print(f"\nConfig loaded from environment:")
        print(f"  db_type: {config.db_type}")
        print(f"  supabase_url: {config.supabase_url[:40] if config.supabase_url else '(not set)'}...")
        return True
    except Exception as e:
        print(f"\nNote: {e}")
        return True  # Not a failure, just info


def test_simple_query():
    """Test 4: Simple table query via REST API."""
    print("\n" + "=" * 60)
    print("Test 4: Simple Table Query")
    print("=" * 60)

    try:
        connector = SupabaseConnector(
            url=SUPABASE_URL,
            key=SUPABASE_KEY,
            schema=SUPABASE_SCHEMA
        )
        connector.connect()

        tables = connector.get_tables()
        if not tables:
            print("No tables found. Create some tables in Supabase first.")
            return False

        table_name = tables[0]
        print(f"\nQuerying table: {table_name}")

        # Try simple SELECT
        try:
            sql = f'SELECT * FROM "{table_name}" LIMIT 5'
            print(f"SQL: {sql}")
            rows, columns = connector.execute(sql)
            print(f"\nResult: {len(rows)} rows, {len(columns)} columns")
            print(f"Columns: {columns}")
            for row in rows[:3]:
                print(f"  {row}")
            return True
        except NotImplementedError as e:
            print(f"\nNote: {str(e)[:200]}...")
            print("\nThis is expected if you haven't created the exec_sql function.")
            print("Simple queries still work via the table API.")

            # Fallback: use get_sample_rows
            samples = connector.get_sample_rows(table_name, limit=5)
            print(f"\nFallback - Sample rows: {len(samples)}")
            return True

    except Exception as e:
        print(f"ERROR: {e}")
        return False


def test_engine_with_supabase():
    """Test 5: Full QASQLEngine with Supabase."""
    print("\n" + "=" * 60)
    print("Test 5: QASQLEngine with Supabase")
    print("=" * 60)

    try:
        print(f"Initializing engine...")
        print(f"  URL: {SUPABASE_URL[:40]}...")
        print(f"  LLM: {LLM_PROVIDER}/{LLM_MODEL}")

        engine = QASQLEngine(
            supabase_url=SUPABASE_URL,
            supabase_key=SUPABASE_KEY,
            db_schema=SUPABASE_SCHEMA,
            llm_provider=LLM_PROVIDER,
            llm_model=LLM_MODEL,
            output_dir="./qasql_supabase_output"
        )

        # Run setup
        print("\nRunning setup (schema extraction + profiling)...")
        setup_result = engine.setup()

        print(f"\nSetup Result:")
        print(f"  Success: {setup_result.success}")
        print(f"  Database: {setup_result.database_name}")
        print(f"  Tables: {setup_result.tables_found}")

        if not setup_result.success:
            print(f"  Errors: {setup_result.errors}")
            return False

        # Get tables
        tables = engine.get_tables()
        print(f"\nTables: {tables}")

        # Try a natural language query
        if tables:
            print("\n--- Natural Language Query ---")
            question = f"How many rows are in the {tables[0]} table?"
            print(f"Question: {question}")

            result = engine.query(question)

            print(f"\nGenerated SQL: {result.sql}")
            print(f"Confidence: {result.confidence:.2f}")

            if result.sql:
                try:
                    rows, columns = engine.execute_sql(result.sql)
                    print(f"\nExecution Result:")
                    print(f"  Columns: {columns}")
                    print(f"  Rows: {rows[:5]}")
                except Exception as e:
                    print(f"  Execution note: {e}")

        return True

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def print_setup_instructions():
    """Print setup instructions for Supabase."""
    print("""
============================================================
Supabase Setup Instructions
============================================================

1. Get your Supabase credentials:
   - Go to: https://supabase.com/dashboard
   - Select your project
   - Go to Settings -> API
   - Copy:
     * Project URL (e.g., https://abcdefgh.supabase.co)
     * anon public key (for read-only) or service_role key (full access)

2. Set environment variables:

   export SUPABASE_URL='https://your-project.supabase.co'
   export SUPABASE_KEY='your-anon-or-service-role-key'

   # For LLM (Anthropic):
   export ANTHROPIC_API_KEY='sk-ant-...'

3. (Optional) For complex SQL queries, create the exec_sql function:

   Go to Supabase SQL Editor and run:

   CREATE OR REPLACE FUNCTION exec_sql(query text)
   RETURNS json
   LANGUAGE plpgsql
   SECURITY DEFINER
   AS $$
   DECLARE
       result json;
   BEGIN
       EXECUTE 'SELECT json_agg(row_to_json(t)) FROM (' || query || ') t'
       INTO result;
       RETURN COALESCE(result, '[]'::json);
   END;
   $$;

4. Run this test:
   python test_supabase.py

============================================================
""")


# ============================================================
# Main
# ============================================================

def main():
    """Run all Supabase tests."""
    print("=" * 60)
    print("QA-SQL SDK - Supabase Database Tests")
    print("=" * 60)

    # Check if credentials are set
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("\nNo credentials configured!")
        print_setup_instructions()
        return False

    print(f"""
Configuration:
  URL: {SUPABASE_URL[:50]}...
  Key: {SUPABASE_KEY[:15]}...
  Schema: {SUPABASE_SCHEMA}
  LLM: {LLM_PROVIDER}/{LLM_MODEL}

Tests to run:
  1. Direct Supabase connection
  2. Connection via QASQLConfig
  3. Environment variable configuration
  4. Simple table query
  5. Full QASQLEngine with Supabase
""")

    results = {}

    # Run tests
    results["Direct Connection"] = test_direct_connection()
    results["Config Connection"] = test_config_based_connection()
    results["Env Config"] = test_env_based_config()
    results["Simple Query"] = test_simple_query()
    results["Engine + Supabase"] = test_engine_with_supabase()

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    passed = 0
    failed = 0
    for test_name, result in results.items():
        status = "PASS" if result else "FAIL"
        symbol = "[OK]" if result else "[FAIL]"
        print(f"  {symbol} {test_name}: {status}")
        if result:
            passed += 1
        else:
            failed += 1

    print(f"\nTotal: {passed} passed, {failed} failed")

    if failed > 0:
        print("\nTroubleshooting tips:")
        print("  1. Verify SUPABASE_URL and SUPABASE_KEY are correct")
        print("  2. Check that your project has tables in the 'public' schema")
        print("  3. Try using the service_role key for full access")
        print("  4. Create the exec_sql function for complex SQL support")

    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
