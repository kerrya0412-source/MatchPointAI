from backend.app.models.match_event import EventType, MatchEvent


CHAOS_WEIGHTS = {
    EventType.TURNOVER: 2.0,
    EventType.BALL_RECOVERY: 1.0,
    EventType.TACKLE: 1.0,
    EventType.INTERCEPTION: 1.5,
    EventType.PROGRESSIVE_PASS: 1.0,
    EventType.PENALTY_AREA_ENTRY: 3.0,
    EventType.SHOT: 4.0,
    EventType.SHOT_ON_TARGET: 5.0,
    EventType.GOAL: 8.0,
    EventType.CORNER: 2.0,
    EventType.FOUL: 1.0,
    EventType.YELLOW_CARD: 2.0,
    EventType.RED_CARD: 6.0,
}


def calculate_chaos_index(
    events: list[MatchEvent],
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

    if not recent_events:
        return 0.0

    raw_score = sum(
        CHAOS_WEIGHTS.get(event.event_type, 0.0)
        for event in recent_events
    )

    possession_ids = {
        event.possession_id
        for event in recent_events
        if event.possession_id is not None
    }

    possession_changes = max(
        0,
        len(possession_ids) - 1,
    )

    raw_score += possession_changes * 1.5

    chaos_index = min(
        100.0,
        raw_score * 0.8,
    )

    return round(chaos_index, 1)

