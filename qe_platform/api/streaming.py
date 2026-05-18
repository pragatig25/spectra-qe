from __future__ import annotations

import json
import time
import uuid
from pathlib import Path
from typing import Generator

import structlog
from fastapi.responses import StreamingResponse

from qe_platform.config import Settings

logger = structlog.get_logger()


def _sse(data: dict) -> str:
    return f"data: {json.dumps(data)}\n\n"


def _evt(stage: str, status: str, **kwargs: object) -> str:
    return _sse({"stage": stage, "status": status, "ts": time.time(), **kwargs})


def risk_score_stream(
    spec_path: Path, settings: Settings
) -> StreamingResponse:
    def generate() -> Generator[str, None, None]:
        from qe_platform.ingestion.risk_scorer import RiskScorer
        from qe_platform.ingestion.spec_parser import parse_openapi
        from qe_platform.models.risk import RiskReport

        try:
            yield _evt("parse", "started")
            spec = parse_openapi(spec_path)
            yield _evt(
                "parse",
                "complete",
                detail={
                    "endpoint_count": len(spec.endpoints),
                    "title": spec.title,
                },
            )
        except Exception as exc:
            yield _evt("parse", "error", error=str(exc))
            return

        total = len(spec.endpoints)
        yield _evt(
            "risk_score", "started", detail={"total_endpoints": total}
        )

        try:
            scorer = RiskScorer(settings)
        except Exception as exc:
            yield _evt("risk_score", "error", error=str(exc))
            return

        assessments = []
        tier_dist: dict[str, int] = {}

        for i, endpoint in enumerate(spec.endpoints):
            yield _evt(
                "risk_score",
                "scoring",
                detail={
                    "index": i + 1,
                    "total": total,
                    "path": endpoint.path,
                    "method": endpoint.method.value,
                },
            )

            try:
                assessment = scorer.score_endpoint(endpoint)
                assessment.priority_order = i
                assessments.append(assessment)
                tier_dist[assessment.risk_tier.value] = (
                    tier_dist.get(assessment.risk_tier.value, 0) + 1
                )

                yield _evt(
                    "risk_score",
                    "scored",
                    detail={
                        "index": i + 1,
                        "total": total,
                        "path": endpoint.path,
                        "method": endpoint.method.value,
                        "tier": assessment.risk_tier.value,
                        "score": assessment.risk_score,
                    },
                )
            except Exception as exc:
                yield _evt(
                    "risk_score",
                    "error",
                    error=str(exc),
                    detail={
                        "path": endpoint.path,
                        "method": endpoint.method.value,
                    },
                )
                return

        report = RiskReport(
            spec_title=spec.title,
            total_endpoints=len(assessments),
            assessments=assessments,
            tier_distribution=tier_dist,
        )

        result_assessments = []
        for a in report.sorted_by_risk():
            result_assessments.append(
                {
                    "path": a.path,
                    "method": a.method,
                    "risk_tier": a.risk_tier.value,
                    "risk_score": a.risk_score,
                    "recommended_test_count": a.recommended_test_count,
                    "factors": [f.model_dump() for f in a.factors],
                }
            )

        yield _evt(
            "risk_score",
            "complete",
            result={
                "spec_title": report.spec_title,
                "total_endpoints": report.total_endpoints,
                "tier_distribution": report.tier_distribution,
                "assessments": result_assessments,
            },
        )

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


def generate_stream(
    spec_path: Path,
    settings: Settings,
    skip_execution: bool = True,
    base_url: str = "",
) -> StreamingResponse:
    def generate() -> Generator[str, None, None]:
        from qe_platform.generation.case_deduplicator import CaseDeduplicator
        from qe_platform.generation.test_generator import TestGenerator
        from qe_platform.ingestion.risk_scorer import RiskScorer
        from qe_platform.ingestion.spec_parser import parse_openapi
        from qe_platform.models.risk import RiskReport

        run_id = f"run_{uuid.uuid4().hex[:12]}"

        # --- Parse ---
        try:
            yield _evt("parse", "started", run_id=run_id)
            spec = parse_openapi(spec_path)
            yield _evt(
                "parse",
                "complete",
                run_id=run_id,
                detail={
                    "endpoint_count": len(spec.endpoints),
                    "title": spec.title,
                },
            )
        except Exception as exc:
            yield _evt("parse", "error", run_id=run_id, error=str(exc))
            return

        total = len(spec.endpoints)

        # --- Risk Score ---
        yield _evt(
            "risk_score",
            "started",
            run_id=run_id,
            detail={"total_endpoints": total},
        )

        try:
            scorer = RiskScorer(settings)
        except Exception as exc:
            yield _evt(
                "risk_score", "error", run_id=run_id, error=str(exc)
            )
            return

        risk_assessments = []
        tier_dist: dict[str, int] = {}

        for i, endpoint in enumerate(spec.endpoints):
            yield _evt(
                "risk_score",
                "scoring",
                run_id=run_id,
                detail={
                    "index": i + 1,
                    "total": total,
                    "path": endpoint.path,
                    "method": endpoint.method.value,
                },
            )

            try:
                assessment = scorer.score_endpoint(endpoint)
                assessment.priority_order = i
                risk_assessments.append(assessment)
                tier_dist[assessment.risk_tier.value] = (
                    tier_dist.get(assessment.risk_tier.value, 0) + 1
                )

                yield _evt(
                    "risk_score",
                    "scored",
                    run_id=run_id,
                    detail={
                        "index": i + 1,
                        "total": total,
                        "path": endpoint.path,
                        "method": endpoint.method.value,
                        "tier": assessment.risk_tier.value,
                        "score": assessment.risk_score,
                    },
                )
            except Exception as exc:
                yield _evt(
                    "risk_score",
                    "error",
                    run_id=run_id,
                    error=str(exc),
                )
                return

        risk_report = RiskReport(
            spec_title=spec.title,
            total_endpoints=len(risk_assessments),
            assessments=risk_assessments,
            tier_distribution=tier_dist,
        )

        yield _evt(
            "risk_score",
            "complete",
            run_id=run_id,
            detail={"distribution": tier_dist},
        )

        # --- Generate ---
        yield _evt(
            "generate",
            "started",
            run_id=run_id,
            detail={"total_endpoints": total},
        )

        try:
            generator = TestGenerator(settings)
        except Exception as exc:
            yield _evt(
                "generate", "error", run_id=run_id, error=str(exc)
            )
            return

        risk_map = {
            (a.path, a.method): a for a in risk_report.assessments
        }
        suites = []
        total_tests = 0

        for i, endpoint in enumerate(spec.endpoints):
            key = (endpoint.path, endpoint.method.value)
            risk = risk_map.get(key)
            if not risk:
                continue

            yield _evt(
                "generate",
                "generating",
                run_id=run_id,
                detail={
                    "index": i + 1,
                    "total": total,
                    "path": endpoint.path,
                    "method": endpoint.method.value,
                },
            )

            try:
                suite = generator.generate_suite(endpoint, risk)
                suites.append(suite)
                total_tests += len(suite.test_cases)

                yield _evt(
                    "generate",
                    "generated",
                    run_id=run_id,
                    detail={
                        "index": i + 1,
                        "total": total,
                        "path": endpoint.path,
                        "method": endpoint.method.value,
                        "test_count": len(suite.test_cases),
                    },
                )
            except Exception as exc:
                yield _evt(
                    "generate",
                    "error",
                    run_id=run_id,
                    error=str(exc),
                )
                return

        # --- Dedup ---
        yield _evt("dedup", "started", run_id=run_id)

        deduplicator = CaseDeduplicator(settings)
        duplicates_removed = 0
        for suite in suites:
            original = len(suite.test_cases)
            suite.test_cases = deduplicator.deduplicate(suite.test_cases)
            duplicates_removed += original - len(suite.test_cases)

        total_after_dedup = sum(len(s.test_cases) for s in suites)

        if duplicates_removed == 0 and not settings.openai_api_key:
            yield _evt(
                "dedup",
                "skipped",
                run_id=run_id,
                detail={"reason": "no_openai_api_key"},
            )
        else:
            yield _evt(
                "dedup",
                "complete",
                run_id=run_id,
                detail={
                    "removed": duplicates_removed,
                    "remaining": total_after_dedup,
                },
            )

        # --- Final result ---
        suites_data = _serialize_suites(suites)

        yield _evt(
            "pipeline",
            "complete",
            run_id=run_id,
            result={
                "run_id": run_id,
                "spec_title": spec.title,
                "total_endpoints": len(suites),
                "total_tests_generated": total_tests,
                "total_tests_after_dedup": total_after_dedup,
                "duplicates_removed": duplicates_removed,
                "suites": suites_data,
                "report": None,
            },
        )

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


def _serialize_suites(suites: list) -> list[dict]:
    out = []
    for s in suites:
        out.append(
            {
                "endpoint_path": s.endpoint_path,
                "method": s.method,
                "risk_tier": s.risk_tier,
                "test_cases": [
                    tc.model_dump(mode="json") for tc in s.test_cases
                ],
            }
        )
    return out


def report_stream(
    spec_path: Path,
    settings: Settings,
) -> StreamingResponse:
    def generate() -> Generator[str, None, None]:
        from qe_platform.generation.case_deduplicator import CaseDeduplicator
        from qe_platform.generation.test_generator import TestGenerator
        from qe_platform.ingestion.risk_scorer import RiskScorer
        from qe_platform.ingestion.spec_parser import parse_openapi
        from qe_platform.models.risk import RiskReport
        from qe_platform.models.test_case import TestGenerationRun
        from qe_platform.report.report_generator import ReportGenerator

        run_id = f"run_{uuid.uuid4().hex[:12]}"
        pipeline_start = time.time()

        # --- Parse ---
        try:
            yield _evt("parse", "started", run_id=run_id)
            spec = parse_openapi(spec_path)
            yield _evt(
                "parse",
                "complete",
                run_id=run_id,
                detail={
                    "endpoint_count": len(spec.endpoints),
                    "title": spec.title,
                },
            )
        except Exception as exc:
            yield _evt("parse", "error", run_id=run_id, error=str(exc))
            return

        total = len(spec.endpoints)

        # --- Risk Score ---
        yield _evt(
            "risk_score",
            "started",
            run_id=run_id,
            detail={"total_endpoints": total},
        )

        try:
            scorer = RiskScorer(settings)
        except Exception as exc:
            yield _evt(
                "risk_score", "error", run_id=run_id, error=str(exc)
            )
            return

        risk_assessments = []
        tier_dist: dict[str, int] = {}

        for i, endpoint in enumerate(spec.endpoints):
            yield _evt(
                "risk_score",
                "scoring",
                run_id=run_id,
                detail={
                    "index": i + 1,
                    "total": total,
                    "path": endpoint.path,
                    "method": endpoint.method.value,
                },
            )

            try:
                assessment = scorer.score_endpoint(endpoint)
                assessment.priority_order = i
                risk_assessments.append(assessment)
                tier_dist[assessment.risk_tier.value] = (
                    tier_dist.get(assessment.risk_tier.value, 0) + 1
                )

                yield _evt(
                    "risk_score",
                    "scored",
                    run_id=run_id,
                    detail={
                        "index": i + 1,
                        "total": total,
                        "path": endpoint.path,
                        "method": endpoint.method.value,
                        "tier": assessment.risk_tier.value,
                        "score": assessment.risk_score,
                    },
                )
            except Exception as exc:
                yield _evt(
                    "risk_score",
                    "error",
                    run_id=run_id,
                    error=str(exc),
                )
                return

        risk_report = RiskReport(
            spec_title=spec.title,
            total_endpoints=len(risk_assessments),
            assessments=risk_assessments,
            tier_distribution=tier_dist,
        )

        yield _evt(
            "risk_score",
            "complete",
            run_id=run_id,
            detail={"distribution": tier_dist},
        )

        # --- Generate ---
        yield _evt(
            "generate",
            "started",
            run_id=run_id,
            detail={"total_endpoints": total},
        )

        try:
            test_gen = TestGenerator(settings)
        except Exception as exc:
            yield _evt(
                "generate", "error", run_id=run_id, error=str(exc)
            )
            return

        risk_map = {
            (a.path, a.method): a for a in risk_report.assessments
        }
        suites = []
        total_tests = 0

        for i, endpoint in enumerate(spec.endpoints):
            key = (endpoint.path, endpoint.method.value)
            risk = risk_map.get(key)
            if not risk:
                continue

            yield _evt(
                "generate",
                "generating",
                run_id=run_id,
                detail={
                    "index": i + 1,
                    "total": total,
                    "path": endpoint.path,
                    "method": endpoint.method.value,
                },
            )

            try:
                suite = test_gen.generate_suite(endpoint, risk)
                suites.append(suite)
                total_tests += len(suite.test_cases)

                yield _evt(
                    "generate",
                    "generated",
                    run_id=run_id,
                    detail={
                        "index": i + 1,
                        "total": total,
                        "path": endpoint.path,
                        "method": endpoint.method.value,
                        "test_count": len(suite.test_cases),
                    },
                )
            except Exception as exc:
                yield _evt(
                    "generate",
                    "error",
                    run_id=run_id,
                    error=str(exc),
                )
                return

        # --- Dedup ---
        yield _evt("dedup", "started", run_id=run_id)

        deduplicator = CaseDeduplicator(settings)
        duplicates_removed = 0
        for suite in suites:
            original = len(suite.test_cases)
            suite.test_cases = deduplicator.deduplicate(suite.test_cases)
            duplicates_removed += original - len(suite.test_cases)

        total_after_dedup = sum(len(s.test_cases) for s in suites)

        if duplicates_removed == 0 and not settings.openai_api_key:
            yield _evt(
                "dedup",
                "skipped",
                run_id=run_id,
                detail={"reason": "no_openai_api_key"},
            )
        else:
            yield _evt(
                "dedup",
                "complete",
                run_id=run_id,
                detail={
                    "removed": duplicates_removed,
                    "remaining": total_after_dedup,
                },
            )

        # --- Report ---
        yield _evt("report", "started", run_id=run_id)

        run = TestGenerationRun(
            run_id=run_id,
            spec_title=spec.title,
            total_endpoints=len(suites),
            total_tests_generated=total_tests,
            total_tests_after_dedup=total_after_dedup,
            duplicates_removed=duplicates_removed,
            suites=suites,
        )

        duration = time.time() - pipeline_start
        reporter = ReportGenerator(settings)
        pipeline_report = reporter.generate(
            run, results=[], duration_seconds=duration
        )
        report_data = pipeline_report.model_dump(mode="json")
        markdown = reporter.to_markdown(pipeline_report)

        yield _evt(
            "report",
            "complete",
            run_id=run_id,
            detail={
                "total_tests": pipeline_report.total_tests,
                "coverage_pct": pipeline_report.coverage.coverage_pct,
            },
        )

        # --- Final ---
        suites_data = _serialize_suites(suites)

        yield _evt(
            "pipeline",
            "complete",
            run_id=run_id,
            result={
                "run_id": run_id,
                "spec_title": spec.title,
                "total_endpoints": len(suites),
                "total_tests_generated": total_tests,
                "total_tests_after_dedup": total_after_dedup,
                "duplicates_removed": duplicates_removed,
                "suites": suites_data,
                "report": report_data,
                "markdown": markdown,
                "duration_seconds": duration,
                "tier_distribution": tier_dist,
            },
        )

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
