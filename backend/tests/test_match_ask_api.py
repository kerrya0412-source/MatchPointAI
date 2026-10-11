from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.simulation.match_engine import SyntheticMatchEngine
from backend.app.analytics.attacking import calculate_attacking_activity


client = TestClient(app)


def test_ask_matchpoint_verified_statistics():
    engine = SyntheticMatchEngine(seed=42)
    match = engine.create_match()
    events = engine.simulate_until(match=match, target_minute=10)

    home = calculate_attacking_activity(events, match.home_team.team_id)
    away = calculate_attacking_activity(events, match.away_team.team_id)

    captured = {}

    def fake_answer(self, question, facts):
        captured["facts"] = facts
        return {
            "answer": "Verified statistics available.",
            "evidence_event_ids": [],
        }

    with patch(
        "backend.app.api.match_intelligence.MatchQuestionService.answer",
        new=fake_answer,
    ):
        response = client.post(
            "/api/match/ask",
            json={"question": "How many shots per team?", "seconds": 605},
        )

    assert response.status_code == 200, response.text

    facts = captured["facts"]

    for team, stats in (
        (match.home_team, home),
        (match.away_team, away),
    ):
        assert (
            f"Verified statistics for {team.name}: "
            f"{stats.shots} total shots, "
            f"{stats.shots_on_target} shots on target, "
            f"{stats.goals} goals."
        ) in facts

        assert stats.shots >= stats.shots_on_target >= stats.goals

    assert (
        "Goals are included in both total shots and shots on target."
        in facts
    )


def test_ask_matchpoint_final_score():
    captured = {}

    def fake_answer(self, question, facts):
        captured["facts"] = facts
        return {
            "answer": "Final simulation score available.",
            "evidence_event_ids": [],
        }

    with patch(
        "backend.app.api.match_intelligence.MatchQuestionService.answer",
        new=fake_answer,
    ):
        response = client.post(
            "/api/match/ask",
            json={"question": "What is the final score?", "seconds": 605},
        )

    assert response.status_code == 200, response.text

    engine = SyntheticMatchEngine(seed=42)
    match = engine.create_match()
    events = engine.simulate_until(match=match, target_minute=10)

    home_goals = sum(
        e.event_type.value == "goal"
        and e.team_id == match.home_team.team_id
        for e in events
    )
    away_goals = sum(
        e.event_type.value == "goal"
        and e.team_id == match.away_team.team_id
        for e in events
    )

    expected = (
        f"Final 10-minute simulation score: "
        f"{match.home_team.name} {home_goals}, "
        f"{match.away_team.name} {away_goals}."
    )

    assert expected in captured["facts"]
    assert home_goals + away_goals == 3