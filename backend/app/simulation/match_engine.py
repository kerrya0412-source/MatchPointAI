import random
from uuid import uuid4

from backend.app.models.match import Match, MatchStatus, Team
from backend.app.models.match_event import EventType, MatchEvent
from backend.app.simulation.sequences import SEQUENCE_TEMPLATES
from backend.app.simulation.shot import resolve_shot
from backend.app.simulation.pitch import generate_event_coordinates, generate_next_coordinates


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

    def generate_event(
        self,
        match: Match,
        event_type: EventType | None = None,
        team: Team | None = None,
        possession_id: str | None = None,
    ) -> MatchEvent:
        if team is None:
            team = self.random.choice(
                [match.home_team, match.away_team]
            )

        if event_type is None:
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

        x, y, end_x, end_y = generate_event_coordinates(
            event_type,
            self.random,
        )

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
            possession_id=possession_id,
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

    def choose_sequence(self):
        return self.random.choices(
            SEQUENCE_TEMPLATES,
            weights=[template.weight for template in SEQUENCE_TEMPLATES],
            k=1,
        )[0]

    def generate_sequence(
        self,
        match: Match,
        team: Team | None = None,
    ) -> tuple[str, list[MatchEvent]]:
        if team is None:
            team = self.random.choice(
                [match.home_team, match.away_team]
            )

        template = self.choose_sequence()
        possession_id = str(uuid4())

        events = []

        current_x = round(self.random.uniform(20, 45), 1)
        current_y = round(self.random.uniform(20, 80), 1)

        for event_type in template.events:
            self.advance_clock(match)

            event = self.generate_event(
                match=match,
                event_type=event_type,
                team=team,
                possession_id=possession_id,
            )

            x, y, end_x, end_y = generate_next_coordinates(
                event_type=event_type,
                rng=self.random,
                start_x=current_x,
                start_y=current_y,
            )

            event.x = x
            event.y = y
            event.end_x = end_x
            event.end_y = end_y

            if event_type == EventType.SHOT:
                outcome = resolve_shot(
                    x=event.x,
                    y=event.y,
                    rng=self.random,
                )

                event.expected_goals = outcome.xg

                if outcome.goal:
                    event.event_type = EventType.GOAL
                    event.description = (
                        f"Goal with {outcome.xg:.3f} xG"
                    )

                    if team.team_id == match.home_team.team_id:
                        match.home_score += 1
                    else:
                        match.away_score += 1

                elif outcome.on_target:
                    event.event_type = EventType.SHOT_ON_TARGET
                    event.description = (
                        f"Shot saved with {outcome.xg:.3f} xG"
                    )

                else:
                    event.description = (
                        f"Shot missed with {outcome.xg:.3f} xG"
                    )

            events.append(event)

            current_x = end_x
            current_y = end_y

        return template.name, events






    def simulate_until(
        self,
        match: Match,
        target_minute: int,
    ) -> list[MatchEvent]:
        events = []

        team = self.random.choice(
            [match.home_team, match.away_team]
        )

        while match.minute < target_minute:
            _, possession_events = self.generate_sequence(
                match=match,
                team=team,
            )

            events.extend(possession_events)

            if team.team_id == match.home_team.team_id:
                team = match.away_team
            else:
                team = match.home_team

        return events

