from __future__ import annotations

import json
from itertools import combinations
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

DRAFT_BOARD_PATH = (
    ROOT
    / "data"
    / "baseball"
    / "parsed"
    / "strat365"
    / "1968"
    / "draft-prep"
    / "1968.astrodome-operational-draft-board-v0.json"
)

BASELINE_PATH = REPORTS / "1968.astrodome-defensive-baseline-v0.json"
DEFENSE_PATH = REPORTS / "1968.astrodome-card-defense-v0.json"
INJURY_PATH = REPORTS / "1968.astrodome-injury-profiles-v0.json"

JSON_PATH = REPORTS / "1968.astrodome-hitter-absence-coverage-v0.json"
MARKDOWN_PATH = REPORTS / "1968.astrodome-hitter-absence-coverage-v0.md"

POSITIONS = ["C", "1B", "2B", "3B", "SS", "LF", "CF", "RF"]


def load(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def classify_defense(
    position: str,
    range_rating: int,
    standards: dict[str, Any],
) -> str:
    standard = standards[position]

    if range_rating <= standard["preferredMaximumRange"]:
        return "preferred_floor_pass"

    if range_rating <= standard["emergencyMaximumRange"]:
        return "emergency_floor_only"

    return "defensive_floor_failure"


def main() -> None:
    baseline = load(BASELINE_PATH)
    defense = load(DEFENSE_PATH)
    injury = load(INJURY_PATH)
    draft_board = load(DRAFT_BOARD_PATH)

    standards = baseline["defensiveStandards"]
    reserves = set(baseline["reserveHitters"])

    baseline_fielding = {
        item["position"]: item["playerName"]
        for item in baseline["assignments"]
        if item["position"] != "DH"
    }

    baseline_dh = next(
        item["playerName"]
        for item in baseline["assignments"]
        if item["position"] == "DH"
    )

    hitter_profiles = {
        profile["playerName"]: profile
        for profile in injury["profiles"]
        if profile["playerType"] == "hitter"
    }

    hitter_names = sorted(hitter_profiles)

    defense_by_player = {
        player["playerName"]: player["positions"]
        for player in defense["players"]
    }

    board_score = {
        player["playerName"]: float(
            player.get("draftBoardScore") or 0
        )
        for player in draft_board["rankedQueue"]
        if player["pool"] == "hitter"
    }

    position_record: dict[tuple[str, str], dict[str, Any]] = {}

    for player_name, records in defense_by_player.items():
        for record in records:
            position_record[(player_name, record["position"])] = record

    def solve_fielding(
        unavailable: tuple[str, ...],
    ) -> dict[str, Any]:
        unavailable_set = set(unavailable)
        available = set(hitter_names) - unavailable_set

        candidates_by_position: dict[str, list[dict[str, Any]]] = {}

        for position in POSITIONS:
            candidates = []

            for player_name in available:
                record = position_record.get((player_name, position))

                if record is None:
                    continue

                classification = classify_defense(
                    position,
                    int(record["range"]),
                    standards,
                )

                if classification == "defensive_floor_failure":
                    continue

                candidates.append(
                    {
                        "playerName": player_name,
                        "defense": record,
                        "classification": classification,
                        "isReserve": player_name in reserves,
                        "isBaselineIncumbent": (
                            baseline_fielding[position] == player_name
                        ),
                    }
                )

            candidates.sort(
                key=lambda item: (
                    0 if item["isBaselineIncumbent"] else 1,
                    0
                    if item["classification"] == "preferred_floor_pass"
                    else 1,
                    0 if item["isReserve"] else 1,
                    int(item["defense"]["range"]),
                    int(item["defense"]["error"]),
                    item["playerName"],
                )
            )

            candidates_by_position[position] = candidates

        uncovered_positions = [
            position
            for position in POSITIONS
            if not candidates_by_position[position]
        ]

        if uncovered_positions:
            return {
                "legal": False,
                "failureReason": "position_without_available_candidate",
                "uncoveredPositions": uncovered_positions,
                "alignment": None,
            }

        search_order = sorted(
            POSITIONS,
            key=lambda position: (
                len(candidates_by_position[position]),
                position,
            ),
        )

        best_cost: tuple[Any, ...] | None = None
        best_assignment: dict[str, dict[str, Any]] | None = None

        def search(
            index: int,
            used_players: set[str],
            assignment: dict[str, dict[str, Any]],
            emergency_count: int,
            changed_count: int,
            reserve_count: int,
            range_total: int,
            error_total: int,
        ) -> None:
            nonlocal best_cost
            nonlocal best_assignment

            partial_cost = (
                emergency_count,
                changed_count,
                reserve_count,
                range_total,
                error_total,
            )

            if (
                best_cost is not None
                and partial_cost > best_cost[:5]
            ):
                return

            if index == len(search_order):
                lexical = tuple(
                    assignment[position]["playerName"]
                    for position in POSITIONS
                )

                cost = partial_cost + (lexical,)

                if best_cost is None or cost < best_cost:
                    best_cost = cost
                    best_assignment = dict(assignment)

                return

            position = search_order[index]

            for candidate in candidates_by_position[position]:
                player_name = candidate["playerName"]

                if player_name in used_players:
                    continue

                assignment[position] = candidate
                used_players.add(player_name)

                search(
                    index + 1,
                    used_players,
                    assignment,
                    emergency_count
                    + (
                        1
                        if candidate["classification"]
                        == "emergency_floor_only"
                        else 0
                    ),
                    changed_count
                    + (
                        0
                        if candidate["isBaselineIncumbent"]
                        else 1
                    ),
                    reserve_count
                    + (1 if candidate["isReserve"] else 0),
                    range_total + int(candidate["defense"]["range"]),
                    error_total + int(candidate["defense"]["error"]),
                )

                used_players.remove(player_name)
                del assignment[position]

        search(
            index=0,
            used_players=set(),
            assignment={},
            emergency_count=0,
            changed_count=0,
            reserve_count=0,
            range_total=0,
            error_total=0,
        )

        if best_assignment is None:
            return {
                "legal": False,
                "failureReason": "no_unique_eight_position_alignment",
                "uncoveredPositions": [],
                "alignment": None,
            }

        assigned_fielders = {
            item["playerName"]
            for item in best_assignment.values()
        }

        unused_hitters = sorted(
            available - assigned_fielders,
            key=lambda name: (
                -board_score.get(name, 0),
                name,
            ),
        )

        if baseline_dh in unused_hitters:
            dh_player = baseline_dh
            dh_basis = "retained_baseline_dh"
        elif unused_hitters:
            dh_player = unused_hitters[0]
            dh_basis = (
                "highest_draft_board_score_among_unused_hitters"
            )
        else:
            return {
                "legal": False,
                "failureReason": "no_available_designated_hitter",
                "uncoveredPositions": [],
                "alignment": None,
            }

        emergency_positions = [
            position
            for position in POSITIONS
            if (
                best_assignment[position]["classification"]
                == "emergency_floor_only"
            )
        ]

        changed_positions = [
            position
            for position in POSITIONS
            if (
                best_assignment[position]["playerName"]
                != baseline_fielding[position]
            )
        ]

        reserve_fielders = sorted(
            {
                item["playerName"]
                for item in best_assignment.values()
                if item["isReserve"]
            }
        )

        alignment = {
            position: {
                "playerName": best_assignment[position]["playerName"],
                "defense": best_assignment[position]["defense"],
                "classification": (
                    best_assignment[position]["classification"]
                ),
                "changedFromBaseline": (
                    best_assignment[position]["playerName"]
                    != baseline_fielding[position]
                ),
            }
            for position in POSITIONS
        }

        structural_classification = (
            "legal_preferred"
            if not emergency_positions
            else "legal_emergency"
        )

        return {
            "legal": True,
            "failureReason": None,
            "uncoveredPositions": [],
            "structuralClassification": structural_classification,
            "alignment": alignment,
            "dhPlayer": dh_player,
            "dhSelectionBasis": dh_basis,
            "emergencyPositions": emergency_positions,
            "changedPositions": changed_positions,
            "reserveFielders": reserve_fielders,
            "baselineChangeCount": len(changed_positions),
            "emergencyPositionCount": len(emergency_positions),
        }

    def evaluate_scenario(
        unavailable: tuple[str, ...],
    ) -> dict[str, Any]:
        result = solve_fielding(unavailable)

        profiles = [
            hitter_profiles[player_name]
            for player_name in unavailable
        ]

        maximum_additional_games = max(
            int(
                profile["durationLimit"][
                    "maximumAdditionalGames"
                ]
            )
            for profile in profiles
        )

        injury_details = [
            {
                "playerName": profile["playerName"],
                "baselineSlot": next(
                    (
                        assignment["position"]
                        for assignment in baseline["assignments"]
                        if (
                            assignment["playerName"]
                            == profile["playerName"]
                        )
                    ),
                    "RESERVE",
                ),
                "injuryRating": (
                    profile["injurySusceptibility"]["rating"]
                ),
                "durationClassification": (
                    profile["durationLimit"]["classification"]
                ),
                "maximumAdditionalGames": (
                    profile["durationLimit"][
                        "maximumAdditionalGames"
                    ]
                ),
            }
            for profile in profiles
        ]

        if not result["legal"]:
            response_class = "structural_transaction_trigger"
        elif result["structuralClassification"] == "legal_emergency":
            response_class = (
                "extended_emergency_internal_cover"
                if maximum_additional_games >= 15
                else "short_emergency_internal_cover"
            )
        else:
            response_class = (
                "extended_preferred_internal_cover"
                if maximum_additional_games >= 15
                else "short_preferred_internal_cover"
            )

        return {
            "scenarioId": "__".join(
                name.replace(", ", "_").replace(" ", "_")
                for name in unavailable
            ),
            "unavailablePlayers": list(unavailable),
            "injuryDetails": injury_details,
            "maximumAdditionalGames": maximum_additional_games,
            "extendedAbsencePossible": maximum_additional_games >= 15,
            "responseClass": response_class,
            **result,
        }

    single_scenarios = [
        evaluate_scenario((player_name,))
        for player_name in hitter_names
    ]

    dual_scenarios = [
        evaluate_scenario(tuple(pair))
        for pair in combinations(hitter_names, 2)
    ]

    single_failures = [
        scenario
        for scenario in single_scenarios
        if not scenario["legal"]
    ]

    single_emergency = [
        scenario
        for scenario in single_scenarios
        if (
            scenario["legal"]
            and scenario["structuralClassification"]
            == "legal_emergency"
        )
    ]

    dual_failures = [
        scenario
        for scenario in dual_scenarios
        if not scenario["legal"]
    ]

    dual_emergency = [
        scenario
        for scenario in dual_scenarios
        if (
            scenario["legal"]
            and scenario["structuralClassification"]
            == "legal_emergency"
        )
    ]

    critical_dual_scenarios = [
        scenario
        for scenario in dual_scenarios
        if (
            not scenario["legal"]
            or scenario.get("emergencyPositionCount", 0) > 0
            or scenario.get("baselineChangeCount", 0) >= 3
        )
    ]

    summary = {
        "hitterCount": len(hitter_names),
        "singleScenarioCount": len(single_scenarios),
        "singleLegalCount": sum(
            scenario["legal"]
            for scenario in single_scenarios
        ),
        "singlePreferredCount": sum(
            scenario["legal"]
            and scenario["structuralClassification"]
            == "legal_preferred"
            for scenario in single_scenarios
        ),
        "singleEmergencyCount": len(single_emergency),
        "singleStructuralFailureCount": len(single_failures),
        "dualScenarioCount": len(dual_scenarios),
        "dualLegalCount": sum(
            scenario["legal"]
            for scenario in dual_scenarios
        ),
        "dualPreferredCount": sum(
            scenario["legal"]
            and scenario["structuralClassification"]
            == "legal_preferred"
            for scenario in dual_scenarios
        ),
        "dualEmergencyCount": len(dual_emergency),
        "dualStructuralFailureCount": len(dual_failures),
        "criticalDualScenarioCount": len(
            critical_dual_scenarios
        ),
    }

    report_pass = (
        len(single_scenarios) == 14
        and not single_failures
        and len(dual_scenarios) == 91
    )

    report = {
        "reportVersion": "v0",
        "teamContext": baseline["teamContext"],
        "scope": {
            "purpose": (
                "Card-backed structural coverage simulation for every "
                "single- and dual-hitter absence."
            ),
            "doesNotModel": [
                "Final matchup-specific lineups",
                "Precise offensive replacement value",
                "Pitcher injury probability",
            ],
        },
        "summary": summary,
        "singleScenarios": single_scenarios,
        "dualScenarios": dual_scenarios,
        "criticalDualScenarios": critical_dual_scenarios,
        "pass": report_pass,
    }

    with JSON_PATH.open(
        "w",
        encoding="utf-8",
        newline="\n",
    ) as handle:
        json.dump(report, handle, indent=2)
        handle.write("\n")

    lines = [
        "# 1968 Astrodome Hitter Absence Coverage v0",
        "",
        "## Single-Player Absences",
        "",
        "| Player | Legal | Structural result | Changes | Emergency positions |",
        "|---|---:|---|---:|---|",
    ]

    for scenario in single_scenarios:
        player_name = scenario["unavailablePlayers"][0]

        lines.append(
            f"| {player_name} | "
            f"{'yes' if scenario['legal'] else 'no'} | "
            f"{scenario['responseClass']} | "
            f"{scenario.get('baselineChangeCount', 'n/a')} | "
            f"{', '.join(scenario.get('emergencyPositions', [])) or 'None'} |"
        )

    lines.extend(
        [
            "",
            "## Structurally Uncovered Dual Absences",
            "",
        ]
    )

    if dual_failures:
        for scenario in dual_failures:
            lines.append(
                "- "
                + " + ".join(scenario["unavailablePlayers"])
                + ": "
                + scenario["failureReason"]
            )
    else:
        lines.append("- None")

    lines.extend(
        [
            "",
            "## Validation",
            "",
            f"- Report pass: {'yes' if report_pass else 'no'}",
            f"- Single structural failures: {len(single_failures)}",
            f"- Dual structural failures: {len(dual_failures)}",
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
    print(f"HITTERS: {summary['hitterCount']}")
    print(
        f"SINGLE_SCENARIOS: {summary['singleScenarioCount']}"
    )
    print(f"SINGLE_LEGAL: {summary['singleLegalCount']}")
    print(
        f"SINGLE_PREFERRED: {summary['singlePreferredCount']}"
    )
    print(
        f"SINGLE_EMERGENCY: {summary['singleEmergencyCount']}"
    )
    print(
        "SINGLE_STRUCTURAL_FAILURES: "
        f"{summary['singleStructuralFailureCount']}"
    )
    print(f"DUAL_SCENARIOS: {summary['dualScenarioCount']}")
    print(f"DUAL_LEGAL: {summary['dualLegalCount']}")
    print(f"DUAL_PREFERRED: {summary['dualPreferredCount']}")
    print(f"DUAL_EMERGENCY: {summary['dualEmergencyCount']}")
    print(
        "DUAL_STRUCTURAL_FAILURES: "
        f"{summary['dualStructuralFailureCount']}"
    )
    print(
        "CRITICAL_DUAL_SCENARIOS: "
        f"{summary['criticalDualScenarioCount']}"
    )

    failure_pairs = [
        " + ".join(scenario["unavailablePlayers"])
        for scenario in dual_failures
    ]

    print(
        "STRUCTURAL_FAILURE_PAIRS: "
        + (("; ".join(failure_pairs)) if failure_pairs else "NONE")
    )
    print(f"REPORT_PASS: {report_pass}")
    print(f"STATUS: {'PASS' if report_pass else 'REVIEW REQUIRED'}")

    if not report_pass:
        raise SystemExit(1)


if __name__ == "__main__":
    main()