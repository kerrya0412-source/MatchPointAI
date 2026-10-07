from enum import StrEnum
from typing import Optional

from pydantic import BaseModel, Field


class EventType(StrEnum):
    KICKOFF = "kickoff"
    PASS = "pass"
    PROGRESSIVE_PASS = "progressive_pass"
    BALL_RECOVERY = "ball_recovery"
    TACKLE = "tackle"
    INTERCEPTION = "interception"
    TURNOVER = "turnover"
    PENALTY_AREA_ENTRY = "penalty_area_entry"
    SHOT = "shot"
    SHOT_ON_TARGET = "shot_on_target"
    GOAL = "goal"
    SAVE = "save"
    CORNER = "corner"
    FOUL = "foul"
    YELLOW_CARD = "yellow_card"
    RED_CARD = "red_card"
    OFFSIDE = "offside"
    SUBSTITUTION = "substitution"
    HALFTIME = "halftime"
    FULLTIME = "fulltime"


class MatchEvent(BaseModel):
    event_id: str
    match_id: str

    minute: int = Field(ge=0, le=120)
    second: int = Field(ge=0, le=59)

    event_type: EventType

    team_id: Optional[str] = None
    team_name: Optional[str] = None

    player_id: Optional[str] = None
    player_name: Optional[str] = None

    target_player_id: Optional[str] = None
    target_player_name: Optional[str] = None

    x: Optional[float] = Field(default=None, ge=0, le=100)
    y: Optional[float] = Field(default=None, ge=0, le=100)

    end_x: Optional[float] = Field(default=None, ge=0, le=100)
    end_y: Optional[float] = Field(default=None, ge=0, le=100)

    successful: Optional[bool] = None

    possession_id: Optional[str] = None

    expected_goals: Optional[float] = Field(
        default=None,
        ge=0,
        le=1,
    )

    description: Optional[str] = None
