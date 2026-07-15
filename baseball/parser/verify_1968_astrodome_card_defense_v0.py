from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]

REPORT_PATH = (
    ROOT
    / "data"
    / "baseball"
    / "parsed"
    / "strat365"
    / "1968"
    / "reports"
    / "1968.astrodome-card-defense-v0.json"
)


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def require(
    condition: bool,
    message: str,
    failures: list[str],
) -> None:
    if not condition:
        failures.append(message)


def position_map(player: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        position["position"]: position
        for position in player["positions"]
    }


def main() -> None:
    report = load_json(REPORT_PATH)
    summary = report["summary"]
    players = report["players"]
    failures: list[str] = []

    require(report["pass"] is True, "Report pass is not true", failures)
    require(
        summary["expectedHitterCount"] == 14,
        "Expected hitter count is not 14",
        failures,
    )
    require(
        summary["parsedHitterCount"] == 14,
        "Parsed hitter count is not 14",
        failures,
    )
    require(
        summary["sourceComplete"] is True,
        "Card-defense source is not complete",
        failures,
    )
    require(
        summary["positionRecordCount"] == 33,
        "Position record count is not 33",
        failures,
    )
    require(
        summary["multiPositionHitters"] == 10,
        "Multi-position hitter count is not 10",
        failures,
    )
    require(
        summary["catcherEligibleHitters"] == 2,
        "Catcher-eligible hitter count is not 2",
        failures,
    )
    require(
        summary["parseFailureCount"] == 0,
        "One or more defense segments failed to parse",
        failures,
    )
    require(
        summary["primaryPositionMismatchCount"] == 0,
        "One or more primary positions are missing from card eligibility",
        failures,
    )

    player_ids = [player["playerId"] for player in players]
    player_names = [player["playerName"] for player in players]

    require(
        len(set(player_ids)) == len(player_ids),
        "Duplicate player IDs found",
        failures,
    )
    require(
        len(set(player_names)) == len(player_names),
        "Duplicate player names found",
        failures,
    )

    allowed_positions = {
        "C", "1B", "2B", "3B", "SS", "LF", "CF", "RF"
    }

    for player in players:
        positions = player["positions"]
        position_names = [
            position["position"]
            for position in positions
        ]

        require(
            player["cardBacked"] is True,
            f"{player['playerName']}: cardBacked is not true",
            failures,
        )
        require(
            player["source"]["fieldPath"]
            == "$.hitterTraits.defenseText",
            (
                f"{player['playerName']}: unexpected source field "
                f"{player['source']['fieldPath']}"
            ),
            failures,
        )
        require(
            len(positions) == player["positionCount"],
            f"{player['playerName']}: position count mismatch",
            failures,
        )
        require(
            len(position_names) == len(set(position_names)),
            f"{player['playerName']}: duplicate position found",
            failures,
        )
        require(
            player["browserPrimaryPosition"] in position_names,
            (
                f"{player['playerName']}: browser primary position "
                "not present in card positions"
            ),
            failures,
        )

        for position in positions:
            require(
                position["position"] in allowed_positions,
                (
                    f"{player['playerName']}: unsupported position "
                    f"{position['position']}"
                ),
                failures,
            )
            require(
                1 <= position["range"] <= 5,
                (
                    f"{player['playerName']} {position['position']}: "
                    "range outside 1-5"
                ),
                failures,
            )
            require(
                position["error"] >= 0,
                (
                    f"{player['playerName']} {position['position']}: "
                    "negative error rating"
                ),
                failures,
            )
            require(
                bool(position["raw"]),
                (
                    f"{player['playerName']} {position['position']}: "
                    "raw segment missing"
                ),
                failures,
            )

    by_name = {
        player["playerName"]: player
        for player in players
    }

    expected_position_sets = {
        "Freehan, Bill": {"C", "1B", "RF"},
        "Parker, Wes": {"1B", "LF", "CF", "RF"},
        "Torres, Hector": {"SS", "2B"},
        "Brinkman, Ed": {"SS", "2B", "LF"},
        "McAuliffe, Dick": {"2B", "SS"},
        "Mota, Manny": {"LF", "CF", "RF", "2B"},
        "Gosger, Jim": {"LF", "CF", "RF"},
        "Tartabull, Jose": {"RF", "CF", "LF"},
    }

    for player_name, expected_positions in expected_position_sets.items():
        player = by_name.get(player_name)

        require(
            player is not None,
            f"Expected player missing: {player_name}",
            failures,
        )

        if player is None:
            continue

        actual_positions = {
            position["position"]
            for position in player["positions"]
        }

        require(
            actual_positions == expected_positions,
            (
                f"{player_name}: expected positions "
                f"{sorted(expected_positions)}; found "
                f"{sorted(actual_positions)}"
            ),
            failures,
        )

    freehan_positions = position_map(by_name["Freehan, Bill"])
    freehan_catcher = freehan_positions["C"]

    require(
        freehan_catcher["range"] == 1,
        "Freehan catcher range should be 1",
        failures,
    )
    require(
        freehan_catcher["arm"] == -2,
        "Freehan catcher arm should be -2",
        failures,
    )
    require(
        freehan_catcher["error"] == 8,
        "Freehan catcher error rating should be 8",
        failures,
    )
    require(
        freehan_catcher["tRating"] == 3,
        "Freehan catcher T-rating should be 3",
        failures,
    )
    require(
        freehan_catcher["passedBallRating"] == 3,
        "Freehan catcher passed-ball rating should be 3",
        failures,
    )

    fernandez_positions = position_map(by_name["Fernandez, Frank"])
    fernandez_catcher = fernandez_positions["C"]

    require(
        fernandez_catcher["range"] == 3,
        "Fernandez catcher range should be 3",
        failures,
    )
    require(
        fernandez_catcher["arm"] == 0,
        "Fernandez catcher arm should be 0",
        failures,
    )
    require(
        fernandez_catcher["tRating"] == 8,
        "Fernandez catcher T-rating should be 8",
        failures,
    )
    require(
        fernandez_catcher["passedBallRating"] == 2,
        "Fernandez passed-ball rating should be 2",
        failures,
    )

    position_counts = summary["positionCounts"]

    require(position_counts["C"] == 2, "C coverage should be 2", failures)
    require(position_counts["1B"] == 2, "1B coverage should be 2", failures)
    require(position_counts["2B"] == 5, "2B coverage should be 5", failures)
    require(position_counts["3B"] == 2, "3B coverage should be 2", failures)
    require(position_counts["SS"] == 5, "SS coverage should be 5", failures)
    require(position_counts["LF"] == 6, "LF coverage should be 6", failures)
    require(position_counts["CF"] == 5, "CF coverage should be 5", failures)
    require(position_counts["RF"] == 6, "RF coverage should be 6", failures)

    result = {
        "reportPath": str(REPORT_PATH.relative_to(ROOT)),
        "checks": {
            "hitterCount": summary["parsedHitterCount"],
            "positionRecordCount": summary["positionRecordCount"],
            "multiPositionHitters": summary["multiPositionHitters"],
            "catcherEligibleHitters": summary["catcherEligibleHitters"],
            "criticalPlayersChecked": len(expected_position_sets),
            "freehanCatcherRatingsVerified": True,
            "fernandezCatcherRatingsVerified": True,
            "positionCoverageVerified": True,
        },
        "failures": failures,
        "pass": not failures,
    }

    print(json.dumps(result, indent=2))

    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()