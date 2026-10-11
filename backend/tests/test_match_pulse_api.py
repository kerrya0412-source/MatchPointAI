import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.simulation.match_engine import SyntheticMatchEngine


client = TestClient(app)


@pytest.fixture(scope="module")
def demo_events():
    engine = SyntheticMatchEngine(seed=42)
    match = engine.create_match()
    return engine.simulate_until(match=match, target_minute=10)


@pytest.mark.parametrize("seconds", [0, 60, 180, 300, 600])
def test_pulse_respects_playback_time(seconds, demo_events):
    response = client.get("/api/match/pulse", params={"seconds": seconds})

    assert response.status_code == 200

    data = response.json()

    expected_count = sum(
        event.minute * 60 + event.second <= seconds
        for event in demo_events
    )

    assert data["playback_seconds"] == seconds
    assert data["event_count"] == expected_count
    assert "match_pulse" in data


@pytest.mark.parametrize(
    "requested,expected",
    [(-100, 0), (9999, 605)],
)
def test_pulse_clamps_playback_time(requested, expected):
    response = client.get(
        "/api/match/pulse",
        params={"seconds": requested},
    )

    assert response.status_code == 200
    assert response.json()["playback_seconds"] == expected