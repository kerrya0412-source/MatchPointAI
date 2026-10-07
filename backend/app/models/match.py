from enum import StrEnum

from pydantic import BaseModel, Field


class MatchStatus(StrEnum):
    NOT_STARTED = "not_started"
    FIRST_HALF = "first_half"
    HALFTIME = "halftime"
    SECOND_HALF = "second_half"
    FULLTIME = "fulltime"


class Team(BaseModel):
    team_id: str
    name: str
    short_name: str


class Match(BaseModel):
    match_id: str

    home_team: Team
    away_team: Team

    home_score: int = Field(default=0, ge=0)
    away_score: int = Field(default=0, ge=0)

    minute: int = Field(default=0, ge=0, le=120)
    second: int = Field(default=0, ge=0, le=59)

    status: MatchStatus = MatchStatus.NOT_STARTED
