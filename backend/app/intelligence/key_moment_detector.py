from uuid import uuid4

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
) -> list[KeyMoment]:
    moments: list[KeyMoment] = []

    moments.extend(
        detect_goal_moments(events)
    )

    moments.extend(
        detect_high_xg_moments(events)
    )

    moments.sort(
        key=lambda moment: (
            moment.minute,
            moment.second,
        )
    )

    return moments
