from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from baseball.parser.adapt_strat365_playerset_to_bie_metadata_v0 import (
    adapt_defense_player,
    adapt_roster_player,
    money,
    parse_browser_defense,
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    hitter = {
        "role": "hitter",
        "season": "1968",
        "sourcePositionId": "10",
        "playerId": "30000",
        "playerName": "Aaron, Hank",
        "team": "ATL '68",
        "teamId": "15253",
        "bats": "R",
        "primaryPosition": "RF",
        "defense": "1(-2)e3",
        "ab": 606,
        "runs": 84,
        "hits": 174,
        "doubles": 33,
        "triples": 4,
        "homeRuns": 29,
        "rbi": 86,
        "walks": 64,
        "strikeouts": 62,
        "stolenBases": 28,
        "caughtStealing": 5,
        "steal": "A",
        "runRating": "1-16",
        "battingAverage": 0.287,
        "onBasePercentage": 0.354,
        "sluggingPercentage": 0.498,
        "injury": "1",
        "balance": "2R",
        "salary": {
            "raw": "10.92M",
            "millions": 10.92,
        },
    }

    pitcher = {
        "role": "pitcher",
        "season": "1968",
        "sourcePositionId": "1",
        "playerId": "31000",
        "playerName": "Gibson, Bob",
        "team": "STL '68",
        "teamId": "15261",
        "throws": "R",
        "endurance": "S9*",
        "wins": 22,
        "losses": 9,
        "saves": 0,
        "inningsPitched": "304.2",
        "hitsAllowed": 198,
        "earnedRuns": 38,
        "walks": 62,
        "strikeouts": 268,
        "homeRunsAllowed": 11,
        "hold": "-3",
        "balkRating": "0",
        "wildPitchRating": "5",
        "batting": "1WR",
        "era": 1.12,
        "whip": 0.85,
        "balance": "1R",
        "salary": {
            "raw": "9.03M",
            "millions": 9.03,
        },
    }

    parsed_money = money("10.92M", 10.92)
    require(parsed_money["millions"]["numerator"] == 273, "salary numerator mismatch")
    require(parsed_money["millions"]["denominator"] == 25, "salary denominator mismatch")
    require(parsed_money["millions"]["decimal"] == 10.92, "salary decimal mismatch")
    require(parsed_money["dollars"] == 10_920_000, "salary dollars mismatch")

    parsed_defense = parse_browser_defense("RF", "1(-2)e3")
    require(parsed_defense["defenseUnavailable"] is False, "defense should be available")
    require(parsed_defense["defenseRaw"] == "rf-1(-2)e3", "defenseRaw mismatch")
    require(len(parsed_defense["positions"]) == 1, "defense position count mismatch")
    require(parsed_defense["positions"][0]["position"] == "RF", "defense position mismatch")
    require(parsed_defense["positions"][0]["range"] == 1, "defense range mismatch")
    require(parsed_defense["positions"][0]["arm"] == -2, "defense arm mismatch")
    require(parsed_defense["positions"][0]["error"] == 3, "defense error mismatch")

    roster_hitter = adapt_roster_player(hitter, 1968)
    roster_pitcher = adapt_roster_player(pitcher, 1968)

    require(roster_hitter["playerId"] == 30000, "roster hitter playerId mismatch")
    require(roster_hitter["teamId"] == 15253, "roster hitter teamId mismatch")
    require(roster_hitter["salary"]["millions"]["decimal"] == 10.92, "roster hitter salary mismatch")
    require(roster_hitter["hitter"]["primaryPosition"] == "RF", "roster hitter position mismatch")
    require("/player/30000/1968/5/1968" in roster_hitter["sourceUrl"], "roster hitter sourceUrl mismatch")

    require(roster_pitcher["playerId"] == 31000, "roster pitcher playerId mismatch")
    require(roster_pitcher["teamId"] == 15261, "roster pitcher teamId mismatch")
    require(roster_pitcher["salary"]["millions"]["decimal"] == 9.03, "roster pitcher salary mismatch")
    require(roster_pitcher["pitcher"]["endurance"] == "S9*", "roster pitcher endurance mismatch")

    defense_hitter = adapt_defense_player(hitter, 1968)
    defense_pitcher = adapt_defense_player(pitcher, 1968)

    require(defense_hitter["hitterDefense"]["defenseUnavailable"] is False, "hitter defense unavailable mismatch")
    require(defense_hitter["hitterDefense"]["positions"][0]["raw"] == "rf-1(-2)e3", "hitter defense raw mismatch")

    require(defense_pitcher["pitcherDefense"]["defenseUnavailable"] is True, "pitcher defense availability mismatch")
    require(defense_pitcher["pitcherDefense"]["throws"] == "R", "pitcher throws mismatch")
    require(defense_pitcher["pitcherDefense"]["endurance"] == "S9*", "pitcher endurance mismatch")

    print("PASS: Strat365 playerset-to-BIE metadata adapter smoke verification")
    print(f"Roster hitter: {roster_hitter['playerName']} | {roster_hitter['team']} | {roster_hitter['salary']['raw']}")
    print(f"Roster pitcher: {roster_pitcher['playerName']} | {roster_pitcher['team']} | {roster_pitcher['salary']['raw']}")
    print(f"Hitter defense: {defense_hitter['hitterDefense']['defenseRaw']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
