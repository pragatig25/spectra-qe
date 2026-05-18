from __future__ import annotations

from typing import Any

import structlog

from qe_platform.config import Settings
from qe_platform.models.report import TokenCostMetric

logger = structlog.get_logger()

COST_PER_1K_TOKENS: dict[str, dict[str, float]] = {
    "gpt-4o": {"prompt": 0.0025, "completion": 0.01},
    "gpt-4o-mini": {"prompt": 0.00015, "completion": 0.0006},
    "claude-sonnet-4-6": {"prompt": 0.003, "completion": 0.015},
    "claude-haiku-4-5": {"prompt": 0.0008, "completion": 0.004},
}


class TokenDashboard:
    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or Settings()
        self._runs: list[dict[str, Any]] = []
        self._wandb_run = None

    def init_wandb(self) -> bool:
        if not self._settings.wandb_api_key:
            logger.info("wandb_disabled")
            return False

        try:
            import wandb

            self._wandb_run = wandb.init(
                project=self._settings.wandb_project,
                entity=self._settings.wandb_entity or None,
                config={
                    "llm_model": self._settings.llm_model,
                    "llm_provider": self._settings.llm_provider,
                    "temperature": self._settings.llm_temperature,
                },
            )
            logger.info("wandb_initialized", project=self._settings.wandb_project)
            return True
        except ImportError:
            logger.warning("wandb_not_installed")
            return False
        except Exception as exc:
            logger.error("wandb_init_error", error=str(exc))
            return False

    def log_generation(
        self,
        endpoint: str,
        prompt_tokens: int,
        completion_tokens: int,
        test_count: int,
    ) -> TokenCostMetric:
        total = prompt_tokens + completion_tokens
        model = self._settings.llm_model
        costs = COST_PER_1K_TOKENS.get(model, {"prompt": 0.003, "completion": 0.015})

        cost = (
            (prompt_tokens / 1000) * costs["prompt"]
            + (completion_tokens / 1000) * costs["completion"]
        )
        cost_per_test = cost / max(test_count, 1)

        entry = {
            "endpoint": endpoint,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total,
            "cost_usd": round(cost, 6),
            "cost_per_test": round(cost_per_test, 6),
            "test_count": test_count,
        }
        self._runs.append(entry)

        if self._wandb_run:
            try:
                import wandb

                wandb.log(entry)
            except Exception as exc:
                logger.warning("wandb_log_error", error=str(exc))

        logger.info(
            "token_usage",
            endpoint=endpoint,
            total_tokens=total,
            cost_usd=cost,
            cost_per_test=cost_per_test,
        )

        return TokenCostMetric(
            total_prompt_tokens=prompt_tokens,
            total_completion_tokens=completion_tokens,
            total_tokens=total,
            total_cost_usd=cost,
            avg_cost_per_test=cost_per_test,
        )

    def get_summary(self) -> TokenCostMetric:
        total_prompt = sum(r["prompt_tokens"] for r in self._runs)
        total_completion = sum(r["completion_tokens"] for r in self._runs)
        total_cost = sum(r["cost_usd"] for r in self._runs)
        total_tests = sum(r["test_count"] for r in self._runs)

        return TokenCostMetric(
            total_prompt_tokens=total_prompt,
            total_completion_tokens=total_completion,
            total_tokens=total_prompt + total_completion,
            total_cost_usd=total_cost,
            avg_cost_per_test=total_cost / max(total_tests, 1),
        )

    def finish(self) -> None:
        if self._wandb_run:
            try:
                import wandb

                summary = self.get_summary()
                wandb.log(
                    {
                        "summary_total_tokens": summary.total_tokens,
                        "summary_total_cost": summary.total_cost_usd,
                        "summary_avg_cost_per_test": summary.avg_cost_per_test,
                    }
                )
                wandb.finish()
            except Exception as exc:
                logger.warning("wandb_finish_error", error=str(exc))
