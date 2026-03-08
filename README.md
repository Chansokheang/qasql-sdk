# QA-SQL SDK

**Local-first Text-to-SQL engine for enterprise deployment.**

All processing happens locally - sensitive database schemas never leave your network.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Terminal UI](#terminal-ui)
- [CLI Usage](#cli-usage)
- [Python SDK](#python-sdk)
- [Configuration](#configuration)
- [How It Works](#how-it-works)
- [Examples](#examples)
- [API Reference](#api-reference)
- [Troubleshooting](#troubleshooting)

---

## Features

- **Privacy-First**: Use local LLMs (Ollama) - zero data leaves your network
- **Multi-Strategy Generation**: Generates 4-5 SQL candidates using different approaches
- **Automatic Schema Discovery**: Extracts and profiles database structure
- **Smart Selection**: LLM-as-a-Judge picks the best SQL candidate
- **Database Support**: SQLite and PostgreSQL
- **Flexible LLM Support**: Ollama (local), Anthropic Claude, OpenAI GPT

---

## Installation

### Step 1: Install the SDK

```bash
# From source (development)
cd qasql-sdk
pip install -e .

# Or from PyPI (after publish)
pip install qasql
```

### Step 2: Install Optional Dependencies

```bash
# For Terminal UI (recommended)
pip install qasql[ui]

# For Anthropic Claude
pip install qasql[anthropic]

# For OpenAI
pip install qasql[openai]

# For PostgreSQL
pip install qasql[postgres]

# All extras
pip install qasql[all]
```

### Step 3: Setup LLM Provider

#### Option A: Ollama (Local - Recommended for Privacy)

```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Start Ollama server (keep running in terminal)
ollama serve

# In another terminal, pull a model
ollama pull llama3.2

# Or for better SQL generation
ollama pull codellama:13b
```

#### Option B: Anthropic API

```bash
export ANTHROPIC_API_KEY='your-anthropic-api-key'
```

#### Option C: OpenAI API

```bash
export OPENAI_API_KEY='your-openai-api-key'
```

---

## Quick Start

### 1. Test Schema Extraction (No LLM Required)

```bash
cd qasql-sdk/examples
python test_schema_only.py
```

### 2. Full Text-to-SQL Test (Requires LLM)

```bash
# Make sure Ollama is running first
ollama serve

# Then run the test
cd qasql-sdk/examples
python test_california_schools.py
```

### 3. Interactive Demo

```bash
cd qasql-sdk/examples
python interactive_demo.py --db-uri sqlite:///../../app/california_schools.sqlite
```

---

## Terminal UI

Interactive terminal interface similar to Claude Code.

### Install with UI Support

```bash
pip install qasql[ui]
```

### Launch Terminal UI

```bash
# Start UI (configure LLM and database interactively)
python -m qasql.tui

# Or connect to database on startup
python -m qasql.tui --db ./database.sqlite

# With different LLM providers
python -m qasql.tui --provider ollama --model llama3.2:3b
python -m qasql.tui --provider anthropic --api-key sk-ant-xxx
python -m qasql.tui --provider openai --api-key sk-xxx

# Use remote Ollama server
python -m qasql.tui --base-url http://192.168.1.100:11434
```

### Terminal UI Preview

```
╔═══════════════════════════════════════════════════════════════╗
║   ██████╗  █████╗ ███████╗ ██████╗ ██╗                       ║
║  ██╔═══██╗██╔══██╗██╔════╝██╔═══██╗██║                       ║
║  ██║   ██║███████║███████╗██║   ██║██║                       ║
║  ╚██████╔╝██║  ██║███████║╚██████╔╝███████╗                  ║
║   Text-to-SQL Engine - Local & Private                       ║
╚═══════════════════════════════════════════════════════════════╝

qasql> /db ./california_schools.sqlite
✓ Connected to: california_schools (3 tables)

qasql> How many schools are there?
┌─────────────────────────────────────────┐
│ Generated SQL (confidence: 85%)         │
├─────────────────────────────────────────┤
│ SELECT COUNT(*) FROM schools;           │
└─────────────────────────────────────────┘
```

### Terminal UI Commands

**Connection Commands:**
| Command | Description |
|---------|-------------|
| `/llm` | Show current LLM configuration |
| `/llm ollama [model]` | Use local Ollama |
| `/llm ollama [model] [url]` | Use Ollama at custom URL |
| `/llm anthropic [api_key]` | Use Claude API |
| `/llm openai [api_key]` | Use OpenAI API |
| `/db` | Show current database |
| `/db <path_or_uri>` | Connect to database |

**Query Commands:**
| Command | Description |
|---------|-------------|
| `/tables` | List all tables |
| `/schema <table>` | Show table schema |
| `/hint <text>` | Set hint for next query |
| `/sql <query>` | Execute raw SQL |
| `/history` | Show query history |

**Other Commands:**
| Command | Description |
|---------|-------------|
| `/status` | Show current configuration |
| `/clear` | Clear screen |
| `/help` | Show help |
| `/quit` | Exit |

Or just type a natural language question to generate SQL!

### Database Connection Formats

| Type | Example |
|------|---------|
| SQLite (file path) | `/db ./database.sqlite` |
| SQLite (URI) | `/db sqlite:///path/to/db.sqlite` |
| PostgreSQL | `/db postgresql://user:pass@localhost:5432/dbname` |

---

## CLI Usage

### Using `python -m qasql`

```bash
cd qasql-sdk

# List tables
python -m qasql tables --db-uri sqlite:///path/to/database.sqlite

# Setup database (extract schema)
python -m qasql setup --db-uri sqlite:///path/to/database.sqlite

# Generate SQL from question
python -m qasql query --db-uri sqlite:///path/to/database.sqlite \
    --question "How many customers are there?"

# Generate SQL with hint (enables SME strategy)
python -m qasql query --db-uri sqlite:///path/to/database.sqlite \
    --question "What is the total revenue?" \
    --hint "revenue = sum(amount) from orders table"

# Execute the generated SQL
python -m qasql query --db-uri sqlite:///path/to/database.sqlite \
    --question "List all products" \
    --execute

# Show verbose output with timings
python -m qasql query --db-uri sqlite:///path/to/database.sqlite \
    --question "Count orders by status" \
    --verbose
```

### CLI Options

```
Global Options:
  --config, -c       Path to config file (JSON)
  --db-uri           Database URI (sqlite:/// or postgresql://)
  --provider         LLM provider: ollama, anthropic, openai (default: ollama)
  --model            LLM model name (default: llama3.2)
  --ollama-url       Ollama server URL (default: http://localhost:11434)
  --output-dir, -o   Output directory (default: ./qasql_output)

Commands:
  setup              Extract schema and generate descriptions
    --readable-names   Path to readable names mapping file
    --force, -f        Force regeneration

  query              Generate SQL from natural language
    --question, -q     Natural language question (required)
    --hint             SME hint for better accuracy
    --execute, -e      Execute the generated SQL
    --verbose, -v      Show timing information
    --json             Output as JSON

  tables             List database tables
```

---

## Python SDK

### Basic Usage

```python
from qasql import QASQLEngine

# Initialize engine
engine = QASQLEngine(
    db_uri="sqlite:///path/to/database.sqlite",
    llm_provider="ollama",      # or "anthropic", "openai"
    llm_model="llama3.2",       # model name
    output_dir="./qasql_output"
)

# One-time setup (extracts schema, generates column descriptions)
setup_result = engine.setup()
print(f"Tables found: {setup_result.tables_found}")

# Query WITHOUT hint → generates 4 candidates
result = engine.query("How many customers are there?")
print(result.sql)
print(result.confidence)

# Query WITH hint → generates 5 candidates (includes SME strategy)
result = engine.query(
    question="What is the total revenue by month?",
    hint="revenue = sum(order_amount), use orders table"
)
print(result.sql)
print(result.reasoning)

# Execute SQL directly
rows, columns = engine.execute_sql(result.sql)
print(columns)
print(rows)
```

### With Configuration File

```python
from qasql import QASQLEngine

# Load from config file
engine = QASQLEngine(config_file="qasql.config.json")
engine.setup()
result = engine.query("Show all orders")
```

### Inspect Schema

```python
# Get table list
tables = engine.get_tables()
print(tables)  # ['customers', 'orders', 'products']

# Get full schema
schema = engine.get_schema()
for table_name, info in schema.items():
    print(f"{table_name}: {len(info['columns'])} columns, {info['row_count']} rows")

# Get column descriptions
profile = engine.get_profile()
```

### Inspect Query Results

```python
result = engine.query("Show top 10 customers by revenue")

# Access all fields
print(result.sql)           # Generated SQL
print(result.confidence)    # 0.0 - 1.0
print(result.reasoning)     # Why this SQL was selected
print(result.question)      # Original question
print(result.hint)          # Hint if provided

# Candidate details
print(f"Candidates: {result.successful_candidates}/{result.total_candidates}")
for candidate in result.candidates:
    print(f"  [{candidate.strategy}] {candidate.success} - {candidate.sql[:50]}...")

# Timing information
for stage, ms in result.metadata.get("timings", {}).items():
    print(f"  {stage}: {ms:.0f}ms")

# Convert to dictionary
result_dict = result.to_dict()
```

---

## Configuration

### Config File (qasql.config.json)

```json
{
  "database": {
    "type": "sqlite",
    "uri": "./database.sqlite"
  },
  "llm": {
    "provider": "ollama",
    "model": "llama3.2",
    "base_url": "http://localhost:11434"
  },
  "options": {
    "readable_names": "mappings.json",
    "relevance_threshold": 0.5,
    "query_timeout": 30,
    "output_dir": "./output"
  }
}
```

### PostgreSQL Configuration

```json
{
  "database": {
    "type": "postgresql",
    "uri": "postgresql://user:password@localhost:5432/mydb"
  },
  "llm": {
    "provider": "ollama",
    "model": "llama3.2"
  }
}
```

### Environment Variables

```bash
export QASQL_DB_URI="sqlite:///database.sqlite"
export QASQL_DB_TYPE="sqlite"
export QASQL_LLM_PROVIDER="ollama"
export QASQL_LLM_MODEL="llama3.2"
export QASQL_OLLAMA_URL="http://localhost:11434"

# For cloud providers
export ANTHROPIC_API_KEY="sk-ant-..."
export OPENAI_API_KEY="sk-..."
```

### Readable Names Mapping

If your database has cryptic column names, provide a mapping file:

**JSON format:**
```json
{
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
      "amt_val": "Order Amount"
    }
  }
}
```

**CSV format:**
```csv
table,column,readable_name
tbl_cust_01,col_a,Customer Name
tbl_cust_01,col_b,Email Address
tbl_ord_02,amt_val,Order Amount
```

---

## How It Works

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        QA-SQL SDK                            │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────┐    ┌──────────────┐    ┌──────────────────┐  │
│  │ Database │───▶│ QASQLEngine  │───▶│ LLM Provider     │  │
│  │ SQLite/  │    │              │    │ Ollama/Anthropic │  │
│  │ Postgres │◀───│              │◀───│ /OpenAI          │  │
│  └──────────┘    └──────────────┘    └──────────────────┘  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Two-Phase Flow

**Phase 1: Setup (One-time)**
```
Database → Schema Extraction → Column Descriptions → Ready
```

**Phase 2: Query (Runtime)**
```
Question → Schema Agent → Candidate Generation → Execution → Judge → SQL
           (Map-Reduce)   (4-5 strategies)       (retry)     (select best)
```

### Candidate Generation Strategies

| Strategy | Description | With Hint | Without Hint |
|----------|-------------|-----------|--------------|
| full_schema | Complete database schema | ✓ | ✓ |
| sme_metadata | Schema + domain expert hints | ✓ | ✗ (skipped) |
| minimal_profile | Column names only | ✓ | ✓ |
| focused_schema | Relevant tables only | ✓ | ✓ |
| full_profile | Schema + descriptions | ✓ | ✓ |
| **Total** | | **5** | **4** |

When no hint is provided, the SME strategy is skipped since it requires domain knowledge.

---

## Examples

### Example 1: Simple Query

```python
from qasql import QASQLEngine

engine = QASQLEngine(db_uri="sqlite:///sales.sqlite")
engine.setup()

result = engine.query("How many orders were placed last month?")
print(result.sql)
# SELECT COUNT(*) FROM orders WHERE order_date >= date('now', '-1 month')
```

### Example 2: Query with Hint

```python
result = engine.query(
    question="What is the average order value by customer segment?",
    hint="order value = quantity * unit_price, segment is in customers table"
)
print(result.sql)
print(result.confidence)  # Higher confidence with hint
```

### Example 3: Execute and Display Results

```python
result = engine.query("List top 5 customers by total purchases")

if result.sql:
    rows, columns = engine.execute_sql(result.sql)

    # Print as table
    print(" | ".join(columns))
    print("-" * 50)
    for row in rows:
        print(" | ".join(str(v) for v in row))
```

### Example 4: Using Anthropic

```python
import os
os.environ["ANTHROPIC_API_KEY"] = "your-key"

engine = QASQLEngine(
    db_uri="sqlite:///mydb.sqlite",
    llm_provider="anthropic",
    llm_model="claude-sonnet-4-5-20250929"
)
```

---

## API Reference

### QASQLEngine

```python
class QASQLEngine:
    def __init__(
        self,
        db_uri: str = None,              # Database URI
        db_type: str = None,             # "sqlite" or "postgresql"
        llm_provider: str = "ollama",    # "ollama", "anthropic", "openai"
        llm_model: str = "llama3.2",     # Model name
        llm_base_url: str = "http://localhost:11434",
        readable_names: str = None,      # Path to mappings file
        output_dir: str = "./qasql_output",
        config_file: str = None,         # Path to config JSON
    ): ...

    def setup(self, force: bool = False) -> SetupResult: ...
    def query(self, question: str, hint: str = None) -> QueryResult: ...
    def execute_sql(self, sql: str) -> tuple[list, list]: ...
    def get_tables(self) -> list[str]: ...
    def get_schema(self) -> dict: ...
    def get_profile(self) -> dict: ...
```

### QueryResult

```python
@dataclass
class QueryResult:
    sql: str                    # Generated SQL
    confidence: float           # 0.0 - 1.0
    question: str               # Original question
    hint: str | None            # Provided hint
    reasoning: str              # Selection reasoning
    candidates: list            # All candidates
    successful_candidates: int  # Count of successful
    total_candidates: int       # Total count
    metadata: dict              # Timings, etc.

    def to_dict(self) -> dict: ...
```

### SetupResult

```python
@dataclass
class SetupResult:
    success: bool
    database_name: str
    tables_found: int
    schema_path: str | None
    descriptions_path: str | None
    errors: list[str]
```

---

## Troubleshooting

### "command not found: qasql"

Use `python -m qasql` instead:
```bash
python -m qasql tables --db-uri sqlite:///mydb.sqlite
```

### "Cannot connect to Ollama"

Make sure Ollama is running:
```bash
# Terminal 1
ollama serve

# Terminal 2
ollama pull llama3.2
```

### "ANTHROPIC_API_KEY not found"

Set the environment variable:
```bash
export ANTHROPIC_API_KEY='your-key'
```

### "Database not found"

Check the path is correct:
```bash
# Use absolute path
python -m qasql tables --db-uri sqlite:////absolute/path/to/db.sqlite

# Or relative path
python -m qasql tables --db-uri sqlite:///./relative/path/db.sqlite
```

### "No module named 'qasql'"

Install the package:
```bash
cd qasql-sdk
pip install -e .
```

---

## Data Privacy

| Provider | Data Location | Recommendation |
|----------|---------------|----------------|
| **Ollama** | 100% Local | Enterprise / Sensitive data |
| Anthropic | Cloud (Anthropic servers) | Development / Non-sensitive |
| OpenAI | Cloud (OpenAI servers) | Development / Non-sensitive |

**With Ollama, zero data leaves your network.**

---

## License

MIT License - see [LICENSE](LICENSE) for details.

---

## Support

- Issues: [GitHub Issues](https://github.com/Chansokheang/Map-Reduce-Schema-sdk/issues)
- Documentation: [GitHub](https://github.com/Chansokheang/Map-Reduce-Schema-sdk)
- PyPI: [pypi.org/project/qasql](https://pypi.org/project/qasql/)
