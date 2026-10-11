from backend.app.simulation.match_engine import SyntheticMatchEngine
from backend.app.intelligence.key_moment_detector import detect_key_moments
from backend.app.models.key_moment import KeyMomentType


def test_key_moments_and_evidence_timing():
    engine = SyntheticMatchEngine(seed=42)
    match = engine.create_match()
    events = engine.simulate_until(match=match, target_minute=10)

    moments = detect_key_moments(
        events=events,
        home_team_id=match.home_team.team_id,
        home_team_name=match.home_team.name,
        away_team_id=match.away_team.team_id,
        away_team_name=match.away_team.name,
    )

    assert len(moments) == 9

    surges = [
        moment for moment in moments
        if moment.moment_type == KeyMomentType.PRESSURE_SURGE
    ]

    assert {(m.team_name, m.minute, m.second) for m in surges} == {
        ("North City", 3, 59),
        ("South United", 5, 59),
    }

    events_by_id = {event.event_id: event for event in events}
    previous_time = -1

    for moment in moments:
        timestamp = moment.minute * 60 + moment.second

        assert timestamp >= previous_time
        previous_time = timestamp

        for event_id in moment.evidence_event_ids:
            assert event_id in events_by_id

            event = events_by_id[event_id]
            event_time = event.minute * 60 + event.second

            assert event_time <= timestamp
