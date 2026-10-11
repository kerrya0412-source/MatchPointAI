from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def test_demo_match_api():
    response = client.get("/api/match/demo")

    assert response.status_code == 200

    data = response.json()

    expected_fields = {
        "match",
        "match_pulse",
        "key_moments",
        "why_explanations",
        "event_count",
        "events",
    }

    assert expected_fields.issubset(data.keys())
    assert data["event_count"] == len(data["events"])
    assert data["event_count"] > 0
    assert len(data["key_moments"]) == len(data["why_explanations"])
    assert len(data["key_moments"]) > 0