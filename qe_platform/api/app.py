from __future__ import annotations

import asyncio
import tempfile
import time
from pathlib import Path
from typing import List

import structlog
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from qe_platform import __version__
from qe_platform.api.demo_specs import get_demo_spec_path, list_demo_specs
from qe_platform.api.schemas import (
    DemoSpec,
    GenerateRequest,
    GenerateResponse,
    HealthResponse,
    ParseRequest,
    ParseResponse,
    ReportExportRequest,
    ReportExportResponse,
    ReportRequest,
    RiskScoreRequest,
    RiskScoreResponse,
)
from qe_platform.api.streaming import (
    generate_stream,
    report_stream,
    risk_score_stream,
)
from qe_platform.config import Settings

logger = structlog.get_logger()

app = FastAPI(
    title="Spectra — AI Test Generation Platform",
    description="AI-powered test orchestration: parse specs, score risk, generate tests",
    version=__version__,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_settings = Settings()


def _resolve_spec_path(spec_content: str | None, spec_id: str | None) -> Path:
    if spec_id:
        path = get_demo_spec_path(spec_id)
        if not path:
            raise HTTPException(404, f"Demo spec '{spec_id}' not found")
        return path

    if spec_content:
        tmp = tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        )
        tmp.write(spec_content)
        tmp.close()
        return Path(tmp.name)

    raise HTTPException(400, "Provide spec_content or spec_id")


@app.get("/api/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(
        version=__version__,
        llm_provider=_settings.llm_provider,
        llm_model=_settings.llm_model,
        demo_mode=_settings.demo_mode,
    )


@app.get("/api/specs", response_model=List[DemoSpec])
async def get_specs() -> List[dict]:
    return list_demo_specs()


@app.post("/api/parse", response_model=ParseResponse)
async def parse_spec(req: ParseRequest) -> ParseResponse:
    from qe_platform.ingestion.spec_parser import parse_openapi

    spec_path = _resolve_spec_path(req.spec_content, req.spec_id)
    spec = parse_openapi(spec_path)

    endpoints = []
    for ep in spec.endpoints:
        endpoints.append(
            {
                "path": ep.path,
                "method": ep.method.value,
                "operation_id": ep.operation_id,
                "summary": ep.summary,
                "description": ep.description,
                "tags": ep.tags,
                "requires_auth": ep.requires_auth,
                "parameters": [p.model_dump(exclude_none=True) for p in ep.parameters],
                "request_body": ep.request_body.model_dump(exclude_none=True) if ep.request_body else None,
                "responses": [r.model_dump() for r in ep.responses],
            }
        )

    return ParseResponse(
        title=spec.title,
        version=spec.version,
        base_url=spec.base_url,
        description=spec.description,
        endpoint_count=len(spec.endpoints),
        endpoints=endpoints,
        source_type=spec.source_type,
    )


@app.post("/api/risk-score", response_model=RiskScoreResponse)
async def risk_score(req: RiskScoreRequest) -> RiskScoreResponse:
    from qe_platform.ingestion.risk_scorer import RiskScorer
    from qe_platform.ingestion.spec_parser import parse_openapi

    spec_path = _resolve_spec_path(req.spec_content, req.spec_id)
    spec = parse_openapi(spec_path)
    scorer = RiskScorer(_settings)
    report = scorer.score_endpoints(spec)

    assessments = []
    for a in report.sorted_by_risk():
        assessments.append(
            {
                "path": a.path,
                "method": a.method,
                "risk_tier": a.risk_tier.value,
                "risk_score": a.risk_score,
                "recommended_test_count": a.recommended_test_count,
                "factors": [f.model_dump() for f in a.factors],
            }
        )

    return RiskScoreResponse(
        spec_title=report.spec_title,
        total_endpoints=report.total_endpoints,
        tier_distribution=report.tier_distribution,
        assessments=assessments,
    )


@app.post("/api/generate", response_model=GenerateResponse)
async def generate_tests(req: GenerateRequest) -> GenerateResponse:
    from qe_platform.execution.runner import TestRunner
    from qe_platform.generation.case_deduplicator import CaseDeduplicator
    from qe_platform.generation.test_generator import TestGenerator
    from qe_platform.ingestion.risk_scorer import RiskScorer
    from qe_platform.ingestion.spec_parser import parse_openapi
    from qe_platform.report.report_generator import ReportGenerator

    spec_path = _resolve_spec_path(req.spec_content, req.spec_id)
    spec = parse_openapi(spec_path)

    scorer = RiskScorer(_settings)
    risk_report = scorer.score_endpoints(spec)

    generator = TestGenerator(_settings)
    run = generator.generate_all(spec, risk_report)

    deduplicator = CaseDeduplicator(_settings)
    for suite in run.suites:
        original = len(suite.test_cases)
        suite.test_cases = deduplicator.deduplicate(suite.test_cases)
        run.duplicates_removed += original - len(suite.test_cases)
    run.total_tests_after_dedup = sum(len(s.test_cases) for s in run.suites)

    report_data = None
    if not req.skip_execution and req.base_url:
        runner = TestRunner(_settings)
        results = await runner.run_all(run.suites, req.base_url)
        reporter = ReportGenerator(_settings)
        report = reporter.generate(run, results)
        report_data = report.model_dump(mode="json")

    suites = []
    for s in run.suites:
        suites.append(
            {
                "endpoint_path": s.endpoint_path,
                "method": s.method,
                "risk_tier": s.risk_tier,
                "test_cases": [tc.model_dump(mode="json") for tc in s.test_cases],
            }
        )

    return GenerateResponse(
        run_id=run.run_id,
        spec_title=run.spec_title,
        total_endpoints=run.total_endpoints,
        total_tests_generated=run.total_tests_generated,
        total_tests_after_dedup=run.total_tests_after_dedup,
        duplicates_removed=run.duplicates_removed,
        suites=suites,
        report=report_data,
    )


@app.post("/api/risk-score/stream")
async def risk_score_sse(req: RiskScoreRequest):
    spec_path = _resolve_spec_path(req.spec_content, req.spec_id)
    return risk_score_stream(spec_path, _settings)


@app.post("/api/generate/stream")
async def generate_sse(req: GenerateRequest):
    spec_path = _resolve_spec_path(req.spec_content, req.spec_id)
    return generate_stream(
        spec_path, _settings, req.skip_execution, req.base_url
    )


@app.post("/api/report/stream")
async def report_sse(req: ReportRequest):
    spec_path = _resolve_spec_path(req.spec_content, req.spec_id)
    return report_stream(spec_path, _settings)


@app.post("/api/report/export", response_model=ReportExportResponse)
async def export_report(req: ReportExportRequest) -> ReportExportResponse:
    import json as json_mod

    from qe_platform.models.report import PipelineReport
    from qe_platform.report.report_generator import ReportGenerator

    run_id = req.report.get("run_id", "unknown")

    if req.format == "markdown":
        report_obj = PipelineReport(**req.report)
        reporter = ReportGenerator(_settings)
        content = reporter.to_markdown(report_obj)
        filename = f"report_{run_id}.md"
    else:
        content = json_mod.dumps(req.report, indent=2, default=str)
        filename = f"report_{run_id}.json"

    return ReportExportResponse(
        content=content,
        filename=filename,
        format=req.format,
    )


UI_DIR = Path(__file__).parent.parent.parent / "ui" / "dist"
if UI_DIR.exists():
    app.mount("/", StaticFiles(directory=str(UI_DIR), html=True), name="ui")
