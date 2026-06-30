from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from baseball.parser.report_strat365_browser_baseline_park_movers_v0 import (
    descriptor,
    movement,
    player_line,
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    row = {
        "player": {
            "playerId": "12345",
            "playerName": "Test, Player",
            "team": "TST '68",
        },
        "role": "hitter",
        "salary": {
            "raw": "1.25M",
            "millions": 1.25,
        },
        "hitter": {
            "primaryPosition": "LF",
        },
        "browserBaselineRank": 100,
        "browserBaselineDraftScore": {
            "score": 42.0,
        },
        "ballparkFits": [
            {
                "ballparkName": "Test Park 1968",
                "parkAdjustedBrowserRank": 75,
                "parkAdjustedBrowserScore": {
                    "score": 47.5,
                },
            }
        ],
    }

    item = movement(row, "Test Park 1968")

    require(descriptor(row) == "LF", "descriptor mismatch")
    require(item["globalRank"] == 100, "global rank mismatch")
    require(item["parkRank"] == 75, "park rank mismatch")
    require(item["rankDelta"] == 25, "rank delta mismatch")
    require(item["baselineScore"] == 42.0, "baseline score mismatch")
    require(item["parkScore"] == 47.5, "park score mismatch")
    require(item["scoreDelta"] == 5.5, "score delta mismatch")

    line = player_line(item)
    require("Test, Player" in line, "player line missing name")
    require("global 100 -> park 75" in line, "player line missing rank transition")
    require("rank +25" in line, "player line missing positive rank delta")
    require("42.00 -> 47.50 (+5.50)" in line, "player line missing score movement")

    print("PASS: Strat365 browser-baseline park mover report smoke verification")
    print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
