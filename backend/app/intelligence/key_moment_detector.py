from uuid import uuid4

from backend.app.analytics.pressure import calculate_recent_pressure
from backend.app.models.key_moment import (
    KeyMoment,
    KeyMomentSeverity,
    KeyMomentType,
)
from backend.app.models.match_event import EventType, MatchEvent


def detect_goal_moments(
    events: list[MatchEvent],
) -> list[KeyMoment]:
    moments: list[KeyMoment] = []

    for event in events:
        if event.event_type != EventType.GOAL:
            continue

        xg_text = ""

        if event.expected_goals is not None:
            xg_text = (
                f" The chance carried "
                f"{event.expected_goals:.3f} xG."
            )

        moments.append(
            KeyMoment(
                moment_id=str(uuid4()),
                match_id=event.match_id,
                minute=event.minute,
                second=event.second,
                moment_type=KeyMomentType.GOAL,
                severity=KeyMomentSeverity.CRITICAL,
                team_id=event.team_id,
                team_name=event.team_name,
                title=f"Goal - {event.team_name}",
                description=(
                    f"{event.team_name} scored at "
                    f"{event.minute:02d}:{event.second:02d}."
                    f"{xg_text}"
                ),
                evidence_event_ids=[
                    event.event_id,
                ],
                confidence=1.0,
            )
        )

    return moments
def detect_high_xg_moments(
    events: list[MatchEvent],
    threshold: float = 0.50,
) -> list[KeyMoment]:
    moments: list[KeyMoment] = []

    for event in events:
        if event.event_type not in (
            EventType.SHOT,
            EventType.SHOT_ON_TARGET,
        ):
            continue

        if event.expected_goals is None:
            continue

        if event.expected_goals < threshold:
            continue

        moments.append(
            KeyMoment(
                moment_id=str(uuid4()),
                match_id=event.match_id,
                minute=event.minute,
                second=event.second,
                moment_type=KeyMomentType.HIGH_XG_CHANCE,
                severity=KeyMomentSeverity.HIGH,
                team_id=event.team_id,
                team_name=event.team_name,
                title=f"Major Chance - {event.team_name}",
                description=(
                    f"{event.team_name} created a major chance "
                    f"at {event.minute:02d}:{event.second:02d} "
                    f"worth {event.expected_goals:.3f} xG "
                    f"but did not score."
                ),
                evidence_event_ids=[
                    event.event_id,
                ],
                confidence=1.0,
            )
        )

    return moments


def detect_key_moments(
    events: list[MatchEvent],
    home_team_id: str,
    home_team_name: str,
    away_team_id: str,
    away_team_name: str,
) -> list[KeyMoment]:
    moments: list[KeyMoment] = []

    moments.extend(
        detect_goal_moments(events)
    )

    moments.extend(
        detect_high_xg_moments(events)
    )

    moments.extend(
        detect_pressure_surge_moments(
            events=events,
            team_id=home_team_id,
            team_name=home_team_name,
        )
    )

    moments.extend(
        detect_pressure_surge_moments(
            events=events,
            team_id=away_team_id,
            team_name=away_team_name,
        )
    )

    moments.sort(
        key=lambda moment: (
            moment.minute,
            moment.second,
        )
    )

    return moments



def detect_pressure_surge_moments(
    events: list[MatchEvent],
    team_id: str,
    team_name: str,
    threshold: float = 40.0,
    window_minutes: int = 2,
) -> list[KeyMoment]:
    moments: list[KeyMoment] = []

    if not events:
        return moments

    max_minute = max(
        event.minute
        for event in events
    )

    previous_pressure = 0.0

    for minute in range(1, max_minute + 1):
        pressure = calculate_recent_pressure(
            events=events,
            team_id=team_id,
            current_minute=minute,
            window_minutes=window_minutes,
        )

        if (
            pressure >= threshold
            and previous_pressure < threshold
        ):
            start_minute = max(
                0,
                minute - window_minutes,
            )

            evidence = [
                event.event_id
                for event in events
                if (
                    event.team_id == team_id
                    and start_minute <= event.minute <= minute
                )
            ]

            moments.append(
                KeyMoment(
                    moment_id=str(uuid4()),
                    match_id=events[0].match_id,
                    minute=minute,
                    second=0,
                    moment_type=KeyMomentType.PRESSURE_SURGE,
                    severity=KeyMomentSeverity.HIGH,
                    team_id=team_id,
                    team_name=team_name,
                    title=f"Pressure Surge - {team_name}",
                    description=(
                        f"{team_name} entered a sustained "
                        f"pressure phase at minute {minute} "
                        f"with a pressure score of "
                        f"{pressure:.2f}."
                    ),
                    evidence_event_ids=evidence,
                    confidence=1.0,
                )
            )

        previous_pressure = pressure

    return moments

