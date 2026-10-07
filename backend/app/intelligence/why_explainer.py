from collections import Counter

from backend.app.intelligence.evidence_builder import build_evidence_chain
from backend.app.models.explanation import WhyExplanation
from backend.app.models.key_moment import KeyMoment
from backend.app.models.match_event import MatchEvent


def build_why_explanation(
    moment: KeyMoment,
    events: list[MatchEvent],
) -> WhyExplanation:
    evidence = build_evidence_chain(
        moment=moment,
        events=events,
    )

    event_counts = Counter(
        event.event_type
        for event in evidence
    )

    event_summary = ", ".join(
        f"{count} {event_type.replace('_', ' ')}"
        for event_type, count in event_counts.items()
    )

    xg_events = [
        event
        for event in evidence
        if event.expected_goals is not None
    ]

    total_xg = sum(
        event.expected_goals or 0
        for event in xg_events
    )

    evidence_summary = (
        f"{len(evidence)} supporting events"
    )

    if event_summary:
        evidence_summary += (
            f": {event_summary}"
        )

    if xg_events:
        evidence_summary += (
            f". Combined shot xG: {total_xg:.3f}"
        )

    return WhyExplanation(
        moment_id=moment.moment_id,
        match_id=moment.match_id,
        moment_type=moment.moment_type,
        question=f"Why did MatchPoint flag '{moment.title}'?",
        answer=(
            f"{moment.description} "
            f"MatchPoint identified this from "
            f"{len(evidence)} underlying match events."
        ),
        evidence_summary=evidence_summary,
        evidence_events=evidence,
        confidence=moment.confidence,
    )
