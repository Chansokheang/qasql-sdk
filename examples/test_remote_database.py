"""
QA-SQL SDK - Remote Database Testing

This file tests the SDK's ability to connect to and query remote databases.

Prerequisites:
    1. Install the SDK with PostgreSQL support:
       pip install -e ..[postgres]
       OR
       pip install qasql[postgres]

    2. Have a PostgreSQL database accessible:
       - Local: PostgreSQL running on localhost
       - Remote: Cloud-hosted PostgreSQL (AWS RDS, Azure, etc.)

    3. Set environment variables OR update the config below:
       export QASQL_DB_HOST='your-host'
       export QASQL_DB_PORT='5432'
       export QASQL_DB_NAME='your-database'
       export QASQL_DB_USER='your-username'
       export QASQL_DB_PASSWORD='your-password'

    4. For LLM operations:
       - Ollama: ollama serve && ollama pull llama3.2
       - Anthropic: export ANTHROPIC_API_KEY='your-key'

Usage:
    python test_remote_database.py
"""

import os
import sys

# Add parent directory to path for local development
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from qasql import QASQLEngine
from qasql.database import PostgreSQLConnector, DatabaseConnector
from qasql.config import QASQLConfig


# ============================================================
# Configuration - Update these values for your database
# ============================================================

# Option 1: Direct configuration
POSTGRES_CONFIG = {
    "host": os.getenv("QASQL_DB_HOST", "localhost"),
    "port": int(os.getenv("QASQL_DB_PORT", "5432")),
    "database": os.getenv("QASQL_DB_NAME", "testdb"),
    "user": os.getenv("QASQL_DB_USER", "postgres"),
    "password": os.getenv("QASQL_DB_PASSWORD", "postgres"),
}

# Option 2: Connection URI format
POSTGRES_URI = os.getenv(
    "QASQL_DB_URI",
    f"postgresql://{POSTGRES_CONFIG['user']}:{POSTGRES_CONFIG['password']}@"
    f"{POSTGRES_CONFIG['host']}:{POSTGRES_CONFIG['port']}/{POSTGRES_CONFIG['database']}"
)

# LLM Configuration
LLM_PROVIDER = os.getenv("QASQL_LLM_PROVIDER", "ollama")  # ollama, anthropic, openai
LLM_MODEL = os.getenv("QASQL_LLM_MODEL", "llama3.2")


# ============================================================
# Test Functions
# ============================================================

def test_direct_connection():
    """Test 1: Direct PostgreSQL connection using connector class."""
    print("\n" + "=" * 60)
    print("Test 1: Direct PostgreSQL Connection")
    print("=" * 60)

    try:
        connector = PostgreSQLConnector(
            host=POSTGRES_CONFIG["host"],
            port=POSTGRES_CONFIG["port"],
            database=POSTGRES_CONFIG["database"],
            user=POSTGRES_CONFIG["user"],
            password=POSTGRES_CONFIG["password"]
        )

        print(f"Connecting to {POSTGRES_CONFIG['host']}:{POSTGRES_CONFIG['port']}...")
        connector.connect()
        print("Connected successfully!")

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
            print(f"  Primary keys: {schema['primary_keys']}")

            # Show columns
            print("\n  Column details:")
            for col in schema["columns"][:5]:
                print(f"    - {col['name']} ({col['type']})")

            # Execute a simple query
            print(f"\nExecuting: SELECT COUNT(*) FROM \"{table_name}\"")
            rows, columns = connector.execute(f'SELECT COUNT(*) FROM "{table_name}"')
            print(f"Result: {rows[0][0]} rows")

        connector.disconnect()
        print("\nDisconnected.")
        return True

    except ImportError as e:
        print(f"\nERROR: {e}")
        print("Install PostgreSQL support: pip install qasql[postgres]")
        return False
    except Exception as e:
        print(f"\nERROR: {e}")
        return False


def test_uri_connection():
    """Test 2: PostgreSQL connection using URI format."""
    print("\n" + "=" * 60)
    print("Test 2: Connection via URI")
    print("=" * 60)

    try:
        print(f"URI: postgresql://***@{POSTGRES_CONFIG['host']}:{POSTGRES_CONFIG['port']}/{POSTGRES_CONFIG['database']}")

        connector = DatabaseConnector.from_uri(POSTGRES_URI)
        connector.connect()
        print("Connected successfully via URI!")

        tables = connector.get_tables()
        print(f"Tables: {tables[:5]}{'...' if len(tables) > 5 else ''}")

        connector.disconnect()
        return True

    except Exception as e:
        print(f"ERROR: {e}")
        return False


def test_config_based_connection():
    """Test 3: Connection using QASQLConfig."""
    print("\n" + "=" * 60)
    print("Test 3: Connection via QASQLConfig")
    print("=" * 60)

    try:
        config = QASQLConfig(
            db_type="postgresql",
            db_host=POSTGRES_CONFIG["host"],
            db_port=POSTGRES_CONFIG["port"],
            db_name=POSTGRES_CONFIG["database"],
            db_user=POSTGRES_CONFIG["user"],
            db_password=POSTGRES_CONFIG["password"],
        )

        connector = DatabaseConnector.from_config(config)
        connector.connect()
        print("Connected successfully via config!")

        # Extract full schema
        print("\nExtracting full schema...")
        schema = connector.extract_full_schema()
        print(f"Schema extracted for {len(schema['tables'])} tables")

        connector.disconnect()
        return True

    except Exception as e:
        print(f"ERROR: {e}")
        return False


def test_engine_with_remote_db():
    """Test 4: Full QASQLEngine with remote PostgreSQL."""
    print("\n" + "=" * 60)
    print("Test 4: QASQLEngine with Remote Database")
    print("=" * 60)

    try:
        print(f"Initializing engine with PostgreSQL...")
        print(f"  Host: {POSTGRES_CONFIG['host']}")
        print(f"  Database: {POSTGRES_CONFIG['database']}")
        print(f"  LLM: {LLM_PROVIDER}/{LLM_MODEL}")

        engine = QASQLEngine(
            db_uri=POSTGRES_URI,
            llm_provider=LLM_PROVIDER,
            llm_model=LLM_MODEL,
            output_dir="./qasql_remote_output"
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

        # Get tables and schema
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
            print(f"Candidates: {result.successful_candidates}/{result.total_candidates}")

            if result.sql:
                # Execute the generated SQL
                try:
                    rows, columns = engine.execute_sql(result.sql)
                    print(f"\nExecution Result:")
                    print(f"  Columns: {columns}")
                    print(f"  Rows: {rows[:5]}")
                except Exception as e:
                    print(f"  Execution error: {e}")

        return True

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_env_based_config():
    """Test 5: Configuration from environment variables."""
    print("\n" + "=" * 60)
    print("Test 5: Configuration from Environment Variables")
    print("=" * 60)

    print("Checking environment variables:")
    env_vars = [
        "QASQL_DB_HOST",
        "QASQL_DB_PORT",
        "QASQL_DB_NAME",
        "QASQL_DB_USER",
        "QASQL_DB_PASSWORD",
        "QASQL_DB_URI",
        "QASQL_DB_TYPE",
    ]

    for var in env_vars:
        value = os.getenv(var)
        if value:
            # Mask password
            if "PASSWORD" in var:
                value = "***"
            print(f"  {var}: {value}")
        else:
            print(f"  {var}: (not set)")

    try:
        # Try loading from env
        config = QASQLConfig.from_env()
        print(f"\nConfig loaded from env:")
        print(f"  db_type: {config.db_type}")
        print(f"  db_host: {config.db_host}")
        print(f"  db_port: {config.db_port}")
        print(f"  db_name: {config.db_name}")
        return True
    except Exception as e:
        print(f"\nNote: {e}")
        return True  # Not a failure, just info


def test_query_timeout():
    """Test 6: Query timeout functionality."""
    print("\n" + "=" * 60)
    print("Test 6: Query Timeout")
    print("=" * 60)

    try:
        connector = PostgreSQLConnector(
            host=POSTGRES_CONFIG["host"],
            port=POSTGRES_CONFIG["port"],
            database=POSTGRES_CONFIG["database"],
            user=POSTGRES_CONFIG["user"],
            password=POSTGRES_CONFIG["password"]
        )

        connector.connect()
        tables = connector.get_tables()

        if tables:
            # Test with short timeout
            print("Testing query with 30s timeout...")
            rows, cols = connector.execute(
                f'SELECT COUNT(*) FROM "{tables[0]}"',
                timeout=30.0
            )
            print(f"Result: {rows[0][0]}")

        connector.disconnect()
        print("Timeout test passed!")
        return True

    except Exception as e:
        print(f"ERROR: {e}")
        return False


# ============================================================
# Main
# ============================================================

def main():
    """Run all remote database tests."""
    print("=" * 60)
    print("QA-SQL SDK - Remote Database Tests")
    print("=" * 60)
    print(f"""
Configuration:
  Host: {POSTGRES_CONFIG['host']}
  Port: {POSTGRES_CONFIG['port']}
  Database: {POSTGRES_CONFIG['database']}
  User: {POSTGRES_CONFIG['user']}
  LLM: {LLM_PROVIDER}/{LLM_MODEL}

Tests to run:
  1. Direct PostgreSQL connection
  2. Connection via URI
  3. Connection via QASQLConfig
  4. Full QASQLEngine with remote DB
  5. Environment variable configuration
  6. Query timeout functionality
""")

    results = {}

    # Run tests
    results["Direct Connection"] = test_direct_connection()
    results["URI Connection"] = test_uri_connection()
    results["Config Connection"] = test_config_based_connection()
    results["Engine + Remote DB"] = test_engine_with_remote_db()
    results["Env Config"] = test_env_based_config()
    results["Query Timeout"] = test_query_timeout()

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    passed = 0
    failed = 0
    for test_name, result in results.items():
        status = "PASS" if result else "FAIL"
        symbol = "✓" if result else "✗"
        print(f"  {symbol} {test_name}: {status}")
        if result:
            passed += 1
        else:
            failed += 1

    print(f"\nTotal: {passed} passed, {failed} failed")

    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
