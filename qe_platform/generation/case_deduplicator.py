from __future__ import annotations

import numpy as np
import structlog

from qe_platform.config import Settings
from qe_platform.models.test_case import GeneratedTestCase

logger = structlog.get_logger()


class CaseDeduplicator:
    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or Settings()
        self._threshold = self._settings.dedup_similarity_threshold
        self._model = self._settings.embedding_model
        self._has_openai = bool(self._settings.openai_api_key)

    def _get_openai_client(self):  # type: ignore[no-untyped-def]
        from openai import OpenAI

        return OpenAI(api_key=self._settings.openai_api_key)

    def deduplicate(
        self, test_cases: list[GeneratedTestCase]
    ) -> list[GeneratedTestCase]:
        if len(test_cases) <= 1:
            return test_cases

        if not self._has_openai:
            logger.info(
                "deduplication_skipped",
                reason="no_openai_api_key",
                test_count=len(test_cases),
            )
            return test_cases

        texts = [self._case_to_text(tc) for tc in test_cases]
        try:
            embeddings = self._get_embeddings(texts)
        except Exception as exc:
            logger.warning(
                "deduplication_skipped",
                reason="embedding_error",
                error=str(exc),
                test_count=len(test_cases),
            )
            return test_cases
        similarity_matrix = self._cosine_similarity_matrix(embeddings)

        duplicates: set[int] = set()
        for i in range(len(test_cases)):
            if i in duplicates:
                continue
            for j in range(i + 1, len(test_cases)):
                if j in duplicates:
                    continue
                sim = similarity_matrix[i][j]
                if sim >= self._threshold:
                    test_cases[j].is_duplicate = True
                    test_cases[j].similarity_score = float(sim)
                    duplicates.add(j)

        unique = [tc for i, tc in enumerate(test_cases) if i not in duplicates]

        logger.info(
            "deduplication_complete",
            original=len(test_cases),
            unique=len(unique),
            removed=len(duplicates),
            threshold=self._threshold,
        )
        return unique

    def _case_to_text(self, tc: GeneratedTestCase) -> str:
        return (
            f"{tc.name} | {tc.test_type.value} | {tc.endpoint_path} {tc.method} | "
            f"{tc.description} | status={tc.expected_status} | "
            f"input={tc.input_data}"
        )

    def _get_embeddings(self, texts: list[str]) -> np.ndarray:
        client = self._get_openai_client()
        response = client.embeddings.create(
            model=self._model,
            input=texts,
        )
        vectors = [item.embedding for item in response.data]
        return np.array(vectors)

    @staticmethod
    def _cosine_similarity_matrix(embeddings: np.ndarray) -> np.ndarray:
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        norms = np.where(norms == 0, 1, norms)
        normalized = embeddings / norms
        return normalized @ normalized.T
