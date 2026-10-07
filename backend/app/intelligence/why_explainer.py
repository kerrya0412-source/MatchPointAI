from collections import Counter

from backend.app.intelligence.evidence_builder import build_evidence_chain
from backend.app.models.explanation import WhyExplanation
from backend.app.models.key_moment import KeyMoment, KeyMomentType
from backend.app.models.match_event import MatchEvent


def build_type_specific_answer(
    moment: KeyMoment,
    evidence,
) -> str:
    if moment.moment_type == KeyMomentType.GOAL:
        shot = next(
            (
                event
                for event in evidence
                if event.expected_goals is not None
            ),
            None,
        )

        if shot is not None:
            return (
                f"{moment.team_name} scored from a chance "
                f"worth {shot.expected_goals:.3f} xG. "
                f"The goal itself is the direct evidence "
                f"for this key moment."
            )

    if moment.moment_type == KeyMomentType.HIGH_XG_CHANCE:
        shot = next(
            (
                event
                for event in evidence
                if event.expected_goals is not None
            ),
            None,
        )

        if shot is not None:
            return (
                f"{moment.team_name} created a high-quality "
                f"chance worth {shot.expected_goals:.3f} xG "
                f"but did not score."
            )

    if moment.moment_type == KeyMomentType.PRESSURE_SURGE:
        progressive = sum(
            event.event_type == "progressive_pass"
            for event in evidence
        )
        entries = sum(
            event.event_type == "penalty_area_entry"
            for event in evidence
        )
        shots = sum(
            event.event_type in (
                "shot",
                "shot_on_target",
                "goal",
            )
            for event in evidence
        )

        return (
            f"{moment.team_name} generated sustained "
            f"attacking pressure through {progressive} "
            f"progressive passes, {entries} penalty-area "
            f"entries, and {shots} shots in the supporting "
            f"evidence window."
        )

    if moment.moment_type == KeyMomentType.MOMENTUM_SWING:
        teams = Counter(
            event.team_name
            for event in evidence
            if event.team_name
        )

        return (
            f"MatchPoint detected a major change in match "
            f"control toward {moment.team_name}. "
            f"The supporting window contains "
            f"{len(evidence)} events across both teams, "
            f"showing the sequence surrounding the change "
            f"in momentum."
        )

    if moment.moment_type == KeyMomentType.CHAOTIC_PERIOD:
        turnovers = sum(
            event.event_type == "turnover"
            for event in evidence
        )
        attacking_events = sum(
            event.event_type in (
                "progressive_pass",
                "penalty_area_entry",
                "shot",
                "shot_on_target",
                "goal",
            )
            for event in evidence
        )

        return (
            f"MatchPoint identified an unstable period "
            f"containing {turnovers} turnovers and "
            f"{attacking_events} high-tempo attacking "
            f"events across {len(evidence)} supporting "
            f"events."
        )

    return (
        f"{moment.description} "
        f"MatchPoint identified this from "
        f"{len(evidence)} underlying match events."
    )

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
        answer=build_type_specific_answer(
            moment=moment,
            evidence=evidence,
        ),
        evidence_summary=evidence_summary,
        evidence_events=evidence,
        confidence=moment.confidence,
    )


