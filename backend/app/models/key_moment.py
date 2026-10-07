from enum import StrEnum

from pydantic import BaseModel, Field


class KeyMomentType(StrEnum):
    GOAL = "goal"
    HIGH_XG_CHANCE = "high_xg_chance"
    PRESSURE_SURGE = "pressure_surge"
    MOMENTUM_SWING = "momentum_swing"
    CHAOTIC_PERIOD = "chaotic_period"


class KeyMomentSeverity(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class KeyMoment(BaseModel):
    moment_id: str

    match_id: str

    minute: int = Field(
        ge=0,
        le=120,
    )

    second: int = Field(
        ge=0,
        le=59,
    )

    moment_type: KeyMomentType

    severity: KeyMomentSeverity

    team_id: str | None = None
    team_name: str | None = None

    title: str
    description: str

    evidence_event_ids: list[str] = []

    confidence: float = Field(
        default=1.0,
        ge=0,
        le=1,
    )
