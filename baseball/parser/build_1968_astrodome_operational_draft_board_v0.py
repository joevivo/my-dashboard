from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path
from typing import Any


BASE = Path("data/baseball/parsed/strat365/1968/draft-prep")

SCENARIO_CSV = BASE / "1968.astrodome-overlay-roster-scenarios-v0.csv"
SCENARIO_MD = BASE / "1968.astrodome-overlay-roster-scenarios-v0.md"
RANKED_BOARD_JSON = BASE / "1968.astrodome-ranked-draft-board-v0.json"
CHEAT_SHEET_JSON = BASE / "1968.astrodome-draft-room-cheat-sheet-v0.json"
ROSTER_FIXTURE_JSON = Path("data/baseball/fixtures/rosters/1968_astrodome_alou_freehan_chance_parker_v0.json")
DEFENSE_CSV = Path("data/baseball/parsed/strat365/1968/defense/1968.hitter-defense-assignments-v0.csv")
HITTER_OVERLAY_CSV = BASE / "1968.astrodome-hitter-recommendation-overlay-v0.csv"
STARTER_OVERLAY_CSV = BASE / "1968.astrodome-starter-recommendation-overlay-v0.csv"
RELIEVER_OVERLAY_CSV = BASE / "1968.astrodome-reliever-recommendation-overlay-v0.csv"

OUT_JSON = BASE / "1968.astrodome-operational-draft-board-v0.json"
OUT_MD = BASE / "1968.astrodome-operational-draft-board-v0.md"

RECOMMENDATION_WEIGHT = {
    "core_target": 1000,
    "position_priority": 950,
    "closer_target": 900,
    "core_relief_target": 850,
    "useful_value": 700,
    "roster_structure_fallback": 100,
}

ROLE_BONUS = {
    "clean_cf": 90,
    "primary_catcher": 85,
    "clean_ss": 80,
    "clean_2b": 75,
    "clean_3b": 70,
    "starter_target": 65,
    "closer_target": 60,
    "relief_target": 55,
    "salary_fit_starter": 50,
    "hitter_target": 45,
    "salary_fit_hitter": 10,
}

BUCKET_ORDER = {
    "A-list": 0,
    "A-list with review": 1,
    "B-list": 2,
    "C-list": 3,
    "Watch/Avoid": 9,
}


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Missing required input: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def read_summaries(path: Path) -> dict[str, dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(f"Missing required input: {path}")
    with path.open("r", newline="", encoding="utf-8") as handle:
        return {
            row["scenario"]: row
            for row in csv.DictReader(handle)
        }


def player_name(label: str) -> str:
    return label.split(" (", 1)[0].strip()


def parse_scenario_rosters(path: Path) -> dict[str, list[dict[str, Any]]]:
    if not path.exists():
        raise FileNotFoundError(f"Missing required input: {path}")

    lines = path.read_text(encoding="utf-8").splitlines()
    rosters: dict[str, list[dict[str, Any]]] = {}

    current_scenario: str | None = None
    in_roster_table = False

    for line in lines:
        if line.startswith("## ") and line.strip() != "## Scenario Summary":
            current_scenario = line.replace("## ", "", 1).strip()
            rosters[current_scenario] = []
            in_roster_table = False
            continue

        if current_scenario is None:
            continue

        if line.startswith(
            "| Role | Pool | Recommendation | Player | Salary | Position/Endurance | Warnings |"
        ):
            in_roster_table = True
            continue

        if in_roster_table and line.startswith("|---"):
            continue

        if in_roster_table and not line.startswith("|"):
            in_roster_table = False
            continue

        if in_roster_table and line.startswith("|"):
            parts = [part.strip() for part in line.strip("|").split("|")]
            if len(parts) != 7:
                continue

            role, pool, recommendation, label, salary, position, warnings = parts
            rosters[current_scenario].append(
                {
                    "role": role,
                    "pool": pool,
                    "recommendation": recommendation,
                    "playerLabel": label,
                    "playerName": player_name(label),
                    "salary": float(salary),
                    "positionEndurance": position,
                    "warnings": [
                        warning.strip()
                        for warning in warnings.split(";")
                        if warning.strip()
                    ],
                }
            )

    return rosters


def build_player_index(
    ranked_board: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}

    for row in ranked_board.get("hitters", []):
        index[row["playerName"]] = {
            **row,
            "recordType": "hitter",
        }

    for row in ranked_board.get("pitchers", []):
        index[row["playerName"]] = {
            **row,
            "recordType": "pitcher",
        }

    return index


def merge_overlay_player_index(
    index: dict[str, dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    overlay_sources = [
        (HITTER_OVERLAY_CSV, "hitter"),
        (STARTER_OVERLAY_CSV, "pitcher"),
        (RELIEVER_OVERLAY_CSV, "pitcher"),
    ]

    for path, record_type in overlay_sources:
        if not path.exists():
            raise FileNotFoundError(f"Missing required input: {path}")

        with path.open("r", newline="", encoding="utf-8-sig") as handle:
            for row in csv.DictReader(handle):
                name = str(row.get("playerName") or "").strip()
                if not name or name in index:
                    continue

                warnings = [
                    value.strip()
                    for value in str(row.get("warnings") or "").split(";")
                    if value.strip()
                ]

                index[name] = {
                    **row,
                    "recordType": record_type,
                    "draftBoardScore": float(row.get("astrodomeScore") or 0),
                    "riskTags": warnings,
                    "rawDefense": row.get("browserDefense"),
                    "cardBacked": True,
                }

    return index

def board_score(record: dict[str, Any] | None) -> float:
    if not record:
        return 0.0
    return float(record.get("draftBoardScore") or 0.0)


def priority_phase(row: dict[str, Any]) -> str:
    recommendation = row["recommendation"]
    role = row["role"]

    if recommendation == "core_target":
        return "Must-target anchor"

    if recommendation in {
        "position_priority",
        "closer_target",
        "core_relief_target",
    }:
        return "Early priority"

    if role in {
        "primary_catcher",
        "clean_cf",
        "clean_ss",
        "clean_2b",
        "clean_3b",
        "starter_target",
        "salary_fit_starter",
        "relief_target",
    }:
        return "Roster structure"

    return "Late salary fit"


def operational_priority(
    row: dict[str, Any],
    player_index: dict[str, dict[str, Any]],
    family_count: int,
) -> float:
    return round(
        RECOMMENDATION_WEIGHT.get(row["recommendation"], 0)
        + ROLE_BONUS.get(row["role"], 0)
        + (family_count * 50)
        + board_score(player_index.get(row["playerName"])),
        2,
    )


def enrich_row(
    row: dict[str, Any],
    player_index: dict[str, dict[str, Any]],
    memberships: list[str],
) -> dict[str, Any]:
    record = player_index.get(row["playerName"], {})

    return {
        **row,
        "familyMembership": memberships,
        "familyCount": len(memberships),
        "phase": priority_phase(row),
        "operationalPriority": operational_priority(
            row,
            player_index,
            len(memberships),
        ),
        "draftBoardScore": record.get("draftBoardScore"),
        "draftBoardRank": record.get("rank"),
        "manualBucket": record.get("manualBucket"),
        "manualRead": record.get("manualRead"),
        "rawDefense": record.get("rawDefense"),
        "cardBacked": record.get("cardBacked", True),
    }


def unique_candidates(
    rows: list[dict[str, Any]],
    excluded_names: set[str],
    limit: int,
    max_salary: float | None = None,
) -> list[dict[str, Any]]:
    seen: set[str] = set()
    candidates: list[dict[str, Any]] = []

    for row in rows:
        name = row.get("playerName")
        if not name or name in seen or name in excluded_names:
            continue
        if row.get("manualBucket") == "Watch/Avoid":
            continue
        if row.get("cardBacked") is False:
            continue

        seen.add(name)
        candidates.append(row)

    candidates.sort(
        key=lambda row: (
            0
            if max_salary is None
            or float(row.get("salary") or 0) <= max_salary
            else 1,
            BUCKET_ORDER.get(row.get("manualBucket"), 8),
            -float(row.get("draftBoardScore") or 0),
            row.get("playerName", ""),
        )
    )

    return candidates[:limit]


def contingency_entry(row: dict[str, Any]) -> dict[str, Any]:
    position = row.get("position") or row.get("browserEndurance") or ""

    return {
        "playerName": row.get("playerName"),
        "team": row.get("team"),
        "salary": row.get("salary"),
        "positionEndurance": position,
        "rawDefense": row.get("rawDefense"),
        "draftBoardScore": row.get("draftBoardScore"),
        "manualBucket": row.get("manualBucket"),
        "manualRead": row.get("manualRead"),
        "riskTags": row.get("riskTags") or [],
    }


def markdown_table(
    headers: list[str],
    rows: list[list[Any]],
    alignments: list[str] | None = None,
) -> list[str]:
    if alignments is None:
        alignments = ["---"] * len(headers)

    lines = [
        "| " + " | ".join(headers) + " |",
        "|" + "|".join(alignments) + "|",
    ]

    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                str(value) if value is not None else ""
                for value in row
            )
            + " |"
        )

    return lines


def render_priority_rows(rows: list[dict[str, Any]]) -> list[list[Any]]:
    rendered: list[list[Any]] = []

    for index, row in enumerate(rows, start=1):
        rendered.append(
            [
                index,
                row["playerLabel"],
                row["phase"],
                row["role"],
                row["recommendation"],
                f"{row['salary']:.2f}",
                row["positionEndurance"],
                row.get("draftBoardRank") or "",
                row.get("draftBoardScore") or "",
                "; ".join(row["warnings"]),
            ]
        )

    return rendered


def render_contingencies(rows: list[dict[str, Any]]) -> list[list[Any]]:
    rendered: list[list[Any]] = []

    for index, row in enumerate(rows, start=1):
        rendered.append(
            [
                index,
                row.get("playerName"),
                row.get("team"),
                row.get("positionEndurance"),
                f"{float(row.get('salary') or 0):.2f}",
                row.get("rawDefense") or "",
                row.get("manualBucket") or "",
                row.get("draftBoardScore") or "",
                row.get("manualRead") or "",
            ]
        )

    return rendered


PHASE_ORDER = [
    "Must-target anchor",
    "Early foundation",
    "Pitching structure",
    "Bullpen structure",
    "Value depth",
    "Late salary fit",
]

ANCHOR_PLAYERS = {
    "Freehan, Bill",
    "Alou, Felipe",
    "Chance, Dean",
}

EARLY_FOUNDATION_PLAYERS = {
    "Fregosi, Jim",
    "Santo, Ron",
    "McAuliffe, Dick",
    "Parker, Wes",
    "Niekro, Phil",
}

PITCHING_STRUCTURE_PLAYERS = {
    "Washburn, Ray",
    "Singer, Bill",
    "Moose, Bob",
}

BULLPEN_STRUCTURE_PLAYERS = {
    "Hoerner, Joe",
    "McDaniel, Lindy",
    "Wilhelm, Hoyt",
    "Hamilton, Steve",
}


def normalize_text_list(value: Any) -> list[str]:
    if value is None:
        return []

    if isinstance(value, list):
        return [
            str(item).strip()
            for item in value
            if str(item).strip()
        ]

    text = str(value).strip()
    if not text:
        return []

    return [
        item.strip()
        for item in text.replace(",", ";").split(";")
        if item.strip()
    ]


def fixture_position_endurance(player: dict[str, Any]) -> str:
    if player.get("type") == "hitter":
        return str(player.get("primaryPosition") or "")

    parts: list[str] = []

    starter = player.get("starterEndurance")
    relief = player.get("reliefEndurance")
    closer = player.get("closerEndurance")

    if starter:
        parts.append(str(starter))
    if relief:
        parts.append(str(relief))
    if closer:
        parts.append(str(closer))

    return "/".join(parts)


def phase_for_player(name: str) -> str:
    if name in ANCHOR_PLAYERS:
        return "Must-target anchor"

    if name in EARLY_FOUNDATION_PLAYERS:
        return "Early foundation"

    if name in PITCHING_STRUCTURE_PLAYERS:
        return "Pitching structure"

    if name in BULLPEN_STRUCTURE_PLAYERS:
        return "Bullpen structure"

    if name in {
        "Gosger, Jim",
        "Brinkman, Ed",
        "Torres, Hector",
    }:
        return "Late salary fit"

    return "Value depth"


def role_for_player(player: dict[str, Any]) -> str:
    if player.get("type") == "hitter":
        position = player.get("primaryPosition")

        if position == "C":
            return "primary_catcher"
        if position == "1B":
            return "everyday_first_base"
        if position == "CF":
            return "clean_cf"
        if position in {"2B", "3B", "SS"}:
            return "starting_infield"

        return "hitter_depth"

    starter = player.get("starterEndurance")
    relief = player.get("reliefEndurance")

    if starter and relief:
        return "starter_with_relief"
    if starter:
        return "starter"
    if relief:
        return "pure_reliever"

    return "pitcher_depth"


def recommendation_for_phase(phase: str) -> str:
    return {
        "Must-target anchor": "core_target",
        "Early foundation": "position_priority",
        "Pitching structure": "roster_structure",
        "Bullpen structure": "core_relief_target",
        "Value depth": "useful_value",
        "Late salary fit": "roster_structure_fallback",
    }[phase]


def fixture_row(
    player: dict[str, Any],
    record: dict[str, Any],
) -> dict[str, Any]:
    name = str(player["name"])
    salary_value = float(player.get("salaryMillions") or 0)
    phase = phase_for_player(name)
    team = str(record.get("team") or "").strip()

    if team:
        label = f"{name} ({team}, ${salary_value:.2f})"
    else:
        label = f"{name} (${salary_value:.2f})"

    warnings = normalize_text_list(record.get("riskTags"))

    return {
        "role": role_for_player(player),
        "pool": str(player.get("type") or ""),
        "recommendation": recommendation_for_phase(phase),
        "playerLabel": label,
        "playerName": name,
        "salary": salary_value,
        "positionEndurance": fixture_position_endurance(player),
        "warnings": warnings,
        "phase": phase,
        "operationalPriority": round(
            ((len(PHASE_ORDER) - PHASE_ORDER.index(phase)) * 1000)
            + board_score(record),
            2,
        ),
        "draftBoardScore": record.get("draftBoardScore"),
        "draftBoardRank": record.get("rank"),
        "manualBucket": record.get("manualBucket"),
        "manualRead": record.get("manualRead"),
        "rawDefense": record.get("rawDefense"),
        "cardBacked": record.get("cardBacked", True),
        "team": record.get("team"),
    }


def read_position_coverage(
    path: Path,
    roster_players: list[dict[str, Any]],
) -> tuple[dict[str, list[str]], list[str]]:
    names = {
        str(player["name"])
        for player in roster_players
        if player.get("type") == "hitter"
    }

    coverage: dict[str, set[str]] = {
        name: set()
        for name in names
    }

    if path.exists():
        with path.open("r", newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                name = row.get("playerName")
                position = row.get("position")

                if name in coverage and position:
                    coverage[name].add(position)

    for player in roster_players:
        if player.get("type") != "hitter":
            continue

        name = str(player["name"])
        primary = str(player.get("primaryPosition") or "")

        if primary:
            coverage[name].add(primary)

    rendered = {
        name: sorted(positions)
        for name, positions in sorted(coverage.items())
    }

    all_positions = sorted({
        position
        for positions in coverage.values()
        for position in positions
    })

    return rendered, all_positions


def first_base_candidates(
    path: Path,
    player_index: dict[str, dict[str, Any]],
    excluded_names: set[str],
    limit: int,
    max_salary: float | None = None,
) -> list[dict[str, Any]]:
    assignments: dict[str, str] = {}

    if path.exists():
        with path.open("r", newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                if row.get("position") != "1B":
                    continue

                name = row.get("playerName")
                assignment = row.get("rawAssignment") or ""

                if name and name not in assignments:
                    assignments[name] = assignment

    rows: list[dict[str, Any]] = []

    for name, assignment in assignments.items():
        record = player_index.get(name)

        if not record:
            continue

        rows.append({
            **record,
            "position": "1B",
            "rawDefense": assignment,
        })

    return [
        contingency_entry(row)
        for row in unique_candidates(
            rows,
            excluded_names,
            limit,
            max_salary,
        )
    ]


def main() -> None:
    fixture = load_json(ROSTER_FIXTURE_JSON)
    ranked_board = load_json(RANKED_BOARD_JSON)
    cheat_sheet = load_json(CHEAT_SHEET_JSON)
    player_index = merge_overlay_player_index(
        build_player_index(ranked_board)
    )

    fixture_players = fixture.get("players", [])
    missing_players: list[str] = []
    unbacked_players: list[str] = []
    roster_rows: list[dict[str, Any]] = []

    for player in fixture_players:
        name = str(player.get("name") or "")
        record = player_index.get(name)

        if not record:
            missing_players.append(name)
            continue

        if record.get("cardBacked") is False:
            unbacked_players.append(name)
            continue

        roster_rows.append(
            fixture_row(
                player,
                record,
            )
        )

    if missing_players:
        raise RuntimeError(
            "Players missing from ranked board: "
            + ", ".join(sorted(missing_players))
        )

    if unbacked_players:
        raise RuntimeError(
            "Players lacking card-backed evidence: "
            + ", ".join(sorted(unbacked_players))
        )

    phase_index = {
        phase: index
        for index, phase in enumerate(PHASE_ORDER)
    }

    roster_rows.sort(
        key=lambda row: (
            phase_index[row["phase"]],
            -float(row.get("draftBoardScore") or 0),
            row["playerName"],
        )
    )

    hitters = [
        player
        for player in fixture_players
        if player.get("type") == "hitter"
    ]

    pitchers = [
        player
        for player in fixture_players
        if player.get("type") == "pitcher"
    ]

    primary_catchers = sum(
        1
        for player in hitters
        if player.get("primaryPosition") == "C"
    )

    starter_endurance = sum(
        1
        for player in pitchers
        if player.get("starterEndurance")
    )

    pure_relievers = sum(
        1
        for player in pitchers
        if player.get("reliefEndurance")
        and not player.get("starterEndurance")
    )

    closer_endurance = sum(
        1
        for player in pitchers
        if player.get("closerEndurance")
    )

    salary_total = round(
        sum(
            float(player.get("salaryMillions") or 0)
            for player in fixture_players
        ),
        2,
    )

    cap_room = round(80.0 - salary_total, 2)

    salary_by_name = {
        str(player["name"]): float(player.get("salaryMillions") or 0)
        for player in fixture_players
    }

    direct_replacement_limits = {
        "centerField": round(
            salary_by_name["Alou, Felipe"] + cap_room,
            2,
        ),
        "firstBase": round(
            salary_by_name["Parker, Wes"] + cap_room,
            2,
        ),
        "catcher": round(
            salary_by_name["Freehan, Bill"] + cap_room,
            2,
        ),
        "shortstop": round(
            salary_by_name["Fregosi, Jim"] + cap_room,
            2,
        ),
        "starters": round(
            salary_by_name["Chance, Dean"] + cap_room,
            2,
        ),
        "pureRelievers": round(
            salary_by_name["McDaniel, Lindy"] + cap_room,
            2,
        ),
    }
    coverage_by_player, covered_positions = read_position_coverage(
        DEFENSE_CSV,
        fixture_players,
    )

    required_positions = {
        "C",
        "1B",
        "2B",
        "3B",
        "SS",
        "LF",
        "CF",
        "RF",
    }

    missing_positions = sorted(
        required_positions - set(covered_positions)
    )

    legal_checks = {
        "total_players_25_to_28": 25 <= len(fixture_players) <= 28,
        "salary_cap_80m": salary_total <= 80.0,
        "hitters_13_to_17": 13 <= len(hitters) <= 17,
        "pitchers_11_to_14": 11 <= len(pitchers) <= 14,
        "primary_catchers_2_plus": primary_catchers >= 2,
        "starter_endurance_5_plus": starter_endurance >= 5,
        "pure_relievers_4_plus": pure_relievers >= 4,
        "closer_endurance_1_plus": closer_endurance >= 1,
        "starting_position_coverage_complete": not missing_positions,
    }

    legal = all(legal_checks.values())
    roster_names = {
        row["playerName"]
        for row in roster_rows
    }

    clean_cf = [
        contingency_entry(row)
        for row in unique_candidates(
            cheat_sheet.get("cleanCfPaths", []),
            roster_names,
            6,
            direct_replacement_limits["centerField"],
        )
    ]

    first_base = first_base_candidates(
        DEFENSE_CSV,
        player_index,
        roster_names,
        6,
        direct_replacement_limits["firstBase"],
    )

    catchers = [
        contingency_entry(row)
        for row in unique_candidates(
            cheat_sheet.get("catcherPlans", []),
            roster_names,
            5,
            direct_replacement_limits["catcher"],
        )
    ]

    shortstops = [
        contingency_entry(row)
        for row in unique_candidates(
            cheat_sheet.get("ssPlans", []),
            roster_names,
            6,
            direct_replacement_limits["shortstop"],
        )
    ]

    pitcher_pool = (
        cheat_sheet.get("pitcherAList", [])
        + cheat_sheet.get("pitcherReviewList", [])
        + cheat_sheet.get("pitcherValue", [])
    )

    starter_pool = [
        row
        for row in pitcher_pool
        if row.get("starterEndurance") is not None
    ]

    pure_reliever_pool = [
        row
        for row in pitcher_pool
        if row.get("reliefEndurance") is not None
        and row.get("starterEndurance") is None
    ]

    starter_contingencies = [
        contingency_entry(row)
        for row in unique_candidates(
            starter_pool,
            roster_names,
            8,
            direct_replacement_limits["starters"],
        )
    ]

    bullpen_contingencies = [
        contingency_entry(row)
        for row in unique_candidates(
            pure_reliever_pool,
            roster_names,
            8,
            direct_replacement_limits["pureRelievers"],
        )
    ]

    anchors = [
        row["playerName"]
        for row in roster_rows
        if row["phase"] == "Must-target anchor"
    ]

    report = {
        "schemaVersion": "1968.astrodome-operational-draft-board-v0",
        "season": 1968,
        "park": fixture.get("park") or "Astrodome 1968",
        "leagueFormat": fixture.get("leagueFormat") or "DH",
        "canonicalFixture": fixture.get("fixtureId"),
        "identity": {
            "planLabel": "Alou-Freehan-Chance-Parker",
            "anchors": anchors,
            "decisionRule": (
                "Draft from the validated Alou-Freehan-Chance-Parker roster. "
                "Use the contingency boards only when a target is unavailable, "
                "then recheck salary and roster structure."
            ),
            "doNotMixRule": (
                "No contingency is an automatic one-for-one replacement. "
                "Confirm cap, defensive coverage, and pitching minimums "
                "before final submission."
            ),
        },
        "summary": {
            "legal": legal,
            "salary": salary_total,
            "capRoom": cap_room,
            "directReplacementSalaryLimits": direct_replacement_limits,
            "players": len(fixture_players),
            "hitters": len(hitters),
            "pitchers": len(pitchers),
            "primaryCatchers": primary_catchers,
            "starterEndurancePitchers": starter_endurance,
            "pureRelievers": pure_relievers,
            "closerEndurancePitchers": closer_endurance,
            "coveredPositions": covered_positions,
            "missingPositions": missing_positions,
            "legalChecks": legal_checks,
        },
        "rankedQueue": roster_rows,
        "positionCoverage": {
            "byPlayer": coverage_by_player,
            "positions": covered_positions,
            "missing": missing_positions,
        },
        "contingencies": {
            "centerField": clean_cf,
            "firstBase": first_base,
            "catcher": catchers,
            "shortstop": shortstops,
            "starters": starter_contingencies,
            "pureRelievers": bullpen_contingencies,
        },
        "liveDraftRules": [
            "The validated roster fixture is the canonical draft plan.",
            "Freehan, Alou, and Chance are the primary anchors.",
            "Keep Wes Parker at first base so Freehan remains the primary catcher.",
            "Do not chase home-run-only salary in the Astrodome.",
            "Protect five starter-endurance pitchers, four pure relievers, and at least one closer-endurance pitcher.",
            "Use minimum-salary, low-OB hitters only as late structural pieces.",
            "This plan assumes a DH league. Pitcher batting evaluation remains a non-DH backlog item.",
            "After any contingency substitution, recheck salary, defensive coverage, and roster legality.",
        ],
    }

    OUT_JSON.write_text(
        json.dumps(report, indent=2) + "\n",
        encoding="utf-8",
    )

    lines: list[str] = [
        "# 1968 Astrodome Operational Draft Board v0",
        "",
        "Purpose: provide the live, human-led draft queue for the validated 1968 Astrodome roster.",
        "",
        "This is not an autonomous drafter. Every recommendation remains subject to live availability, salary fit, and human review.",
        "",
        "## Canonical Draft Plan",
        "",
        f"- Plan: **{report['identity']['planLabel']}**",
        f"- Fixture: `{report['canonicalFixture']}`",
        f"- League format: **{report['leagueFormat']}**",
        f"- Park: **{report['park']}**",
        f"- Salary: **${salary_total:.2f}M**",
        f"- Cap room: **${report['summary']['capRoom']:.2f}M**",
        f"- Legal and structurally complete: **{'yes' if legal else 'no'}**",
        f"- Anchors: **{', '.join(anchors)}**",
        f"- Decision rule: {report['identity']['decisionRule']}",
        f"- Substitution discipline: {report['identity']['doNotMixRule']}",
        "",
        "## Roster Structure",
        "",
        "| Measure | Count |",
        "|---|---:|",
        f"| Players | {len(fixture_players)} |",
        f"| Hitters | {len(hitters)} |",
        f"| Pitchers | {len(pitchers)} |",
        f"| Primary catchers | {primary_catchers} |",
        f"| Starter-endurance pitchers | {starter_endurance} |",
        f"| Pure relievers | {pure_relievers} |",
        f"| Closer-endurance pitchers | {closer_endurance} |",
        "",
        "## Operational Queue",
        "",
    ]

    lines.extend(
        markdown_table(
            [
                "Priority",
                "Player",
                "Phase",
                "Role",
                "Recommendation",
                "Salary",
                "Position/Endurance",
                "Board Rank",
                "Board Score",
                "Warnings",
            ],
            render_priority_rows(roster_rows),
            [
                "---:",
                "---",
                "---",
                "---",
                "---",
                "---:",
                "---",
                "---:",
                "---:",
                "---",
            ],
        )
    )

    lines.extend(
        [
            "",
            "## Position Coverage",
            "",
            f"- Covered positions: **{', '.join(covered_positions)}**",
            f"- Missing required positions: **{', '.join(missing_positions) if missing_positions else 'none'}**",
            "",
        ]
    )

    contingency_sections = [
        ("Center Field", clean_cf),
        ("First Base", first_base),
        ("Catcher", catchers),
        ("Shortstop", shortstops),
        ("Starter", starter_contingencies),
        ("Pure Reliever", bullpen_contingencies),
    ]

    lines.extend(
        [
            "## Card-Backed Contingency Boards",
            "",
            "These are alternatives, not automatic one-for-one substitutions. Recheck cap and roster shape before final submission.",
            "",
        ]
    )

    for title, rows in contingency_sections:
        lines.extend(
            [
                f"### {title}",
                "",
            ]
        )

        lines.extend(
            markdown_table(
                [
                    "Priority",
                    "Player",
                    "Team",
                    "Position/Endurance",
                    "Salary",
                    "Defense",
                    "Bucket",
                    "Board Score",
                    "Read",
                ],
                render_contingencies(rows),
                [
                    "---:",
                    "---",
                    "---",
                    "---",
                    "---:",
                    "---",
                    "---",
                    "---:",
                    "---",
                ],
            )
        )

        lines.append("")

    lines.extend(
        [
            "## Live Draft Rules",
            "",
        ]
    )

    for index, rule in enumerate(report["liveDraftRules"], start=1):
        lines.append(f"{index}. {rule}")

    lines.extend(
        [
            "",
            "## Final Submission Gate",
            "",
            "- Confirm total salary is no more than $80M.",
            "- Confirm 25-28 total players.",
            "- Confirm 13-17 hitters and 11-14 pitchers.",
            "- Confirm at least 2 primary catchers.",
            "- Confirm at least 5 starter-endurance pitchers.",
            "- Confirm at least 4 pure relievers.",
            "- Confirm at least 1 closer-endurance pitcher.",
            "- Confirm actual defensive coverage for every starting position.",
            "- Revalidate after every contingency substitution.",
            "",
        ]
    )

    OUT_MD.write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )

    print("# RESULT SUMMARY")
    print(f"OUT_JSON: {OUT_JSON}")
    print(f"OUT_MD: {OUT_MD}")
    print(f"FIXTURE: {fixture.get('fixtureId')}")
    print(f"LEGAL: {'yes' if legal else 'no'}")
    print(f"SALARY: {salary_total:.2f}")
    print(f"CAP_ROOM: {80.0 - salary_total:.2f}")
    print(f"PLAYERS: {len(fixture_players)}")
    print(f"ANCHORS: {', '.join(anchors)}")
    print(f"MISSING_POSITIONS: {', '.join(missing_positions) if missing_positions else 'none'}")
    print(f"CF_CONTINGENCIES: {len(clean_cf)}")
    print(f"FIRST_BASE_CONTINGENCIES: {len(first_base)}")
    print(f"CATCHER_CONTINGENCIES: {len(catchers)}")
    print(f"SS_CONTINGENCIES: {len(shortstops)}")
    print(f"STARTER_CONTINGENCIES: {len(starter_contingencies)}")
    print(f"PURE_RP_CONTINGENCIES: {len(bullpen_contingencies)}")


if __name__ == "__main__":
    main()
