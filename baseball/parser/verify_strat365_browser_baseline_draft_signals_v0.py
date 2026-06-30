from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from baseball.parser.parse_strat365_browser_baseline_draft_signals_v0 import (
    hitter_performance_score,
    innings_to_float,
    pitcher_performance_score,
    range_defense_score,
    running_score,
    salary_value_score,
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    elite_hitter = {
        "onBasePercentage": 0.426,
        "sluggingPercentage": 0.495,
        "ab": 539,
        "homeRuns": 23,
        "walks": 119,
    }

    weak_hitter = {
        "onBasePercentage": 0.230,
        "sluggingPercentage": 0.250,
        "ab": 300,
        "homeRuns": 0,
        "walks": 5,
    }

    elite_pitcher = {
        "era": 1.12,
        "whip": 0.85,
        "inningsPitched": "304.2",
        "strikeouts": 268,
        "walks": 62,
        "homeRunsAllowed": 11,
        "endurance": "S9*",
    }

    weak_pitcher = {
        "era": 5.20,
        "whip": 1.75,
        "inningsPitched": "100.0",
        "strikeouts": 30,
        "walks": 70,
        "homeRunsAllowed": 20,
        "endurance": "R1",
    }

    elite_hitter_score = hitter_performance_score(elite_hitter)
    weak_hitter_score = hitter_performance_score(weak_hitter)
    elite_pitcher_score = pitcher_performance_score(elite_pitcher)
    weak_pitcher_score = pitcher_performance_score(weak_pitcher)

    require(elite_hitter_score > weak_hitter_score, "elite hitter should outscore weak hitter")
    require(elite_pitcher_score > weak_pitcher_score, "elite pitcher should outscore weak pitcher")

    require(range_defense_score("1(-2)e3") > range_defense_score("4(+4)e15"), "good OF defense should beat poor OF defense")
    require(range_defense_score("1e10") > range_defense_score("4e30"), "good IF defense should beat poor IF defense")

    require(running_score("1-17", "AA") > running_score("1-9", "E"), "good running should beat poor running")

    require(innings_to_float("304.2") == 304 + 2 / 3, "innings .2 should convert to two outs")
    require(innings_to_float("100.0") == 100.0, "innings .0 should convert cleanly")

    require(salary_value_score(70, 1.0) > salary_value_score(70, 10.0), "same performance should value cheaper player more")

    print("PASS: Strat365 browser-baseline draft signal smoke verification")
    print(f"Elite hitter score: {elite_hitter_score:.2f}")
    print(f"Weak hitter score: {weak_hitter_score:.2f}")
    print(f"Elite pitcher score: {elite_pitcher_score:.2f}")
    print(f"Weak pitcher score: {weak_pitcher_score:.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
