from __future__ import annotations

import asyncio
import time

import structlog

from qe_platform.config import Settings
from qe_platform.models.report import TestExecutionResult, TestStatus
from qe_platform.models.test_case import GeneratedTestCase, GeneratedTestSuite

logger = structlog.get_logger()


class TestRunner:
    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or Settings()
        self._max_concurrent = self._settings.max_concurrent_tests

    async def run_suite(
        self, suite: GeneratedTestSuite, base_url: str = ""
    ) -> list[TestExecutionResult]:
        semaphore = asyncio.Semaphore(self._max_concurrent)
        tasks = [self._run_single(tc, base_url, semaphore) for tc in suite.test_cases]
        return await asyncio.gather(*tasks)

    async def run_all(
        self,
        suites: list[GeneratedTestSuite],
        base_url: str = "",
    ) -> list[TestExecutionResult]:
        all_results: list[TestExecutionResult] = []
        for suite in suites:
            results = await self.run_suite(suite, base_url)
            all_results.extend(results)
        return all_results

    async def _run_single(
        self,
        test_case: GeneratedTestCase,
        base_url: str,
        semaphore: asyncio.Semaphore,
    ) -> TestExecutionResult:
        async with semaphore:
            start = time.monotonic()
            try:
                result = await self._execute_api_test(test_case, base_url)
                duration = (time.monotonic() - start) * 1000

                status = (
                    TestStatus.PASSED
                    if result["status_code"] == test_case.expected_status
                    else TestStatus.FAILED
                )
                error_msg = ""
                if status == TestStatus.FAILED:
                    error_msg = (
                        f"Expected {test_case.expected_status}, "
                        f"got {result['status_code']}"
                    )

                logger.info(
                    "test_executed",
                    test_id=test_case.id,
                    name=test_case.name,
                    status=status.value,
                    duration_ms=round(duration, 2),
                )

                return TestExecutionResult(
                    test_id=test_case.id,
                    test_name=test_case.name,
                    status=status,
                    duration_ms=round(duration, 2),
                    error_message=error_msg,
                )

            except Exception as exc:
                duration = (time.monotonic() - start) * 1000
                logger.error(
                    "test_error",
                    test_id=test_case.id,
                    error=str(exc),
                )
                return TestExecutionResult(
                    test_id=test_case.id,
                    test_name=test_case.name,
                    status=TestStatus.ERROR,
                    duration_ms=round(duration, 2),
                    error_message=str(exc),
                )

    async def _execute_api_test(
        self,
        test_case: GeneratedTestCase,
        base_url: str,
    ) -> dict:
        import httpx

        url = f"{base_url.rstrip('/')}{test_case.endpoint_path}"
        method = test_case.method.lower()
        headers = test_case.input_data.get("headers", {})
        params = test_case.input_data.get("params", {})
        body = test_case.input_data.get("body")

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                json=body,
            )

        return {
            "status_code": response.status_code,
            "body": response.text,
            "headers": dict(response.headers),
        }
