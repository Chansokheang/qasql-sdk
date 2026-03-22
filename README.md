# QA-SQL SDK

**Local-first Text-to-SQL engine** - Convert natural language to SQL queries.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## About

QA-SQL (Query Augmentation to SQL) is a multi-stage pipeline that converts natural language questions into SQL queries. It uses a **Map-Reduce Schema Agent** to identify relevant tables and a **SQL Selection Agent** that generates multiple SQL candidates and selects the best one using LLM-as-a-Judge.

**Key Features:**
- **Privacy-First**: Run locally with Ollama - no data leaves your network
- **Multi-Strategy Generation**: Generates 4-5 SQL candidates using different approaches
- **Smart Selection**: LLM-as-a-Judge evaluates and picks the best SQL
- **Database Support**: SQLite, PostgreSQL, MySQL, and Supabase
- **Flexible LLM**: Ollama, Anthropic Claude, or OpenAI

---

## Table of Contents

- [Installation](#installation)
- [Python SDK](#python-sdk)
  - [Basic Usage](#basic-usage)
  - [With Hint](#with-hint-better-accuracy)
  - [Cloud LLM Providers](#using-cloud-llm-providers)
  - [Remote Database](#remote-database-connection)
- [MySQL](#mysql)
  - [MySQL Python SDK](#mysql-python-sdk)
  - [MySQL Terminal UI](#mysql-terminal-ui)
- [Supabase](#supabase)
  - [Supabase Setup](#supabase-setup)
  - [Supabase Python SDK](#supabase-python-sdk)
  - [Supabase Terminal UI](#supabase-terminal-ui)
- [Terminal UI](#terminal-ui)
  - [Launch Terminal UI](#launch-terminal-ui)
  - [Terminal UI Commands](#terminal-ui-commands)
- [CLI Commands](#cli-commands)
- [Database Support](#database-support)
- [Examples](#examples)
- [Troubleshooting](#troubleshooting)

---

## Installation

```bash
# Install SDK
pip install -e .

# Install with Terminal UI
pip install -e ".[ui]"

# Install with PostgreSQL support
pip install -e ".[postgres]"

# Install with MySQL support
pip install -e ".[mysql]"

# Install all extras
pip install -e ".[all]"
```

### Setup LLM Provider

**Option A: Ollama (Local - Recommended)**
```bash
# Install Ollama: https://ollama.ai
ollama serve
ollama pull llama3.2
```

**Option B: Anthropic Claude**
```bash
export ANTHROPIC_API_KEY='your-key'
```

**Option C: OpenAI**
```bash
export OPENAI_API_KEY='your-key'
```

---

# Python SDK

Use QA-SQL programmatically in your Python code.

## Basic Usage

```python
from qasql import QASQLEngine

# Initialize with SQLite
engine = QASQLEngine(db_uri="sqlite:///database.sqlite")

# Or with PostgreSQL (remote)
engine = QASQLEngine(db_uri="postgresql://user:pass@host:5432/mydb")

# Setup (one-time - extracts schema)
engine.setup()

# Generate SQL from natural language
result = engine.query("How many customers are there?")
print(result.sql)        # SELECT COUNT(*) FROM customers
print(result.confidence) # 0.85

# Execute the SQL
rows, columns = engine.execute_sql(result.sql)
print(rows)
```

## With Hint (Better Accuracy)

```python
result = engine.query(
    question="What is the total revenue?",
    hint="revenue = sum(amount) from orders table"
)
```

## Using Cloud LLM Providers

```python
# Anthropic Claude
engine = QASQLEngine(
    db_uri="sqlite:///database.sqlite",
    llm_provider="anthropic",
    llm_model="claude-sonnet-4-5-20250929"
)

# OpenAI
engine = QASQLEngine(
    db_uri="sqlite:///database.sqlite",
    llm_provider="openai",
    llm_model="gpt-4o"
)
```

## Remote Database Connection

```python
# PostgreSQL
engine = QASQLEngine(
    db_uri="postgresql://user:pass@localhost:5432/mydb"
)

# MySQL
engine = QASQLEngine(
    db_uri="mysql://user:pass@localhost:3306/mydb"
)

# AWS RDS (PostgreSQL)
engine = QASQLEngine(
    db_uri="postgresql://admin:pass@mydb.xxx.rds.amazonaws.com:5432/prod"
)

# AWS RDS (MySQL)
engine = QASQLEngine(
    db_uri="mysql://admin:pass@mydb.xxx.rds.amazonaws.com:3306/prod"
)
```

### Environment Variables

```bash
export QASQL_DB_HOST='your-host'
export QASQL_DB_PORT='5432'
export QASQL_DB_NAME='mydb'
export QASQL_DB_USER='postgres'
export QASQL_DB_PASSWORD='password'
```

---

# MySQL

Connect to MySQL databases using `mysql-connector-python` or `pymysql`.

## MySQL Python SDK

**Step 1: Install MySQL support**

```bash
pip install -e ".[mysql]"
# or manually:
pip install mysql-connector-python
# or:
pip install pymysql
```

**Step 2: Connect with a URI**

```python
from qasql import QASQLEngine

engine = QASQLEngine(
    db_uri="mysql://user:password@localhost:3306/mydb"
)
engine.setup()

result = engine.query("How many orders were placed this month?")
print(result.sql)

rows, columns = engine.execute_sql(result.sql)
```

**Or use individual parameters:**

```python
from qasql import QASQLEngine
from qasql.config import QASQLConfig

config = QASQLConfig(
    db_type="mysql",
    db_host="localhost",
    db_port=3306,
    db_name="mydb",
    db_user="user",
    db_password="password",
    llm_provider="ollama",
    llm_model="llama3.2"
)
engine = QASQLEngine(config=config)
engine.setup()
```

**Or use environment variables:**

```bash
export QASQL_DB_TYPE='mysql'
export QASQL_DB_HOST='localhost'
export QASQL_DB_PORT='3306'
export QASQL_DB_NAME='mydb'
export QASQL_DB_USER='user'
export QASQL_DB_PASSWORD='password'
```

```python
config = QASQLConfig.from_env()
engine = QASQLEngine(config=config)
```

## MySQL Terminal UI

```bash
# Connect using environment variables (MYSQL_HOST, MYSQL_DATABASE, MYSQL_USER, MYSQL_PASSWORD)
python -m qasql.tui --mysql

# Connect via URI with --db flag
python -m qasql.tui --db mysql://user:password@localhost:3306/mydb

# Or connect inside the TUI
python -m qasql.tui
# Then type: /mysql localhost mydb user password
# Or with custom port: /mysql localhost:3306 mydb user password
```

**MySQL TUI Commands:**

| Command | Description |
|---------|-------------|
| `/mysql <host> <db> <user> <pass>` | Connect to MySQL on default port 3306 |
| `/mysql <host>:<port> <db> <user> <pass>` | Connect to MySQL on custom port |
| `/db mysql://user:pass@host:3306/db` | Connect using a MySQL URI |

**Environment variables for `--mysql` flag:**

```bash
export MYSQL_HOST='localhost'
export MYSQL_PORT='3306'          # optional, default 3306
export MYSQL_DATABASE='mydb'
export MYSQL_USER='user'
export MYSQL_PASSWORD='password'
```

---

# Supabase

Connect to Supabase databases using the official `supabase-py` client.

## Supabase Setup

**Step 1: Install Supabase support**

```bash
pip install supabase
```

**Step 2: Get your Supabase credentials**

1. Go to [Supabase Dashboard](https://supabase.com/dashboard)
2. Select your project
3. Go to **Settings → API**
4. Copy:
   - **Project URL**: `https://xxx.supabase.co`
   - **Service Role Key** (recommended) or **Anon Key**

**Step 3: Create helper functions in Supabase**

Run this in the **Supabase SQL Editor**:

```sql
-- Function to get all tables (required)
CREATE OR REPLACE FUNCTION get_tables(schema_name text DEFAULT 'public')
RETURNS TABLE(table_name text)
LANGUAGE sql SECURITY DEFINER AS $$
  SELECT t.table_name::text
  FROM information_schema.tables t
  WHERE t.table_schema = schema_name
    AND t.table_type = 'BASE TABLE'
  ORDER BY t.table_name;
$$;

-- Function to execute SQL (required for complex queries)
CREATE OR REPLACE FUNCTION exec_sql(query text)
RETURNS json LANGUAGE plpgsql SECURITY DEFINER AS $$
DECLARE result json;
BEGIN
    EXECUTE 'SELECT COALESCE(json_agg(row_to_json(t)), ''[]''::json) FROM (' || query || ') t' INTO result;
    RETURN result;
END;
$$;
```

**Step 4: Set environment variables**

```bash
export SUPABASE_URL='https://xxx.supabase.co'
export SUPABASE_KEY='your-service-role-key'
```

## Supabase Python SDK

```python
from qasql import QASQLEngine

# Using environment variables
engine = QASQLEngine(
    supabase_url="https://xxx.supabase.co",
    supabase_key="your-service-role-key",
    llm_provider="anthropic"
)

# Setup (extracts schema from Supabase)
engine.setup()

# Generate SQL
result = engine.query("How many users are there?")
print(result.sql)

# Execute SQL
rows, columns = engine.execute_sql(result.sql)
```

Or using environment variables:

```python
from qasql.config import QASQLConfig

# Auto-detects Supabase from SUPABASE_URL env var
config = QASQLConfig.from_env()
engine = QASQLEngine(config=config)
```

## Supabase Terminal UI

```bash
# Connect using environment variables
python -m qasql.tui --supabase

# Or connect inside the TUI
python -m qasql.tui
# Then type: /supabase
```

**Supabase TUI Commands:**

| Command | Description |
|---------|-------------|
| `/supabase` | Connect using SUPABASE_URL and SUPABASE_KEY env vars |
| `/supabase <url> <key>` | Connect with credentials directly |

---

# Terminal UI

Interactive terminal interface for text-to-SQL queries.

## Launch Terminal UI

```bash
# Basic launch
python -m qasql.tui

# With SQLite database
python -m qasql.tui --db ./database.sqlite

# With PostgreSQL (remote database)
python -m qasql.tui --db postgresql://user:pass@localhost:5432/mydb

# With MySQL
python -m qasql.tui --db mysql://user:pass@localhost:3306/mydb
python -m qasql.tui --mysql   # uses MYSQL_* env vars

# With Anthropic Claude
python -m qasql.tui --provider anthropic --api-key sk-ant-xxx

# With OpenAI
python -m qasql.tui --provider openai --api-key sk-xxx

# With remote Ollama server
python -m qasql.tui --base-url http://192.168.1.100:11434
```

## Terminal UI Commands

**Connection:**
| Command | Description |
|---------|-------------|
| `/db <path>` | Connect to SQLite database |
| `/db postgresql://...` | Connect to remote PostgreSQL |
| `/db mysql://...` | Connect to MySQL via URI |
| `/mysql <host> <db> <user> <pass>` | Connect to MySQL |
| `/supabase` | Connect to Supabase (uses env vars) |
| `/supabase <url> <key>` | Connect to Supabase with credentials |
| `/llm ollama [model]` | Use local Ollama |
| `/llm anthropic [key]` | Use Claude API |
| `/llm openai [key]` | Use OpenAI API |
| `/status` | Show current configuration |

**Query:**
| Command | Description |
|---------|-------------|
| `/tables` | List all tables |
| `/schema <table>` | Show table schema |
| `/sql <query>` | Execute raw SQL |
| `/hint <text>` | Set hint for next query |
| `/history` | Show query history |

**Other:**
| Command | Description |
|---------|-------------|
| `/help` | Show all commands |
| `/clear` | Clear screen |
| `/quit` | Exit |

**Natural Language:** Just type a question to generate SQL!

```
qasql> How many customers are there?
```

---

# CLI Commands

Command-line interface for quick operations.

```bash
# List tables
python -m qasql tables --db-uri sqlite:///database.sqlite

# Generate SQL
python -m qasql query --db-uri sqlite:///database.sqlite \
    --question "How many orders?"

# Generate and execute
python -m qasql query --db-uri sqlite:///database.sqlite \
    --question "List all products" --execute
```

---

## Database Support

| Database | Connection | Installation |
|----------|------------|--------------|
| SQLite | `db_uri="sqlite:///path/to/db.sqlite"` | Built-in |
| PostgreSQL | `db_uri="postgresql://user:pass@host:port/db"` | `pip install -e ".[postgres]"` |
| MySQL | `db_uri="mysql://user:pass@host:3306/db"` | `pip install -e ".[mysql]"` |
| Supabase | `supabase_url="https://xxx.supabase.co"` | `pip install supabase` |

---

## Examples

```bash
cd examples

# Test schema extraction (no LLM needed)
python test_schema_only.py

# Test with California Schools database
python test_california_schools.py

# Test remote PostgreSQL connection
python test_remote_database.py

# Test Supabase connection
python test_supabase.py

# Interactive demo
python interactive_demo.py --db-uri sqlite:///path/to/db.sqlite
```

---

## Troubleshooting

| Error | Solution |
|-------|----------|
| `Cannot connect to Ollama` | Run `ollama serve` first |
| `psycopg2 is required` | Run `pip install -e ".[postgres]"` |
| `MySQL driver not found` | Run `pip install -e ".[mysql]"` or `pip install mysql-connector-python` |
| `supabase is required` | Run `pip install supabase` |
| `Connection refused` (PostgreSQL) | Check if PostgreSQL server is running |
| `Connection refused` (MySQL) | Check if MySQL server is running and credentials are correct |
| `Database not found` | Check file path is correct |
| `Could not retrieve tables` (Supabase) | Create `get_tables` function in SQL Editor |
| `Schema is empty` (Supabase) | Create `exec_sql` function in SQL Editor |
| `Wrong SQL generated` (Supabase) | Delete cache (`rm -rf qasql_output/`) and reconnect |

---

## License

MIT License - see [LICENSE](LICENSE)
