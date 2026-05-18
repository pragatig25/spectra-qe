from __future__ import annotations

import json

from qe_platform.models.report import TestExecutionResult, TestStatus
from qe_platform.models.test_case import TestGenerationRun
from qe_platform.report.report_generator import ReportGenerator


class TestReportGenerator:
    def test_generates_report_with_results(
        self, sample_generation_run: TestGenerationRun
    ) -> None:
        results = [
            TestExecutionResult(
                test_id="tc_001",
                test_name="test_create_pet_happy_path",
                status=TestStatus.PASSED,
                duration_ms=150.0,
            ),
            TestExecutionResult(
                test_id="tc_002",
                test_name="test_create_pet_missing_name",
                status=TestStatus.PASSED,
                duration_ms=120.0,
            ),
            TestExecutionResult(
                test_id="tc_003",
                test_name="test_create_pet_no_auth",
                status=TestStatus.FAILED,
                duration_ms=90.0,
                error_message="Expected 401, got 200",
            ),
        ]

        generator = ReportGenerator()
        report = generator.generate(sample_generation_run, results)

        assert report.total_tests == 3
        assert report.passed == 2
        assert report.failed == 1
        assert report.pass_rate == pytest.approx(66.67, abs=0.1)

    def test_generates_report_no_results(
        self, sample_generation_run: TestGenerationRun
    ) -> None:
        generator = ReportGenerator()
        report = generator.generate(sample_generation_run, [])
        assert report.total_tests == 0
        assert report.pass_rate == 0.0

    def test_to_json_format(self, sample_generation_run: TestGenerationRun) -> None:
        generator = ReportGenerator()
        report = generator.generate(sample_generation_run, [])
        json_str = generator.to_json(report)
        data = json.loads(json_str)
        assert data["run_id"] == "run_test123"
        assert "coverage" in data
        assert "token_cost" in data

    def test_to_markdown_contains_headers(
        self, sample_generation_run: TestGenerationRun
    ) -> None:
        generator = ReportGenerator()
        report = generator.generate(sample_generation_run, [])
        md = generator.to_markdown(report)
        assert "# QE Platform - Test Generation Report" in md
        assert "run_test123" in md
        assert "Coverage" in md


# Need pytest import for approx
import pytest  # noqa: E402
