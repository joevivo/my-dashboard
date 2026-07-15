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
    / "1968.astrodome-injury-profiles-v0.json"
)


def load_report() -> dict[str, Any]:
    with REPORT_PATH.open("r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def require(condition: bool, message: str, failures: list[str]) -> None:
    if not condition:
        failures.append(message)


def main() -> None:
    report = load_report()
    summary = report["summary"]
    profiles = report["profiles"]

    failures: list[str] = []

    require(
        summary["rosterCount"] == 25,
        f"Expected 25 players; found {summary['rosterCount']}",
        failures,
    )
    require(
        summary["hitterCount"] == 14,
        f"Expected 14 hitters; found {summary['hitterCount']}",
        failures,
    )
    require(
        summary["pitcherCount"] == 11,
        f"Expected 11 pitchers; found {summary['pitcherCount']}",
        failures,
    )
    require(
        summary["sourceComplete"] is True,
        "Source completeness is not true",
        failures,
    )
    require(
        report["rosterLegality"]["pass"] is True,
        "Roster legality did not pass",
        failures,
    )

    player_ids = [profile["playerId"] for profile in profiles]
    player_names = [profile["playerName"] for profile in profiles]

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

    duration_counts = summary["durationCounts"]

    require(
        duration_counts.get("remainder_of_current_game") == 1,
        "Expected one remainder-of-game profile",
        failures,
    )
    require(
        duration_counts.get("three_additional_games") == 8,
        "Expected eight three-additional-game profiles",
        failures,
    )
    require(
        duration_counts.get("fifteen_additional_games") == 16,
        "Expected sixteen fifteen-additional-game profiles",
        failures,
    )

    by_name = {
        profile["playerName"]: profile
        for profile in profiles
    }

    expected_players = {
        "Alou, Felipe": {
            "classification": "remainder_of_current_game",
            "maximumAdditionalGames": 0,
            "usageValue": 710,
        },
        "Freehan, Bill": {
            "classification": "three_additional_games",
            "maximumAdditionalGames": 3,
            "usageValue": 605,
        },
        "Moose, Bob": {
            "classification": "fifteen_additional_games",
            "maximumAdditionalGames": 15,
            "usageValue": 171.1,
        },
        "Chance, Dean": {
            "classification": "three_additional_games",
            "maximumAdditionalGames": 3,
            "usageValue": 292.0,
        },
        "Niekro, Phil": {
            "classification": "three_additional_games",
            "maximumAdditionalGames": 3,
            "usageValue": 257.0,
        },
        "Singer, Bill": {
            "classification": "three_additional_games",
            "maximumAdditionalGames": 3,
            "usageValue": 256.1,
        },
        "Washburn, Ray": {
            "classification": "three_additional_games",
            "maximumAdditionalGames": 3,
            "usageValue": 215.0,
        },
    }

    for player_name, expected in expected_players.items():
        profile = by_name.get(player_name)

        require(
            profile is not None,
            f"Missing expected profile: {player_name}",
            failures,
        )

        if profile is None:
            continue

        require(
            profile["durationLimit"]["classification"]
            == expected["classification"],
            (
                f"{player_name}: expected classification "
                f"{expected['classification']}; found "
                f"{profile['durationLimit']['classification']}"
            ),
            failures,
        )
        require(
            profile["durationLimit"]["maximumAdditionalGames"]
            == expected["maximumAdditionalGames"],
            (
                f"{player_name}: expected maximumAdditionalGames "
                f"{expected['maximumAdditionalGames']}; found "
                f"{profile['durationLimit']['maximumAdditionalGames']}"
            ),
            failures,
        )
        require(
            profile["usageValue"] == expected["usageValue"],
            (
                f"{player_name}: expected usage {expected['usageValue']}; "
                f"found {profile['usageValue']}"
            ),
            failures,
        )

    freehan = by_name["Freehan, Bill"]
    freehan_positions = {
        position["position"]
        for position in freehan["defensiveEligibility"]
    }

    require(
        freehan_positions == {"C"},
        (
            "Freehan defensive eligibility should be catcher only; "
            f"found {sorted(freehan_positions)}"
        ),
        failures,
    )

    pitchers = [
        profile
        for profile in profiles
        if profile["playerType"] == "pitcher"
    ]

    require(
        all(
            profile["injurySusceptibility"]["status"]
            == "not_exposed_in_player_set_metadata"
            for profile in pitchers
        ),
        "One or more pitcher susceptibility records were improperly inferred",
        failures,
    )

    result = {
        "reportPath": str(REPORT_PATH.relative_to(ROOT)),
        "checks": {
            "rosterCount": summary["rosterCount"],
            "hitterCount": summary["hitterCount"],
            "pitcherCount": summary["pitcherCount"],
            "sourceComplete": summary["sourceComplete"],
            "rosterLegalityPass": report["rosterLegality"]["pass"],
            "durationCounts": duration_counts,
            "criticalPlayersChecked": len(expected_players),
            "freehanEligibility": sorted(freehan_positions),
            "pitcherSusceptibilityNotInferred": True,
        },
        "failures": failures,
        "pass": not failures,
    }

    print(json.dumps(result, indent=2))

    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
