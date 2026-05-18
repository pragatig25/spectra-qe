from __future__ import annotations

from fastapi.testclient import TestClient

from qe_platform.api.app import app

client = TestClient(app)


class TestHealthEndpoint:
    def test_returns_healthy(self) -> None:
        r = client.get("/api/health")
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "llm_provider" in data

    def test_returns_version(self) -> None:
        r = client.get("/api/health")
        assert r.json()["version"] == "0.1.0"


class TestSpecsEndpoint:
    def test_returns_list(self) -> None:
        r = client.get("/api/specs")
        assert r.status_code == 200
        specs = r.json()
        assert isinstance(specs, list)
        assert len(specs) >= 1

    def test_petstore_spec_available(self) -> None:
        r = client.get("/api/specs")
        ids = [s["id"] for s in r.json()]
        assert "petstore" in ids


class TestParseEndpoint:
    def test_parse_demo_spec(self) -> None:
        r = client.post("/api/parse", json={"spec_id": "petstore"})
        assert r.status_code == 200
        data = r.json()
        assert data["title"] == "Petstore API"
        assert data["endpoint_count"] == 7
        assert len(data["endpoints"]) == 7

    def test_parse_invalid_spec_id(self) -> None:
        r = client.post("/api/parse", json={"spec_id": "nonexistent"})
        assert r.status_code == 404

    def test_parse_no_input(self) -> None:
        r = client.post("/api/parse", json={})
        assert r.status_code == 400

    def test_parse_endpoints_have_methods(self) -> None:
        r = client.post("/api/parse", json={"spec_id": "petstore"})
        endpoints = r.json()["endpoints"]
        methods = {ep["method"] for ep in endpoints}
        assert "GET" in methods
        assert "POST" in methods
        assert "DELETE" in methods

    def test_parse_shows_auth(self) -> None:
        r = client.post("/api/parse", json={"spec_id": "petstore"})
        endpoints = r.json()["endpoints"]
        auth_endpoints = [ep for ep in endpoints if ep["requires_auth"]]
        no_auth = [ep for ep in endpoints if not ep["requires_auth"]]
        assert len(auth_endpoints) > 0
        assert len(no_auth) > 0
