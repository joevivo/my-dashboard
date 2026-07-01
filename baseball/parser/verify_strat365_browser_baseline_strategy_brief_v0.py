from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from baseball.parser.report_strat365_browser_baseline_strategy_brief_v0 import (
    best_park,
    descriptor,
    player_line,
    salary,
    score,
    spread,
    worst_park,
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    pitcher = {
        "player": {
            "playerId": "54321",
            "playerName": "Test, Pitcher",
            "team": "TST '68",
        },
        "role": "pitcher",
        "salary": {
            "raw": ".50M",
            "millions": 0.5,
        },
        "pitcher": {
            "endurance": "R3",
        },
        "browserBaselineRank": 12,
        "browserBaselineDraftScore": {
            "score": 67.0,
        },
        "ballparkProfile": {
            "fitSpread": {
                "score": 3.25,
            },
            "bestFit": {
                "ballparkName": "Pitcher Park 1968",
            },
            "worstFit": {
                "ballparkName": "Hitter Park 1968",
            },
        },
    }

    hitter = {
        "player": {
            "playerId": "12345",
            "playerName": "Test, Hitter",
            "team": "TST '68",
        },
        "role": "hitter",
        "salary": {
            "raw": "2.50M",
            "millions": 2.5,
        },
        "hitter": {
            "primaryPosition": "RF",
        },
        "browserBaselineRank": 42,
        "browserBaselineDraftScore": {
            "score": 51.25,
        },
        "ballparkProfile": {
            "fitSpread": {
                "score": 7.75,
            },
            "bestFit": {
                "ballparkName": "Best Park 1968",
            },
            "worstFit": {
                "ballparkName": "Worst Park 1968",
            },
        },
    }

    require(score(pitcher["browserBaselineDraftScore"]) == 67.0, "pitcher score mismatch")
    require(salary(pitcher) == 0.5, "pitcher salary mismatch")
    require(spread(pitcher) == 3.25, "pitcher spread mismatch")
    require(best_park(pitcher) == "Pitcher Park 1968", "pitcher best park mismatch")
    require(worst_park(pitcher) == "Hitter Park 1968", "pitcher worst park mismatch")
    require(descriptor(pitcher) == "R3", "pitcher descriptor mismatch")

    require(score(hitter["browserBaselineDraftScore"]) == 51.25, "hitter score mismatch")
    require(salary(hitter) == 2.5, "hitter salary mismatch")
    require(spread(hitter) == 7.75, "hitter spread mismatch")
    require(descriptor(hitter) == "RF", "hitter descriptor mismatch")

    pitcher_line = player_line(pitcher)
    hitter_line = player_line(hitter)

    require("Test, Pitcher" in pitcher_line, "pitcher line missing name")
    require("R3 | .50M" in pitcher_line, "pitcher line missing descriptor/salary")
    require("rank 12" in pitcher_line, "pitcher line missing rank")
    require("score 67.00" in pitcher_line, "pitcher line missing score")
    require("spread 3.25" in pitcher_line, "pitcher line missing spread")

    require("Test, Hitter" in hitter_line, "hitter line missing name")
    require("RF | 2.50M" in hitter_line, "hitter line missing descriptor/salary")
    require("best Best Park 1968" in hitter_line, "hitter line missing best park")
    require("worst Worst Park 1968" in hitter_line, "hitter line missing worst park")

    print("PASS: Strat365 browser-baseline strategy brief smoke verification")
    print(pitcher_line)
    print(hitter_line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
