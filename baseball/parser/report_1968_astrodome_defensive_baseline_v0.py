from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]

FIXTURE_PATH = (
    ROOT
    / "data"
    / "baseball"
    / "fixtures"
    / "rosters"
    / "1968_astrodome_alou_freehan_chance_parker_v0.json"
)

DEFENSE_REPORT_PATH = (
    ROOT
    / "data"
    / "baseball"
    / "parsed"
    / "strat365"
    / "1968"
    / "reports"
    / "1968.astrodome-card-defense-v0.json"
)

OUTPUT_DIR = (
    ROOT
    / "data"
    / "baseball"
    / "parsed"
    / "strat365"
    / "1968"
    / "reports"
)

JSON_OUTPUT_PATH = (
    OUTPUT_DIR
    / "1968.astrodome-defensive-baseline-v0.json"
)

MARKDOWN_OUTPUT_PATH = (
    OUTPUT_DIR
    / "1968.astrodome-defensive-baseline-v0.md"
)

BASELINE_ASSIGNMENTS = {
    "C": "Freehan, Bill",
    "1B": "Parker, Wes",
    "2B": "McAuliffe, Dick",
    "3B": "Santo, Ron",
    "SS": "Fregosi, Jim",
    "LF": "Mota, Manny",
    "CF": "Alou, Felipe",
    "RF": "Tartabull, Jose",
    "DH": "Jimenez, Manny",
}

ASSIGNMENT_RATIONALE = {
    "C": "Core catcher and strongest verified catcher defense.",
    "1B": "Canonical everyday first baseman and elite 1B defense.",
    "2B": "Early-foundation second baseman with verified 2B-2e10.",
    "3B": "Early-foundation third baseman with verified 3B-1e15.",
    "SS": "Early-foundation shortstop with verified SS-2e30.",
    "LF": (
        "Baseline corner-outfield assignment; LF-2e6 avoids exposing "
        "Jimenez's LF-4(+2)e25."
    ),
    "CF": "Canonical clean center fielder with verified CF-2(-1)e8.",
    "RF": "Natural right-field assignment with verified RF-3(0)e6.",
    "DH": (
        "Uses Jimenez's bat without exposing his defense-risk LF rating."
    ),
}

DEFENSIVE_STANDARDS = {
    "C": {
        "preferredMaximumRange": 2,
        "emergencyMaximumRange": 3,
    },
    "1B": {
        "preferredMaximumRange": 3,
        "emergencyMaximumRange": 4,
    },
    "2B": {
        "preferredMaximumRange": 2,
        "emergencyMaximumRange": 3,
    },
    "3B": {
        "preferredMaximumRange": 3,
        "emergencyMaximumRange": 4,
    },
    "SS": {
        "preferredMaximumRange": 2,
        "emergencyMaximumRange": 3,
    },
    "LF": {
        "preferredMaximumRange": 3,
        "emergencyMaximumRange": 4,
    },
    "CF": {
        "preferredMaximumRange": 2,
        "emergencyMaximumRange": 3,
    },
    "RF": {
        "preferredMaximumRange": 3,
        "emergencyMaximumRange": 4,
    },
}


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def classify_defense(position: str, range_rating: int) -> str:
    standard = DEFENSIVE_STANDARDS[position]

    if range_rating <= standard["preferredMaximumRange"]:
        return "preferred_floor_pass"

    if range_rating <= standard["emergencyMaximumRange"]:
        return "emergency_floor_only"

    return "defensive_floor_failure"


def main() -> None:
    fixture = load_json(FIXTURE_PATH)
    defense_report = load_json(DEFENSE_REPORT_PATH)

    roster_players = fixture["players"]
    roster_names = {
        player["name"]
        for player in roster_players
    }

    hitter_names = {
        player["name"]
        for player in roster_players
        if player["type"] != "pitcher"
    }

    defense_by_name = {
        player["playerName"]: player
        for player in defense_report["players"]
    }

    assignments = []
    failures = []

    assigned_names = list(BASELINE_ASSIGNMENTS.values())

    if len(set(assigned_names)) != len(assigned_names):
        failures.append("A player is assigned to multiple baseline slots.")

    for position, player_name in BASELINE_ASSIGNMENTS.items():
        if player_name not in roster_names:
            failures.append(
                f"{player_name} is not present in the canonical fixture."
            )
            continue

        if player_name not in hitter_names:
            failures.append(
                f"{player_name} is not a canonical fixture hitter."
            )
            continue

        assignment: dict[str, Any] = {
            "position": position,
            "playerName": player_name,
            "rationale": ASSIGNMENT_RATIONALE[position],
            "cardBacked": position != "DH",
            "defense": None,
            "defensiveClassification": "not_applicable",
        }

        if position != "DH":
            player_defense = defense_by_name.get(player_name)

            if player_defense is None:
                failures.append(
                    f"Card-defense record missing for {player_name}."
                )
                continue

            position_record = next(
                (
                    record
                    for record in player_defense["positions"]
                    if record["position"] == position
                ),
                None,
            )

            if position_record is None:
                failures.append(
                    f"{player_name} is not card-eligible at {position}."
                )
                continue

            assignment["defense"] = position_record
            assignment["defensiveClassification"] = classify_defense(
                position,
                int(position_record["range"]),
            )

            if (
                assignment["defensiveClassification"]
                == "defensive_floor_failure"
            ):
                failures.append(
                    f"{player_name} fails the emergency floor at {position}."
                )

        assignments.append(assignment)

    assigned_hitter_names = {
        assignment["playerName"]
        for assignment in assignments
    }

    reserve_hitters = sorted(
        hitter_names - assigned_hitter_names
    )

    expected_reserves = {
        "Fernandez, Frank",
        "Schaal, Paul",
        "Gosger, Jim",
        "Brinkman, Ed",
        "Torres, Hector",
    }

    if set(reserve_hitters) != expected_reserves:
        failures.append(
            "Baseline reserve set does not match the expected five hitters."
        )

    preferred_passes = sum(
        assignment["defensiveClassification"]
        == "preferred_floor_pass"
        for assignment in assignments
    )

    emergency_only = sum(
        assignment["defensiveClassification"]
        == "emergency_floor_only"
        for assignment in assignments
    )

    floor_failures = sum(
        assignment["defensiveClassification"]
        == "defensive_floor_failure"
        for assignment in assignments
    )

    report = {
        "reportVersion": "v0",
        "teamContext": {
            "playerSet": "1968",
            "park": "Astrodome",
            "fixtureId": fixture["fixtureId"],
        },
        "scope": {
            "purpose": (
                "Defensive baseline for injury and positional-cascade "
                "modeling."
            ),
            "isFinalMatchupLineup": False,
            "flexibleSlots": ["LF", "RF", "DH"],
            "note": (
                "The later matchup engine may alter LF, RF, and DH without "
                "changing the fixed defensive core."
            ),
        },
        "defensiveStandards": DEFENSIVE_STANDARDS,
        "summary": {
            "fixtureRosterCount": len(roster_players),
            "fixtureHitterCount": len(hitter_names),
            "baselineSlotCount": len(assignments),
            "fieldingAssignmentCount": sum(
                assignment["position"] != "DH"
                for assignment in assignments
            ),
            "designatedHitterCount": sum(
                assignment["position"] == "DH"
                for assignment in assignments
            ),
            "reserveHitterCount": len(reserve_hitters),
            "preferredFloorPasses": preferred_passes,
            "emergencyFloorOnly": emergency_only,
            "defensiveFloorFailures": floor_failures,
            "failureCount": len(failures),
        },
        "assignments": assignments,
        "reserveHitters": reserve_hitters,
        "failures": failures,
        "pass": not failures,
    }

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    with JSON_OUTPUT_PATH.open(
        "w",
        encoding="utf-8",
        newline="\n",
    ) as handle:
        json.dump(report, handle, indent=2)
        handle.write("\n")

    markdown_lines = [
        "# 1968 Astrodome Defensive Baseline v0",
        "",
        "## Scope",
        "",
        report["scope"]["purpose"],
        "",
        (
            "**This is not the final matchup lineup.** "
            "LF, RF, and DH remain matchup-flexible."
        ),
        "",
        "## Baseline Alignment",
        "",
        "| Position | Player | Defense | Classification |",
        "|---|---|---|---|",
    ]

    for assignment in assignments:
        defense = assignment["defense"]
        defense_text = (
            defense["raw"]
            if defense is not None
            else "DH"
        )

        markdown_lines.append(
            f"| {assignment['position']} | "
            f"{assignment['playerName']} | "
            f"{defense_text} | "
            f"{assignment['defensiveClassification']} |"
        )

    markdown_lines.extend(
        [
            "",
            "## Reserve Hitters",
            "",
        ]
    )

    for player_name in reserve_hitters:
        markdown_lines.append(f"- {player_name}")

    markdown_lines.extend(
        [
            "",
            "## Validation",
            "",
            f"- Pass: {'yes' if report['pass'] else 'no'}",
            f"- Failures: {len(failures)}",
            "",
        ]
    )

    with MARKDOWN_OUTPUT_PATH.open(
        "w",
        encoding="utf-8",
        newline="\n",
    ) as handle:
        handle.write("\n".join(markdown_lines))

    print(
        json.dumps(
            {
                "jsonOutput": str(JSON_OUTPUT_PATH.relative_to(ROOT)),
                "markdownOutput": str(
                    MARKDOWN_OUTPUT_PATH.relative_to(ROOT)
                ),
                "summary": report["summary"],
                "reserveHitters": reserve_hitters,
                "pass": report["pass"],
            },
            indent=2,
        )
    )

    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()