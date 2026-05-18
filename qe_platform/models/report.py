from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class TestStatus(str, Enum):
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"
    HEALED = "healed"


class TestExecutionResult(BaseModel):
    test_id: str
    test_name: str
    status: TestStatus
    duration_ms: float = 0.0
    error_message: str = ""
    healed: bool = False
    heal_attempts: int = 0
    original_locator: str = ""
    healed_locator: str = ""


class CoverageMetric(BaseModel):
    total_endpoints: int = 0
    covered_endpoints: int = 0
    coverage_pct: float = 0.0
    test_type_distribution: dict[str, int] = Field(default_factory=dict)
    risk_tier_distribution: dict[str, int] = Field(default_factory=dict)


class SelfHealingMetric(BaseModel):
    total_failures: int = 0
    heal_attempts: int = 0
    heal_successes: int = 0
    heal_rate: float = 0.0


class TokenCostMetric(BaseModel):
    total_prompt_tokens: int = 0
    total_completion_tokens: int = 0
    total_tokens: int = 0
    total_cost_usd: float = 0.0
    avg_cost_per_test: float = 0.0


class PipelineReport(BaseModel):
    run_id: str
    spec_title: str = ""
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    total_tests: int = 0
    passed: int = 0
    failed: int = 0
    error: int = 0
    healed: int = 0
    pass_rate: float = 0.0
    results: list[TestExecutionResult] = Field(default_factory=list)
    coverage: CoverageMetric = Field(default_factory=CoverageMetric)
    self_healing: SelfHealingMetric = Field(default_factory=SelfHealingMetric)
    token_cost: TokenCostMetric = Field(default_factory=TokenCostMetric)
    duration_seconds: float = 0.0
