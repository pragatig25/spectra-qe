from __future__ import annotations

import json

import structlog
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from qe_platform.config import Settings
from qe_platform.models.risk import (
    EndpointRiskAssessment,
    RiskFactor,
    RiskReport,
    RiskTier,
)
from qe_platform.models.spec import EndpointSpec, ParsedSpec

logger = structlog.get_logger()

RISK_SCORING_PROMPT = """\
You are a senior QA engineer performing risk assessment on API endpoints.

Analyze the following API endpoint and assign a risk tier based on these factors:
1. **Data Sensitivity**: Does it handle PII, financial data, auth tokens?
2. **Authentication**: Does it require auth? What happens if auth is bypassed?
3. **Write Operations**: Does it create, update, or delete data?
4. **Downstream Dependencies**: Could failures cascade?
5. **Input Complexity**: How many parameters? Are there complex nested objects?

Endpoint:
- Path: {path}
- Method: {method}
- Summary: {summary}
- Description: {description}
- Parameters: {parameters}
- Request Body: {request_body}
- Requires Auth: {requires_auth}
- Tags: {tags}
"""


class _RiskAssessmentLLMOutput(BaseModel):
    risk_tier: str = Field(description="One of: Low, Med, High, Critical")
    risk_score: float = Field(ge=0.0, le=1.0, description="0.0 to 1.0")
    factors: list[dict] = Field(
        description="List of {name, score, reasoning} dicts"
    )
    recommended_test_count: int = Field(
        default=5, ge=1, le=20, description="How many tests to generate"
    )


class RiskScorer:
    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or Settings()
        self._llm = self._build_llm()
        self._structured_llm = self._llm.with_structured_output(_RiskAssessmentLLMOutput)
        self._prompt = ChatPromptTemplate.from_template(RISK_SCORING_PROMPT)

    def _build_llm(self):  # type: ignore[no-untyped-def]
        if self._settings.llm_provider == "anthropic":
            from langchain_anthropic import ChatAnthropic

            return ChatAnthropic(
                model=self._settings.llm_model,
                temperature=self._settings.llm_temperature,
                anthropic_api_key=self._settings.anthropic_api_key,
            )
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=self._settings.llm_model,
            temperature=self._settings.llm_temperature,
            openai_api_key=self._settings.openai_api_key,
        )

    def score_endpoint(self, endpoint: EndpointSpec) -> EndpointRiskAssessment:
        params_str = json.dumps(
            [p.model_dump(exclude_none=True) for p in endpoint.parameters],
            indent=2,
        )
        body_str = (
            json.dumps(endpoint.request_body.model_dump(exclude_none=True), indent=2)
            if endpoint.request_body
            else "None"
        )

        chain = self._prompt | self._structured_llm
        result: _RiskAssessmentLLMOutput = chain.invoke(
            {
                "path": endpoint.path,
                "method": endpoint.method.value,
                "summary": endpoint.summary,
                "description": endpoint.description,
                "parameters": params_str,
                "request_body": body_str,
                "requires_auth": endpoint.requires_auth,
                "tags": ", ".join(endpoint.tags),
            }
        )

        tier = _parse_tier(result.risk_tier)
        factors = [
            RiskFactor(name=f["name"], score=f["score"], reasoning=f.get("reasoning", ""))
            for f in result.factors
        ]

        assessment = EndpointRiskAssessment(
            path=endpoint.path,
            method=endpoint.method.value,
            risk_tier=tier,
            risk_score=result.risk_score,
            factors=factors,
            recommended_test_count=result.recommended_test_count,
        )

        logger.info(
            "scored_endpoint",
            path=endpoint.path,
            method=endpoint.method.value,
            tier=tier.value,
            score=result.risk_score,
        )
        return assessment

    def score_endpoints(self, parsed_spec: ParsedSpec) -> RiskReport:
        assessments: list[EndpointRiskAssessment] = []

        for i, endpoint in enumerate(parsed_spec.endpoints):
            assessment = self.score_endpoint(endpoint)
            assessment.priority_order = i
            assessments.append(assessment)

        tier_dist: dict[str, int] = {}
        for a in assessments:
            tier_dist[a.risk_tier.value] = tier_dist.get(a.risk_tier.value, 0) + 1

        report = RiskReport(
            spec_title=parsed_spec.title,
            total_endpoints=len(assessments),
            assessments=assessments,
            tier_distribution=tier_dist,
        )

        logger.info(
            "risk_report_complete",
            title=parsed_spec.title,
            total=report.total_endpoints,
            distribution=tier_dist,
        )
        return report


def _parse_tier(raw: str) -> RiskTier:
    normalized = raw.strip().lower()
    mapping = {
        "low": RiskTier.LOW,
        "med": RiskTier.MEDIUM,
        "medium": RiskTier.MEDIUM,
        "high": RiskTier.HIGH,
        "critical": RiskTier.CRITICAL,
    }
    return mapping.get(normalized, RiskTier.MEDIUM)
