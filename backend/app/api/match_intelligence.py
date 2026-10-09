from fastapi import APIRouter

from backend.app.simulation.match_engine import SyntheticMatchEngine
from backend.app.analytics.match_pulse import calculate_match_pulse
from backend.app.intelligence.key_moment_detector import detect_key_moments
from backend.app.intelligence.why_explainer import build_why_explanation


from backend.app.services.azure_commentary_service import AzureCommentaryService

azure_commentary = AzureCommentaryService()
azure_goal_cache = {}

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





@router.get("/pulse")
def get_live_match_pulse(seconds: int = 0):
    seconds = max(0, min(seconds, 605))

    engine = SyntheticMatchEngine(seed=42)
    match = engine.create_match()

    events = engine.simulate_until(
        match=match,
        target_minute=10,
    )

    visible_events = [
        event
        for event in events
        if event.minute * 60 + event.second <= seconds
    ]

    match.minute = seconds // 60
    match.second = seconds % 60

    pulse = calculate_match_pulse(
        match=match,
        events=visible_events,
    )

    return {
        "playback_seconds": seconds,
        "event_count": len(visible_events),
        "match_pulse": pulse,
    }


@router.get("/analyst")
def get_match_analyst(seconds: int = 0):
    from backend.app.agents.match_analyst import MatchAnalystAgent

    seconds = max(0, min(seconds, 605))

    engine = SyntheticMatchEngine(seed=42)
    match = engine.create_match()

    events = engine.simulate_until(
        match=match,
        target_minute=10,
    )

    visible_events = [
        event
        for event in events
        if event.minute * 60 + event.second <= seconds
    ]

    match.minute = seconds // 60
    match.second = seconds % 60

    pulse = calculate_match_pulse(
        match=match,
        events=visible_events,
    )

    agent = MatchAnalystAgent()

    analysis = agent.analyze(
        match=match,
        events=visible_events,
        pulse=pulse,
    )

    from backend.app.agents.evidence_validator import EvidenceValidatorAgent

    validation = EvidenceValidatorAgent().validate(
        events=visible_events,
        evidence_event_ids=analysis.evidence_event_ids,
    )

    return {
        "playback_seconds": seconds,
        "event_count": len(visible_events),
        "analysis": analysis,
        "evidence_validation": validation,
    }


@router.get("/tactical")
def get_tactical_intelligence(seconds: int = 0):
    from backend.app.agents.tactical_intelligence import TacticalIntelligenceAgent

    seconds = max(0, min(seconds, 605))

    engine = SyntheticMatchEngine(seed=42)
    match = engine.create_match()

    events = engine.simulate_until(
        match=match,
        target_minute=10,
    )

    visible_events = [
        event
        for event in events
        if event.minute * 60 + event.second <= seconds
    ]

    match.minute = seconds // 60
    match.second = seconds % 60

    pulse = calculate_match_pulse(
        match=match,
        events=visible_events,
    )

    analysis = TacticalIntelligenceAgent().analyze(
        match=match,
        events=visible_events,
        pulse=pulse,
    )

    from backend.app.agents.evidence_validator import EvidenceValidatorAgent

    validation = EvidenceValidatorAgent().validate(
        events=visible_events,
        evidence_event_ids=analysis.evidence_event_ids,
    )

    return {
        "playback_seconds": seconds,
        "event_count": len(visible_events),
        "analysis": analysis,
        "evidence_validation": validation,
    }




@router.get("/storyteller")
def get_match_storyteller(seconds: int = 0, audience: str = "analyst"):
    from fastapi import HTTPException
    from backend.app.agents.match_analyst import MatchAnalystAgent
    from backend.app.agents.tactical_intelligence import TacticalIntelligenceAgent
    from backend.app.agents.evidence_validator import EvidenceValidatorAgent
    from backend.app.agents.storyteller import StorytellerAgent

    storyteller = StorytellerAgent()
    audience = audience.lower().strip()

    if audience not in storyteller.SUPPORTED_AUDIENCES:
        raise HTTPException(
            status_code=422,
            detail=f"Unsupported audience: {audience}",
        )

    seconds = max(0, min(seconds, 605))

    engine = SyntheticMatchEngine(seed=42)
    match = engine.create_match()
    events = engine.simulate_until(match=match, target_minute=10)

    visible_events = [
        event for event in events
        if event.minute * 60 + event.second <= seconds
    ]

    match.minute = seconds // 60
    match.second = seconds % 60

    pulse = calculate_match_pulse(
        match=match,
        events=visible_events,
    )

    match_analysis = MatchAnalystAgent().analyze(
        match, visible_events, pulse
    )

    tactical_analysis = TacticalIntelligenceAgent().analyze(
        match, visible_events, pulse
    )

    validator = EvidenceValidatorAgent()

    match_validation = validator.validate(
        visible_events,
        match_analysis.evidence_event_ids,
    )

    tactical_validation = validator.validate(
        visible_events,
        tactical_analysis.evidence_event_ids,
    )

    narrative = storyteller.generate(
        match_analysis,
        tactical_analysis,
        match_validation,
        tactical_validation,
        audience=audience,
    )

    commentary_source = "deterministic"
    ai_commentary_validated = False

    # Azure commentary is optional and never bypasses evidence validation.
    if narrative.evidence_verified:
        goal_events = [
            event for event in visible_events
            if event.event_type.value == "goal"
        ]

        if goal_events:
            latest_goal = goal_events[-1]
            goal_second = latest_goal.minute * 60 + latest_goal.second

            # Cache by goal moment and audience, not playback timestamp.
            cache_key = (goal_second, audience)

            # Calculate the score for both new and cached commentary.
            home_goals = sum(
                event.team_id == match.home_team.team_id
                for event in goal_events
            )
            away_goals = sum(
                event.team_id == match.away_team.team_id
                for event in goal_events
            )

            if cache_key not in azure_goal_cache:
                # Use only facts associated with this goal.
                # Never include analysis from a later playback time.
                facts = (
                    f"Goal time: {latest_goal.minute:02d}:"
                    f"{latest_goal.second:02d}. "
                    f"Scoring team: {latest_goal.team_name}. "
                    f"Score immediately after this goal: "
                    f"{match.home_team.name} {home_goals}, "
                    f"{match.away_team.name} {away_goals}. "
                    f"Expected goals for this chance: "
                    f"{latest_goal.expected_goals}. "
                    "Describe only this goal using these facts."
                )

                azure_goal_cache[cache_key] = (
                    azure_commentary.generate_cached(facts, audience)
                )

            ai_text = azure_goal_cache.get(cache_key)

            if ai_text:
                from backend.app.agents.commentary_validator import (
                    CommentaryValidator,
                )

                result = CommentaryValidator().validate(
                    commentary=ai_text,
                    scoring_team=latest_goal.team_name,
                    goal_minute=latest_goal.minute,
                    goal_second=latest_goal.second,
                    home_team=match.home_team.name,
                    away_team=match.away_team.name,
                    home_goals=home_goals,
                    away_goals=away_goals,
                )

                if result.valid:
                    narrative.narrative = ai_text
                    commentary_source = "azure"
                    ai_commentary_validated = True
                else:
                    # Reject invalid AI text and retain deterministic fallback.
                    # Remember rejection to avoid repeated Azure charges.
                    azure_goal_cache[cache_key] = None

    return {
        "playback_seconds": seconds,
        "audience": audience,
        "narrative": narrative,
        "commentary_source": commentary_source,
        "ai_commentary_validated": ai_commentary_validated,
        "match_validation": match_validation,
        "tactical_validation": tactical_validation,
    }
