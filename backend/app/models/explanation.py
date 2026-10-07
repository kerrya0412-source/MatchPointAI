from pydantic import BaseModel, Field

from backend.app.models.key_moment import KeyMomentType


class EvidenceEvent(BaseModel):
    event_id: str
    minute: int = Field(ge=0, le=120)
    second: int = Field(ge=0, le=59)
    event_type: str
    team_id: str | None = None
    team_name: str | None = None
    expected_goals: float | None = None
    description: str | None = None


class WhyExplanation(BaseModel):
    moment_id: str
    match_id: str
    moment_type: KeyMomentType

    question: str
    answer: str

    evidence_summary: str

    evidence_events: list[EvidenceEvent]

    confidence: float = Field(
        default=1.0,
        ge=0,
        le=1,
    )
