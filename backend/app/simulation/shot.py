import random
from dataclasses import dataclass

from backend.app.simulation.xg import calculate_xg


@dataclass
class ShotOutcome:
    xg: float
    on_target: bool
    goal: bool
    saved: bool


def resolve_shot(
    x: float,
    y: float,
    rng: random.Random,
) -> ShotOutcome:
    xg = calculate_xg(x, y)

    goal = rng.random() < xg

    if goal:
        return ShotOutcome(
            xg=xg,
            on_target=True,
            goal=True,
            saved=False,
        )

    on_target_probability = min(
        0.75,
        0.30 + (xg * 0.55),
    )

    on_target = rng.random() < on_target_probability

    return ShotOutcome(
        xg=xg,
        on_target=on_target,
        goal=False,
        saved=on_target,
    )
