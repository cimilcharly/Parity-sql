"""Parity Command Line Interface."""

import json
from pathlib import Path
import sys
from typing import Optional

try:
    import typer
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.syntax import Syntax
except ImportError:
    print("Core CLI libraries (typer, rich) are missing. Please install dependencies.")
    sys.exit(1)

from parity import __version__
from parity.benchmark.runner import BenchmarkRunner
from parity.config import settings
from parity.kb.loader import kb
from parity.reporting.html_report import generate_object_report_html
from parity.transpiler import Transpiler
from parity.verifier import verifier

app = typer.Typer(
    name="parity",
    help="Parity: Deterministic-first Oracle to PostgreSQL SQL transpilation & semantic verification.",
    add_completion=False,
)
console = Console()


@app.command()
def version():
    """Display Parity version."""
    console.print(f"[bold cyan]Parity[/bold cyan] version [green]{__version__}[/green]")


@app.command()
def doctor():
    """Check system requirements, Docker, and database health."""
    console.print(Panel.fit("[bold blue]Parity System Doctor[/bold blue]", border_style="blue"))
    table = Table(title="Component Status", show_header=True, header_style="bold magenta")
    table.add_column("Component", style="cyan")
    table.add_column("Status", style="bold")
    table.add_column("Details")

    # Python version
    py_ver = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    py_ok = sys.version_info >= (3, 11)
    table.add_row("Python", "[green]PASS[/green]" if py_ok else "[red]FAIL[/red]", f"Version {py_ver}")

    # sqlglot check
    try:
        import sqlglot
        table.add_row("sqlglot", "[green]PASS[/green]", f"Version {sqlglot.__version__}")
    except ImportError:
        table.add_row("sqlglot", "[red]MISSING[/red]", "Run pip install sqlglot")

    # Database Drivers
    try:
        import oracledb
        table.add_row("oracledb driver", "[green]PASS[/green]", "Thin mode available")
    except ImportError:
        table.add_row("oracledb driver", "[yellow]NOT INSTALLED[/yellow]", "pip install oracledb")

    try:
        import psycopg
        table.add_row("psycopg driver", "[green]PASS[/green]", "PostgreSQL client available (psycopg v3)")
    except ImportError:
        try:
            import psycopg2
            table.add_row("psycopg driver", "[green]PASS[/green]", f"PostgreSQL client available (psycopg2 v{psycopg2.__version__})")
        except ImportError:
            table.add_row("psycopg driver", "[yellow]NOT INSTALLED[/yellow]", "pip install 'psycopg[binary]' or psycopg2-binary")

    # Knowledge Base
    kb_count = len(kb.get_all())
    table.add_row("Knowledge Base", "[green]READY[/green]", f"{kb_count} dialect differences loaded")

    console.print(table)


@app.command()
def transpile(
    sql_or_file: str = typer.Argument(..., help="Path to Oracle SQL file or inline query string"),
    use_rules: bool = typer.Option(True, "--rules/--no-rules", help="Apply Parity custom AST rules"),
):
    """Transpile Oracle SQL into PostgreSQL SQL."""
    p = Path(sql_or_file)
    if p.exists() and p.is_file():
        source_sql = p.read_text(encoding="utf-8").strip()
    else:
        source_sql = sql_or_file.strip()

    engine = Transpiler(use_parity_rules=use_rules)
    result = engine.transpile(source_sql)

    if not result.success:
        console.print(f"[bold red]Transpilation Error:[/bold red] {result.error}")
        raise typer.Exit(code=1)

    console.print("\n[bold cyan]--- Source Oracle SQL ---[/bold cyan]")
    console.print(Syntax(source_sql, "sql", theme="monokai", line_numbers=True))

    console.print("\n[bold green]--- Target PostgreSQL SQL ---[/bold green]")
    console.print(Syntax(result.target_sql, "sql", theme="monokai", line_numbers=True))

    if result.applied_rules:
        console.print(f"\n[bold yellow]Applied Rules:[/bold yellow] {', '.join(result.applied_rules)}")


@app.command()
def verify(
    sql_or_file: str = typer.Argument(..., help="Path to Oracle SQL file"),
    report_html: bool = typer.Option(True, "--html/--no-html", help="Generate HTML evidence report"),
):
    """Run all 5 verification layers on an Oracle query against PostgreSQL."""
    p = Path(sql_or_file)
    if not p.exists() or not p.is_file():
        console.print(f"[bold red]File not found:[/bold red] {sql_or_file}")
        raise typer.Exit(code=1)

    source_sql = p.read_text(encoding="utf-8").strip()
    engine = Transpiler(use_parity_rules=True)
    t_res = engine.transpile(source_sql)

    if not t_res.success:
        console.print(f"[bold red]Transpilation Error:[/bold red] {t_res.error}")
        raise typer.Exit(code=1)

    report = verifier.verify_query(
        query_name=p.stem,
        oracle_sql=source_sql,
        postgres_sql=t_res.target_sql,
    )

    table = Table(title=f"Verification Results: {p.stem}", show_header=True)
    table.add_column("Layer", style="cyan")
    table.add_column("Name")
    table.add_column("Status", style="bold")
    table.add_column("Diagnostics")

    for l in report.layers:
        status_styled = (
            f"[green]{l.status.value}[/green]"
            if l.passed
            else f"[red]{l.status.value}[/red]"
        )
        table.add_row(f"L{l.layer_number}", l.name, status_styled, l.message)

    console.print(table)

    if report.error:
        console.print(f"\n[bold yellow]Notice:[/bold yellow] {report.error}")
        console.print("[dim]Tip: To run live multi-layer verification against Oracle & PostgreSQL, launch containers with 'docker compose up -d'.[/dim]\n")

    if report_html:
        out_path = Path("reports") / "output" / f"{p.stem}_evidence.html"
        generate_object_report_html(report, out_path)
        console.print(f"[green]Evidence report generated:[/green] {out_path.resolve()}")


@app.command()
def bench(
    mode: str = typer.Option("parity_rules", "--mode", "-m", help="Mode: parity_rules or sqlglot_only"),
    output: str = typer.Option("baseline.json", "--out", "-o", help="Output JSON filename"),
):
    """Run baseline benchmark across corpus and calculate pass rate."""
    runner = BenchmarkRunner()
    console.print(f"[bold cyan]Running Parity Benchmark suite (Mode: {mode})...[/bold cyan]")
    summary = runner.run_benchmark(mode=mode, filename=output)

    table = Table(title="Corpus Benchmark Summary", show_header=True)
    table.add_column("Query Object", style="cyan")
    table.add_column("Transpile", style="bold")
    table.add_column("Status", style="bold")
    table.add_column("Details")

    for item in summary.get("results", []):
        trans_ok = "[green]OK[/green]" if item.get("transpile_success") else "[red]FAIL[/red]"
        status = "[green]PASS[/green]" if item.get("overall_passed") else "[red]FAIL[/red]"
        table.add_row(item["name"], trans_ok, status, item.get("error") or "Clean")

    console.print(table)
    console.print(
        f"\n[bold]Total:[/bold] {summary['total_queries']} | "
        f"[green]Passed:[/green] {summary['passed']} | "
        f"[red]Failed:[/red] {summary['failed']} | "
        f"[bold yellow]Pass Rate: {summary['pass_rate_pct']}%[/bold yellow]"
    )


@app.command(name="kb")
def knowledge_base(
    query: Optional[str] = typer.Argument(None, help="Search term in knowledge base"),
):
    """Query or browse the Oracle -> PostgreSQL semantic differences catalog."""
    entries = kb.search(query) if query else kb.get_all()

    table = Table(title=f"Knowledge Base ({len(entries)} entries)", show_header=True)
    table.add_column("ID", style="bold cyan")
    table.add_column("Severity", style="magenta")
    table.add_column("Title")
    table.add_column("Oracle vs Postgres Summary")

    for e in entries:
        sev_color = "red" if e.severity == "HIGH" else ("yellow" if e.severity == "MEDIUM" else "green")
        table.add_row(
            e.id,
            f"[{sev_color}]{e.severity}[/{sev_color}]",
            e.title,
            f"Oracle: {e.oracle_behavior[:50]}... -> Postgres: {e.postgres_behavior[:50]}...",
        )

    console.print(table)


if __name__ == "__main__":
    app()
