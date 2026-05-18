from __future__ import annotations

import json
import re
import uuid

import structlog
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from qe_platform.config import Settings
from qe_platform.generation.prompts import TEST_GENERATION_PROMPT
from qe_platform.models.risk import EndpointRiskAssessment, RiskReport
from qe_platform.models.spec import EndpointSpec, ParsedSpec
from qe_platform.models.test_case import (
    GeneratedTestCase,
    GeneratedTestSuite,
    TestGenerationRun,
    TestType,
)

logger = structlog.get_logger()


def _extract_json(text: str) -> dict:
    """Strip markdown fences and parse JSON from LLM output, repairing if needed."""
    from json_repair import repair_json
    # Strip ```json ... ``` or ``` ... ``` blocks
    match = re.search(r"```(?:json)?\s*([\s\S]+?)\s*```", text)
    if match:
        text = match.group(1)
    # Find the first {...} block in case of leading prose
    brace_match = re.search(r"(\{[\s\S]+)", text)
    if brace_match:
        text = brace_match.group(1)
    repaired = repair_json(text.strip())
    return json.loads(repaired)


class TestGenerator:
    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or Settings()
        self._llm = self._build_llm()
        self._chain = ChatPromptTemplate.from_template(TEST_GENERATION_PROMPT) | self._llm | StrOutputParser()
        self._total_tokens = 0

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

    def generate_suite(
        self,
        endpoint: EndpointSpec,
        risk: EndpointRiskAssessment,
    ) -> GeneratedTestSuite:
        params_str = json.dumps(
            [p.model_dump(exclude_none=True) for p in endpoint.parameters],
            indent=2,
        )
        body_str = (
            json.dumps(endpoint.request_body.model_dump(exclude_none=True), indent=2)
            if endpoint.request_body
            else "None"
        )
        responses_str = json.dumps(
            [r.model_dump() for r in endpoint.responses],
            indent=2,
        )

        chain = self._chain
        # Cap test_count to avoid oversized LLM responses that produce malformed JSON
        test_count = min(risk.recommended_test_count, 8)
        raw: str = chain.invoke(
            {
                "path": endpoint.path,
                "method": endpoint.method.value,
                "summary": endpoint.summary,
                "description": endpoint.description,
                "parameters": params_str,
                "request_body": body_str,
                "responses": responses_str,
                "requires_auth": endpoint.requires_auth,
                "risk_tier": risk.risk_tier.value,
                "risk_score": risk.risk_score,
                "test_count": test_count,
            }
        )
        data = _extract_json(raw)
        test_cases_raw: list[dict] = data.get("test_cases", [])

        test_cases: list[GeneratedTestCase] = []
        for tc in test_cases_raw:
            test_type = _parse_test_type(tc.get("test_type", "happy_path"))
            test_cases.append(
                GeneratedTestCase(
                    id=f"tc_{uuid.uuid4().hex[:8]}",
                    name=tc.get("name", "unnamed_test"),
                    test_type=test_type,
                    endpoint_path=endpoint.path,
                    method=endpoint.method.value,
                    description=tc.get("description", ""),
                    input_data=tc.get("input_data", {}),
                    expected_status=tc.get("expected_status", 200),
                    assertions=tc.get("assertions", []),
                    risk_tier=risk.risk_tier.value,
                )
            )

        suite = GeneratedTestSuite(
            endpoint_path=endpoint.path,
            method=endpoint.method.value,
            risk_tier=risk.risk_tier.value,
            test_cases=test_cases,
        )

        logger.info(
            "generated_test_suite",
            path=endpoint.path,
            method=endpoint.method.value,
            test_count=len(test_cases),
        )
        return suite

    def generate_all(
        self,
        parsed_spec: ParsedSpec,
        risk_report: RiskReport,
    ) -> TestGenerationRun:
        run_id = f"run_{uuid.uuid4().hex[:12]}"
        risk_map = {
            (a.path, a.method): a for a in risk_report.assessments
        }

        suites: list[GeneratedTestSuite] = []
        total_tests = 0

        for endpoint in parsed_spec.endpoints:
            key = (endpoint.path, endpoint.method.value)
            risk = risk_map.get(key)
            if not risk:
                logger.warning("no_risk_assessment", path=key[0], method=key[1])
                continue

            suite = self.generate_suite(endpoint, risk)
            suites.append(suite)
            total_tests += len(suite.test_cases)

        run = TestGenerationRun(
            run_id=run_id,
            spec_title=parsed_spec.title,
            total_endpoints=len(suites),
            total_tests_generated=total_tests,
            total_tests_after_dedup=total_tests,
            suites=suites,
        )

        logger.info(
            "generation_run_complete",
            run_id=run_id,
            endpoints=len(suites),
            total_tests=total_tests,
        )
        return run


def _parse_test_type(raw: str) -> TestType:
    mapping = {
        "happy_path": TestType.HAPPY_PATH,
        "boundary": TestType.BOUNDARY,
        "auth_bypass": TestType.AUTH_BYPASS,
        "malformed_input": TestType.MALFORMED_INPUT,
        "negative": TestType.NEGATIVE,
    }
    return mapping.get(raw.strip().lower(), TestType.HAPPY_PATH)
