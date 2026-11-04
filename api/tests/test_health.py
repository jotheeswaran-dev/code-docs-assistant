from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


def client(**overrides: str) -> TestClient:
    return TestClient(create_app(Settings(**overrides)))


def test_health_reports_ok():
    body = client().get("/health").json()
    assert body["status"] == "ok"
    assert body["version"]


def test_health_reports_a_missing_key():
    assert client(anthropic_api_key="").get("/health").json()["anthropic_key_set"] is False


def test_health_never_returns_the_key():
    response = client(anthropic_api_key="secret-value").get("/health")
    assert response.json()["anthropic_key_set"] is True
    assert "secret-value" not in response.text
