from __future__ import annotations

import pytest

from qe_platform.models.risk import EndpointRiskAssessment, RiskReport, RiskTier
from qe_platform.models.spec import EndpointSpec, HttpMethod, ParsedSpec
from qe_platform.models.test_case import (
    GeneratedTestCase,
    GeneratedTestSuite,
    TestType,
)


class TestEndpointSpec:
    def test_creates_valid_endpoint(self, sample_endpoint: EndpointSpec) -> None:
        assert sample_endpoint.path == "/pets"
        assert sample_endpoint.method == HttpMethod.POST
        assert sample_endpoint.requires_auth is True

    def test_defaults(self) -> None:
        ep = EndpointSpec(path="/test", method=HttpMethod.GET)
        assert ep.tags == []
        assert ep.parameters == []
        assert ep.request_body is None
        assert ep.requires_auth is False


class TestRiskReport:
    def test_get_by_tier(self, sample_risk_report: RiskReport) -> None:
        low = sample_risk_report.get_by_tier(RiskTier.LOW)
        assert len(low) == 1
        assert low[0].path == "/pets"
        assert low[0].method == "GET"

    def test_sorted_by_risk(self, sample_risk_report: RiskReport) -> None:
        sorted_a = sample_risk_report.sorted_by_risk()
        assert sorted_a[0].risk_score >= sorted_a[1].risk_score

    def test_tier_distribution(self, sample_risk_report: RiskReport) -> None:
        assert sample_risk_report.tier_distribution == {"Low": 1, "High": 1}


class TestGeneratedTestCase:
    def test_creates_valid_case(self) -> None:
        tc = GeneratedTestCase(
            id="tc_test",
            name="test_something",
            test_type=TestType.HAPPY_PATH,
            expected_status=200,
        )
        assert tc.is_duplicate is False
        assert tc.similarity_score is None

    def test_suite_aggregation(
        self, sample_test_suite: GeneratedTestSuite
    ) -> None:
        assert len(sample_test_suite.test_cases) == 3
        types = {tc.test_type for tc in sample_test_suite.test_cases}
        assert TestType.HAPPY_PATH in types
        assert TestType.AUTH_BYPASS in types
