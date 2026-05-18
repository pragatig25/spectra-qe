from __future__ import annotations

from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from qe_platform.generation.case_deduplicator import CaseDeduplicator
from qe_platform.models.test_case import GeneratedTestCase, TestType


@pytest.fixture
def mock_settings() -> MagicMock:
    settings = MagicMock()
    settings.dedup_similarity_threshold = 0.92
    settings.openai_api_key = "test-key"
    settings.embedding_model = "text-embedding-3-small"
    return settings


class TestCaseDeduplicator:
    def test_returns_single_case_unchanged(self, mock_settings: MagicMock) -> None:
        tc = GeneratedTestCase(
            id="tc_1",
            name="test_one",
            test_type=TestType.HAPPY_PATH,
        )
        with patch.object(CaseDeduplicator, "__init__", lambda self, s=None: None):
            dedup = CaseDeduplicator.__new__(CaseDeduplicator)
            dedup._threshold = 0.92
            result = dedup.deduplicate([tc])
        assert len(result) == 1

    def test_removes_near_duplicates(self, mock_settings: MagicMock) -> None:
        cases = [
            GeneratedTestCase(
                id="tc_1",
                name="test_create_pet_valid",
                test_type=TestType.HAPPY_PATH,
                endpoint_path="/pets",
                method="POST",
                description="Creates pet with valid data",
            ),
            GeneratedTestCase(
                id="tc_2",
                name="test_create_pet_valid_input",
                test_type=TestType.HAPPY_PATH,
                endpoint_path="/pets",
                method="POST",
                description="Creates pet with valid input data",
            ),
            GeneratedTestCase(
                id="tc_3",
                name="test_create_pet_no_auth",
                test_type=TestType.AUTH_BYPASS,
                endpoint_path="/pets",
                method="POST",
                description="Attempts creation without authentication",
            ),
        ]

        embeddings = np.array([
            [1.0, 0.0, 0.0],
            [0.99, 0.05, 0.0],
            [0.0, 1.0, 0.0],
        ])

        with patch.object(CaseDeduplicator, "__init__", lambda self, s=None: None):
            dedup = CaseDeduplicator.__new__(CaseDeduplicator)
            dedup._threshold = 0.92
            dedup._settings = mock_settings
            dedup._client = MagicMock()
            dedup._model = "text-embedding-3-small"
            dedup._has_openai = True

        with patch.object(dedup, "_get_embeddings", return_value=embeddings):
            result = dedup.deduplicate(cases)

        assert len(result) == 2
        result_ids = {tc.id for tc in result}
        assert "tc_1" in result_ids
        assert "tc_3" in result_ids

    def test_cosine_similarity_matrix(self) -> None:
        embeddings = np.array([
            [1.0, 0.0],
            [0.0, 1.0],
            [1.0, 0.0],
        ])
        matrix = CaseDeduplicator._cosine_similarity_matrix(embeddings)
        assert matrix[0][2] == pytest.approx(1.0, abs=0.01)
        assert matrix[0][1] == pytest.approx(0.0, abs=0.01)
