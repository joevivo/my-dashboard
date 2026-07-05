from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
SEASON = "1968"
SALARY_CAP = 80.0

BASE = ROOT / "data" / "baseball" / "parsed" / "strat365" / SEASON
DRAFT_BOARD_PATH = BASE / "draft-boards" / "1968.hybrid-card-backed-draft-board.csv"
ROSTER_METADATA_PATH = BASE / "player-roster-metadata" / "1968.player-roster-metadata.json"
CARDS_DIR = BASE / "cards"
OUTPUT_DIR = BASE / "draft-boards"

JSON_OUT = OUTPUT_DIR / "1968.salary-aware-roster-template-v0.json"
MD_OUT = OUTPUT_DIR / "1968.salary-aware-roster-template-v0.md"


def fnum(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


def load_board() -> list[dict[str, Any]]:
    with DRAFT_BOARD_PATH.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def load_roster_players() -> list[dict[str, Any]]:
    data = json.loads(ROSTER_METADATA_PATH.read_text(encoding="utf-8-sig"))
    players = data.get("players", [])
    if isinstance(players, dict):
        return list(players.values())
    return players


def roster_endurance(player: dict[str, Any] | None) -> str:
    if not player:
        return ""
    return ((player.get("pitcher") or {}).get("endurance") or "").strip()


def primary_position(player: dict[str, Any] | None) -> str:
    if not player:
        return ""
    return ((player.get("hitter") or {}).get("primaryPosition") or "").strip()


def parse_starter_endurance(endurance: str) -> str | None:
    match = re.search(r"\bS(\d+)\*?", endurance or "")
    return f"S{match.group(1)}" if match else None


def parse_roster_relief_endurance(endurance: str) -> str | None:
    match = re.search(r"\bR(\d+)\b", endurance or "")
    return f"R{match.group(1)}" if match else None


def parse_card_relief_text(player_id: str) -> tuple[str | None, str | None, str | None]:
    path = CARDS_DIR / f"{player_id}.parsed-card-evidence.json"
    if not path.exists():
        return None, None, None

    data = json.loads(path.read_text(encoding="utf-8-sig"))
    traits = data.get("pitcherTraits") or {}
    relief_text = traits.get("reliefText")

    if not relief_text:
        raw = json.dumps(data, ensure_ascii=False)
        match = re.search(r"relief\((\d+)\)(?:/(\d+))?", raw, flags=re.I)
        relief_text = match.group(0) if match else None

    if not relief_text:
        return None, None, None

    match = re.search(r"relief\((\d+)\)(?:/(\d+))?", relief_text, flags=re.I)
    if not match:
        return relief_text, None, None

    relief = f"R{match.group(1)}"
    closer = None
    if match.group(2) is not None:
        closer_number = int(match.group(2))
        if closer_number > 0:
            closer = f"C{closer_number}"

    return relief_text, relief, closer


def enrich_row(row: dict[str, Any], roster_by_id: dict[str, dict[str, Any]]) -> dict[str, Any]:
    player_id = str(row.get("playerId", "")).strip()
    roster = roster_by_id.get(player_id)

    end = roster_endurance(roster)
    card_relief_text, card_relief, card_closer = parse_card_relief_text(player_id)

    starter = parse_starter_endurance(end)
    roster_relief = parse_roster_relief_endurance(end)
    relief = card_relief or roster_relief
    primary = primary_position(roster)

    role = row.get("role", "")
    salary = fnum(row.get("salaryMillions"))
    score = fnum(row.get("hybridDraftScore"))
    value = fnum(row.get("hybridValueScore"))

    return {
        **row,
        "playerId": player_id,
        "salaryMillions": salary,
        "hybridDraftScore": score,
        "hybridValueScore": value,
        "primaryPosition": primary,
        "rosterEndurance": end,
        "starterEndurance": starter,
        "reliefEndurance": relief,
        "closerEndurance": card_closer,
        "cardReliefText": card_relief_text,
        "isHitter": role == "hitter",
        "isPitcher": role == "pitcher",
        "isPrimaryCatcher": role == "hitter" and primary == "C",
        "isStarterEndurancePitcher": role == "pitcher" and starter is not None,
        "isPureReliever": role == "pitcher" and relief is not None and starter is None,
        "isCloserEndurancePitcher": role == "pitcher" and card_closer is not None,
        "isCardBacked": row.get("confidenceTier") == "card-backed",
    }


def draft_score(row: dict[str, Any]) -> float:
    # v0 balance: reward production, card-backed confidence, value, and affordability.
    score = float(row["hybridDraftScore"])
    value = min(float(row["hybridValueScore"]), 80.0)
    salary = float(row["salaryMillions"])
    card_bonus = 5.0 if row.get("isCardBacked") else 0.0
    return score + value * 0.22 + card_bonus - salary * 1.35


def role_text(row: dict[str, Any]) -> str:
    parts = [
        row.get("primaryPosition"),
        row.get("starterEndurance"),
        row.get("reliefEndurance"),
        row.get("closerEndurance"),
    ]
    return "/".join(str(part) for part in parts if part)


def compact(row: dict[str, Any], reason: str) -> dict[str, Any]:
    return {
        "playerId": row.get("playerId"),
        "playerName": row.get("playerName"),
        "team": row.get("team"),
        "role": row.get("role"),
        "templateReason": reason,
        "primaryPosition": row.get("primaryPosition"),
        "rosterEndurance": row.get("rosterEndurance"),
        "starterEndurance": row.get("starterEndurance"),
        "reliefEndurance": row.get("reliefEndurance"),
        "closerEndurance": row.get("closerEndurance"),
        "cardReliefText": row.get("cardReliefText"),
        "salaryMillions": row.get("salaryMillions"),
        "hybridDraftScore": row.get("hybridDraftScore"),
        "hybridValueScore": row.get("hybridValueScore"),
        "confidenceTier": row.get("confidenceTier"),
    }


def select_one(
    pool: list[dict[str, Any]],
    selected_ids: set[str],
    remaining_salary: float,
    remaining_slots_after_pick: int,
) -> dict[str, Any]:
    max_salary = remaining_salary - (remaining_slots_after_pick * 0.50)
    candidates = [
        row for row in pool
        if row["playerId"] not in selected_ids
        and row["salaryMillions"] <= max_salary + 0.0001
    ]

    if not candidates:
        raise RuntimeError(
            f"No candidate available within salary guard. "
            f"remainingSalary={remaining_salary:.2f}, remainingSlotsAfterPick={remaining_slots_after_pick}"
        )

    return sorted(
        candidates,
        key=lambda row: (-draft_score(row), -row["hybridDraftScore"], row["salaryMillions"], str(row.get("playerName"))),
    )[0]


def add_pick(
    roster: list[dict[str, Any]],
    selected_ids: set[str],
    pool: list[dict[str, Any]],
    reason: str,
    salary_cap: float,
    total_slots: int = 25,
) -> None:
    used_salary = sum(row["salaryMillions"] for row in roster)
    remaining_salary = salary_cap - used_salary
    remaining_slots_after_pick = total_slots - len(roster) - 1

    row = select_one(pool, selected_ids, remaining_salary, remaining_slots_after_pick)
    row["_templateReason"] = reason

    roster.append(row)
    selected_ids.add(row["playerId"])


def count_roster(roster: list[dict[str, Any]], predicate) -> int:
    return sum(1 for row in roster if predicate(row))


def build_template(rows: list[dict[str, Any]], salary_cap: float) -> dict[str, Any]:
    roster: list[dict[str, Any]] = []
    selected_ids: set[str] = set()

    hitters = [r for r in rows if r["isHitter"]]
    pitchers = [r for r in rows if r["isPitcher"]]
    catchers = [r for r in rows if r["isPrimaryCatcher"]]
    starter_pitchers = [r for r in rows if r["isStarterEndurancePitcher"]]
    pure_relievers = [r for r in rows if r["isPureReliever"]]
    pure_closers = [r for r in rows if r["isPureReliever"] and r["isCloserEndurancePitcher"]]
    closers = [r for r in rows if r["isCloserEndurancePitcher"]]

    # Pitching legality spine.
    for _ in range(5):
        add_pick(roster, selected_ids, starter_pitchers, "starter-endurance pitcher", salary_cap)

    add_pick(roster, selected_ids, pure_closers or closers, "closer-qualified pure reliever", salary_cap)

    while count_roster(roster, lambda r: r["isPureReliever"]) < 4:
        add_pick(roster, selected_ids, pure_relievers, "pure reliever", salary_cap)

    while count_roster(roster, lambda r: r["isPitcher"]) < 11:
        add_pick(roster, selected_ids, pitchers, "pitcher depth", salary_cap)

    # Hitter legality and positional spine.
    for _ in range(2):
        add_pick(roster, selected_ids, catchers, "primary catcher", salary_cap)

    for position in ["1B", "2B", "3B", "SS", "LF", "CF", "RF"]:
        if count_roster(roster, lambda r, p=position: r.get("primaryPosition") == p) == 0:
            pool = [r for r in hitters if r.get("primaryPosition") == position]
            add_pick(roster, selected_ids, pool, f"primary position coverage: {position}", salary_cap)

    # Hitter depth should not collapse into one cheap position bucket.
    # v0 guardrail: prefer positions with fewer than 2 rostered hitters, then allow best remaining hitter.
    while count_roster(roster, lambda r: r["isHitter"]) < 14:
        hitter_depth_pool = [
            row for row in hitters
            if count_roster(roster, lambda r, p=row.get("primaryPosition"): r.get("primaryPosition") == p) < 2
        ]
        if not hitter_depth_pool:
            hitter_depth_pool = hitters

        add_pick(roster, selected_ids, hitter_depth_pool, "hitter depth", salary_cap)

    if len(roster) != 25:
        raise RuntimeError(f"Expected 25 roster spots, found {len(roster)}")

    selected = [compact(row, row["_templateReason"]) for row in roster]

    counts = {
        "players": len(roster),
        "hitters": count_roster(roster, lambda r: r["isHitter"]),
        "pitchers": count_roster(roster, lambda r: r["isPitcher"]),
        "primaryCatchers": count_roster(roster, lambda r: r["isPrimaryCatcher"]),
        "starterEndurancePitchers": count_roster(roster, lambda r: r["isStarterEndurancePitcher"]),
        "pureRelievers": count_roster(roster, lambda r: r["isPureReliever"]),
        "closerEndurancePitchers": count_roster(roster, lambda r: r["isCloserEndurancePitcher"]),
        "cardBackedPlayers": count_roster(roster, lambda r: r["isCardBacked"]),
    }

    total_salary = round(sum(row["salaryMillions"] for row in roster), 2)

    legality = [
        ("players", counts["players"] == 25),
        ("hitters>=13", counts["hitters"] >= 13),
        ("pitchers>=11", counts["pitchers"] >= 11),
        ("primaryCatchers>=2", counts["primaryCatchers"] >= 2),
        ("starterEndurancePitchers>=5", counts["starterEndurancePitchers"] >= 5),
        ("pureRelievers>=4", counts["pureRelievers"] >= 4),
        ("closerEndurancePitchers>=1", counts["closerEndurancePitchers"] >= 1),
        ("salaryCap", total_salary <= salary_cap),
    ]

    return {
        "templateId": "1968.salary-aware-roster-template-v0.default-80m",
        "salaryCapMillions": salary_cap,
        "salaryUsedMillions": total_salary,
        "salaryRemainingMillions": round(salary_cap - total_salary, 2),
        "counts": counts,
        "legality": [
            {"check": name, "status": "PASS" if passed else "FAIL"}
            for name, passed in legality
        ],
        "players": selected,
        "limitations": [
            "Greedy v0 selection, not exhaustive optimization.",
            "Does not model live draft availability.",
            "Does not yet optimize for a chosen ballpark.",
            "Does not model platoons or defensive substitutions.",
            "Uses salary guard and role constraints, not a complete Strat365 team-quality model.",
        ],
    }


def build_markdown(payload: dict[str, Any]) -> str:
    template = payload["template"]

    lines: list[str] = [
        "# 1968 Salary-Aware Roster Template v0",
        "",
        "Purpose: generate a first legal 25-player candidate roster from the role-balanced draft pools.",
        "",
        "This is a draft-assist template, not a final team recommendation.",
        "",
        "## Summary",
        "",
        f"- Salary cap: {template['salaryCapMillions']:.2f}M",
        f"- Salary used: {template['salaryUsedMillions']:.2f}M",
        f"- Salary remaining: {template['salaryRemainingMillions']:.2f}M",
        "",
        "## Counts",
        "",
        "| Metric | Count |",
        "|---|---:|",
    ]

    for key, value in template["counts"].items():
        lines.append(f"| {key} | {value} |")

    lines.extend([
        "",
        "## Legality",
        "",
        "| Check | Status |",
        "|---|---|",
    ])

    for item in template["legality"]:
        lines.append(f"| {item['check']} | {item['status']} |")

    lines.extend([
        "",
        "## Candidate Roster",
        "",
        "| # | Player | Team | Role | Reason | Salary | Score | Value | Tier |",
        "|---:|---|---|---|---|---:|---:|---:|---|",
    ])

    for index, row in enumerate(template["players"], 1):
        lines.append(
            f"| {index} | {row['playerName']} | {row['team']} | {role_text(row)} | "
            f"{row['templateReason']} | {row['salaryMillions']:.2f} | "
            f"{row['hybridDraftScore']:.2f} | {row['hybridValueScore']:.2f} | {row['confidenceTier']} |"
        )

    lines.extend([
        "",
        "## Limitations",
        "",
    ])

    for item in template["limitations"]:
        lines.append(f"- {item}")

    return "\n".join(lines) + "\n"


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    board = load_board()
    roster_players = load_roster_players()
    roster_by_id = {str(player.get("playerId")): player for player in roster_players}
    rows = [enrich_row(row, roster_by_id) for row in board]

    template = build_template(rows, SALARY_CAP)

    payload = {
        "schemaVersion": "bie.salary-aware-roster-template.v0",
        "season": int(SEASON),
        "inputs": {
            "draftBoard": str(DRAFT_BOARD_PATH.relative_to(ROOT)).replace("\\", "/"),
            "rosterMetadata": str(ROSTER_METADATA_PATH.relative_to(ROOT)).replace("\\", "/"),
            "cardEvidenceDir": str(CARDS_DIR.relative_to(ROOT)).replace("\\", "/"),
        },
        "template": template,
    }

    JSON_OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    MD_OUT.write_text(build_markdown(payload), encoding="utf-8")

    print("# SALARY-AWARE TEMPLATE SUMMARY")
    print(f"salaryCapMillions: {template['salaryCapMillions']:.2f}")
    print(f"salaryUsedMillions: {template['salaryUsedMillions']:.2f}")
    print(f"salaryRemainingMillions: {template['salaryRemainingMillions']:.2f}")
    for key, value in template["counts"].items():
        print(f"{key}: {value}")

    print("\n# LEGALITY")
    for item in template["legality"]:
        print(f"{item['status']}: {item['check']}")

    print("\n# CANDIDATE ROSTER")
    for index, row in enumerate(template["players"], 1):
        print(
            f"{index:02d}. {row['playerName']} | {row['team']} | role={role_text(row)} | "
            f"reason={row['templateReason']} | salary={row['salaryMillions']:.2f} | "
            f"score={row['hybridDraftScore']:.2f} | value={row['hybridValueScore']:.2f} | "
            f"tier={row['confidenceTier']}"
        )

    print("\n# OUTPUT FILES")
    print(JSON_OUT.relative_to(ROOT))
    print(MD_OUT.relative_to(ROOT))

    print("\n# RESULT SUMMARY")
    print("Created 1968 salary-aware roster template v0.")
    print("Paste back:")
    print("1. # SALARY-AWARE TEMPLATE SUMMARY")
    print("2. # LEGALITY")
    print("3. # CANDIDATE ROSTER")
    print("4. # OUTPUT FILES")
    print("5. # BASEBALL GIT STATUS")
    print("6. # RESULT SUMMARY")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
