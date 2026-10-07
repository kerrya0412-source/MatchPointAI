import random

from backend.app.models.match_event import EventType


def generate_event_coordinates(
    event_type: EventType,
    rng: random.Random,
) -> tuple[float, float, float, float]:
    if event_type == EventType.PROGRESSIVE_PASS:
        x = rng.uniform(25, 65)
        end_x = rng.uniform(max(x + 10, 50), 85)

    elif event_type == EventType.PENALTY_AREA_ENTRY:
        x = rng.uniform(65, 82)
        end_x = rng.uniform(83, 95)

    elif event_type in (
        EventType.SHOT,
        EventType.SHOT_ON_TARGET,
        EventType.GOAL,
    ):
        x = rng.uniform(78, 94)
        end_x = 100.0

    elif event_type == EventType.PASS:
        x = rng.uniform(10, 75)
        movement = rng.uniform(-8, 18)
        end_x = max(0, min(100, x + movement))

    elif event_type in (
        EventType.BALL_RECOVERY,
        EventType.INTERCEPTION,
        EventType.TACKLE,
        EventType.TURNOVER,
    ):
        x = rng.uniform(15, 80)
        end_x = x

    else:
        x = rng.uniform(0, 100)
        end_x = rng.uniform(0, 100)

    y = rng.uniform(10, 90)

    if event_type in (
        EventType.PENALTY_AREA_ENTRY,
        EventType.SHOT,
        EventType.SHOT_ON_TARGET,
        EventType.GOAL,
    ):
        end_y = rng.uniform(25, 75)
    else:
        end_y = max(0, min(100, y + rng.uniform(-20, 20)))

    return (
        round(x, 1),
        round(y, 1),
        round(end_x, 1),
        round(end_y, 1),
    )


def generate_next_coordinates(
    event_type: EventType,
    rng: random.Random,
    start_x: float,
    start_y: float,
) -> tuple[float, float, float, float]:
    x = max(0, min(100, start_x))
    y = max(0, min(100, start_y))

    if event_type == EventType.PROGRESSIVE_PASS:
        end_x = min(92, x + rng.uniform(10, 25))
        end_y = y + rng.uniform(-15, 15)

    elif event_type == EventType.PENALTY_AREA_ENTRY:
        end_x = rng.uniform(max(83, x + 5), 95)
        end_y = rng.uniform(25, 75)

    elif event_type in (
        EventType.SHOT,
        EventType.SHOT_ON_TARGET,
        EventType.GOAL,
    ):
        end_x = 100.0
        end_y = rng.uniform(35, 65)

    elif event_type == EventType.PASS:
        end_x = x + rng.uniform(-5, 15)
        end_y = y + rng.uniform(-18, 18)

    elif event_type in (
        EventType.BALL_RECOVERY,
        EventType.INTERCEPTION,
        EventType.TACKLE,
        EventType.TURNOVER,
    ):
        end_x = x
        end_y = y

    else:
        end_x = x + rng.uniform(-10, 10)
        end_y = y + rng.uniform(-15, 15)

    end_x = max(0, min(100, end_x))
    end_y = max(0, min(100, end_y))

    return (
        round(x, 1),
        round(y, 1),
        round(end_x, 1),
        round(end_y, 1),
    )


