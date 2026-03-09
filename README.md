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
- **Database Support**: SQLite (local) and PostgreSQL (remote)
- **Flexible LLM**: Ollama, Anthropic Claude, or OpenAI

---

## Table of Contents

- [Installation](#installation)
- [Python SDK](#python-sdk)
  - [Basic Usage](#basic-usage)
  - [With Hint](#with-hint-better-accuracy)
  - [Cloud LLM Providers](#using-cloud-llm-providers)
  - [Remote Database](#remote-database-connection)
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

# AWS RDS
engine = QASQLEngine(
    db_uri="postgresql://admin:pass@mydb.xxx.rds.amazonaws.com:5432/prod"
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

| Database | URI Format | Installation |
|----------|------------|--------------|
| SQLite | `sqlite:///path/to/db.sqlite` | Built-in |
| PostgreSQL | `postgresql://user:pass@host:port/db` | `pip install -e ".[postgres]"` |

---

## Examples

```bash
cd examples

# Test schema extraction (no LLM needed)
python test_schema_only.py

# Test with California Schools database
python test_california_schools.py

# Test remote database connection
python test_remote_database.py

# Interactive demo
python interactive_demo.py --db-uri sqlite:///path/to/db.sqlite
```

---

## Troubleshooting

| Error | Solution |
|-------|----------|
| `Cannot connect to Ollama` | Run `ollama serve` first |
| `psycopg2 is required` | Run `pip install -e ".[postgres]"` |
| `Connection refused` (PostgreSQL) | Check if PostgreSQL server is running |
| `Database not found` | Check file path is correct |

---

## License

MIT License - see [LICENSE](LICENSE)
