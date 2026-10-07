import math


def calculate_xg(
    x: float,
    y: float,
) -> float:
    """
    Calculate synthetic expected goals (xG) from shot location.

    Pitch coordinates:
        x: 0-100, with the attacking goal at x=100
        y: 0-100, with the center of goal at y=50

    This is a deterministic synthetic model for MatchPoint AI.
    It is not trained from real player or league data.
    """

    distance_to_goal = math.sqrt(
        ((100 - x) ** 2)
        + ((50 - y) ** 2)
    )

    centrality = 1 - min(abs(50 - y) / 50, 1)

    distance_score = max(
        0,
        1 - (distance_to_goal / 35),
    )

    xg = (
        distance_score * 0.75
        + centrality * 0.25
    )

    return round(
        max(0.01, min(0.95, xg)),
        3,
    )
