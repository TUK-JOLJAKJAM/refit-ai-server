from fastapi.testclient import TestClient

from app.demo import build_demo_session
from main import app


client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_demo_analysis() -> None:
    response = client.post("/api/v1/analyze_session", json=build_demo_session())
    assert response.status_code == 200
    body = response.json()
    assert body["score"] > 0
    assert body["metrics"]["total_actions"] == 6
    assert body["data_quality"]["status"] == "GOOD"
    assert body["difficulty_recommend"] in {"UP", "MAINTAIN", "DOWN"}


def test_current_unity_legacy_game_data_is_accepted() -> None:
    payload = {
        "historyId": "legacy-history",
        "gameId": "Adventure",
        "primaryPart": "SHOULDER",
        "actionCount": 2,
        "successCount": 1,
        "failCount": 1,
        "gameData": [
            {"attackGrade, GyroQuaternion, attackTime": "Good, (0.0, 0.2, 0.0, 0.98), 0.42"},
            {"attackGrade, GyroQuaternion, attackTime": "Miss, (0.0, 0.1, 0.0, 0.99), 1.00"},
        ],
    }
    response = client.post("/api/v1/analyze_session", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["metrics"]["success_rate"] == 0.5
    assert "LEGACY_COMPOSITE_ACTION" in body["data_quality"]["flags"]
    assert "MISSING_ROM" in body["data_quality"]["flags"]


def test_empty_payload_returns_low_confidence_result() -> None:
    response = client.post("/api/v1/analyze_session", json={})
    assert response.status_code == 200
    body = response.json()
    assert body["score"] == 0
    assert body["data_quality"]["status"] == "INSUFFICIENT"
    assert body["data_quality"]["assessable"] is False
    assert body["safety_status"] == "UNKNOWN"
