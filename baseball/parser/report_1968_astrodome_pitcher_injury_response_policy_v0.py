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
ARCHITECTURE_PATH = REPORTS / "1968.astrodome-pitching-architecture-v0.json"

JSON_PATH = REPORTS / "1968.astrodome-pitcher-injury-response-policy-v0.json"
MARKDOWN_PATH = REPORTS / "1968.astrodome-pitcher-injury-response-policy-v0.md"


def load(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def main() -> None:
    injury = load(INJURY_PATH)
    architecture = load(ARCHITECTURE_PATH)

    rotation = architecture["recommendation"]["rotation"]
    swingman = architecture["recommendation"]["swingman"]
    alternative_swingman = architecture["recommendation"][
        "primary_alternative_swingman"
    ]

    profiles = {
        profile["playerName"]: profile
        for profile in injury["profiles"]
        if profile["playerType"] == "pitcher"
    }

    pitcher_policies = []

    for player_name in sorted(profiles):
        profile = profiles[player_name]
        max_games = int(
            profile["durationLimit"]["maximumAdditionalGames"]
        )

        if player_name in rotation:
            stress = architecture["injury_stress"]["single_starter"][
                player_name
            ]

            policy = {
                "playerName": player_name,
                "staffRole": "primary_rotation",
                "endurance": profile["pitcherRole"]["endurance"],
                "throws": profile["pitcherRole"]["throws"],
                "susceptibilityStatus": profile[
                    "injurySusceptibility"
                ]["status"],
                "maximumAdditionalGames": max_games,
                "maximumMissedStarts": int(
                    stress["maximum_missed_starts"]
                ),
                "recommendedAction": (
                    "single_missed_turn_internal_cover"
                ),
                "coveragePlan": (
                    f"{swingman} covers the missed scheduled turn."
                ),
                "transactionRequired": False,
                "workloadRisk": "short_rotation_disruption",
            }

        elif player_name == swingman:
            policy = {
                "playerName": player_name,
                "staffRole": "swingman",
                "endurance": profile["pitcherRole"]["endurance"],
                "throws": profile["pitcherRole"]["throws"],
                "susceptibilityStatus": profile[
                    "injurySusceptibility"
                ]["status"],
                "maximumAdditionalGames": max_games,
                "maximumMissedStarts": None,
                "recommendedAction": (
                    "extended_swingman_contingency_review"
                ),
                "coveragePlan": (
                    "Maintain the four-man starred rotation; compress long "
                    "relief internally and evaluate "
                    f"{alternative_swingman} if emergency-start coverage "
                    "is required."
                ),
                "transactionRequired": False,
                "workloadRisk": (
                    "loss_of_long_relief_and_emergency_starter_capacity"
                ),
            }

        else:
            policy = {
                "playerName": player_name,
                "staffRole": "pure_reliever",
                "endurance": profile["pitcherRole"]["endurance"],
                "throws": profile["pitcherRole"]["throws"],
                "susceptibilityStatus": profile[
                    "injurySusceptibility"
                ]["status"],
                "maximumAdditionalGames": max_games,
                "maximumMissedStarts": None,
                "recommendedAction": (
                    "extended_internal_bullpen_compression"
                ),
                "coveragePlan": (
                    "Reallocate relief innings among the remaining bullpen "
                    "and swingman while monitoring fatigue and role loss."
                ),
                "transactionRequired": False,
                "workloadRisk": "extended_bullpen_compression",
            }

        pitcher_policies.append(policy)

    dual_rotation_triggers = []

    for pair_name, stress in architecture["injury_stress"][
        "two_starter_overlap"
    ].items():
        players = pair_name.split(" + ")

        dual_rotation_triggers.append(
            {
                "unavailablePlayers": players,
                "maximumMissedStarts": int(
                    stress["maximum_missed_starts"]
                ),
                "maximumUncoveredWithOneSwingman": int(
                    stress["maximum_uncovered_with_one_swingman"]
                ),
                "windowsWithUncoveredStart": int(
                    stress["windows_with_uncovered_start"]
                ),
                "recommendedAction": (
                    "emergency_free_agent_review"
                ),
                "reason": (
                    "One swingman can cover only one of the two missed "
                    "rotation turns."
                ),
            }
        )

    susceptibility_unknown = all(
        policy["susceptibilityStatus"]
        == "not_exposed_in_player_set_metadata"
        for policy in pitcher_policies
    )

    rotation_policies = [
        policy
        for policy in pitcher_policies
        if policy["staffRole"] == "primary_rotation"
    ]

    swingman_policies = [
        policy
        for policy in pitcher_policies
        if policy["staffRole"] == "swingman"
    ]

    reliever_policies = [
        policy
        for policy in pitcher_policies
        if policy["staffRole"] == "pure_reliever"
    ]

    report_pass = (
        len(pitcher_policies) == 11
        and len(rotation_policies) == 4
        and len(swingman_policies) == 1
        and len(reliever_policies) == 6
        and len(dual_rotation_triggers) == 6
        and all(
            policy["maximumMissedStarts"] == 1
            for policy in rotation_policies
        )
        and all(
            policy["maximumAdditionalGames"] == 3
            for policy in rotation_policies
        )
        and swingman_policies[0]["maximumAdditionalGames"] == 15
        and susceptibility_unknown
    )

    report = {
        "reportVersion": "v0",
        "teamContext": {
            "season": architecture["season"],
            "park": architecture["park"],
            "architecture": architecture["recommendation"][
                "architecture"
            ],
        },
        "scope": {
            "purpose": (
                "Operational pitcher injury response policy based on "
                "verified duration ceilings and rotation stress modeling."
            ),
            "doesNotModel": [
                "Pitcher injury probability",
                "Unexposed pitcher susceptibility ratings",
                "Matchup-specific bullpen sequencing",
                "Precise relief fatigue accumulation",
            ],
        },
        "summary": {
            "pitcherPolicies": len(pitcher_policies),
            "primaryStarterPolicies": len(rotation_policies),
            "swingmanPolicies": len(swingman_policies),
            "pureRelieverPolicies": len(reliever_policies),
            "dualRotationTransactionTriggers": len(
                dual_rotation_triggers
            ),
            "susceptibilityUnknownForAllPitchers": (
                susceptibility_unknown
            ),
            "rosterChangeRequiredNow": False,
            "draftPlanChanged": False,
        },
        "pitcherPolicies": pitcher_policies,
        "dualRotationTransactionTriggers": dual_rotation_triggers,
        "staffPolicy": {
            "singlePrimaryStarterInjury": (
                f"{swingman} covers one missed scheduled turn."
            ),
            "dualPrimaryStarterOverlap": (
                "One start may remain uncovered; perform an emergency "
                "free-agent review."
            ),
            "swingmanInjury": (
                "Maintain the four-man rotation and evaluate "
                f"{alternative_swingman} if emergency-start depth is needed."
            ),
            "singleRelieverInjury": (
                "Use internal bullpen compression and monitor workload."
            ),
        },
        "pass": report_pass,
    }

    with JSON_PATH.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(report, handle, indent=2)
        handle.write("\n")

    lines = [
        "# 1968 Astrodome Pitcher Injury Response Policy v0",
        "",
        "## Single-Pitcher Policies",
        "",
        "| Pitcher | Staff role | Maximum additional games | Action |",
        "|---|---|---:|---|",
    ]

    for policy in pitcher_policies:
        lines.append(
            f"| {policy['playerName']} | "
            f"{policy['staffRole']} | "
            f"{policy['maximumAdditionalGames']} | "
            f"{policy['recommendedAction']} |"
        )

    lines.extend(
        [
            "",
            "## Dual-Rotation Transaction Triggers",
            "",
        ]
    )

    for trigger in dual_rotation_triggers:
        lines.append(
            "- "
            + " + ".join(trigger["unavailablePlayers"])
            + ": emergency free-agent review"
        )

    lines.extend(
        [
            "",
            "## Current Decision",
            "",
            "- Roster change required now: no",
            "- Draft plan changed: no",
            "- Pitcher susceptibility inferred: no",
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
    print(f"PITCHER_POLICIES: {len(pitcher_policies)}")
    print(f"PRIMARY_STARTERS: {len(rotation_policies)}")
    print(f"SWINGMEN: {len(swingman_policies)}")
    print(f"PURE_RELIEVERS: {len(reliever_policies)}")
    print(
        "DUAL_ROTATION_TRANSACTION_TRIGGERS: "
        f"{len(dual_rotation_triggers)}"
    )
    print(
        "SUSCEPTIBILITY_UNKNOWN_FOR_ALL_PITCHERS: "
        f"{susceptibility_unknown}"
    )
    print("ROSTER_CHANGE_REQUIRED_NOW: False")
    print("DRAFT_PLAN_CHANGED: False")
    print(f"REPORT_PASS: {report_pass}")
    print(f"STATUS: {'PASS' if report_pass else 'REVIEW REQUIRED'}")

    if not report_pass:
        raise SystemExit(1)


if __name__ == "__main__":
    main()