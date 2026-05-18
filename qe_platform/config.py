from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    # LLM Provider
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    llm_provider: str = Field(default="openai", pattern="^(openai|anthropic)$")
    llm_model: str = "gpt-4o"
    embedding_model: str = "text-embedding-3-small"
    llm_temperature: float = 0.2

    # LangSmith
    langchain_tracing_v2: bool = False
    langchain_api_key: str = ""
    langchain_project: str = "qe-platform"

    # Weights & Biases
    wandb_api_key: str = ""
    wandb_project: str = "qe-platform"
    wandb_entity: str = ""

    # Execution
    max_concurrent_tests: int = 5
    self_heal_max_retries: int = 2
    dedup_similarity_threshold: float = 0.92

    # Paths
    reports_dir: Path = Path("reports")
    generated_tests_dir: Path = Path("generated_tests")
