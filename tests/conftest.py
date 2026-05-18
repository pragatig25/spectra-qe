from __future__ import annotations

from pathlib import Path

import pytest

from qe_platform.config import Settings
from qe_platform.models.risk import (
    EndpointRiskAssessment,
    RiskFactor,
    RiskReport,
    RiskTier,
)
from qe_platform.models.spec import (
    EndpointParameter,
    EndpointSpec,
    HttpMethod,
    ParsedSpec,
    RequestBody,
    ResponseSpec,
)
from qe_platform.models.test_case import (
    GeneratedTestCase,
    GeneratedTestSuite,
    TestGenerationRun,
    TestType,
)

FIXTURES_DIR = Path(__file__).parent / "fixtures"
DEMO_DIR = Path(__file__).parent.parent / "demo"


@pytest.fixture
def demo_spec_path() -> Path:
    return DEMO_DIR / "petstore_openapi.yaml"


@pytest.fixture
def settings() -> Settings:
    return Settings(
        openai_api_key="test-key",
        anthropic_api_key="test-key",
        llm_provider="openai",
        llm_model="gpt-4o",
        llm_temperature=0.2,
        dedup_similarity_threshold=0.92,
    )


@pytest.fixture
def sample_endpoint() -> EndpointSpec:
    return EndpointSpec(
        path="/pets",
        method=HttpMethod.POST,
        operation_id="createPet",
        summary="Create a new pet",
        description="Create a new pet in the store",
        tags=["pets"],
        parameters=[],
        request_body=RequestBody(
            content_type="application/json",
            schema_def={
                "type": "object",
                "required": ["name", "species"],
                "properties": {
                    "name": {"type": "string"},
                    "species": {"type": "string", "enum": ["dog", "cat"]},
                    "age": {"type": "integer", "minimum": 0},
                },
            },
            required=True,
        ),
        responses=[
            ResponseSpec(status_code=201, description="Pet created"),
            ResponseSpec(status_code=400, description="Invalid input"),
            ResponseSpec(status_code=401, description="Unauthorized"),
        ],
        security=[{"bearerAuth": []}],
        requires_auth=True,
    )


@pytest.fixture
def sample_parsed_spec(sample_endpoint: EndpointSpec) -> ParsedSpec:
    return ParsedSpec(
        title="Petstore API",
        version="1.0.0",
        base_url="https://petstore.example.com/api/v1",
        endpoints=[
            EndpointSpec(
                path="/pets",
                method=HttpMethod.GET,
                operation_id="listPets",
                summary="List all pets",
                tags=["pets"],
                parameters=[
                    EndpointParameter(
                        name="limit",
                        location="query",
                        param_type="integer",
                        required=False,
                    )
                ],
                responses=[
                    ResponseSpec(status_code=200, description="A list of pets"),
                ],
            ),
            sample_endpoint,
        ],
        source_type="openapi",
    )


@pytest.fixture
def sample_risk_assessment() -> EndpointRiskAssessment:
    return EndpointRiskAssessment(
        path="/pets",
        method="POST",
        risk_tier=RiskTier.HIGH,
        risk_score=0.75,
        factors=[
            RiskFactor(name="write_operation", score=0.8, reasoning="Creates data"),
            RiskFactor(name="auth_required", score=0.7, reasoning="Needs JWT"),
        ],
        recommended_test_count=5,
    )


@pytest.fixture
def sample_risk_report(sample_risk_assessment: EndpointRiskAssessment) -> RiskReport:
    return RiskReport(
        spec_title="Petstore API",
        total_endpoints=2,
        assessments=[
            EndpointRiskAssessment(
                path="/pets",
                method="GET",
                risk_tier=RiskTier.LOW,
                risk_score=0.2,
                factors=[],
                recommended_test_count=3,
            ),
            sample_risk_assessment,
        ],
        tier_distribution={"Low": 1, "High": 1},
    )


@pytest.fixture
def sample_test_cases() -> list[GeneratedTestCase]:
    return [
        GeneratedTestCase(
            id="tc_001",
            name="test_create_pet_happy_path",
            test_type=TestType.HAPPY_PATH,
            endpoint_path="/pets",
            method="POST",
            description="Valid pet creation",
            input_data={"body": {"name": "Buddy", "species": "dog", "age": 3}},
            expected_status=201,
            assertions=["response has id field", "name matches input"],
            risk_tier="High",
        ),
        GeneratedTestCase(
            id="tc_002",
            name="test_create_pet_missing_name",
            test_type=TestType.MALFORMED_INPUT,
            endpoint_path="/pets",
            method="POST",
            description="Missing required name field",
            input_data={"body": {"species": "dog"}},
            expected_status=400,
            assertions=["error message mentions name"],
            risk_tier="High",
        ),
        GeneratedTestCase(
            id="tc_003",
            name="test_create_pet_no_auth",
            test_type=TestType.AUTH_BYPASS,
            endpoint_path="/pets",
            method="POST",
            description="Request without auth token",
            input_data={"body": {"name": "Buddy", "species": "dog"}},
            expected_status=401,
            assertions=["returns unauthorized error"],
            risk_tier="High",
        ),
    ]


@pytest.fixture
def sample_test_suite(
    sample_test_cases: list[GeneratedTestCase],
) -> GeneratedTestSuite:
    return GeneratedTestSuite(
        endpoint_path="/pets",
        method="POST",
        risk_tier="High",
        test_cases=sample_test_cases,
    )


@pytest.fixture
def sample_generation_run(
    sample_test_suite: GeneratedTestSuite,
) -> TestGenerationRun:
    return TestGenerationRun(
        run_id="run_test123",
        spec_title="Petstore API",
        total_endpoints=1,
        total_tests_generated=3,
        total_tests_after_dedup=3,
        suites=[sample_test_suite],
    )
