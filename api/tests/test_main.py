"""Tests for the ASGI application."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from api.main import app


@pytest.fixture(scope="module")
def client() -> TestClient:
    return TestClient(app)


def test_health_reports_ok(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": "0.1.0"}


def test_graphql_endpoint_answers_a_query(client: TestClient) -> None:
    response = client.post(
        "/graphql",
        json={"query": "{ company { name latestQuarter { id } } }"},
    )
    assert response.status_code == 200
    assert response.json() == {
        "data": {"company": {"name": "Sanofi", "latestQuarter": {"id": "Q1-2026"}}}
    }


def test_graphql_reports_invalid_queries(client: TestClient) -> None:
    response = client.post("/graphql", json={"query": "{ nonsense }"})
    assert response.status_code == 200
    assert response.json()["errors"]


def test_graphql_playground_is_served(client: TestClient) -> None:
    response = client.get("/graphql", headers={"Accept": "text/html"})
    assert response.status_code == 200


def test_cors_allows_the_vite_dev_server(client: TestClient) -> None:
    response = client.options(
        "/graphql",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
        },
    )
    assert response.status_code == 200
    assert (
        response.headers["access-control-allow-origin"] == "http://localhost:5173"
    )
