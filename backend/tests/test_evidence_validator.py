import pytest

from backend.app.agents.evidence_validator import EvidenceValidatorAgent
from backend.app.simulation.match_engine import SyntheticMatchEngine


@pytest.fixture
def sample_events():
    engine = SyntheticMatchEngine(seed=42)
    match = engine.create_match()
    return engine.simulate_until(match=match, target_minute=10)


def test_valid_evidence(sample_events):
    ids = [event.event_id for event in sample_events[:3]]
    result = EvidenceValidatorAgent().validate(sample_events, ids)

    assert result.valid
    assert result.total_references == 3
    assert result.verified_references == 3
    assert result.missing_event_ids == []


def test_missing_event_id(sample_events):
    result = EvidenceValidatorAgent().validate(
        sample_events, ["nonexistent-event"]
    )

    assert not result.valid
    assert result.verified_references == 0
    assert result.missing_event_ids == ["nonexistent-event"]


def test_duplicate_evidence(sample_events):
    event_id = sample_events[0].event_id
    result = EvidenceValidatorAgent().validate(
        sample_events, [event_id, event_id]
    )

    assert not result.valid
    assert result.total_references == 2
    assert result.verified_references == 2
    assert any("duplicate" in text.lower() for text in result.observations)


def test_empty_evidence(sample_events):
    result = EvidenceValidatorAgent().validate(sample_events, [])

    assert not result.valid
    assert result.total_references == 0
    assert result.verified_references == 0


def test_mixed_valid_and_invalid_evidence(sample_events):
    valid_id = sample_events[0].event_id
    result = EvidenceValidatorAgent().validate(
        sample_events, [valid_id, "missing-event"]
    )

    assert not result.valid
    assert result.total_references == 2
    assert result.verified_references == 1
    assert result.missing_event_ids == ["missing-event"]
