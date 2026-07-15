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

BASELINE_PATH = REPORTS / "1968.astrodome-defensive-baseline-v0.json"
BACKUP_PATH = REPORTS / "1968.astrodome-defensive-backup-graph-v0.json"
ABSENCE_PATH = REPORTS / "1968.astrodome-hitter-absence-coverage-v0.json"
POLICY_PATH = REPORTS / "1968.astrodome-hitter-injury-response-policy-v0.json"

EXPECTED_FAILURE_PAIRS = {
    frozenset(("Fernandez, Frank", "Freehan, Bill")),
    frozenset(("Fernandez, Frank", "Parker, Wes")),
    frozenset(("Freehan, Bill", "Parker, Wes")),
    frozenset(("Santo, Ron", "Schaal, Paul")),
}


def load(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def main() -> None:
    checks: list[tuple[str, bool]] = []
    failures: list[str] = []

    def check(name: str, result: bool) -> None:
        checks.append((name, result))

        if not result:
            failures.append(name)

    baseline = load(BASELINE_PATH)
    backup = load(BACKUP_PATH)
    absence = load(ABSENCE_PATH)
    policy = load(POLICY_PATH)

    check("baseline_report_pass", baseline.get("pass") is True)
    check("backup_report_pass", backup.get("pass") is True)
    check("absence_report_pass", absence.get("pass") is True)
    check("policy_report_pass", policy.get("pass") is True)

    check(
        "baseline_has_nine_slots",
        baseline["summary"]["baselineSlotCount"] == 9,
    )

    check(
        "baseline_has_five_reserves",
        baseline["summary"]["reserveHitterCount"] == 5,
    )

    check(
        "all_positions_have_direct_backup",
        backup["summary"]["positionsWithDirectBackup"] == 8,
    )

    check(
        "no_direct_defensive_floor_failures",
        backup["summary"]["directDefensiveFloorFailures"] == 0,
    )

    check(
        "fourteen_single_absence_scenarios",
        absence["summary"]["singleScenarioCount"] == 14,
    )

    check(
        "all_single_absences_are_legal",
        absence["summary"]["singleLegalCount"] == 14,
    )

    check(
        "three_single_emergency_scenarios",
        absence["summary"]["singleEmergencyCount"] == 3,
    )

    check(
        "ninety_one_dual_scenarios",
        absence["summary"]["dualScenarioCount"] == 91,
    )

    check(
        "four_dual_structural_failures",
        absence["summary"]["dualStructuralFailureCount"] == 4,
    )

    actual_failure_pairs = {
        frozenset(scenario["unavailablePlayers"])
        for scenario in absence["dualScenarios"]
        if not scenario["legal"]
    }

    check(
        "dual_failure_pairs_match_expected",
        actual_failure_pairs == EXPECTED_FAILURE_PAIRS,
    )

    policy_by_player = {
        item["playerName"]: item
        for item in policy["singleAbsencePolicies"]
    }

    check(
        "fourteen_single_response_policies",
        len(policy_by_player) == 14,
    )

    check(
        "parker_is_transaction_review_trigger",
        (
            policy_by_player["Parker, Wes"]["recommendedAction"]
            == "transaction_review_trigger"
        ),
    )

    check(
        "freehan_is_short_emergency_cover",
        (
            policy_by_player["Freehan, Bill"]["recommendedAction"]
            == "short_internal_emergency_cover"
        ),
    )

    check(
        "mcauliffe_is_short_emergency_cover",
        (
            policy_by_player["McAuliffe, Dick"]["recommendedAction"]
            == "short_internal_emergency_cover"
        ),
    )

    critical_reserves = {
        item["playerName"]
        for item in policy["reserveDependencies"]
        if (
            item["dependencyClass"]
            == "critical_single_backup_dependency"
        )
    }

    check(
        "critical_reserves_match_expected",
        critical_reserves == {"Fernandez, Frank", "Schaal, Paul"},
    )

    policy_trigger_pairs = {
        frozenset(item["unavailablePlayers"])
        for item in policy["dualTransactionTriggers"]
    }

    check(
        "policy_trigger_pairs_match_absence_failures",
        policy_trigger_pairs == actual_failure_pairs,
    )

    check(
        "no_current_roster_change_required",
        policy["summary"]["rosterChangeRequiredNow"] is False,
    )

    check(
        "draft_plan_unchanged",
        policy["summary"]["draftPlanChanged"] is False,
    )

    print("# RESULT SUMMARY")
    print(f"CHECKS_RUN: {len(checks)}")
    print(f"CHECKS_PASSED: {sum(result for _, result in checks)}")
    print(f"CHECKS_FAILED: {len(failures)}")

    for name, result in checks:
        print(f"CHECK: {name} | {'PASS' if result else 'FAIL'}")

    print(
        "FAILURE_NAMES: "
        + (",".join(failures) if failures else "NONE")
    )
    print(f"VERIFICATION_PASS: {not failures}")
    print(f"STATUS: {'PASS' if not failures else 'REVIEW REQUIRED'}")

    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()