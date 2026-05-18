from __future__ import annotations

from pathlib import Path

import pytest

from qe_platform.ingestion.spec_parser import parse_openapi, parse_user_story
from qe_platform.models.spec import HttpMethod


class TestParseOpenAPI:
    def test_parses_petstore_spec(self, demo_spec_path: Path) -> None:
        spec = parse_openapi(demo_spec_path)
        assert spec.title == "Petstore API"
        assert spec.version == "1.0.0"
        assert spec.base_url == "https://petstore.example.com/api/v1"
        assert len(spec.endpoints) == 7

    def test_extracts_all_methods(self, demo_spec_path: Path) -> None:
        spec = parse_openapi(demo_spec_path)
        methods = {(ep.path, ep.method) for ep in spec.endpoints}
        assert ("/pets", HttpMethod.GET) in methods
        assert ("/pets", HttpMethod.POST) in methods
        assert ("/pets/{petId}", HttpMethod.GET) in methods
        assert ("/pets/{petId}", HttpMethod.PUT) in methods
        assert ("/pets/{petId}", HttpMethod.DELETE) in methods

    def test_parses_parameters(self, demo_spec_path: Path) -> None:
        spec = parse_openapi(demo_spec_path)
        list_pets = next(
            ep for ep in spec.endpoints
            if ep.path == "/pets" and ep.method == HttpMethod.GET
        )
        assert len(list_pets.parameters) == 2
        limit_param = next(p for p in list_pets.parameters if p.name == "limit")
        assert limit_param.location == "query"
        assert limit_param.param_type == "integer"
        assert not limit_param.required

    def test_parses_request_body(self, demo_spec_path: Path) -> None:
        spec = parse_openapi(demo_spec_path)
        create_pet = next(
            ep for ep in spec.endpoints
            if ep.path == "/pets" and ep.method == HttpMethod.POST
        )
        assert create_pet.request_body is not None
        assert create_pet.request_body.required is True
        assert create_pet.request_body.content_type == "application/json"

    def test_parses_auth_requirements(self, demo_spec_path: Path) -> None:
        spec = parse_openapi(demo_spec_path)
        create_pet = next(
            ep for ep in spec.endpoints
            if ep.path == "/pets" and ep.method == HttpMethod.POST
        )
        assert create_pet.requires_auth is True

        list_pets = next(
            ep for ep in spec.endpoints
            if ep.path == "/pets" and ep.method == HttpMethod.GET
        )
        assert list_pets.requires_auth is False

    def test_parses_responses(self, demo_spec_path: Path) -> None:
        spec = parse_openapi(demo_spec_path)
        create_pet = next(
            ep for ep in spec.endpoints
            if ep.path == "/pets" and ep.method == HttpMethod.POST
        )
        status_codes = {r.status_code for r in create_pet.responses}
        assert 201 in status_codes
        assert 400 in status_codes
        assert 401 in status_codes

    def test_source_type_is_openapi(self, demo_spec_path: Path) -> None:
        spec = parse_openapi(demo_spec_path)
        assert spec.source_type == "openapi"


class TestParseUserStory:
    def test_parses_single_story(self) -> None:
        content = """\
## Create Pet

As a user, I want to create a pet so I can track it.

Acceptance Criteria:
- Pet is saved with name and species
- Returns 201 on success
- Returns 400 if name is missing
"""
        spec = parse_user_story(content)
        assert spec.source_type == "user_story"
        assert "Create Pet" in spec.title

    def test_parses_plain_text(self) -> None:
        content = "Users should be able to list all pets via GET /pets"
        spec = parse_user_story(content)
        assert spec.source_type == "user_story"
        assert spec.description
