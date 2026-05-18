from __future__ import annotations

from dataclasses import dataclass

import structlog
from langchain_core.prompts import ChatPromptTemplate

from qe_platform.config import Settings
from qe_platform.generation.prompts import SELF_HEALING_PROMPT

logger = structlog.get_logger()


@dataclass
class HealResult:
    success: bool
    original_locator: str
    healed_locator: str
    attempts: int
    error: str = ""


class SelfHealer:
    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or Settings()
        self._max_retries = self._settings.self_heal_max_retries
        self._llm = self._build_llm()
        self._prompt = ChatPromptTemplate.from_template(SELF_HEALING_PROMPT)

    def _build_llm(self):  # type: ignore[no-untyped-def]
        if self._settings.llm_provider == "anthropic":
            from langchain_anthropic import ChatAnthropic

            return ChatAnthropic(
                model=self._settings.llm_model,
                temperature=0.0,
                anthropic_api_key=self._settings.anthropic_api_key,
            )
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=self._settings.llm_model,
            temperature=0.0,
            openai_api_key=self._settings.openai_api_key,
        )

    def attempt_heal(
        self,
        test_name: str,
        error_message: str,
        broken_locator: str,
        dom_snapshot: str,
    ) -> HealResult:
        trimmed_dom = dom_snapshot[:8000]

        for attempt in range(1, self._max_retries + 1):
            try:
                chain = self._prompt | self._llm
                response = chain.invoke(
                    {
                        "test_name": test_name,
                        "broken_locator": broken_locator,
                        "error_message": error_message,
                        "dom_snapshot": trimmed_dom,
                    }
                )

                new_locator = response.content.strip().strip("'\"` ")

                if not new_locator or new_locator == broken_locator:
                    logger.warning(
                        "heal_same_locator",
                        test_name=test_name,
                        attempt=attempt,
                    )
                    continue

                logger.info(
                    "heal_suggested",
                    test_name=test_name,
                    attempt=attempt,
                    original=broken_locator,
                    healed=new_locator,
                )

                return HealResult(
                    success=True,
                    original_locator=broken_locator,
                    healed_locator=new_locator,
                    attempts=attempt,
                )

            except Exception as exc:
                logger.error(
                    "heal_error",
                    test_name=test_name,
                    attempt=attempt,
                    error=str(exc),
                )

        return HealResult(
            success=False,
            original_locator=broken_locator,
            healed_locator="",
            attempts=self._max_retries,
            error="Max retries exhausted",
        )
