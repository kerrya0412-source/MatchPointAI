from dataclasses import dataclass

from backend.app.models.match_event import EventType, MatchEvent


@dataclass
class AttackingActivity:
    progressive_passes: int
    penalty_area_entries: int
    shots: int
    shots_on_target: int
    goals: int
    total_xg: float


def calculate_attacking_activity(
    events: list[MatchEvent],
    team_id: str,
) -> AttackingActivity:
    team_events = [
        event
        for event in events
        if event.team_id == team_id
    ]

    progressive_passes = sum(
        event.event_type == EventType.PROGRESSIVE_PASS
        for event in team_events
    )

    penalty_area_entries = sum(
        event.event_type == EventType.PENALTY_AREA_ENTRY
        for event in team_events
    )

    shots = sum(
        event.event_type
        in (
            EventType.SHOT,
            EventType.SHOT_ON_TARGET,
            EventType.GOAL,
        )
        for event in team_events
    )

    shots_on_target = sum(
        event.event_type
        in (
            EventType.SHOT_ON_TARGET,
            EventType.GOAL,
        )
        for event in team_events
    )

    goals = sum(
        event.event_type == EventType.GOAL
        for event in team_events
    )

    total_xg = sum(
        event.expected_goals or 0
        for event in team_events
    )

    return AttackingActivity(
        progressive_passes=progressive_passes,
        penalty_area_entries=penalty_area_entries,
        shots=shots,
        shots_on_target=shots_on_target,
        goals=goals,
        total_xg=round(total_xg, 3),
    )
