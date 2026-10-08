from dataclasses import dataclass, field

from backend.app.models.match_event import MatchEvent


@dataclass
class EvidenceValidation:
    valid: bool
    total_references: int
    verified_references: int
    missing_event_ids: list[str] = field(default_factory=list)
    observations: list[str] = field(default_factory=list)


class EvidenceValidatorAgent:
    """Checks whether referenced evidence exists in match events."""

    def validate(
        self,
        events: list[MatchEvent],
        evidence_event_ids: list[str],
    ) -> EvidenceValidation:
        available_ids = {event.event_id for event in events}

        missing_ids = list(dict.fromkeys(
            event_id
            for event_id in evidence_event_ids
            if event_id not in available_ids
        ))

        verified_count = sum(
            1
            for event_id in evidence_event_ids
            if event_id in available_ids
        )

        duplicate_count = (
            len(evidence_event_ids) - len(set(evidence_event_ids))
        )

        observations = [
            f"Verified {verified_count} of {len(evidence_event_ids)} evidence references."
        ]

        if missing_ids:
            observations.append(
                f"{len(missing_ids)} referenced event IDs could not be found."
            )

        if duplicate_count:
            observations.append(
                f"{duplicate_count} duplicate evidence references detected."
            )

        if not evidence_event_ids:
            observations.append("No supporting evidence was provided.")

        valid = (
            bool(evidence_event_ids)
            and not missing_ids
            and duplicate_count == 0
        )

        return EvidenceValidation(
            valid=valid,
            total_references=len(evidence_event_ids),
            verified_references=verified_count,
            missing_event_ids=missing_ids,
            observations=observations,
        )

