from __future__ import annotations

from pathlib import Path

import structlog
import yaml

from qe_platform.models.spec import (
    EndpointParameter,
    EndpointSpec,
    HttpMethod,
    ParsedSpec,
    RequestBody,
    ResponseSpec,
    UserStory,
)

logger = structlog.get_logger()

_HTTP_METHODS = {m.value.lower() for m in HttpMethod}


def parse_openapi(source: str | Path) -> ParsedSpec:
    raw = _load_source(source)
    info = raw.get("info", {})
    servers = raw.get("servers", [])
    base_url = servers[0].get("url", "") if servers else ""

    endpoints: list[EndpointSpec] = []
    paths = raw.get("paths", {})

    for path, path_item in paths.items():
        for method_str, operation in path_item.items():
            if method_str.lower() not in _HTTP_METHODS:
                continue

            parameters = _parse_parameters(
                operation.get("parameters", []) + path_item.get("parameters", [])
            )
            request_body = _parse_request_body(operation.get("requestBody"))
            responses = _parse_responses(operation.get("responses", {}))
            security = operation.get("security", raw.get("security", []))

            endpoint = EndpointSpec(
                path=path,
                method=HttpMethod(method_str.upper()),
                operation_id=operation.get("operationId", ""),
                summary=operation.get("summary", ""),
                description=operation.get("description", ""),
                tags=operation.get("tags", []),
                parameters=parameters,
                request_body=request_body,
                responses=responses,
                security=security,
                requires_auth=bool(security),
            )
            endpoints.append(endpoint)

    spec = ParsedSpec(
        title=info.get("title", ""),
        version=info.get("version", ""),
        base_url=base_url,
        description=info.get("description", ""),
        endpoints=endpoints,
        source_type="openapi",
        raw_spec=raw,
    )

    logger.info(
        "parsed_openapi_spec",
        title=spec.title,
        endpoint_count=len(spec.endpoints),
    )
    return spec


def parse_user_story(source: str | Path) -> ParsedSpec:
    path = Path(source)
    if path.is_file():
        content = path.read_text()
    else:
        content = str(source)

    stories = _extract_user_stories(content)
    endpoints: list[EndpointSpec] = []
    for story in stories:
        endpoints.extend(story.endpoints)

    spec = ParsedSpec(
        title=stories[0].title if stories else "User Story Spec",
        description=content[:500],
        endpoints=endpoints,
        source_type="user_story",
    )

    logger.info(
        "parsed_user_stories",
        story_count=len(stories),
        endpoint_count=len(endpoints),
    )
    return spec


def _load_source(source: str | Path) -> dict:
    path = Path(source)
    if path.is_file():
        text = path.read_text()
    else:
        text = str(source)

    return yaml.safe_load(text)


def _parse_parameters(raw_params: list[dict]) -> list[EndpointParameter]:
    seen: set[str] = set()
    params: list[EndpointParameter] = []

    for p in raw_params:
        key = f"{p.get('in', 'query')}:{p.get('name', '')}"
        if key in seen:
            continue
        seen.add(key)

        schema = p.get("schema", {})
        params.append(
            EndpointParameter(
                name=p.get("name", ""),
                location=p.get("in", "query"),
                param_type=schema.get("type", "string"),
                required=p.get("required", False),
                description=p.get("description", ""),
                example=(
                    str(schema.get("example", "")) if schema.get("example") else None
                ),
                enum=schema.get("enum"),
            )
        )
    return params


def _parse_request_body(raw: dict | None) -> RequestBody | None:
    if not raw:
        return None

    content = raw.get("content", {})
    content_type = next(iter(content), "application/json")
    media = content.get(content_type, {})
    schema = media.get("schema", {})
    example = media.get("example")

    return RequestBody(
        content_type=content_type,
        schema_def=schema,
        required=raw.get("required", False),
        example=example,
    )


def _parse_responses(raw: dict) -> list[ResponseSpec]:
    responses: list[ResponseSpec] = []
    for status_code, resp in raw.items():
        try:
            code = int(status_code)
        except ValueError:
            code = 0

        content = resp.get("content", {})
        schema = {}
        if content:
            first_media = next(iter(content.values()), {})
            schema = first_media.get("schema", {})

        responses.append(
            ResponseSpec(
                status_code=code,
                description=resp.get("description", ""),
                schema_def=schema,
            )
        )
    return responses


def _extract_user_stories(content: str) -> list[UserStory]:
    stories: list[UserStory] = []
    sections = content.split("##")

    for section in sections:
        section = section.strip()
        if not section:
            continue

        lines = section.split("\n")
        title = lines[0].strip().lstrip("#").strip()
        description_lines: list[str] = []
        criteria: list[str] = []
        in_criteria = False

        for line in lines[1:]:
            stripped = line.strip()
            if stripped.lower().startswith(
                "acceptance criteria"
            ) or stripped.lower().startswith("ac:"):
                in_criteria = True
                continue
            if in_criteria and stripped.startswith("- "):
                criteria.append(stripped[2:])
            elif not in_criteria:
                description_lines.append(stripped)

        stories.append(
            UserStory(
                title=title,
                description="\n".join(description_lines).strip(),
                acceptance_criteria=criteria,
            )
        )

    if not stories and content.strip():
        stories.append(
            UserStory(
                title="User Story",
                description=content.strip()[:500],
            )
        )

    return stories
