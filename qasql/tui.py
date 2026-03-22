"""
QA-SQL Terminal UI

Interactive terminal interface for text-to-SQL queries.
Similar to Claude Code's interface using rich library.
"""

import os
import sys
import time
from pathlib import Path
from typing import Optional, Literal

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.syntax import Syntax
    from rich.prompt import Prompt, Confirm
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.markdown import Markdown
    from rich.layout import Layout
    from rich.text import Text
    from rich import box
except ImportError:
    print("Error: rich library not installed.")
    print("Install with: pip install qasql[ui]")
    sys.exit(1)

from qasql.engine import QASQLEngine
from qasql.result import QueryResult


class TerminalUI:
    """Interactive terminal UI for QA-SQL."""

    def __init__(self):
        self.console = Console()
        self.engine: Optional[QASQLEngine] = None
        self.history: list[dict] = []

        # LLM Configuration
        self.llm_provider: str = "ollama"
        self.llm_model: str = "llama3.2:3b"
        self.llm_base_url: str = "http://localhost:11434"
        self.llm_api_key: Optional[str] = None

        # Database Configuration
        self.db_uri: Optional[str] = None
        self.db_type: Optional[str] = None

        # Supabase Configuration
        self.supabase_url: Optional[str] = None
        self.supabase_key: Optional[str] = None

        # MySQL Configuration
        self.mysql_host: Optional[str] = None
        self.mysql_port: int = 3306
        self.mysql_db: Optional[str] = None
        self.mysql_user: Optional[str] = None
        self.mysql_password: Optional[str] = None

    def print_banner(self):
        """Print welcome banner."""
        banner = """
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║   ██████╗  █████╗ ███████╗ ██████╗ ██╗                       ║
║  ██╔═══██╗██╔══██╗██╔════╝██╔═══██╗██║                       ║
║  ██║   ██║███████║███████╗██║   ██║██║                       ║
║  ██║▄▄ ██║██╔══██║╚════██║██║▄▄ ██║██║                       ║
║  ╚██████╔╝██║  ██║███████║╚██████╔╝███████╗                  ║
║   ╚══▀▀═╝ ╚═╝  ╚═╝╚══════╝ ╚══▀▀═╝ ╚══════╝                  ║
║                                                               ║
║   Text-to-SQL Engine - Local & Private                       ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
"""
        self.console.print(banner, style="bold cyan")
        self.console.print("  Type [bold green]/help[/] for commands, [bold green]/quit[/] to exit\n")

    def print_help(self):
        """Print help information."""
        # Connection Commands
        conn_table = Table(title="Connection Commands", box=box.ROUNDED)
        conn_table.add_column("Command", style="cyan", no_wrap=True)
        conn_table.add_column("Description", style="white")

        conn_commands = [
            ("/llm", "Show current LLM configuration"),
            ("/llm ollama [model]", "Use local Ollama (default: llama3.2:3b)"),
            ("/llm ollama [model] [url]", "Use Ollama at custom URL"),
            ("/llm anthropic [api_key]", "Use Claude API"),
            ("/llm openai [api_key]", "Use OpenAI API"),
            ("/db", "Show current database connection"),
            ("/db <path_or_uri>", "Connect to SQLite/PostgreSQL/MySQL database"),
            ("/supabase", "Connect to Supabase (uses env vars)"),
            ("/supabase <url> <key>", "Connect to Supabase with credentials"),
            ("/mysql <host> <db> <user> <pass>", "Connect to MySQL database"),
            ("/mysql <host>:<port> <db> <user> <pass>", "Connect to MySQL on custom port"),
        ]

        for cmd, desc in conn_commands:
            conn_table.add_row(cmd, desc)

        self.console.print(conn_table)
        self.console.print()

        # Query Commands
        query_table = Table(title="Query Commands", box=box.ROUNDED)
        query_table.add_column("Command", style="cyan", no_wrap=True)
        query_table.add_column("Description", style="white")

        query_commands = [
            ("/tables", "List all tables"),
            ("/schema <table>", "Show table schema"),
            ("/hint <text>", "Set hint for next query"),
            ("/sql <query>", "Execute raw SQL"),
            ("/history", "Show query history"),
        ]

        for cmd, desc in query_commands:
            query_table.add_row(cmd, desc)

        self.console.print(query_table)
        self.console.print()

        # Other Commands
        other_table = Table(title="Other Commands", box=box.ROUNDED)
        other_table.add_column("Command", style="cyan", no_wrap=True)
        other_table.add_column("Description", style="white")

        other_commands = [
            ("/status", "Show current configuration"),
            ("/clear", "Clear screen"),
            ("/help", "Show this help"),
            ("/quit", "Exit the application"),
        ]

        for cmd, desc in other_commands:
            other_table.add_row(cmd, desc)

        self.console.print(other_table)
        self.console.print("\n[dim]Or just type a natural language question to generate SQL.[/dim]\n")

    def show_status(self):
        """Show current configuration status."""
        status_table = Table(title="Current Configuration", box=box.ROUNDED)
        status_table.add_column("Setting", style="cyan")
        status_table.add_column("Value", style="white")

        # LLM Status
        llm_status = f"{self.llm_provider} / {self.llm_model}"
        if self.llm_provider == "ollama":
            llm_status += f" @ {self.llm_base_url}"
        status_table.add_row("LLM Provider", llm_status)

        # API Key Status
        if self.llm_api_key:
            masked_key = self.llm_api_key[:8] + "..." + self.llm_api_key[-4:]
            status_table.add_row("API Key", masked_key)
        else:
            status_table.add_row("API Key", "[dim]Not set[/dim]")

        # Database Status
        if self.supabase_url:
            status_table.add_row("Database", f"Supabase: {self.supabase_url[:40]}...")
        elif self.mysql_host:
            status_table.add_row("Database", f"MySQL: {self.mysql_user}@{self.mysql_host}:{self.mysql_port}/{self.mysql_db}")
        elif self.db_uri:
            status_table.add_row("Database", self.db_uri)
        else:
            status_table.add_row("Database", "[yellow]Not connected[/yellow]")

        # Engine Status
        if self.engine:
            tables = len(self.engine.get_tables())
            status_table.add_row("Status", f"[green]Connected ({tables} tables)[/green]")
        else:
            status_table.add_row("Status", "[yellow]Not initialized[/yellow]")

        self.console.print(status_table)

    def configure_llm(self, args: str):
        """Configure LLM provider."""
        parts = args.split()

        if not parts:
            # Show current config
            self.console.print(Panel(
                f"[cyan]Provider:[/cyan] {self.llm_provider}\n"
                f"[cyan]Model:[/cyan] {self.llm_model}\n"
                f"[cyan]URL:[/cyan] {self.llm_base_url}\n"
                f"[cyan]API Key:[/cyan] {'Set' if self.llm_api_key else 'Not set'}",
                title="Current LLM Configuration",
                border_style="blue"
            ))
            return

        provider = parts[0].lower()

        if provider == "ollama":
            self.llm_provider = "ollama"
            self.llm_model = parts[1] if len(parts) > 1 else "llama3.2:3b"
            self.llm_base_url = parts[2] if len(parts) > 2 else "http://localhost:11434"
            self.llm_api_key = None

            self.console.print(Panel(
                f"[green]Provider:[/green] Ollama (Local)\n"
                f"[green]Model:[/green] {self.llm_model}\n"
                f"[green]URL:[/green] {self.llm_base_url}",
                title="LLM Configured",
                border_style="green"
            ))

        elif provider == "anthropic":
            self.llm_provider = "anthropic"
            if len(parts) > 1:
                self.llm_api_key = parts[1]
            else:
                self.llm_api_key = os.environ.get("ANTHROPIC_API_KEY")
                if not self.llm_api_key:
                    self.llm_api_key = Prompt.ask("[cyan]Enter Anthropic API key[/cyan]", password=True)

            self.llm_model = parts[2] if len(parts) > 2 else "claude-sonnet-4-5-20250929"

            self.console.print(Panel(
                f"[green]Provider:[/green] Anthropic (Claude)\n"
                f"[green]Model:[/green] {self.llm_model}\n"
                f"[green]API Key:[/green] {self.llm_api_key[:8]}...{self.llm_api_key[-4:]}",
                title="LLM Configured",
                border_style="green"
            ))

        elif provider == "openai":
            self.llm_provider = "openai"
            if len(parts) > 1:
                self.llm_api_key = parts[1]
            else:
                self.llm_api_key = os.environ.get("OPENAI_API_KEY")
                if not self.llm_api_key:
                    self.llm_api_key = Prompt.ask("[cyan]Enter OpenAI API key[/cyan]", password=True)

            self.llm_model = parts[2] if len(parts) > 2 else "gpt-4o"

            self.console.print(Panel(
                f"[green]Provider:[/green] OpenAI\n"
                f"[green]Model:[/green] {self.llm_model}\n"
                f"[green]API Key:[/green] {self.llm_api_key[:8]}...{self.llm_api_key[-4:]}",
                title="LLM Configured",
                border_style="green"
            ))

        else:
            self.console.print(f"[red]Unknown provider: {provider}[/red]")
            self.console.print("[dim]Available: ollama, anthropic, openai[/dim]")

        # Reset engine if LLM changed
        if self.engine:
            self.console.print("[yellow]LLM changed. Run /db to reconnect.[/yellow]")
            self.engine = None

    def parse_db_path(self, path: str) -> str:
        """Parse database path and convert to URI if needed."""
        path = path.strip()

        # Already a URI
        if path.startswith("sqlite:///") or path.startswith("postgresql://") or path.startswith("mysql://"):
            return path

        # PostgreSQL shorthand
        if path.startswith("postgres://"):
            return path.replace("postgres://", "postgresql://")

        # File path - convert to SQLite URI
        file_path = Path(path).expanduser().resolve()

        if file_path.suffix in [".sqlite", ".sqlite3", ".db"]:
            return f"sqlite:///{file_path}"

        # Check if file exists
        if file_path.exists():
            return f"sqlite:///{file_path}"

        # Assume it's a SQLite path
        return f"sqlite:///{file_path}"

    def connect_database(self, path_or_uri: str = None):
        """Connect to a database."""
        if not path_or_uri:
            # Show current connection
            if self.db_uri:
                self.console.print(Panel(
                    f"[cyan]URI:[/cyan] {self.db_uri}\n"
                    f"[cyan]Status:[/cyan] {'Connected' if self.engine else 'Not initialized'}",
                    title="Current Database",
                    border_style="blue"
                ))
            else:
                self.console.print("[yellow]No database connected.[/yellow]")
                self.console.print("\n[bold]Usage:[/bold]")
                self.console.print("  /db /path/to/database.sqlite")
                self.console.print("  /db sqlite:///path/to/database.sqlite")
                self.console.print("  /db postgresql://user:pass@localhost:5432/dbname")
            return

        # Parse the path
        self.db_uri = self.parse_db_path(path_or_uri)

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
        ) as progress:
            task = progress.add_task("Connecting to database...", total=None)

            try:
                # Build engine kwargs
                engine_kwargs = {
                    "db_uri": self.db_uri,
                    "llm_provider": self.llm_provider,
                    "llm_model": self.llm_model,
                    "output_dir": "./qasql_output"
                }

                if self.llm_provider == "ollama":
                    engine_kwargs["llm_base_url"] = self.llm_base_url

                # Set API key in environment if needed
                if self.llm_api_key:
                    if self.llm_provider == "anthropic":
                        os.environ["ANTHROPIC_API_KEY"] = self.llm_api_key
                    elif self.llm_provider == "openai":
                        os.environ["OPENAI_API_KEY"] = self.llm_api_key

                self.engine = QASQLEngine(**engine_kwargs)

                progress.update(task, description="Extracting schema...")
                result = self.engine.setup()

                if result.success:
                    progress.update(task, description="Connected!")
                    time.sleep(0.3)

                    # Determine database type for display
                    if "postgresql" in self.db_uri or "postgres" in self.db_uri:
                        db_type_display = "PostgreSQL"
                    elif "mysql" in self.db_uri:
                        db_type_display = "MySQL"
                    elif "sqlite" in self.db_uri or self.db_uri.endswith((".sqlite", ".db")):
                        db_type_display = "SQLite"
                    else:
                        db_type_display = "SQLite"

                    self.console.print(Panel(
                        f"[green]Type:[/green] {db_type_display}\n"
                        f"[green]Database:[/green] {result.database_name}\n"
                        f"[green]Tables:[/green] {result.tables_found}\n"
                        f"[green]LLM:[/green] {self.llm_provider} / {self.llm_model}\n"
                        f"[green]Cache:[/green] {result.schema_path}",
                        title="Connected Successfully",
                        border_style="green"
                    ))
                    return True
                else:
                    self.console.print(f"[red]Error:[/red] {result.errors}")
                    return False

            except Exception as e:
                self.console.print(f"[red]Connection failed:[/red] {e}")
                return False

    def connect_supabase(self, args: str = None):
        """Connect to Supabase database."""
        parts = args.split() if args else []

        # Get credentials from args or environment
        if len(parts) >= 2:
            self.supabase_url = parts[0]
            self.supabase_key = parts[1]
        else:
            self.supabase_url = os.environ.get("SUPABASE_URL")
            self.supabase_key = os.environ.get("SUPABASE_KEY")

        if not self.supabase_url or not self.supabase_key:
            self.console.print("[red]Supabase credentials not found.[/red]")
            self.console.print("\n[bold]Options:[/bold]")
            self.console.print("  1. Set environment variables:")
            self.console.print("     export SUPABASE_URL='https://xxx.supabase.co'")
            self.console.print("     export SUPABASE_KEY='your-key'")
            self.console.print("\n  2. Pass credentials directly:")
            self.console.print("     /supabase https://xxx.supabase.co your-key")
            return False

        self.db_type = "supabase"

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
        ) as progress:
            task = progress.add_task("Connecting to Supabase...", total=None)

            try:
                # Build engine kwargs
                engine_kwargs = {
                    "supabase_url": self.supabase_url,
                    "supabase_key": self.supabase_key,
                    "llm_provider": self.llm_provider,
                    "llm_model": self.llm_model,
                    "output_dir": "./qasql_output"
                }

                if self.llm_provider == "ollama":
                    engine_kwargs["llm_base_url"] = self.llm_base_url

                # Set API key in environment if needed
                if self.llm_api_key:
                    if self.llm_provider == "anthropic":
                        os.environ["ANTHROPIC_API_KEY"] = self.llm_api_key
                    elif self.llm_provider == "openai":
                        os.environ["OPENAI_API_KEY"] = self.llm_api_key

                self.engine = QASQLEngine(**engine_kwargs)

                progress.update(task, description="Extracting schema...")
                result = self.engine.setup()

                if result.success:
                    progress.update(task, description="Connected!")
                    time.sleep(0.3)

                    # Mask the key for display
                    masked_key = self.supabase_key[:15] + "..." if len(self.supabase_key) > 15 else "***"

                    self.console.print(Panel(
                        f"[green]Type:[/green] Supabase\n"
                        f"[green]URL:[/green] {self.supabase_url}\n"
                        f"[green]Key:[/green] {masked_key}\n"
                        f"[green]Tables:[/green] {result.tables_found}\n"
                        f"[green]LLM:[/green] {self.llm_provider} / {self.llm_model}",
                        title="Connected to Supabase",
                        border_style="green"
                    ))

                    if result.tables_found == 0:
                        self.console.print("\n[yellow]No tables found![/yellow]")
                        self.console.print("[dim]Make sure you created the get_tables function in Supabase SQL Editor:[/dim]")
                        self.console.print("""
[cyan]CREATE OR REPLACE FUNCTION get_tables(schema_name text DEFAULT 'public')
RETURNS TABLE(table_name text)
LANGUAGE sql SECURITY DEFINER AS $$
  SELECT t.table_name::text
  FROM information_schema.tables t
  WHERE t.table_schema = schema_name
    AND t.table_type = 'BASE TABLE'
  ORDER BY t.table_name;
$$;[/cyan]
""")
                    return True
                else:
                    self.console.print(f"[red]Error:[/red] {result.errors}")
                    return False

            except Exception as e:
                self.console.print(f"[red]Connection failed:[/red] {e}")
                return False

    def connect_mysql(self, args: str = None):
        """Connect to MySQL database."""
        parts = args.split() if args else []

        if len(parts) >= 4:
            host_port = parts[0]
            self.mysql_db = parts[1]
            self.mysql_user = parts[2]
            self.mysql_password = parts[3]
            if ":" in host_port:
                self.mysql_host, port_str = host_port.split(":", 1)
                self.mysql_port = int(port_str)
            else:
                self.mysql_host = host_port
                self.mysql_port = 3306
        else:
            self.mysql_host = os.environ.get("MYSQL_HOST", "localhost")
            port_env = os.environ.get("MYSQL_PORT", "3306")
            self.mysql_port = int(port_env)
            self.mysql_db = os.environ.get("MYSQL_DATABASE") or os.environ.get("MYSQL_DB")
            self.mysql_user = os.environ.get("MYSQL_USER")
            self.mysql_password = os.environ.get("MYSQL_PASSWORD")

        if not all([self.mysql_host, self.mysql_db, self.mysql_user, self.mysql_password is not None]):
            self.console.print("[red]MySQL credentials not found.[/red]")
            self.console.print("\n[bold]Options:[/bold]")
            self.console.print("  1. Set environment variables:")
            self.console.print("     export MYSQL_HOST='localhost'")
            self.console.print("     export MYSQL_DATABASE='mydb'")
            self.console.print("     export MYSQL_USER='user'")
            self.console.print("     export MYSQL_PASSWORD='password'")
            self.console.print("\n  2. Pass credentials directly:")
            self.console.print("     /mysql localhost mydb user password")
            self.console.print("     /mysql localhost:3306 mydb user password")
            self.console.print("\n  3. Use a URI with /db:")
            self.console.print("     /db mysql://user:password@localhost:3306/mydb")
            return False

        self.db_type = "mysql"
        mysql_uri = f"mysql://{self.mysql_user}:{self.mysql_password}@{self.mysql_host}:{self.mysql_port}/{self.mysql_db}"

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
        ) as progress:
            task = progress.add_task("Connecting to MySQL...", total=None)

            try:
                engine_kwargs = {
                    "db_uri": mysql_uri,
                    "llm_provider": self.llm_provider,
                    "llm_model": self.llm_model,
                    "output_dir": "./qasql_output"
                }

                if self.llm_provider == "ollama":
                    engine_kwargs["llm_base_url"] = self.llm_base_url

                if self.llm_api_key:
                    if self.llm_provider == "anthropic":
                        os.environ["ANTHROPIC_API_KEY"] = self.llm_api_key
                    elif self.llm_provider == "openai":
                        os.environ["OPENAI_API_KEY"] = self.llm_api_key

                self.engine = QASQLEngine(**engine_kwargs)

                progress.update(task, description="Extracting schema...")
                result = self.engine.setup()

                if result.success:
                    progress.update(task, description="Connected!")
                    time.sleep(0.3)

                    self.console.print(Panel(
                        f"[green]Type:[/green] MySQL\n"
                        f"[green]Host:[/green] {self.mysql_host}:{self.mysql_port}\n"
                        f"[green]Database:[/green] {self.mysql_db}\n"
                        f"[green]User:[/green] {self.mysql_user}\n"
                        f"[green]Tables:[/green] {result.tables_found}\n"
                        f"[green]LLM:[/green] {self.llm_provider} / {self.llm_model}",
                        title="Connected to MySQL",
                        border_style="green"
                    ))
                    return True
                else:
                    self.console.print(f"[red]Error:[/red] {result.errors}")
                    return False

            except Exception as e:
                self.console.print(f"[red]Connection failed:[/red] {e}")
                return False

    def show_tables(self):
        """Show all tables in the database."""
        if not self.engine:
            self.console.print("[yellow]Not connected. Use /db <path> first.[/yellow]")
            return

        tables = self.engine.get_tables()
        schema = self.engine.get_schema()

        table_view = Table(title="Database Tables", box=box.ROUNDED)
        table_view.add_column("Table", style="cyan")
        table_view.add_column("Columns", justify="right", style="green")
        table_view.add_column("Rows", justify="right", style="yellow")

        for table_name in tables:
            info = schema[table_name]
            cols = len(info.get("columns", []))
            rows = info.get("row_count", "?")
            table_view.add_row(table_name, str(cols), str(rows))

        self.console.print(table_view)

    def show_schema(self, table_name: str):
        """Show schema for a specific table."""
        if not self.engine:
            self.console.print("[yellow]Not connected. Use /db <path> first.[/yellow]")
            return

        schema = self.engine.get_schema()
        if table_name not in schema:
            self.console.print(f"[red]Table '{table_name}' not found.[/red]")
            available = ", ".join(schema.keys())
            self.console.print(f"[dim]Available: {available}[/dim]")
            return

        table_info = schema[table_name]
        columns = table_info.get("columns", [])

        col_table = Table(title=f"Schema: {table_name}", box=box.ROUNDED)
        col_table.add_column("Column", style="cyan")
        col_table.add_column("Type", style="yellow")
        col_table.add_column("PK", justify="center")

        for col in columns:
            pk = "✓" if col.get("primary_key") else ""
            col_table.add_row(col["name"], col.get("type", "?"), pk)

        self.console.print(col_table)

    def execute_query(self, question: str, hint: str = None):
        """Execute a natural language query."""
        if not self.engine:
            self.console.print("[yellow]Not connected. Use /db <path> first.[/yellow]")
            return

        self.console.print()

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
        ) as progress:
            task = progress.add_task("Analyzing query...", total=None)

            try:
                progress.update(task, description="Running schema agent...")
                start = time.time()

                result = self.engine.query(question=question, hint=hint)

                elapsed = time.time() - start
                progress.update(task, description=f"Completed in {elapsed:.1f}s")
                time.sleep(0.2)

            except Exception as e:
                self.console.print(f"[red]Error:[/red] {e}")
                return

        # Display result
        self.display_result(result, question)

        # Save to history
        self.history.append({
            "question": question,
            "hint": hint,
            "sql": result.sql,
            "confidence": result.confidence
        })

    def display_result(self, result: QueryResult, question: str):
        """Display query result with formatting."""
        # Question
        self.console.print(Panel(
            question,
            title="Question",
            border_style="blue"
        ))

        # SQL
        if result.sql:
            sql_syntax = Syntax(result.sql, "sql", theme="monokai", line_numbers=False)
            self.console.print(Panel(
                sql_syntax,
                title=f"Generated SQL (confidence: {result.confidence:.0%})",
                border_style="green" if result.confidence >= 0.7 else "yellow"
            ))

            # Candidates info
            self.console.print(
                f"[dim]Candidates: {result.successful_candidates}/{result.total_candidates} successful[/dim]"
            )

            # Try to execute
            if Confirm.ask("\n[cyan]Execute this SQL?[/cyan]", default=True):
                self.execute_sql(result.sql)
        else:
            self.console.print("[red]Failed to generate SQL.[/red]")
            if result.reasoning:
                self.console.print(f"[dim]Reason: {result.reasoning}[/dim]")

    def execute_sql(self, sql: str):
        """Execute SQL and display results."""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
        ) as progress:
            task = progress.add_task("Executing...", total=None)

            try:
                rows, columns = self.engine.execute_sql(sql)
                progress.update(task, description="Done")
                time.sleep(0.1)

            except Exception as e:
                self.console.print(f"[red]Execution error:[/red] {e}")
                return

        # Display results
        if not rows:
            self.console.print("[yellow]No results returned.[/yellow]")
            return

        result_table = Table(
            title=f"Results ({len(rows)} rows)",
            box=box.ROUNDED,
            show_lines=True
        )

        for col in columns:
            result_table.add_column(col, style="cyan")

        # Show first 20 rows
        for row in rows[:20]:
            result_table.add_row(*[str(v) for v in row])

        self.console.print(result_table)

        if len(rows) > 20:
            self.console.print(f"[dim]... and {len(rows) - 20} more rows[/dim]")

    def _is_general_question(self, text: str) -> bool:
        """
        Use LLM to classify if the question is database-related or general chitchat.
        Returns True if NOT related to database/SQL queries.
        """
        if not self.engine:
            return False  # Can't check without LLM, assume it's a query

        # Get table names for context
        try:
            tables = self.engine.get_tables()
            table_context = f"Available tables: {', '.join(tables)}" if tables else ""
        except:
            table_context = ""

        prompt = f"""You are a query classifier for a Text-to-SQL system. The user is connected to a database.

{table_context}

Classify the following user input into one of two categories:
- DATABASE: Any question asking about data, records, counts, statistics, inventory, stock, products, or anything that could potentially be answered by querying a database. This includes questions in ANY language (Korean, Chinese, Japanese, etc.).
- GENERAL: ONLY simple greetings (hi, hello, bye), thank you messages, or questions clearly unrelated to data (e.g., "what is the weather", "tell me a joke", "how are you").

IMPORTANT: When in doubt, ALWAYS classify as DATABASE. The user is connected to a database, so assume they want to query it.

User input: "{text}"

Reply with ONLY one word: DATABASE or GENERAL"""

        try:
            response = self.engine.llm_client.complete(prompt=prompt, max_tokens=10)
            return "GENERAL" in response.upper()
        except:
            return False  # If LLM fails, assume it's a database query

    def show_history(self):
        """Show query history."""
        if not self.history:
            self.console.print("[yellow]No query history yet.[/yellow]")
            return

        history_table = Table(title="Query History", box=box.ROUNDED)
        history_table.add_column("#", style="dim")
        history_table.add_column("Question", style="white")
        history_table.add_column("Confidence", justify="right")

        for i, entry in enumerate(self.history, 1):
            conf = f"{entry['confidence']:.0%}"
            history_table.add_row(str(i), entry["question"][:50], conf)

        self.console.print(history_table)

    def run(
        self,
        db_uri: str = None,
        model: str = None,
        provider: str = None,
        api_key: str = None,
        base_url: str = None,
        supabase: bool = False,
        mysql: bool = False
    ):
        """Main loop."""
        self.print_banner()

        # Apply initial configuration
        if provider:
            self.llm_provider = provider
        if model:
            self.llm_model = model
        if api_key:
            self.llm_api_key = api_key
        if base_url:
            self.llm_base_url = base_url

        # Auto-connect if db_uri or supabase or mysql provided
        if supabase:
            self.connect_supabase()
        elif mysql:
            self.connect_mysql()
        elif db_uri:
            self.connect_database(db_uri)

        current_hint = None

        while True:
            try:
                # Prompt
                if self.engine:
                    prompt_text = "[bold green]qasql>[/bold green] "
                else:
                    prompt_text = "[bold yellow]qasql (not connected)>[/bold yellow] "

                user_input = Prompt.ask(prompt_text).strip()

                if not user_input:
                    continue

                # Commands
                if user_input.startswith("/"):
                    parts = user_input.split(maxsplit=1)
                    cmd = parts[0].lower()
                    arg = parts[1] if len(parts) > 1 else ""

                    if cmd == "/quit" or cmd == "/exit" or cmd == "/q":
                        self.console.print("[cyan]Goodbye![/cyan]")
                        break

                    elif cmd == "/help" or cmd == "/?":
                        self.print_help()

                    elif cmd == "/clear" or cmd == "/cls":
                        self.console.clear()
                        self.print_banner()

                    elif cmd == "/status":
                        self.show_status()

                    elif cmd == "/llm":
                        self.configure_llm(arg)

                    elif cmd == "/db" or cmd == "/connect":
                        self.connect_database(arg if arg else None)

                    elif cmd == "/supabase":
                        self.connect_supabase(arg if arg else None)

                    elif cmd == "/mysql":
                        self.connect_mysql(arg if arg else None)

                    elif cmd == "/tables":
                        self.show_tables()

                    elif cmd == "/schema":
                        if not arg:
                            self.console.print("[yellow]Usage: /schema <table_name>[/yellow]")
                        else:
                            self.show_schema(arg)

                    elif cmd == "/hint":
                        if arg:
                            current_hint = arg
                            self.console.print(f"[green]Hint set:[/green] {current_hint}")
                        else:
                            current_hint = None
                            self.console.print("[green]Hint cleared.[/green]")

                    elif cmd == "/sql":
                        if not arg:
                            self.console.print("[yellow]Usage: /sql <query>[/yellow]")
                        elif self.engine:
                            self.execute_sql(arg)
                        else:
                            self.console.print("[yellow]Not connected.[/yellow]")

                    elif cmd == "/history":
                        self.show_history()

                    else:
                        self.console.print(f"[red]Unknown command: {cmd}[/red]")
                        self.console.print("[dim]Type /help for available commands.[/dim]")

                else:
                    # Check if it's a general question (not database-related)
                    if self._is_general_question(user_input):
                        self.console.print(Panel(
                            "[yellow]I'm QA-SQL, a Text-to-SQL assistant.[/yellow]\n\n"
                            "I can only help with:\n"
                            "  - Converting natural language to SQL queries\n"
                            "  - Database schema exploration\n"
                            "  - Executing SQL on your connected database\n\n"
                            "[dim]Try asking a question about your data, like:[/dim]\n"
                            "  • How many records are in the table?\n"
                            "  • Show me the top 10 customers by revenue\n"
                            "  • What is the average order value?\n\n"
                            "Type [bold]/help[/bold] for available commands.",
                            title="Not a Database Question",
                            border_style="yellow"
                        ))
                    else:
                        # Natural language query
                        self.execute_query(user_input, hint=current_hint)
                        current_hint = None  # Clear hint after use

            except KeyboardInterrupt:
                self.console.print("\n[cyan]Use /quit to exit.[/cyan]")
            except EOFError:
                break


def main():
    """Entry point for TUI."""
    import argparse

    parser = argparse.ArgumentParser(
        description="QA-SQL Terminal UI - Interactive Text-to-SQL",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Start with local Ollama
  python -m qasql.tui

  # Connect to database on startup
  python -m qasql.tui --db ./database.sqlite
  python -m qasql.tui --db sqlite:///path/to/db.sqlite
  python -m qasql.tui --db postgresql://user:pass@localhost/mydb

  # Connect to Supabase (requires SUPABASE_URL and SUPABASE_KEY env vars)
  python -m qasql.tui --supabase

  # Connect to MySQL (requires MYSQL_HOST, MYSQL_DATABASE, MYSQL_USER, MYSQL_PASSWORD env vars)
  python -m qasql.tui --mysql

  # Use different LLM providers
  python -m qasql.tui --provider ollama --model llama3.2:3b
  python -m qasql.tui --provider anthropic --api-key sk-ant-xxx
  python -m qasql.tui --provider openai --api-key sk-xxx

  # Use Ollama on remote server
  python -m qasql.tui --provider ollama --base-url http://192.168.1.100:11434
        """
    )

    # Database options
    parser.add_argument(
        "--db", "-d",
        dest="db_uri",
        help="Database path or URI (SQLite file path or full URI)"
    )
    parser.add_argument(
        "--supabase", "-s",
        action="store_true",
        help="Connect to Supabase (uses SUPABASE_URL and SUPABASE_KEY env vars)"
    )
    parser.add_argument(
        "--mysql",
        action="store_true",
        help="Connect to MySQL (uses MYSQL_HOST, MYSQL_DATABASE, MYSQL_USER, MYSQL_PASSWORD env vars)"
    )

    # LLM options
    parser.add_argument(
        "--provider", "-p",
        choices=["ollama", "anthropic", "openai"],
        default="ollama",
        help="LLM provider (default: ollama)"
    )
    parser.add_argument(
        "--model", "-m",
        help="LLM model name (default: llama3.2:3b for ollama)"
    )
    parser.add_argument(
        "--api-key", "-k",
        dest="api_key",
        help="API key for Anthropic or OpenAI"
    )
    parser.add_argument(
        "--base-url", "-u",
        dest="base_url",
        help="Base URL for Ollama (default: http://localhost:11434)"
    )

    args = parser.parse_args()

    # Set default model based on provider
    if not args.model:
        if args.provider == "ollama":
            args.model = "llama3.2:3b"
        elif args.provider == "anthropic":
            args.model = "claude-sonnet-4-5-20250929"
        elif args.provider == "openai":
            args.model = "gpt-4o"

    tui = TerminalUI()
    tui.run(
        db_uri=args.db_uri,
        model=args.model,
        provider=args.provider,
        api_key=args.api_key,
        base_url=args.base_url,
        supabase=args.supabase,
        mysql=args.mysql
    )


if __name__ == "__main__":
    main()
