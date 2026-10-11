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
    from fastapi import HTTPException, Request
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


# Ask MatchPointAI - evidence-grounded match questions

from pydantic import BaseModel, Field
from fastapi import HTTPException, Request
from backend.app.services.match_question_service import MatchQuestionService
from backend.app.services.ask_rate_limit_service import ask_rate_limiter


class MatchQuestionRequest(BaseModel):
    question: str = Field(min_length=1, max_length=500)
    seconds: int = Field(default=0, ge=0, le=605)


@router.post("/ask")
def ask_matchpoint(request: MatchQuestionRequest, http_request: Request):
    client_ip = http_request.client.host if http_request.client else "unknown"

    if not ask_rate_limiter.allow(client_ip):
        raise HTTPException(
            status_code=429,
            detail="Too many AI questions. Please wait before trying again.",
        )
    engine = SyntheticMatchEngine(seed=42)
    match = engine.create_match()

    events = engine.simulate_until(
        match=match,
        target_minute=10,
    )

    visible_events = [
        event for event in events
        if event.minute * 60 + event.second <= request.seconds
    ]

    home_goals = sum(
        event.event_type.value == "goal"
        and event.team_id == match.home_team.team_id
        for event in visible_events
    )

    away_goals = sum(
        event.event_type.value == "goal"
        and event.team_id == match.away_team.team_id
        for event in visible_events
    )

    from backend.app.analytics.attacking import calculate_attacking_activity

    home_attack = calculate_attacking_activity(
        visible_events, match.home_team.team_id
    )
    away_attack = calculate_attacking_activity(
        visible_events, match.away_team.team_id
    )

    final_home_goals = sum(
        event.event_type.value == "goal"
        and event.team_id == match.home_team.team_id
        for event in events
    )
    final_away_goals = sum(
        event.event_type.value == "goal"
        and event.team_id == match.away_team.team_id
        for event in events
    )

    facts = [
        f"Final 10-minute simulation score: "
        f"{match.home_team.name} {final_home_goals}, "
        f"{match.away_team.name} {final_away_goals}.",
        "The final simulation score covers the complete simulated match. "
        "The current score covers only the selected playback time.",
        f"Verified statistics for {match.home_team.name}: "
        f"{home_attack.shots} total shots, "
        f"{home_attack.shots_on_target} shots on target, "
        f"{home_attack.goals} goals.",
        f"Verified statistics for {match.away_team.name}: "
        f"{away_attack.shots} total shots, "
        f"{away_attack.shots_on_target} shots on target, "
        f"{away_attack.goals} goals.",
        "Goals are included in both total shots and shots on target.",
        f"Playback time: {request.seconds // 60:02d}:"
        f"{request.seconds % 60:02d}",
        f"Home team: {match.home_team.name}",
        f"Away team: {match.away_team.name}",
        f"Current score: {match.home_team.name} {home_goals}, "
        f"{match.away_team.name} {away_goals}",
    ]

    for event in visible_events:
        facts.append(
            f"Event ID: {event.event_id}; "
            f"Time: {event.minute:02d}:{event.second:02d}; "
            f"Team: {event.team_name or 'Unknown'}; "
            f"Type: {event.event_type.value}; "
            f"Player: {event.player_name or 'Unknown'}; "
            f"xG: {event.expected_goals}; "
            f"Description: {event.description or 'None'}"
        )

    answer = MatchQuestionService().answer(
        question=request.question,
        facts="\n".join(facts),
    )

    if not answer:
        raise HTTPException(
            status_code=503,
            detail="AI question answering is temporarily unavailable.",
        )

    from backend.app.models.explanation import EvidenceEvent

    visible_by_id = {
        event.event_id: event
        for event in visible_events
    }

    selected_ids = answer["evidence_event_ids"]

    references_valid = (
        len(selected_ids) == len(set(selected_ids))
        and all(
            event_id in visible_by_id
            for event_id in selected_ids
        )
    )

    if not references_valid:
        raise HTTPException(
            status_code=502,
            detail="AI returned invalid evidence references.",
        )

    evidence_events = [
        EvidenceEvent(
            event_id=event.event_id,
            minute=event.minute,
            second=event.second,
            event_type=event.event_type.value,
            team_id=event.team_id,
            team_name=event.team_name,
            expected_goals=event.expected_goals,
            description=event.description,
        )
        for event_id in selected_ids
        for event in [visible_by_id[event_id]]
    ]

    return {
        "question": request.question,
        "playback_seconds": request.seconds,
        "answer": answer["answer"],
        "answer_source": "azure",
        "evidence_event_ids": selected_ids,
        "evidence_events": evidence_events,
        "evidence_validated": references_valid,
        "claim_validation_performed": False,
    }
