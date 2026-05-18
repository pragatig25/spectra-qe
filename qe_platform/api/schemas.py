from __future__ import annotations

from pydantic import BaseModel, Field


class ParseRequest(BaseModel):
    spec_content: str | None = None
    spec_id: str | None = Field(None, description="ID of a demo spec: petstore, github")


class ParseResponse(BaseModel):
    title: str
    version: str
    base_url: str
    description: str
    endpoint_count: int
    endpoints: list[dict]
    source_type: str


class RiskScoreRequest(BaseModel):
    spec_content: str | None = None
    spec_id: str | None = None


class RiskScoreResponse(BaseModel):
    spec_title: str
    total_endpoints: int
    tier_distribution: dict[str, int]
    assessments: list[dict]


class GenerateRequest(BaseModel):
    spec_content: str | None = None
    spec_id: str | None = None
    skip_execution: bool = True
    base_url: str = ""


class GenerateResponse(BaseModel):
    run_id: str
    spec_title: str
    total_endpoints: int
    total_tests_generated: int
    total_tests_after_dedup: int
    duplicates_removed: int
    suites: list[dict]
    report: dict | None = None


class DemoSpec(BaseModel):
    id: str
    name: str
    description: str
    endpoint_count: int


class ReportRequest(BaseModel):
    spec_content: str | None = None
    spec_id: str | None = None


class ReportExportRequest(BaseModel):
    report: dict
    format: str = "json"


class ReportExportResponse(BaseModel):
    content: str
    filename: str
    format: str


class HealthResponse(BaseModel):
    status: str = "healthy"
    version: str
    llm_provider: str
    llm_model: str
    demo_mode: bool = False
