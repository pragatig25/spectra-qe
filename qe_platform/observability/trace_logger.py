from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Any, Generator

import structlog

from qe_platform.config import Settings

logger = structlog.get_logger()


def configure_tracing(settings: Settings | None = None) -> bool:
    settings = settings or Settings()
    if not settings.langchain_tracing_v2 or not settings.langchain_api_key:
        logger.info("langsmith_tracing_disabled")
        return False

    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_API_KEY"] = settings.langchain_api_key
    os.environ["LANGCHAIN_PROJECT"] = settings.langchain_project

    logger.info(
        "langsmith_tracing_enabled",
        project=settings.langchain_project,
    )
    return True


@contextmanager
def trace_span(
    name: str,
    metadata: dict[str, Any] | None = None,
) -> Generator[dict[str, Any], None, None]:
    context: dict[str, Any] = {"span_name": name, "metadata": metadata or {}}
    logger.info("trace_span_start", span=name)
    try:
        yield context
    except Exception as exc:
        context["error"] = str(exc)
        logger.error("trace_span_error", span=name, error=str(exc))
        raise
    finally:
        logger.info("trace_span_end", span=name)
