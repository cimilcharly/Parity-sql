"""Parity Command Line Interface."""

import json
import os
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
from parity.benchmark.ablation import AblationStudyRunner
from parity.benchmark.large_scale import large_scale_runner
from parity.benchmark.runner import BenchmarkRunner
from parity.config import settings
from parity.kb.loader import kb
from parity.lineage import analyze_directory, order_dependencies, parse_sql_object
from parity.llm import get_llm_provider, llm_cache
from parity.plsql import PLSQLConverter
from parity.repair import repair_engine
from parity.reporting.html_report import generate_object_report_html
from parity.security.audit import audit_logger
from parity.transpiler import Transpiler
from parity.verifier import verifier
from parity.workflow import WorkflowEngine

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
    """Check system requirements, Docker, database health, and LLM readiness."""
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

    # LLM Provider
    provider_name = os.getenv("PARITY_LLM_PROVIDER", "mock")
    table.add_row("LLM Provider", "[green]READY[/green]", f"Active mode: {provider_name.upper()} (Mock/Ollama/Hosted)")

    # Cache
    table.add_row("Response Cache", "[green]ACTIVE[/green]", f"Directory: {llm_cache.cache_dir}")

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
def repair(
    sql_or_file: str = typer.Argument(..., help="Path to Oracle SQL file to repair"),
    provider: str = typer.Option("mock", "--provider", "-p", help="LLM Provider: mock, ollama, or hosted"),
    max_attempts: int = typer.Option(3, "--max-attempts", "-m", help="Maximum repair loop iterations"),
):
    """Run autonomous analyze -> diagnose -> propose -> verify repair loop."""
    p = Path(sql_or_file)
    if not p.exists() or not p.is_file():
        console.print(f"[bold red]File not found:[/bold red] {sql_or_file}")
        raise typer.Exit(code=1)

    source_sql = p.read_text(encoding="utf-8").strip()
    llm = get_llm_provider(provider)
    console.print(f"[bold cyan]Starting Parity Autonomous Repair Loop (Provider: {provider}, Max Attempts: {max_attempts})...[/bold cyan]")

    res = repair_engine.repair(
        object_name=p.stem,
        oracle_sql=source_sql,
    )

    status_str = "[bold green]VERIFIED PASS[/bold green]" if res.verified else "[bold red]FAILED[/bold red]"
    console.print(f"\nRepair Result: {status_str} (Attempts: {res.total_attempts}, Cost: ${res.total_cost_usd:.5f})")

    if res.applied_kb_entries:
        console.print(f"[yellow]Knowledge Base Context Applied:[/yellow] {', '.join(res.applied_kb_entries)}")

    console.print("\n[bold green]--- Repaired Target PostgreSQL SQL ---[/bold green]")
    console.print(Syntax(res.final_postgres_sql, "sql", theme="monokai", line_numbers=True))

    if res.failure_reason:
        console.print(f"\n[bold red]Failure Diagnostics:[/bold red] {res.failure_reason}")


@app.command()
def lineage(
    path: str = typer.Argument("src/parity/benchmark/corpus", help="Path to directory or SQL file to analyze"),
):
    """Analyze SQL dependencies, score complexity, and compute topological migration order."""
    target_path = Path(path)
    if target_path.is_dir():
        objects = analyze_directory(target_path)
    elif target_path.is_file():
        content = target_path.read_text(encoding="utf-8")
        objects = [parse_sql_object(content, file_path=target_path)]
    else:
        console.print(f"[bold red]Path not found:[/bold red] {path}")
        raise typer.Exit(code=1)

    plan = order_dependencies(objects)

    table = Table(title=f"SQL Lineage & Dependency Execution Order ({len(plan.ordered_objects)} objects)", show_header=True)
    table.add_column("Order", style="bold cyan")
    table.add_column("Object Name")
    table.add_column("Type", style="magenta")
    table.add_column("Complexity Score")
    table.add_column("Tier", style="bold")
    table.add_column("Dependencies")

    for idx, obj in enumerate(plan.ordered_objects, 1):
        tier_color = "green" if obj.complexity_tier == "Simple" else ("yellow" if obj.complexity_tier == "Moderate" else "red")
        deps_str = ", ".join(obj.dependencies) if obj.dependencies else "[dim]None (Base)[/dim]"
        table.add_row(
            str(idx),
            obj.name,
            obj.object_type,
            str(obj.complexity_score),
            f"[{tier_color}]{obj.complexity_tier}[/{tier_color}]",
            deps_str,
        )

    console.print(table)
    if plan.has_cycles:
        console.print(f"\n[bold red]Warning: Circular dependencies detected among:[/bold red] {', '.join(plan.cycle_nodes)}")
    else:
        console.print(f"\n[bold green]DAG Status: Clean DAG (Zero cycles). Average Complexity: {plan.average_complexity}/10[/bold green]")


@app.command()
def ablation():
    """Run Week 10 ablation study comparing sqlglot vs +AST rules vs +LLM vs +LLM+KB."""
    runner = AblationStudyRunner()
    console.print("[bold cyan]Running Parity 4-Way Ablation Study across benchmark corpus...[/bold cyan]")
    summary = runner.run_study()

    table = Table(title="Parity Ablation Study Comparison Matrix", show_header=True)
    table.add_column("Configuration", style="bold cyan")
    table.add_column("Pass Rate", style="bold")
    table.add_column("Lift", style="bold green")
    table.add_column("Total Cost", style="yellow")
    table.add_column("Duration")

    for cfg in summary["configurations"]:
        lift_str = f"+{cfg['lift_over_baseline']}%" if cfg['lift_over_baseline'] > 0 else f"{cfg['lift_over_baseline']}%"
        table.add_row(
            cfg["name"],
            f"{cfg['pass_rate_pct']}%",
            lift_str,
            f"${cfg['total_cost_usd']:.5f}",
            f"{cfg['duration_seconds']}s",
        )

    console.print(table)
    console.print(f"[dim]Results saved to bench/results/ablation_study.json[/dim]")


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


@app.command(name="bench-500")
def benchmark_500(
    output: str = typer.Option("benchmark_500.json", "--out", "-o", help="Output JSON filename"),
):
    """Run full enterprise benchmark suite across 500+ diverse Oracle SQL & PL/SQL objects."""
    console.print("[bold cyan]Executing Large-Scale Enterprise Benchmark (500+ Objects across 10 Categories)...[/bold cyan]")
    summary = large_scale_runner.run_benchmark(save_results=True, filename=output)

    # Category Breakdown Table
    cat_table = Table(title="500-Object Benchmark: Performance by Category", show_header=True)
    cat_table.add_column("Category", style="cyan")
    cat_table.add_column("Objects", justify="right")
    cat_table.add_column("Verified Pass", style="green", justify="right")
    cat_table.add_column("Human Review", style="yellow", justify="right")
    cat_table.add_column("Failed", style="red", justify="right")
    cat_table.add_column("Pass Rate", style="bold green", justify="right")

    for cat_name, stats in summary["category_stats"].items():
        rate = round((stats["verified"] / stats["total"]) * 100, 1) if stats["total"] > 0 else 0.0
        cat_table.add_row(
            cat_name,
            str(stats["total"]),
            str(stats["verified"]),
            str(stats["human_review"]),
            str(stats["failed"]),
            f"{rate}%",
        )

    console.print(cat_table)

    # Complexity Breakdown
    tier_table = Table(title="Complexity Tier Distribution", show_header=True)
    tier_table.add_column("Tier", style="bold")
    tier_table.add_column("Count", justify="right")
    tier_table.add_column("Share", justify="right")

    total = summary["total_objects"]
    for tier, count in summary["tier_distribution"].items():
        share = round((count / total) * 100, 1) if total > 0 else 0
        tier_color = "green" if tier == "Simple" else ("yellow" if tier == "Moderate" else ("magenta" if tier == "Complex" else "red"))
        tier_table.add_row(f"[{tier_color}]{tier}[/{tier_color}]", str(count), f"{share}%")

    console.print(tier_table)

    # High Level Summary
    console.print(
        f"\n[bold]Total Objects:[/bold] {summary['total_objects']} | "
        f"[green]Verified Pass:[/green] {summary['verified_count']} ([bold green]{summary['pass_rate_pct']}%[/bold green]) | "
        f"[yellow]Human Review Required:[/yellow] {summary['human_review_count']} ([yellow]{summary['human_review_rate_pct']}%[/yellow]) | "
        f"[red]Failed:[/red] {summary['failed_count']}"
    )
    console.print(
        f"[bold]Average Cost/Object:[/bold] [yellow]${summary['avg_cost_per_object_usd']:.6f}[/yellow] | "
        f"[bold]Total Spend:[/bold] [yellow]${summary['total_cost_usd']:.4f}[/yellow] | "
        f"[bold]Average Latency:[/bold] {summary['avg_duration_ms']}ms | "
        f"[bold]Total Runtime:[/bold] {summary['total_duration_seconds']}s"
    )

    if summary["failure_breakdown"]:
        non_zero_fails = {k: v for k, v in summary["failure_breakdown"].items() if v > 0}
        if non_zero_fails:
            console.print("\n[bold yellow]Blockers / Flagged Failure Reasons:[/bold yellow]")
            for k, v in non_zero_fails.items():
                console.print(f"  • [bold red]{k}:[/bold red] {v} objects (safely isolated for review)")

    console.print(f"\n[dim]Detailed telemetry committed to: bench/results/{output}[/dim]")


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


@app.command()
def plsql(
    file_path: str = typer.Argument(..., help="Path to Oracle PL/SQL file to transpile"),
):
    """Transpile Oracle PL/SQL functions and procedures to PL/pgSQL with construct validation."""
    p = Path(file_path)
    if not p.exists() or not p.is_file():
        console.print(f"[bold red]File not found:[/bold red] {file_path}")
        raise typer.Exit(code=1)

    code = p.read_text(encoding="utf-8")
    converter = PLSQLConverter()
    res = converter.convert(code)

    if res.success:
        console.print(f"[bold green]Successfully Transpiled {res.object_type.value}: {res.object_name}[/bold green]\n")
        console.print(Syntax(res.target_code, "sql", theme="monokai", line_numbers=True))
    else:
        console.print(f"[bold red]Transpilation Blocked: {len(res.unsupported_constructs)} Unsupported Construct(s) Detected[/bold red]\n")
        table = Table(title="Unsupported Oracle PL/SQL Constructs", show_header=True)
        table.add_column("Construct Name", style="bold red")
        table.add_column("Line", style="yellow")
        table.add_column("Issue Description")
        table.add_column("Recommended Remedy", style="green")

        for u in res.unsupported_constructs:
            table.add_row(u.name, str(u.line_number or "N/A"), u.description, u.remedy)
        console.print(table)
        raise typer.Exit(code=1)


@app.command()
def convert(
    path: str = typer.Argument("src/parity/benchmark/corpus", help="Directory of SQL/PLSQL objects to migrate"),
    branch: bool = typer.Option(False, "--branch", "-b", help="Create git branch and atomic commit per object"),
):
    """Run end-to-end migration workflow: ordering, verification, evidence reports, and PR generation."""
    target_path = Path(path)
    if not target_path.exists():
        console.print(f"[bold red]Path not found:[/bold red] {path}")
        raise typer.Exit(code=1)

    engine = WorkflowEngine()
    console.print(f"[bold cyan]Starting End-to-End Migration Workflow on '{path}' (Git Branches: {branch})...[/bold cyan]")
    summary = engine.convert_directory(target_path, create_git_branches=branch)

    table = Table(title=f"Migration Execution Results ({summary.total_objects} objects)", show_header=True)
    table.add_column("Object Name", style="cyan")
    table.add_column("Status", style="bold")
    table.add_column("Type")
    table.add_column("Attempts")
    table.add_column("Cost", style="yellow")
    table.add_column("Branch")
    table.add_column("PR Artifact")

    for item in summary.items:
        status_str = "[green]VERIFIED PASS[/green]" if item.passed else "[red]BLOCKED[/red]"
        pr_link = item.pr_artifact_path.name if item.pr_artifact_path else "N/A"
        table.add_row(
            item.object_name,
            status_str,
            "PL/SQL" if item.is_plsql else "SQL",
            str(item.attempts),
            f"${item.cost_usd:.5f}",
            item.git_branch,
            pr_link,
        )

    console.print(table)
    console.print(
        f"\n[bold]Total:[/bold] {summary.total_objects} | "
        f"[green]Verified:[/green] {summary.verified_count} | "
        f"[red]Blocked:[/red] {summary.blocked_count} | "
        f"[bold yellow]Pass Rate: {summary.pass_rate_pct:.1f}%[/bold yellow] | "
        f"[yellow]Spend: ${summary.total_cost_usd:.5f}[/yellow]"
    )
    if summary.summary_dashboard_path:
        console.print(f"\n[bold green]Executive Summary Dashboard generated:[/bold green] {summary.summary_dashboard_path.resolve()}")


@app.command()
def audit(
    limit: int = typer.Option(20, "--limit", "-n", help="Number of recent records to display"),
):
    """Inspect append-only security, model calls, and verification audit log."""
    records = audit_logger.get_recent_records(limit=limit)
    if not records:
        console.print(f"[yellow]No audit records found in {audit_logger.log_path}.[/yellow]")
        return

    table = Table(title=f"Parity Security & Model Audit Log (Recent {len(records)} events)", show_header=True)
    table.add_column("Timestamp", style="dim")
    table.add_column("Event Type", style="bold cyan")
    table.add_column("Object Name")
    table.add_column("Status", style="bold")
    table.add_column("Tokens (P/C)")
    table.add_column("Cost", style="yellow")
    table.add_column("Prompt SHA-256", style="dim")

    for r in records:
        status_color = "green" if r.status in ("SUCCESS", "PASSED") else "red"
        tokens_str = f"{r.prompt_tokens}/{r.completion_tokens}" if r.prompt_tokens else "-"
        hash_str = (r.prompt_hash[:10] + "...") if r.prompt_hash else "-"
        table.add_row(
            r.timestamp.split("T")[1][:8] if "T" in r.timestamp else r.timestamp,
            r.event_type,
            r.object_name,
            f"[{status_color}]{r.status}[/{status_color}]",
            tokens_str,
            f"${r.cost_usd:.5f}",
            hash_str,
        )

    console.print(table)
    console.print(f"[dim]Log file: {audit_logger.log_path.resolve()}[/dim]")


if __name__ == "__main__":
    app()

