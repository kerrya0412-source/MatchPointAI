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
def test_analyst_evidence_respects_playback(seconds, demo_events):
    response = client.get(
        "/api/match/analyst",
        params={"seconds": seconds},
    )

    assert response.status_code == 200

    data = response.json()
    analysis = data["analysis"]
    validation = data["evidence_validation"]

    visible_events = {
        event.event_id: event
        for event in demo_events
        if event.minute * 60 + event.second <= seconds
    }

    assert data["playback_seconds"] == seconds
    assert data["event_count"] == len(visible_events)
    assert analysis["minute"] == seconds // 60
    assert analysis["second"] == seconds % 60
    assert isinstance(analysis["summary"], str)
    assert analysis["summary"]

    evidence_ids = analysis["evidence_event_ids"]

    assert len(evidence_ids) == len(set(evidence_ids))
    assert all(event_id in visible_events for event_id in evidence_ids)
    assert validation["total_references"] == len(evidence_ids)
    assert validation["verified_references"] == len(evidence_ids)
    assert validation["missing_event_ids"] == []
    assert validation["valid"] == bool(evidence_ids)