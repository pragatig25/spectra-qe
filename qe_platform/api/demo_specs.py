from __future__ import annotations

from pathlib import Path

DEMO_DIR = Path(__file__).parent.parent.parent / "demo"

DEMO_SPECS: dict[str, dict] = {
    "petstore": {
        "name": "Petstore API",
        "description": "Pet management API with CRUD operations, auth, and vaccinations",
        "file": "petstore_openapi.yaml",
    },
    "github": {
        "name": "GitHub Repos API",
        "description": "CI/CD: PRs, deployments, secrets, branch protection",
        "file": "github_repos_openapi.yaml",
    },
}


def get_demo_spec_path(spec_id: str) -> Path | None:
    spec = DEMO_SPECS.get(spec_id)
    if not spec:
        return None
    path = DEMO_DIR / spec["file"]
    return path if path.exists() else None


def get_demo_spec_content(spec_id: str) -> str | None:
    path = get_demo_spec_path(spec_id)
    if not path:
        return None
    return path.read_text()


def list_demo_specs() -> list[dict]:
    results = []
    for spec_id, info in DEMO_SPECS.items():
        path = DEMO_DIR / info["file"]
        endpoint_count = 0
        if path.exists():
            import yaml

            raw = yaml.safe_load(path.read_text())
            paths = raw.get("paths", {})
            for path_item in paths.values():
                for method in path_item:
                    if method.lower() in {"get", "post", "put", "patch", "delete", "head", "options"}:
                        endpoint_count += 1

        results.append(
            {
                "id": spec_id,
                "name": info["name"],
                "description": info["description"],
                "endpoint_count": endpoint_count,
            }
        )
    return results
