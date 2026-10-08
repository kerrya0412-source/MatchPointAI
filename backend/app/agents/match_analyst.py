from dataclasses import dataclass, field

from backend.app.models.match import Match
from backend.app.models.match_event import MatchEvent
from backend.app.analytics.match_pulse import MatchPulse


@dataclass
class MatchAnalysis:
    match_id: str
    minute: int
    second: int
    summary: str
    leading_team: str | None
    momentum_team: str | None
    key_observations: list[str] = field(default_factory=list)
    evidence_event_ids: list[str] = field(default_factory=list)


class MatchAnalystAgent:
    """Produces deterministic, evidence-backed match analysis."""

    def analyze(
        self,
        match: Match,
        events: list[MatchEvent],
        pulse: MatchPulse,
    ) -> MatchAnalysis:

        home_goals = sum(
            1 for event in events
            if event.event_type == "goal"
            and event.team_id == match.home_team.team_id
        )

        away_goals = sum(
            1 for event in events
            if event.event_type == "goal"
            and event.team_id == match.away_team.team_id
        )

        if home_goals > away_goals:
            leading_team = match.home_team.name
        elif away_goals > home_goals:
            leading_team = match.away_team.name
        else:
            leading_team = None

        if pulse.momentum > 0:
            momentum_team = match.home_team.name
        elif pulse.momentum < 0:
            momentum_team = match.away_team.name
        else:
            momentum_team = None

        summary = (
            f"At {match.minute:02d}:{match.second:02d}, "
            f"{match.home_team.name} {home_goals} - "
            f"{away_goals} {match.away_team.name}."
        )

        observations = [
            f"Momentum score: {pulse.momentum:.1f}.",
            f"Chaos Index: {pulse.chaos_index:.1f}.",
            (
                f"Recent pressure: {match.home_team.name} "
                f"{pulse.home.recent_pressure:.2f}, "
                f"{match.away_team.name} "
                f"{pulse.away.recent_pressure:.2f}."
            ),
        ]

        if momentum_team:
            observations.append(
                f"Current momentum favors {momentum_team}."
            )

        significant_events = [
            event for event in events
            if event.event_type in (
                "goal",
                "shot",
                "shot_on_target",
                "red_card",
            )
        ]

        evidence_ids = [
            event.event_id
            for event in significant_events[-10:]
        ]

        return MatchAnalysis(
            match_id=match.match_id,
            minute=match.minute,
            second=match.second,
            summary=summary,
            leading_team=leading_team,
            momentum_team=momentum_team,
            key_observations=observations,
            evidence_event_ids=evidence_ids,
        )
