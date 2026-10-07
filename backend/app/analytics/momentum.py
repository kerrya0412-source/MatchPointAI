from backend.app.models.match_event import MatchEvent
from backend.app.analytics.pressure import calculate_pressure


def calculate_momentum(
    events: list[MatchEvent],
    home_team_id: str,
    away_team_id: str,
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

    home_pressure = calculate_pressure(
        recent_events,
        home_team_id,
    )

    away_pressure = calculate_pressure(
        recent_events,
        away_team_id,
    )

    total_pressure = home_pressure + away_pressure

    if total_pressure == 0:
        return 0.0

    momentum = (
        (home_pressure - away_pressure)
        / total_pressure
    ) * 100

    return round(momentum, 1)
