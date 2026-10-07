from dataclasses import dataclass

from backend.app.models.match import Match
from backend.app.models.match_event import MatchEvent
from backend.app.analytics.attacking import (
    AttackingActivity,
    calculate_attacking_activity,
)
from backend.app.analytics.chaos import calculate_chaos_index
from backend.app.analytics.momentum import calculate_momentum
from backend.app.analytics.pressure import (
    calculate_pressure,
    calculate_recent_pressure,
)


@dataclass
class TeamPulse:
    team_id: str
    team_name: str
    total_pressure: float
    recent_pressure: float
    attacking_activity: AttackingActivity


@dataclass
class MatchPulse:
    minute: int
    second: int
    home: TeamPulse
    away: TeamPulse
    momentum: float
    chaos_index: float


def calculate_match_pulse(
    match: Match,
    events: list[MatchEvent],
    window_minutes: int = 5,
) -> MatchPulse:
    home = TeamPulse(
        team_id=match.home_team.team_id,
        team_name=match.home_team.name,
        total_pressure=calculate_pressure(
            events,
            match.home_team.team_id,
        ),
        recent_pressure=calculate_recent_pressure(
            events,
            match.home_team.team_id,
            match.minute,
            window_minutes,
        ),
        attacking_activity=calculate_attacking_activity(
            events,
            match.home_team.team_id,
        ),
    )

    away = TeamPulse(
        team_id=match.away_team.team_id,
        team_name=match.away_team.name,
        total_pressure=calculate_pressure(
            events,
            match.away_team.team_id,
        ),
        recent_pressure=calculate_recent_pressure(
            events,
            match.away_team.team_id,
            match.minute,
            window_minutes,
        ),
        attacking_activity=calculate_attacking_activity(
            events,
            match.away_team.team_id,
        ),
    )

    return MatchPulse(
        minute=match.minute,
        second=match.second,
        home=home,
        away=away,
        momentum=calculate_momentum(
            events=events,
            home_team_id=match.home_team.team_id,
            away_team_id=match.away_team.team_id,
            current_minute=match.minute,
            window_minutes=window_minutes,
        ),
        chaos_index=calculate_chaos_index(
            events=events,
            current_minute=match.minute,
            window_minutes=window_minutes,
        ),
    )
