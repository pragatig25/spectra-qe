from __future__ import annotations

import asyncio
import time
from pathlib import Path

import click
import structlog

from qe_platform.config import Settings

structlog.configure(
    processors=[
        structlog.stdlib.add_log_level,
        structlog.dev.ConsoleRenderer(),
    ],
)

logger = structlog.get_logger()


@click.group()
@click.option("--env-file", default=".env", help="Path to .env file")
@click.pass_context
def cli(ctx: click.Context, env_file: str) -> None:
    """QE Intelligent Test Generation Platform."""
    ctx.ensure_object(dict)
    ctx.obj["settings"] = Settings(_env_file=env_file)


@cli.command()
@click.argument("spec_path", type=click.Path(exists=True))
@click.option("--format", "fmt", type=click.Choice(["json", "yaml"]), default="json")
@click.pass_context
def parse(ctx: click.Context, spec_path: str, fmt: str) -> None:
    """Parse an OpenAPI spec and display endpoints."""
    from qe_platform.ingestion.spec_parser import parse_openapi

    spec = parse_openapi(spec_path)
    click.echo(f"Parsed: {spec.title} v{spec.version}")
    click.echo(f"Base URL: {spec.base_url}")
    click.echo(f"Endpoints: {len(spec.endpoints)}")
    for ep in spec.endpoints:
        auth = " [AUTH]" if ep.requires_auth else ""
        click.echo(f"  {ep.method.value:7} {ep.path}{auth}")


@cli.command(name="risk-score")
@click.argument("spec_path", type=click.Path(exists=True))
@click.option("--output", "-o", type=click.Path(), help="Output JSON path")
@click.pass_context
def risk_score(ctx: click.Context, spec_path: str, output: str | None) -> None:
    """Score endpoints by risk tier."""
    import json

    from qe_platform.ingestion.risk_scorer import RiskScorer
    from qe_platform.ingestion.spec_parser import parse_openapi

    settings: Settings = ctx.obj["settings"]
    spec = parse_openapi(spec_path)
    scorer = RiskScorer(settings)
    report = scorer.score_endpoints(spec)

    click.echo(f"\nRisk Report: {report.spec_title}")
    click.echo(f"Endpoints: {report.total_endpoints}")
    click.echo(f"Distribution: {report.tier_distribution}")
    click.echo()

    for a in report.sorted_by_risk():
        click.echo(
            f"  [{a.risk_tier.value:8}] {a.risk_score:.2f}  "
            f"{a.method:7} {a.path} → {a.recommended_test_count} tests"
        )

    if output:
        Path(output).write_text(json.dumps(report.model_dump(mode="json"), indent=2))
        click.echo(f"\nSaved to {output}")


@cli.command()
@click.argument("spec_path", type=click.Path(exists=True))
@click.option("--output-dir", "-o", default="reports", help="Report output directory")
@click.option("--base-url", default="", help="Base URL for test execution")
@click.option(
    "--skip-execution", is_flag=True, help="Generate tests without running them"
)
@click.pass_context
def generate(
    ctx: click.Context,
    spec_path: str,
    output_dir: str,
    base_url: str,
    skip_execution: bool,
) -> None:
    """Generate and optionally execute test cases from an API spec."""

    from qe_platform.execution.runner import TestRunner
    from qe_platform.generation.case_deduplicator import CaseDeduplicator
    from qe_platform.generation.test_generator import TestGenerator
    from qe_platform.ingestion.risk_scorer import RiskScorer
    from qe_platform.ingestion.spec_parser import parse_openapi
    from qe_platform.models.report import TestExecutionResult
    from qe_platform.observability.trace_logger import configure_tracing
    from qe_platform.report.report_generator import ReportGenerator

    settings: Settings = ctx.obj["settings"]
    configure_tracing(settings)

    start = time.monotonic()

    click.echo("Parsing spec...")
    spec = parse_openapi(spec_path)
    click.echo(f"  Found {len(spec.endpoints)} endpoints")

    click.echo("Scoring risk...")
    scorer = RiskScorer(settings)
    risk_report = scorer.score_endpoints(spec)

    click.echo("Generating tests...")
    generator = TestGenerator(settings)
    run = generator.generate_all(spec, risk_report)
    click.echo(f"  Generated {run.total_tests_generated} tests")

    click.echo("Deduplicating...")
    deduplicator = CaseDeduplicator(settings)
    for suite in run.suites:
        original_count = len(suite.test_cases)
        suite.test_cases = deduplicator.deduplicate(suite.test_cases)
        run.duplicates_removed += original_count - len(suite.test_cases)

    run.total_tests_after_dedup = sum(len(s.test_cases) for s in run.suites)
    click.echo(
        f"  After dedup: {run.total_tests_after_dedup} "
        f"({run.duplicates_removed} removed)"
    )

    results: list[TestExecutionResult] = []
    if not skip_execution and base_url:
        click.echo(f"Executing tests against {base_url}...")
        runner = TestRunner(settings)
        results = asyncio.run(runner.run_all(run.suites, base_url))
        click.echo(f"  Executed {len(results)} tests")

    duration = time.monotonic() - start

    click.echo("Generating report...")
    reporter = ReportGenerator(settings)
    report = reporter.generate(run, results, duration_seconds=duration)

    out = Path(output_dir)
    reporter.to_json(report, out / f"{run.run_id}_report.json")
    reporter.to_markdown(report, out / f"{run.run_id}_report.md")

    click.echo(f"\nDone in {duration:.2f}s")
    click.echo(f"  Total tests: {report.total_tests}")
    if results:
        click.echo(f"  Pass rate: {report.pass_rate:.1f}%")
    click.echo(f"  Reports saved to {out}/")


@cli.command()
@click.pass_context
def demo(ctx: click.Context) -> None:
    """Run demo with the included Petstore spec."""
    demo_spec = Path(__file__).parent.parent / "demo" / "petstore_openapi.yaml"
    if not demo_spec.exists():
        click.echo(f"Demo spec not found at {demo_spec}")
        raise SystemExit(1)

    click.echo("Running demo with Petstore API spec...")
    ctx.invoke(
        parse,
        spec_path=str(demo_spec),
        fmt="json",
    )
