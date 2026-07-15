from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]

ROSTER_PATH = (
    ROOT
    / "data"
    / "baseball"
    / "parsed"
    / "strat365"
    / "1968"
    / "draft-prep"
    / "1968.astrodome-operational-draft-board-v0.json"
)

ROSTER_METADATA_PATH = (
    ROOT
    / "data"
    / "baseball"
    / "parsed"
    / "strat365"
    / "1968"
    / "player-roster-metadata"
    / "1968.player-roster-metadata.json"
)

DEFENSE_METADATA_PATH = (
    ROOT
    / "data"
    / "baseball"
    / "parsed"
    / "strat365"
    / "1968"
    / "player-defense-metadata"
    / "1968.player-defense-metadata.json"
)

REPORT_DIR = (
    ROOT
    / "data"
    / "baseball"
    / "parsed"
    / "strat365"
    / "1968"
    / "reports"
)

JSON_OUTPUT_PATH = REPORT_DIR / "1968.astrodome-injury-profiles-v0.json"
MARKDOWN_OUTPUT_PATH = REPORT_DIR / "1968.astrodome-injury-profiles-v0.md"

RULE_SOURCE = "https://365.strat-o-matic.com/help/rules/baseball#injuries"
ROSTER_RULE_SOURCE = "https://365.strat-o-matic.com/help/rules/baseball#roster"


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def normalize_name(value: str | None) -> str:
    return " ".join((value or "").strip().lower().split())


def classify_hitter_duration(injury_rating: int, ab_plus_bb: int) -> dict[str, Any]:
    if injury_rating == 0:
        return {
            "classification": "no_injury_chance",
            "maximumAdditionalGames": None,
        }

    if ab_plus_bb >= 680:
        return {
            "classification": "remainder_of_current_game",
            "maximumAdditionalGames": 0,
        }

    if ab_plus_bb >= 600:
        return {
            "classification": "three_additional_games",
            "maximumAdditionalGames": 3,
        }

    return {
        "classification": "fifteen_additional_games",
        "maximumAdditionalGames": 15,
    }


def classify_pitcher_duration(innings_pitched: float) -> dict[str, Any]:
    if innings_pitched >= 300:
        return {
            "classification": "remainder_of_current_game",
            "maximumAdditionalGames": 0,
        }

    if innings_pitched >= 200:
        return {
            "classification": "three_additional_games",
            "maximumAdditionalGames": 3,
        }

    return {
        "classification": "fifteen_additional_games",
        "maximumAdditionalGames": 15,
    }


def build_profile(
    roster_entry: dict[str, Any],
    metadata: dict[str, Any],
    defense: dict[str, Any],
) -> dict[str, Any]:
    is_pitcher = metadata.get("role") == "pitcher"

    common = {
        "playerId": metadata.get("playerId"),
        "playerName": metadata.get("playerName"),
        "rosterOperationalRole": roster_entry.get("role"),
        "playerType": "pitcher" if is_pitcher else "hitter",
        "injurySystem": "standard",
        "ruleSource": RULE_SOURCE,
        "sourcePaths": {
            "roster": str(ROSTER_PATH.relative_to(ROOT)),
            "rosterMetadata": str(ROSTER_METADATA_PATH.relative_to(ROOT)),
            "defenseMetadata": str(DEFENSE_METADATA_PATH.relative_to(ROOT)),
        },
        "warnings": [],
    }

    if is_pitcher:
        innings_pitched = float(metadata["pitcherStats"]["inningsPitched"])
        duration = classify_pitcher_duration(innings_pitched)

        common.update(
            {
                "injurySusceptibility": {
                    "status": "not_exposed_in_player_set_metadata",
                    "rating": None,
                },
                "usageBasis": "innings_pitched",
                "usageValue": innings_pitched,
                "durationLimit": duration,
                "pitcherRole": {
                    "endurance": metadata["pitcher"].get("endurance"),
                    "throws": metadata["pitcher"].get("throws"),
                },
                "defensiveEligibility": [],
            }
        )

        common["warnings"].append(
            "Pitcher injury susceptibility is not exposed as a discrete "
            "player-set metadata field; only the duration ceiling is derived."
        )

        return common

    hitter_stats = metadata["hitterStats"]
    injury_rating = int(metadata["hitter"]["injury"])
    at_bats = int(hitter_stats["ab"])
    walks = int(hitter_stats["walks"])
    ab_plus_bb = at_bats + walks
    duration = classify_hitter_duration(injury_rating, ab_plus_bb)

    positions = []
    for position in defense["hitterDefense"].get("positions", []):
        positions.append(
            {
                "position": position.get("position"),
                "range": position.get("range"),
                "arm": position.get("arm"),
                "error": position.get("error"),
                "raw": position.get("raw"),
            }
        )

    common.update(
        {
            "injurySusceptibility": {
                "status": "verified",
                "rating": injury_rating,
            },
            "usageBasis": "ab_plus_bb",
            "usageValue": ab_plus_bb,
            "usageComponents": {
                "atBats": at_bats,
                "walks": walks,
            },
            "durationLimit": duration,
            "primaryPosition": metadata["hitter"].get("primaryPosition"),
            "defensiveEligibility": positions,
        }
    )

    return common


def validate_roster(
    profiles: list[dict[str, Any]],
) -> dict[str, Any]:
    hitters = [profile for profile in profiles if profile["playerType"] == "hitter"]
    pitchers = [profile for profile in profiles if profile["playerType"] == "pitcher"]

    primary_catchers = [
        profile
        for profile in hitters
        if profile.get("primaryPosition") == "C"
    ]

    starter_pitchers = [
        profile
        for profile in pitchers
        if "S" in (profile.get("pitcherRole", {}).get("endurance") or "")
    ]

    pure_relief_pitchers = [
        profile
        for profile in pitchers
        if (
            "R" in (profile.get("pitcherRole", {}).get("endurance") or "")
            and "S" not in (profile.get("pitcherRole", {}).get("endurance") or "")
        )
    ]

    checks = {
        "totalPlayers": {
            "value": len(profiles),
            "minimum": 25,
            "maximum": 28,
            "pass": 25 <= len(profiles) <= 28,
        },
        "hitters": {
            "value": len(hitters),
            "minimum": 13,
            "maximum": 17,
            "pass": 13 <= len(hitters) <= 17,
        },
        "pitchers": {
            "value": len(pitchers),
            "minimum": 11,
            "maximum": 14,
            "pass": 11 <= len(pitchers) <= 14,
        },
        "primaryCatchers": {
            "value": len(primary_catchers),
            "minimum": 2,
            "pass": len(primary_catchers) >= 2,
        },
        "starterEndurancePitchers": {
            "value": len(starter_pitchers),
            "minimum": 5,
            "pass": len(starter_pitchers) >= 5,
        },
        "pureRelievers": {
            "value": len(pure_relief_pitchers),
            "minimum": 4,
            "pass": len(pure_relief_pitchers) >= 4,
        },
    }

    return {
        "ruleSource": ROSTER_RULE_SOURCE,
        "checks": checks,
        "pass": all(check["pass"] for check in checks.values()),
        "closerEnduranceCheck": {
            "status": "not_evaluated_here",
            "reason": (
                "Closer endurance is derived from authenticated card text "
                "by the existing 1968 role-coverage engine."
            ),
        },
    }


def build_report() -> dict[str, Any]:
    roster_document = load_json(ROSTER_PATH)
    roster_metadata_document = load_json(ROSTER_METADATA_PATH)
    defense_metadata_document = load_json(DEFENSE_METADATA_PATH)

    roster = roster_document["rankedQueue"]
    roster_metadata = roster_metadata_document["players"]
    defense_metadata = defense_metadata_document["players"]

    roster_lookup = {
        normalize_name(player["playerName"]): player
        for player in roster_metadata
    }

    defense_lookup = {
        normalize_name(player["playerName"]): player
        for player in defense_metadata
    }

    profiles = []

    for roster_entry in roster:
        key = normalize_name(roster_entry["playerName"])

        if key not in roster_lookup:
            raise ValueError(
                f"Roster metadata not found for {roster_entry['playerName']}"
            )

        if key not in defense_lookup:
            raise ValueError(
                f"Defense metadata not found for {roster_entry['playerName']}"
            )

        profiles.append(
            build_profile(
                roster_entry,
                roster_lookup[key],
                defense_lookup[key],
            )
        )

    profiles.sort(
        key=lambda profile: (
            profile["playerType"],
            profile["playerName"],
        )
    )

    duration_counts: dict[str, int] = {}

    for profile in profiles:
        classification = profile["durationLimit"]["classification"]
        duration_counts[classification] = duration_counts.get(classification, 0) + 1

    source_complete = all(
        profile.get("playerId") is not None
        and profile.get("playerName")
        and profile.get("usageValue") is not None
        for profile in profiles
    )

    return {
        "reportVersion": "v0",
        "teamContext": {
            "playerSet": "1968",
            "park": "Astrodome",
            "rosterName": "canonical_operational_roster",
        },
        "injurySystem": {
            "name": "standard",
            "ruleSource": RULE_SOURCE,
            "hitterDurationBasis": "AB+BB",
            "pitcherDurationBasis": "IP",
        },
        "summary": {
            "rosterCount": len(profiles),
            "hitterCount": sum(
                profile["playerType"] == "hitter"
                for profile in profiles
            ),
            "pitcherCount": sum(
                profile["playerType"] == "pitcher"
                for profile in profiles
            ),
            "sourceComplete": source_complete,
            "durationCounts": duration_counts,
        },
        "rosterLegality": validate_roster(profiles),
        "profiles": profiles,
    }


def render_markdown(report: dict[str, Any]) -> str:
    summary = report["summary"]
    duration_counts = summary["durationCounts"]

    lines = [
        "# 1968 Astrodome Injury Profiles v0",
        "",
        "## Scope",
        "",
        "Canonical injury susceptibility and maximum-duration profiles for "
        "the current Astrodome operational roster.",
        "",
        "## Summary",
        "",
        f"- Players: {summary['rosterCount']}",
        f"- Hitters: {summary['hitterCount']}",
        f"- Pitchers: {summary['pitcherCount']}",
        f"- Source complete: {'yes' if summary['sourceComplete'] else 'no'}",
        "- Standard Injury System",
        f"- Rule source: {report['injurySystem']['ruleSource']}",
        "",
        "### Duration Distribution",
        "",
    ]

    for classification, count in sorted(duration_counts.items()):
        lines.append(f"- {classification}: {count}")

    lines.extend(
        [
            "",
            "## Player Profiles",
            "",
            "| Player | Type | Injury rating | Usage | Maximum | Position/role |",
            "|---|---|---:|---:|---|---|",
        ]
    )

    for profile in report["profiles"]:
        injury_rating = profile["injurySusceptibility"].get("rating")
        injury_display = (
            str(injury_rating)
            if injury_rating is not None
            else "not exposed"
        )

        usage = f"{profile['usageValue']} {profile['usageBasis']}"

        if profile["playerType"] == "pitcher":
            position_role = profile["pitcherRole"].get("endurance") or ""
        else:
            position_role = "/".join(
                position["position"]
                for position in profile["defensiveEligibility"]
                if position.get("position")
            )

        maximum = profile["durationLimit"]["classification"]

        lines.append(
            f"| {profile['playerName']} | {profile['playerType']} | "
            f"{injury_display} | {usage} | {maximum} | {position_role} |"
        )

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- Hitter injury rating represents susceptibility, not duration.",
            "- Hitter duration is derived from real-life AB+BB.",
            "- Pitcher duration is derived from real-life innings pitched.",
            "- Pitcher susceptibility is not exposed as a discrete field in "
            "the current player-set metadata.",
            "- Defensive eligibility is limited to positions verified in the "
            "defense metadata.",
            "",
        ]
    )

    return "\n".join(lines)


def main() -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    report = build_report()

    with JSON_OUTPUT_PATH.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(report, handle, indent=2)
        handle.write("\n")

    with MARKDOWN_OUTPUT_PATH.open(
        "w",
        encoding="utf-8",
        newline="\n",
    ) as handle:
        handle.write(render_markdown(report))

    print(
        json.dumps(
            {
                "jsonOutput": str(JSON_OUTPUT_PATH.relative_to(ROOT)),
                "markdownOutput": str(MARKDOWN_OUTPUT_PATH.relative_to(ROOT)),
                "summary": report["summary"],
                "rosterLegalityPass": report["rosterLegality"]["pass"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
