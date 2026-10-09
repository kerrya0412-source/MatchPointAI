"""Validate essential facts in AI-generated goal commentary."""

import re
from dataclasses import dataclass, field


@dataclass
class CommentaryValidation:
    valid: bool
    errors: list[str] = field(default_factory=list)


class CommentaryValidator:
    """Checks essential goal facts against generated commentary."""

    def validate(
        self,
        commentary: str,
        scoring_team: str,
        goal_minute: int,
        goal_second: int,
        home_team: str,
        away_team: str,
        home_goals: int,
        away_goals: int,
    ) -> CommentaryValidation:

        errors = []
        text = commentary.casefold()

        if scoring_team.casefold() not in text:
            errors.append("Scoring team missing.")

        # Reject explicit claims that the opposing team scored.
        opposing_team = (
            away_team
            if scoring_team.casefold() == home_team.casefold()
            else home_team
        )

        wrong_scorer_pattern = (
            rf"\b{re.escape(opposing_team.casefold())}\b"
            rf"\s+(?:has\s+)?(?:scored|scores|netted|equalized|equalised)"
            rf"\b"
        )

        if re.search(wrong_scorer_pattern, text):
            errors.append("Incorrect scoring team detected.")

        timestamp = f"{goal_minute:02d}:{goal_second:02d}"

        if timestamp not in commentary:
            errors.append("Goal timestamp missing.")

        expected_scores = {
            (home_goals, away_goals),
            (away_goals, home_goals),
        }

        score_matches = re.findall(
            r"(?<!\d)(\d+)\s*[-–—]\s*(\d+)(?!\d)",
            text,
        )

        if score_matches:
            observed_scores = {
                (int(first), int(second))
                for first, second in score_matches
            }

            if not observed_scores.issubset(expected_scores):
                errors.append("Incorrect score detected.")
        else:
            home_pattern = (
                rf"\b{re.escape(home_team.casefold())}\s+"
                rf"{home_goals}\b"
            )
            away_pattern = (
                rf"\b{re.escape(away_team.casefold())}\s+"
                rf"{away_goals}\b"
            )

            if not (
                re.search(home_pattern, text)
                and re.search(away_pattern, text)
            ):
                errors.append("Expected score missing.")

        return CommentaryValidation(
            valid=not errors,
            errors=errors,
        )



