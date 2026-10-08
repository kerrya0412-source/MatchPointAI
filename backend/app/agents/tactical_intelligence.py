from dataclasses import dataclass, field

from backend.app.models.match import Match
from backend.app.models.match_event import MatchEvent
from backend.app.analytics.match_pulse import MatchPulse
from backend.app.analytics.attacking import calculate_attacking_activity
from backend.app.analytics.pressure import calculate_pressure


@dataclass
class TacticalAnalysis:
    match_id: str
    minute: int
    second: int
    summary: str
    pressure_advantage: str | None
    attacking_advantage: str | None
    tactical_observations: list[str] = field(default_factory=list)
    evidence_event_ids: list[str] = field(default_factory=list)


class TacticalIntelligenceAgent:
    """Analyzes attacking patterns and pressure using match evidence."""

    def analyze(
        self,
        match: Match,
        events: list[MatchEvent],
        pulse: MatchPulse,
    ) -> TacticalAnalysis:
        home_id = match.home_team.team_id
        away_id = match.away_team.team_id

        home_attack = calculate_attacking_activity(events, home_id)
        away_attack = calculate_attacking_activity(events, away_id)

        home_pressure = calculate_pressure(events, home_id)
        away_pressure = calculate_pressure(events, away_id)

        if home_pressure > away_pressure:
            pressure_advantage = match.home_team.name
        elif away_pressure > home_pressure:
            pressure_advantage = match.away_team.name
        else:
            pressure_advantage = None

        home_attacks = (
            home_attack.progressive_passes
            + home_attack.penalty_area_entries
            + home_attack.shots
        )
        away_attacks = (
            away_attack.progressive_passes
            + away_attack.penalty_area_entries
            + away_attack.shots
        )

        if home_attacks > away_attacks:
            attacking_advantage = match.home_team.name
        elif away_attacks > home_attacks:
            attacking_advantage = match.away_team.name
        else:
            attacking_advantage = None

        observations = [
            (
                f"Total pressure: {match.home_team.name} "
                f"{home_pressure:.2f}, {match.away_team.name} "
                f"{away_pressure:.2f}."
            ),
            (
                f"Attacking actions: {match.home_team.name} "
                f"{home_attacks}, {match.away_team.name} "
                f"{away_attacks}."
            ),
            (
                f"Shots: {match.home_team.name} {home_attack.shots}, "
                f"{match.away_team.name} {away_attack.shots}."
            ),
            (
                f"Expected goals: {match.home_team.name} "
                f"{home_attack.total_xg:.2f}, "
                f"{match.away_team.name} {away_attack.total_xg:.2f}."
            ),
            f"Current momentum score: {pulse.momentum:.1f}.",
        ]

        if pressure_advantage:
            summary = f"{pressure_advantage} has generated more total pressure."
        else:
            summary = "Both teams have generated equal total pressure."

        significant_events = [
            event for event in events
            if event.event_type in (
                "progressive_pass",
                "penalty_area_entry",
                "shot",
                "shot_on_target",
                "goal",
            )
        ]

        return TacticalAnalysis(
            match_id=match.match_id,
            minute=match.minute,
            second=match.second,
            summary=summary,
            pressure_advantage=pressure_advantage,
            attacking_advantage=attacking_advantage,
            tactical_observations=observations,
            evidence_event_ids=[
                event.event_id for event in significant_events[-10:]
            ],
        )

