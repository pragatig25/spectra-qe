from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class TestCategory(str, Enum):
    API = "api"
    UI = "ui"
    INTEGRATION = "integration"


class TestType(str, Enum):
    HAPPY_PATH = "happy_path"
    BOUNDARY = "boundary"
    AUTH_BYPASS = "auth_bypass"
    MALFORMED_INPUT = "malformed_input"
    NEGATIVE = "negative"


class GeneratedTestCase(BaseModel):
    id: str
    name: str
    category: TestCategory = TestCategory.API
    test_type: TestType
    endpoint_path: str = ""
    method: str = ""
    description: str = ""
    input_data: dict = Field(default_factory=dict)
    expected_status: int = 200
    expected_response: dict = Field(default_factory=dict)
    assertions: list[str] = Field(default_factory=list)
    risk_tier: str = "Low"
    tags: list[str] = Field(default_factory=list)
    pytest_code: str = ""
    is_duplicate: bool = False
    similarity_score: float | None = None


class GeneratedTestSuite(BaseModel):
    endpoint_path: str
    method: str
    risk_tier: str
    test_cases: list[GeneratedTestCase] = Field(default_factory=list)
    generation_tokens: int = 0
    generation_cost: float = 0.0


class TestGenerationRun(BaseModel):
    run_id: str
    spec_title: str = ""
    total_endpoints: int = 0
    total_tests_generated: int = 0
    total_tests_after_dedup: int = 0
    duplicates_removed: int = 0
    suites: list[GeneratedTestSuite] = Field(default_factory=list)
    total_tokens: int = 0
    total_cost: float = 0.0
