from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from baseball.parser.report_strat365_browser_baseline_park_archetypes_v0 import (
    build_buckets,
    descriptor,
    movement_delta,
    movement_line,
    park_label,
    salary,
    score,
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    hitter = {
        "player": {
            "playerId": "100",
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
        "browserBaselineRank": 100,
        "browserBaselineDraftScore": {
            "score": 40.0,
        },
        "ballparkFits": [
            {
                "ballparkName": "Hitter Park 1968",
                "parkAdjustedBrowserRank": 80,
                "parkAdjustedBrowserScore": {"score": 44.5},
            },
            {
                "ballparkName": "Pitcher Park 1968",
                "parkAdjustedBrowserRank": 120,
                "parkAdjustedBrowserScore": {"score": 36.0},
            },
        ],
    }

    pitcher = {
        "player": {
            "playerId": "200",
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
        "browserBaselineRank": 50,
        "browserBaselineDraftScore": {
            "score": 60.0,
        },
        "ballparkFits": [
            {
                "ballparkName": "Hitter Park 1968",
                "parkAdjustedBrowserRank": 70,
                "parkAdjustedBrowserScore": {"score": 55.0},
            },
            {
                "ballparkName": "Pitcher Park 1968",
                "parkAdjustedBrowserRank": 35,
                "parkAdjustedBrowserScore": {"score": 64.0},
            },
        ],
    }

    require(score(hitter["browserBaselineDraftScore"]) == 40.0, "score mismatch")
    require(salary(hitter) == 2.5, "salary mismatch")
    require(descriptor(hitter) == "RF", "hitter descriptor mismatch")
    require(descriptor(pitcher) == "R3", "pitcher descriptor mismatch")

    hitter_fit = hitter["ballparkFits"][0]
    pitcher_fit = pitcher["ballparkFits"][1]

    require(movement_delta(hitter, hitter_fit) == 4.5, "hitter movement delta mismatch")
    require(movement_delta(pitcher, pitcher_fit) == 4.0, "pitcher movement delta mismatch")

    hitter_line = movement_line(hitter, hitter_fit)
    pitcher_line = movement_line(pitcher, pitcher_fit)

    require("Test, Hitter" in hitter_line, "hitter line missing name")
    require("global 100 -> park 80" in hitter_line, "hitter line missing rank movement")
    require("40.00 -> 44.50 (+4.50)" in hitter_line, "hitter line missing score movement")

    require("Test, Pitcher" in pitcher_line, "pitcher line missing name")
    require("R3 | .50M" in pitcher_line, "pitcher line missing descriptor/salary")
    require("60.00 -> 64.00 (+4.00)" in pitcher_line, "pitcher line missing score movement")

    buckets = build_buckets([hitter, pitcher])

    hitter_bucket = buckets["Hitter Park 1968"]
    pitcher_bucket = buckets["Pitcher Park 1968"]

    require(hitter_bucket["hitter_true_boosts"] == 1, "hitter boost count mismatch")
    require(hitter_bucket["pitcher_casualties"] == 1, "pitcher casualty count mismatch")
    require(len(hitter_bucket["cheap_hitter_boosts"]) == 1, "cheap hitter boost count mismatch")

    require(pitcher_bucket["pitcher_true_boosts"] == 1, "pitcher boost count mismatch")
    require(pitcher_bucket["hitter_casualties"] == 1, "hitter casualty count mismatch")
    require(len(pitcher_bucket["cheap_pitcher_boosts"]) == 1, "cheap pitcher boost count mismatch")

    require(park_label({
        "hitter_true_boosts": 125,
        "hitter_casualties": 0,
        "pitcher_true_boosts": 0,
        "pitcher_casualties": 20,
    }) == "extreme hitter-build", "extreme hitter label mismatch")

    require(park_label({
        "hitter_true_boosts": 0,
        "hitter_casualties": 20,
        "pitcher_true_boosts": 125,
        "pitcher_casualties": 0,
    }) == "extreme pitcher-build", "extreme pitcher label mismatch")

    print("PASS: Strat365 browser-baseline park-archetype report smoke verification")
    print(hitter_line)
    print(pitcher_line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
