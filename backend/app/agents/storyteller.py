from dataclasses import dataclass

from backend.app.agents.match_analyst import MatchAnalysis
from backend.app.agents.tactical_intelligence import TacticalAnalysis
from backend.app.agents.evidence_validator import EvidenceValidation


@dataclass
class MatchNarrative:
    audience: str
    headline: str
    narrative: str
    evidence_verified: bool


class StorytellerAgent:
    """Creates audience-specific, evidence-aware match narratives."""

    SUPPORTED_AUDIENCES = (
        "analyst",
        "broadcaster",
        "fan",
    )

    def generate(
        self,
        match_analysis: MatchAnalysis,
        tactical_analysis: TacticalAnalysis,
        match_validation: EvidenceValidation,
        tactical_validation: EvidenceValidation,
        audience: str = "analyst",
    ) -> MatchNarrative:
        audience = audience.lower().strip()

        if audience not in self.SUPPORTED_AUDIENCES:
            raise ValueError(
                f"Unsupported audience: {audience}"
            )

        if (
            (
                match_validation.total_references == 0
                or tactical_validation.total_references == 0
            )
            and not match_validation.missing_event_ids
            and not tactical_validation.missing_event_ids
            and all(
                validation.valid or (
                    validation.total_references == 0
                    and validation.verified_references == 0
                )
                for validation in (match_validation, tactical_validation)
            )
        ):
            return MatchNarrative(
                audience=audience,
                headline="Waiting for Match Evidence",
                narrative=(
                    "The match is underway. Waiting for sufficient "
                    "event data to generate verified commentary."
                ),
                evidence_verified=False,
            )
        evidence_verified = (
            match_validation.valid
            and tactical_validation.valid
        )

        if not evidence_verified:
            return MatchNarrative(
                audience=audience,
                headline="Analysis Requires Review",
                narrative=(
                    "Some supporting match events could not be "
                    "validated. Commentary is withheld pending review."
                ),
                evidence_verified=False,
            )

        match_summary = match_analysis.summary
        tactical_summary = tactical_analysis.summary

        if audience == "analyst":
            headline = "Match Intelligence Analysis"
            narrative = (
                f"{match_summary} "
                f"{tactical_summary} "
                f"Current momentum favors "
                f"{match_analysis.momentum_team or 'neither team'}. "
                f"Attacking advantage: "
                f"{tactical_analysis.attacking_advantage or 'balanced'}. "
                f"Both analyses have verified event references."
            )

        elif audience == "broadcaster":
            headline = "Live Match Commentary"
            narrative = (
                f"{match_summary} "
                f"{tactical_summary} "
                f"The current momentum advantage belongs to "
                f"{match_analysis.momentum_team or 'neither side'}."
            )

        else:
            headline = "Your Match Update"
            narrative = (
                f"{match_summary} "
                f"{tactical_summary} "
                f"Right now, "
                f"{match_analysis.momentum_team or 'neither team'} "
                f"has the momentum advantage."
            )

        return MatchNarrative(
            audience=audience,
            headline=headline,
            narrative=narrative,
            evidence_verified=True,
        )



