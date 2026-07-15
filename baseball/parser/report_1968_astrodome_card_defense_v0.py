from __future__ import annotations

import json
import re
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

CARD_DIR = (
    ROOT
    / "data"
    / "baseball"
    / "parsed"
    / "strat365"
    / "1968"
    / "cards"
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

JSON_OUTPUT_PATH = REPORT_DIR / "1968.astrodome-card-defense-v0.json"
MARKDOWN_OUTPUT_PATH = REPORT_DIR / "1968.astrodome-card-defense-v0.md"

POSITION_MAP = {
    "c": "C",
    "1b": "1B",
    "2b": "2B",
    "3b": "3B",
    "ss": "SS",
    "lf": "LF",
    "cf": "CF",
    "rf": "RF",
}

DEFENSE_SEGMENT_PATTERN = re.compile(
    r"^\s*"
    r"(?P<position>c|1b|2b|3b|ss|lf|cf|rf)"
    r"-(?P<range>[1-5])"
    r"(?:\((?P<arm>[+-]?\d+)\))?"
    r"e(?P<error>\d+)"
    r"(?:,\s*T-(?P<t_rating>\d+)"
    r"(?:\(pb-(?P<pb_rating>\d+)\))?"
    r")?"
    r"\s*$",
    re.IGNORECASE,
)


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def normalize_name(value: str | None) -> str:
    return " ".join((value or "").strip().lower().split())


def parse_defense_segment(segment: str) -> dict[str, Any]:
    match = DEFENSE_SEGMENT_PATTERN.fullmatch(segment)

    if match is None:
        raise ValueError(f"Unrecognized defense segment: {segment!r}")

    groups = match.groupdict()

    return {
        "position": POSITION_MAP[groups["position"].lower()],
        "range": int(groups["range"]),
        "arm": int(groups["arm"]) if groups["arm"] is not None else None,
        "error": int(groups["error"]),
        "tRating": (
            int(groups["t_rating"])
            if groups["t_rating"] is not None
            else None
        ),
        "passedBallRating": (
            int(groups["pb_rating"])
            if groups["pb_rating"] is not None
            else None
        ),
        "raw": segment.strip(),
    }


def parse_defense_text(defense_text: str) -> list[dict[str, Any]]:
    segments = [
        segment.strip()
        for segment in defense_text.split("/")
        if segment.strip()
    ]

    if not segments:
        raise ValueError("Defense text contains no position segments")

    return [
        parse_defense_segment(segment)
        for segment in segments
    ]


def build_report() -> dict[str, Any]:
    roster_document = load_json(ROSTER_PATH)
    metadata_document = load_json(ROSTER_METADATA_PATH)

    roster = roster_document["rankedQueue"]
    metadata_players = metadata_document["players"]

    metadata_lookup = {
        normalize_name(player["playerName"]): player
        for player in metadata_players
    }

    hitter_entries = []

    for roster_entry in roster:
        key = normalize_name(roster_entry["playerName"])
        metadata = metadata_lookup.get(key)

        if metadata is None:
            raise ValueError(
                f"Roster metadata missing for {roster_entry['playerName']}"
            )

        if metadata.get("role") == "pitcher":
            continue

        hitter_entries.append((roster_entry, metadata))

    players = []
    parse_failures = []
    primary_position_mismatches = []

    for roster_entry, metadata in hitter_entries:
        player_id = int(metadata["playerId"])
        card_path = CARD_DIR / f"{player_id}.parsed-card-evidence.json"

        if not card_path.exists():
            parse_failures.append(
                {
                    "playerId": player_id,
                    "playerName": metadata["playerName"],
                    "reason": "parsed card evidence file missing",
                    "sourcePath": str(card_path.relative_to(ROOT)),
                }
            )
            continue

        card_document = load_json(card_path)
        defense_text = (
            card_document
            .get("hitterTraits", {})
            .get("defenseText")
        )

        if not defense_text:
            parse_failures.append(
                {
                    "playerId": player_id,
                    "playerName": metadata["playerName"],
                    "reason": "hitterTraits.defenseText missing",
                    "sourcePath": str(card_path.relative_to(ROOT)),
                }
            )
            continue

        try:
            positions = parse_defense_text(defense_text)
        except ValueError as error:
            parse_failures.append(
                {
                    "playerId": player_id,
                    "playerName": metadata["playerName"],
                    "reason": str(error),
                    "sourcePath": str(card_path.relative_to(ROOT)),
                    "defenseText": defense_text,
                }
            )
            continue

        primary_position = metadata["hitter"].get("primaryPosition")
        eligible_positions = {
            position["position"]
            for position in positions
        }

        primary_position_verified = (
            primary_position in eligible_positions
        )

        if not primary_position_verified:
            primary_position_mismatches.append(
                {
                    "playerId": player_id,
                    "playerName": metadata["playerName"],
                    "primaryPosition": primary_position,
                    "eligiblePositions": sorted(eligible_positions),
                }
            )

        players.append(
            {
                "playerId": player_id,
                "playerName": metadata["playerName"],
                "rosterOperationalRole": roster_entry.get("role"),
                "browserPrimaryPosition": primary_position,
                "primaryPositionVerified": primary_position_verified,
                "cardBacked": True,
                "source": {
                    "path": str(card_path.relative_to(ROOT)),
                    "fieldPath": "$.hitterTraits.defenseText",
                },
                "defenseText": defense_text,
                "positionCount": len(positions),
                "positions": positions,
            }
        )

    players.sort(key=lambda player: player["playerName"])

    position_counts = {
        position: 0
        for position in POSITION_MAP.values()
    }

    for player in players:
        for position in player["positions"]:
            position_counts[position["position"]] += 1

    source_complete = (
        len(players) == len(hitter_entries)
        and not parse_failures
    )

    summary = {
        "expectedHitterCount": len(hitter_entries),
        "parsedHitterCount": len(players),
        "sourceComplete": source_complete,
        "positionRecordCount": sum(
            player["positionCount"]
            for player in players
        ),
        "singlePositionHitters": sum(
            player["positionCount"] == 1
            for player in players
        ),
        "multiPositionHitters": sum(
            player["positionCount"] > 1
            for player in players
        ),
        "catcherEligibleHitters": position_counts["C"],
        "positionCounts": position_counts,
        "parseFailureCount": len(parse_failures),
        "primaryPositionMismatchCount": len(
            primary_position_mismatches
        ),
    }

    report_pass = (
        summary["expectedHitterCount"] == 14
        and summary["parsedHitterCount"] == 14
        and summary["sourceComplete"]
        and summary["positionRecordCount"] == 33
        and summary["multiPositionHitters"] == 10
        and summary["parseFailureCount"] == 0
        and summary["primaryPositionMismatchCount"] == 0
    )

    return {
        "reportVersion": "v0",
        "teamContext": {
            "playerSet": "1968",
            "park": "Astrodome",
            "rosterName": "canonical_operational_roster",
        },
        "sourcePolicy": {
            "completeEligibilitySource": (
                "authenticated parsed card evidence"
            ),
            "fieldPath": "$.hitterTraits.defenseText",
            "browserMetadataUse": (
                "primary-position and roster-rule validation only"
            ),
        },
        "summary": summary,
        "players": players,
        "parseFailures": parse_failures,
        "primaryPositionMismatches": primary_position_mismatches,
        "pass": report_pass,
    }


def render_markdown(report: dict[str, Any]) -> str:
    summary = report["summary"]

    lines = [
        "# 1968 Astrodome Card Defense v0",
        "",
        "## Scope",
        "",
        "Authenticated card-backed defensive eligibility for every hitter "
        "on the canonical Astrodome roster.",
        "",
        "## Summary",
        "",
        f"- Expected hitters: {summary['expectedHitterCount']}",
        f"- Parsed hitters: {summary['parsedHitterCount']}",
        f"- Position records: {summary['positionRecordCount']}",
        f"- Single-position hitters: {summary['singlePositionHitters']}",
        f"- Multi-position hitters: {summary['multiPositionHitters']}",
        f"- Catcher-eligible hitters: {summary['catcherEligibleHitters']}",
        f"- Parse failures: {summary['parseFailureCount']}",
        (
            "- Primary-position mismatches: "
            f"{summary['primaryPositionMismatchCount']}"
        ),
        f"- Verification pass: {'yes' if report['pass'] else 'no'}",
        "",
        "## Position Coverage",
        "",
        "| Position | Eligible hitters |",
        "|---|---:|",
    ]

    for position, count in summary["positionCounts"].items():
        lines.append(f"| {position} | {count} |")

    lines.extend(
        [
            "",
            "## Player Eligibility",
            "",
            "| Player | Browser primary | Card positions | Defense |",
            "|---|---|---|---|",
        ]
    )

    for player in report["players"]:
        position_list = "/".join(
            position["position"]
            for position in player["positions"]
        )

        lines.append(
            f"| {player['playerName']} | "
            f"{player['browserPrimaryPosition']} | "
            f"{position_list} | "
            f"{player['defenseText']} |"
        )

    lines.extend(
        [
            "",
            "## Source Policy",
            "",
            "- Complete position eligibility comes from authenticated card "
            "evidence.",
            "- The canonical field is `$.hitterTraits.defenseText`.",
            "- Browser metadata remains authoritative for primary-position "
            "roster-rule checks.",
            "- No defensive eligibility is inferred from assumptions or "
            "real-life appearances.",
            "",
        ]
    )

    return "\n".join(lines)


def main() -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    report = build_report()

    with JSON_OUTPUT_PATH.open(
        "w",
        encoding="utf-8",
        newline="\n",
    ) as handle:
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
                "markdownOutput": str(
                    MARKDOWN_OUTPUT_PATH.relative_to(ROOT)
                ),
                "summary": report["summary"],
                "pass": report["pass"],
            },
            indent=2,
        )
    )

    if not report["pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()