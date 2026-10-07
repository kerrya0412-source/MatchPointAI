import random
from uuid import uuid4

from backend.app.models.match import Match, MatchStatus, Team
from backend.app.models.match_event import EventType, MatchEvent


class SyntheticMatchEngine:
    def __init__(self, seed: int | None = None):
        self.random = random.Random(seed)

    def create_match(self) -> Match:
        return Match(
            match_id=str(uuid4()),
            home_team=Team(
                team_id="north-city",
                name="North City",
                short_name="NCT",
            ),
            away_team=Team(
                team_id="south-united",
                name="South United",
                short_name="SUN",
            ),
            status=MatchStatus.FIRST_HALF,
        )

    def generate_event(self, match: Match) -> MatchEvent:
        team = self.random.choice(
            [match.home_team, match.away_team]
        )

        event_type = self.random.choice(
            [
                EventType.PASS,
                EventType.PROGRESSIVE_PASS,
                EventType.BALL_RECOVERY,
                EventType.TACKLE,
                EventType.INTERCEPTION,
                EventType.TURNOVER,
                EventType.PENALTY_AREA_ENTRY,
                EventType.SHOT,
                EventType.FOUL,
            ]
        )

        x = round(self.random.uniform(0, 100), 1)
        y = round(self.random.uniform(0, 100), 1)

        end_x = round(self.random.uniform(0, 100), 1)
        end_y = round(self.random.uniform(0, 100), 1)

        return MatchEvent(
            event_id=str(uuid4()),
            match_id=match.match_id,
            minute=match.minute,
            second=match.second,
            event_type=event_type,
            team_id=team.team_id,
            team_name=team.name,
            x=x,
            y=y,
            end_x=end_x,
            end_y=end_y,
            successful=self.random.random() > 0.2,
        )

    def advance_clock(self, match: Match) -> None:
        seconds_to_add = self.random.randint(3, 15)

        total_seconds = (
            match.minute * 60
            + match.second
            + seconds_to_add
        )

        match.minute = total_seconds // 60
        match.second = total_seconds % 60

    def generate_events(
        self,
        match: Match,
        count: int = 10,
    ) -> list[MatchEvent]:
        events = []

        for _ in range(count):
            self.advance_clock(match)
            events.append(self.generate_event(match))

        return events
