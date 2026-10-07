from dataclasses import dataclass

from backend.app.models.match_event import EventType


@dataclass
class SequenceTemplate:
    name: str
    events: list[EventType]
    weight: int


SEQUENCE_TEMPLATES = [
    SequenceTemplate(
        name="simple_possession",
        events=[
            EventType.PASS,
            EventType.PASS,
            EventType.PASS,
        ],
        weight=35,
    ),
    SequenceTemplate(
        name="progressive_attack",
        events=[
            EventType.BALL_RECOVERY,
            EventType.PASS,
            EventType.PROGRESSIVE_PASS,
            EventType.PENALTY_AREA_ENTRY,
            EventType.SHOT,
        ],
        weight=20,
    ),
    SequenceTemplate(
        name="counter_attack",
        events=[
            EventType.TURNOVER,
            EventType.PROGRESSIVE_PASS,
            EventType.PROGRESSIVE_PASS,
            EventType.PENALTY_AREA_ENTRY,
            EventType.SHOT,
        ],
        weight=15,
    ),
    SequenceTemplate(
        name="interception_attack",
        events=[
            EventType.INTERCEPTION,
            EventType.PASS,
            EventType.PROGRESSIVE_PASS,
            EventType.SHOT,
        ],
        weight=10,
    ),
    SequenceTemplate(
        name="failed_attack",
        events=[
            EventType.PASS,
            EventType.PROGRESSIVE_PASS,
            EventType.TURNOVER,
        ],
        weight=10,
    ),
    SequenceTemplate(
        name="defensive_duel",
        events=[
            EventType.TACKLE,
            EventType.BALL_RECOVERY,
            EventType.PASS,
        ],
        weight=10,
    ),
]
