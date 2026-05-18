from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class RiskTier(str, Enum):
    LOW = "Low"
    MEDIUM = "Med"
    HIGH = "High"
    CRITICAL = "Critical"


class RiskFactor(BaseModel):
    name: str
    score: float = Field(ge=0.0, le=1.0)
    reasoning: str = ""


class EndpointRiskAssessment(BaseModel):
    path: str
    method: str
    risk_tier: RiskTier
    risk_score: float = Field(ge=0.0, le=1.0)
    factors: list[RiskFactor] = Field(default_factory=list)
    recommended_test_count: int = Field(default=3, ge=1, le=20)
    priority_order: int = 0


class RiskReport(BaseModel):
    spec_title: str = ""
    total_endpoints: int = 0
    assessments: list[EndpointRiskAssessment] = Field(default_factory=list)
    tier_distribution: dict[str, int] = Field(default_factory=dict)

    def get_by_tier(self, tier: RiskTier) -> list[EndpointRiskAssessment]:
        return [a for a in self.assessments if a.risk_tier == tier]

    def sorted_by_risk(self) -> list[EndpointRiskAssessment]:
        return sorted(self.assessments, key=lambda a: a.risk_score, reverse=True)
