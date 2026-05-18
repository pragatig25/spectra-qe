from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class HttpMethod(str, Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"


class EndpointParameter(BaseModel):
    name: str
    location: str = Field(description="query, path, header, cookie")
    param_type: str = Field(default="string", description="JSON Schema type")
    required: bool = False
    description: str = ""
    example: str | None = None
    enum: list[str] | None = None


class RequestBody(BaseModel):
    content_type: str = "application/json"
    schema_def: dict = Field(default_factory=dict, description="JSON Schema definition")
    required: bool = False
    example: dict | None = None


class ResponseSpec(BaseModel):
    status_code: int
    description: str = ""
    schema_def: dict = Field(default_factory=dict)


class EndpointSpec(BaseModel):
    path: str
    method: HttpMethod
    operation_id: str = ""
    summary: str = ""
    description: str = ""
    tags: list[str] = Field(default_factory=list)
    parameters: list[EndpointParameter] = Field(default_factory=list)
    request_body: RequestBody | None = None
    responses: list[ResponseSpec] = Field(default_factory=list)
    security: list[dict] = Field(default_factory=list)
    requires_auth: bool = False


class ParsedSpec(BaseModel):
    title: str = ""
    version: str = ""
    base_url: str = ""
    description: str = ""
    endpoints: list[EndpointSpec] = Field(default_factory=list)
    source_type: str = Field(default="openapi", description="openapi or user_story")
    raw_spec: dict | None = None


class UserStory(BaseModel):
    title: str
    description: str
    acceptance_criteria: list[str] = Field(default_factory=list)
    endpoints: list[EndpointSpec] = Field(default_factory=list)
