from backend.app.models.match_event import EventType, MatchEvent


PRESSURE_WEIGHTS = {
    EventType.PASS: 0.5,
    EventType.PROGRESSIVE_PASS: 2.0,
    EventType.BALL_RECOVERY: 1.0,
    EventType.TACKLE: 0.5,
    EventType.INTERCEPTION: 1.0,
    EventType.TURNOVER: 0.5,
    EventType.PENALTY_AREA_ENTRY: 4.0,
    EventType.SHOT: 5.0,
    EventType.SHOT_ON_TARGET: 7.0,
    EventType.GOAL: 10.0,
    EventType.CORNER: 3.0,
}


def calculate_pressure(
    events: list[MatchEvent],
    team_id: str,
) -> float:
    score = 0.0

    for event in events:
        if event.team_id != team_id:
            continue

        score += PRESSURE_WEIGHTS.get(
            event.event_type,
            0.0,
        )

        if event.expected_goals is not None:
            score += event.expected_goals * 5

    return round(score, 2)


def calculate_recent_pressure(
    events: list[MatchEvent],
    team_id: str,
    current_minute: int,
    window_minutes: int = 5,
) -> float:
    start_minute = max(
        0,
        current_minute - window_minutes,
    )

    recent_events = [
        event
        for event in events
        if start_minute <= event.minute <= current_minute
    ]

    return calculate_pressure(
        recent_events,
        team_id,
    )
