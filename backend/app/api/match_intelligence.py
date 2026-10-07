from fastapi import APIRouter

from backend.app.simulation.match_engine import SyntheticMatchEngine
from backend.app.analytics.match_pulse import calculate_match_pulse
from backend.app.intelligence.key_moment_detector import detect_key_moments
from backend.app.intelligence.why_explainer import build_why_explanation


router = APIRouter(
    prefix="/api/match",
    tags=["Match Intelligence"],
)


@router.get("/demo")
def get_demo_match():
    engine = SyntheticMatchEngine(seed=42)
    match = engine.create_match()

    events = engine.simulate_until(
        match=match,
        target_minute=10,
    )

    pulse = calculate_match_pulse(
        match=match,
        events=events,
    )

    key_moments = detect_key_moments(
        events=events,
        home_team_id=match.home_team.team_id,
        home_team_name=match.home_team.name,
        away_team_id=match.away_team.team_id,
        away_team_name=match.away_team.name,
    )

    explanations = [
        build_why_explanation(
            moment=moment,
            events=events,
        )
        for moment in key_moments
    ]

    return {
        "match": match,
        "match_pulse": pulse,
        "key_moments": key_moments,
        "why_explanations": explanations,
        "event_count": len(events),
        "events": events,
    }



