from backend.app.models.explanation import EvidenceEvent
from backend.app.models.key_moment import KeyMoment
from backend.app.models.match_event import MatchEvent


def build_evidence_chain(
    moment: KeyMoment,
    events: list[MatchEvent],
) -> list[EvidenceEvent]:
    evidence_ids = set(
        moment.evidence_event_ids
    )

    matching_events = [
        event
        for event in events
        if event.event_id in evidence_ids
    ]

    matching_events.sort(
        key=lambda event: (
            event.minute,
            event.second,
        )
    )

    return [
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
        for event in matching_events
    ]
