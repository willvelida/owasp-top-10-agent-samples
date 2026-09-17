"""FastAPI contract tests."""

from fastapi.testclient import TestClient

from api.main import app


def test_health_reports_local_rehearsal() -> None:
    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_full_unsafe_then_rollback_flow() -> None:
    with TestClient(app) as client:
        client.post("/demo/reset")
        unsafe = client.post("/demo/unsafe")
        rollback = client.post("/demo/rollback")

    assert unsafe.status_code == 200
    assert rollback.status_code == 200
    assert unsafe.json()["release_assistant"]["answer"].startswith(
        "Localization-only"
    )
    assert rollback.json()["query"]["answer"].startswith("Every production")


def test_query_rejects_unknown_persona() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/query",
            json={"persona": "intruder", "question": "What is the rule?"},
        )

    assert response.status_code == 400
