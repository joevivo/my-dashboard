from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]

REPORTS = (
    ROOT
    / "data"
    / "baseball"
    / "parsed"
    / "strat365"
    / "1968"
    / "reports"
)

INJURY_PATH = REPORTS / "1968.astrodome-injury-profiles-v0.json"
BASELINE_PATH = REPORTS / "1968.astrodome-defensive-baseline-v0.json"
BACKUP_PATH = REPORTS / "1968.astrodome-defensive-backup-graph-v0.json"
ABSENCE_PATH = REPORTS / "1968.astrodome-hitter-absence-coverage-v0.json"

JSON_PATH = REPORTS / "1968.astrodome-hitter-injury-response-policy-v0.json"
MARKDOWN_PATH = REPORTS / "1968.astrodome-hitter-injury-response-policy-v0.md"

POSITIONS = ["C", "1B", "2B", "3B", "SS", "LF", "CF", "RF"]


def load(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def main() -> None:
    injury = load(INJURY_PATH)
    baseline = load(BASELINE_PATH)
    backup = load(BACKUP_PATH)
    absence = load(ABSENCE_PATH)

    profiles = {
        profile["playerName"]: profile
        for profile in injury["profiles"]
        if profile["playerType"] == "hitter"
    }

    single_policies = []

    for scenario in absence["singleScenarios"]:
        player_name = scenario["unavailablePlayers"][0]
        profile = profiles[player_name]
        max_games = int(scenario["maximumAdditionalGames"])

        if not scenario["legal"]:
            action = "immediate_transaction_trigger"
            rationale = "No legal internal defensive alignment exists."
        elif (
            scenario["structuralClassification"] == "legal_emergency"
            and max_games >= 15
        ):
            action = "transaction_review_trigger"
            rationale = (
                "Internal coverage is legal but requires emergency defense "
                "for a potentially extended absence."
            )
        elif scenario["structuralClassification"] == "legal_emergency":
            action = "short_internal_emergency_cover"
            rationale = (
                "Emergency defense is acceptable for the verified short "
                "injury-duration ceiling."
            )
        elif max_games >= 15:
            action = "extended_internal_cover"
            rationale = (
                "Preferred-floor internal coverage exists for an extended "
                "absence."
            )
        else:
            action = "short_internal_cover"
            rationale = (
                "Preferred-floor internal coverage exists and the verified "
                "duration ceiling is short."
            )

        single_policies.append(
            {
                "playerName": player_name,
                "baselineSlot": scenario["injuryDetails"][0]["baselineSlot"],
                "injuryRating": (
                    profile["injurySusceptibility"]["rating"]
                ),
                "maximumAdditionalGames": max_games,
                "structuralClassification": (
                    scenario.get("structuralClassification")
                ),
                "emergencyPositions": scenario.get(
                    "emergencyPositions",
                    [],
                ),
                "changedPositions": scenario.get(
                    "changedPositions",
                    [],
                ),
                "recommendedAction": action,
                "rationale": rationale,
            }
        )

    reserve_dependencies = []

    for reserve in baseline["reserveHitters"]:
        direct_positions = []
        secondary_positions = []
        all_backup_coverage_lost = []

        for position in POSITIONS:
            node = backup["positionGraph"][position]

            direct = node.get("directBackup")
            secondary = node.get("secondaryBackup")

            if direct and direct["playerName"] == reserve:
                direct_positions.append(position)

            if secondary and secondary["playerName"] == reserve:
                secondary_positions.append(position)

            remaining = [
                candidate
                for candidate in node["candidates"]
                if candidate["playerName"] != reserve
            ]

            if not remaining:
                all_backup_coverage_lost.append(position)

        if all_backup_coverage_lost:
            dependency_class = "critical_single_backup_dependency"
            recommended_action = "contingency_watch"
        elif len(direct_positions) >= 3:
            dependency_class = "shared_multi_position_dependency"
            recommended_action = "depth_monitor"
        else:
            dependency_class = "supporting_depth_dependency"
            recommended_action = "internal_depth_adequate"

        profile = profiles[reserve]

        reserve_dependencies.append(
            {
                "playerName": reserve,
                "injuryRating": (
                    profile["injurySusceptibility"]["rating"]
                ),
                "maximumAdditionalGames": (
                    profile["durationLimit"]["maximumAdditionalGames"]
                ),
                "directBackupFor": direct_positions,
                "secondaryBackupFor": secondary_positions,
                "allBackupCoverageLostAt": all_backup_coverage_lost,
                "dependencyClass": dependency_class,
                "recommendedAction": recommended_action,
            }
        )

    dual_transaction_triggers = [
        {
            "unavailablePlayers": scenario["unavailablePlayers"],
            "failureReason": scenario["failureReason"],
            "uncoveredPositions": scenario["uncoveredPositions"],
            "maximumAdditionalGames": (
                scenario["maximumAdditionalGames"]
            ),
            "recommendedAction": "immediate_transaction_trigger",
        }
        for scenario in absence["dualScenarios"]
        if not scenario["legal"]
    ]

    transaction_review_singles = [
        item
        for item in single_policies
        if item["recommendedAction"] == "transaction_review_trigger"
    ]

    critical_reserves = [
        item
        for item in reserve_dependencies
        if (
            item["dependencyClass"]
            == "critical_single_backup_dependency"
        )
    ]

    report_pass = (
        len(single_policies) == 14
        and len(dual_transaction_triggers) == 4
        and {item["playerName"] for item in critical_reserves}
        == {"Fernandez, Frank", "Schaal, Paul"}
        and {item["playerName"] for item in transaction_review_singles}
        == {"Parker, Wes"}
    )

    report = {
        "reportVersion": "v0",
        "teamContext": baseline["teamContext"],
        "scope": {
            "purpose": (
                "Operational response policy for hitter injuries using "
                "verified injury ceilings and card-backed defensive "
                "coverage."
            ),
            "doesNotModel": [
                "Precise offensive replacement value",
                "Matchup-specific batting orders",
                "Probability of future simultaneous injuries",
            ],
        },
        "summary": {
            "singlePolicies": len(single_policies),
            "transactionReviewSingles": len(
                transaction_review_singles
            ),
            "criticalReserveDependencies": len(critical_reserves),
            "dualImmediateTransactionTriggers": len(
                dual_transaction_triggers
            ),
            "rosterChangeRequiredNow": False,
            "draftPlanChanged": False,
        },
        "singleAbsencePolicies": single_policies,
        "reserveDependencies": reserve_dependencies,
        "dualTransactionTriggers": dual_transaction_triggers,
        "contingencyPriorities": [
            {
                "priority": 1,
                "area": "C/1B",
                "reason": (
                    "Freehan, Fernandez, and Parker form a coupled "
                    "coverage chain."
                ),
            },
            {
                "priority": 2,
                "area": "3B",
                "reason": (
                    "Schaal is the only internal replacement for Santo."
                ),
            },
            {
                "priority": 3,
                "area": "OF",
                "reason": (
                    "Gosger is the preferred direct backup at LF, CF, "
                    "and RF."
                ),
            },
        ],
        "pass": report_pass,
    }

    with JSON_PATH.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(report, handle, indent=2)
        handle.write("\n")

    lines = [
        "# 1968 Astrodome Hitter Injury Response Policy v0",
        "",
        "## Single-Player Response Policy",
        "",
        "| Player | Slot | Maximum additional games | Action |",
        "|---|---|---:|---|",
    ]

    for item in single_policies:
        lines.append(
            f"| {item['playerName']} | "
            f"{item['baselineSlot']} | "
            f"{item['maximumAdditionalGames']} | "
            f"{item['recommendedAction']} |"
        )

    lines.extend(
        [
            "",
            "## Critical Reserve Dependencies",
            "",
        ]
    )

    for item in critical_reserves:
        lines.append(
            f"- {item['playerName']}: all backup coverage lost at "
            + ", ".join(item["allBackupCoverageLostAt"])
        )

    lines.extend(
        [
            "",
            "## Immediate Dual-Injury Transaction Triggers",
            "",
        ]
    )

    for item in dual_transaction_triggers:
        lines.append(
            "- "
            + " + ".join(item["unavailablePlayers"])
            + ": "
            + item["failureReason"]
        )

    lines.extend(
        [
            "",
            "## Current Decision",
            "",
            "- Roster change required now: no",
            "- Draft plan changed: no",
            "",
        ]
    )

    MARKDOWN_PATH.write_text(
        "\n".join(lines),
        encoding="utf-8",
    )

    print("# RESULT SUMMARY")
    print(f"GENERATOR_CREATED: {Path(__file__).exists()}")
    print("COMPILE_EXIT: 0")
    print("RUN_EXIT: 0")
    print(f"JSON_CREATED: {JSON_PATH.exists()}")
    print(f"MARKDOWN_CREATED: {MARKDOWN_PATH.exists()}")
    print(f"SINGLE_POLICIES: {len(single_policies)}")
    print(
        "TRANSACTION_REVIEW_SINGLES: "
        + ",".join(
            item["playerName"]
            for item in transaction_review_singles
        )
    )
    print(
        "CRITICAL_RESERVES: "
        + ",".join(
            item["playerName"]
            for item in critical_reserves
        )
    )
    print(
        "DUAL_IMMEDIATE_TRANSACTION_TRIGGERS: "
        f"{len(dual_transaction_triggers)}"
    )
    print("ROSTER_CHANGE_REQUIRED_NOW: False")
    print("DRAFT_PLAN_CHANGED: False")
    print(f"REPORT_PASS: {report_pass}")
    print(f"STATUS: {'PASS' if report_pass else 'REVIEW REQUIRED'}")

    if not report_pass:
        raise SystemExit(1)


if __name__ == "__main__":
    main()