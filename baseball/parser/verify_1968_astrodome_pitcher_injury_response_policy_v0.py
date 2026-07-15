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

INJURY_PATH = REPORTS / "1968.astrodome-injury-profiles-v0.json"
ARCHITECTURE_PATH = REPORTS / "1968.astrodome-pitching-architecture-v0.json"
POLICY_PATH = REPORTS / "1968.astrodome-pitcher-injury-response-policy-v0.json"

EXPECTED_ROTATION = {
    "Chance, Dean",
    "Niekro, Phil",
    "Singer, Bill",
    "Washburn, Ray",
}

EXPECTED_RELIEVERS = {
    "Aguirre, Hank",
    "Hamilton, Steve",
    "Hoerner, Joe",
    "Knowles, Darold",
    "McDaniel, Lindy",
    "Wilhelm, Hoyt",
}


def load(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def main() -> None:
    injury = load(INJURY_PATH)
    architecture = load(ARCHITECTURE_PATH)
    policy = load(POLICY_PATH)

    checks: list[tuple[str, bool]] = []
    failures: list[str] = []

    def check(name: str, result: bool) -> None:
        checks.append((name, result))

        if not result:
            failures.append(name)

    check("policy_report_pass", policy.get("pass") is True)

    check(
        "eleven_pitcher_policies",
        policy["summary"]["pitcherPolicies"] == 11,
    )

    check(
        "four_primary_starter_policies",
        policy["summary"]["primaryStarterPolicies"] == 4,
    )

    check(
        "one_swingman_policy",
        policy["summary"]["swingmanPolicies"] == 1,
    )

    check(
        "six_pure_reliever_policies",
        policy["summary"]["pureRelieverPolicies"] == 6,
    )

    check(
        "six_dual_rotation_triggers",
        policy["summary"]["dualRotationTransactionTriggers"] == 6,
    )

    check(
        "susceptibility_unknown_for_all_pitchers",
        policy["summary"]["susceptibilityUnknownForAllPitchers"] is True,
    )

    check(
        "no_current_roster_change_required",
        policy["summary"]["rosterChangeRequiredNow"] is False,
    )

    check(
        "draft_plan_unchanged",
        policy["summary"]["draftPlanChanged"] is False,
    )

    policy_by_name = {
        item["playerName"]: item
        for item in policy["pitcherPolicies"]
    }

    check(
        "policy_names_match_injury_profiles",
        set(policy_by_name)
        == {
            profile["playerName"]
            for profile in injury["profiles"]
            if profile["playerType"] == "pitcher"
        },
    )

    rotation_names = {
        name
        for name, item in policy_by_name.items()
        if item["staffRole"] == "primary_rotation"
    }

    check(
        "rotation_names_match_expected",
        rotation_names == EXPECTED_ROTATION,
    )

    check(
        "architecture_rotation_matches_policy",
        set(architecture["recommendation"]["rotation"])
        == rotation_names,
    )

    check(
        "all_primary_starters_have_three_game_ceiling",
        all(
            policy_by_name[name]["maximumAdditionalGames"] == 3
            for name in EXPECTED_ROTATION
        ),
    )

    check(
        "all_primary_starters_have_one_missed_turn",
        all(
            policy_by_name[name]["maximumMissedStarts"] == 1
            for name in EXPECTED_ROTATION
        ),
    )

    check(
        "all_primary_starters_use_internal_cover",
        all(
            policy_by_name[name]["recommendedAction"]
            == "single_missed_turn_internal_cover"
            for name in EXPECTED_ROTATION
        ),
    )

    check(
        "moose_is_swingman",
        policy_by_name["Moose, Bob"]["staffRole"] == "swingman",
    )

    check(
        "moose_has_fifteen_game_ceiling",
        policy_by_name["Moose, Bob"]["maximumAdditionalGames"] == 15,
    )

    check(
        "architecture_swingman_matches_policy",
        architecture["recommendation"]["swingman"] == "Moose, Bob",
    )

    reliever_names = {
        name
        for name, item in policy_by_name.items()
        if item["staffRole"] == "pure_reliever"
    }

    check(
        "reliever_names_match_expected",
        reliever_names == EXPECTED_RELIEVERS,
    )

    check(
        "all_relief_ceiling_values_are_fifteen",
        all(
            policy_by_name[name]["maximumAdditionalGames"] == 15
            for name in EXPECTED_RELIEVERS
        ),
    )

    check(
        "all_relievers_use_bullpen_compression",
        all(
            policy_by_name[name]["recommendedAction"]
            == "extended_internal_bullpen_compression"
            for name in EXPECTED_RELIEVERS
        ),
    )

    expected_pairs = {
        frozenset(pair)
        for pair in combinations(sorted(EXPECTED_ROTATION), 2)
    }

    actual_pairs = {
        frozenset(item["unavailablePlayers"])
        for item in policy["dualRotationTransactionTriggers"]
    }

    check(
        "dual_trigger_pairs_cover_all_rotation_pairs",
        actual_pairs == expected_pairs,
    )

    check(
        "every_dual_trigger_has_one_uncovered_start",
        all(
            item["maximumUncoveredWithOneSwingman"] == 1
            for item in policy["dualRotationTransactionTriggers"]
        ),
    )

    check(
        "every_dual_trigger_requires_free_agent_review",
        all(
            item["recommendedAction"]
            == "emergency_free_agent_review"
            for item in policy["dualRotationTransactionTriggers"]
        ),
    )

    check(
        "no_pitcher_susceptibility_was_inferred",
        all(
            item["susceptibilityStatus"]
            == "not_exposed_in_player_set_metadata"
            for item in policy["pitcherPolicies"]
        ),
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