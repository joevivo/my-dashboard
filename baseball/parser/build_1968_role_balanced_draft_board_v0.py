from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
SEASON = "1968"

BASE = ROOT / "data" / "baseball" / "parsed" / "strat365" / SEASON
DRAFT_BOARD_PATH = BASE / "draft-boards" / "1968.hybrid-card-backed-draft-board.csv"
ROSTER_METADATA_PATH = BASE / "player-roster-metadata" / "1968.player-roster-metadata.json"
CARDS_DIR = BASE / "cards"
OUTPUT_DIR = BASE / "draft-boards"

JSON_OUT = OUTPUT_DIR / "1968.role-balanced-draft-board-v0.json"
MD_OUT = OUTPUT_DIR / "1968.role-balanced-draft-board-v0.md"


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
        closer_num = int(match.group(2))
        if closer_num > 0:
            closer = f"C{closer_num}"

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
        "browserBaselineDraftScore": fnum(row.get("browserBaselineDraftScore")),
        "rawCardScore": fnum(row.get("rawCardScore")),
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
        "isCheap": salary <= 2.0,
        "isValue": value >= 35.0,
    }


def sort_score(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(rows, key=lambda r: (-r["hybridDraftScore"], r["salaryMillions"], str(r.get("playerName"))))


def sort_value(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(rows, key=lambda r: (-r["hybridValueScore"], -r["hybridDraftScore"], r["salaryMillions"], str(r.get("playerName"))))


def compact(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "playerId": row.get("playerId"),
        "playerName": row.get("playerName"),
        "team": row.get("team"),
        "role": row.get("role"),
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


def take(rows: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    return [compact(row) for row in rows[:limit]]


def role_text(row: dict[str, Any]) -> str:
    parts = [
        row.get("primaryPosition"),
        row.get("starterEndurance"),
        row.get("reliefEndurance"),
        row.get("closerEndurance"),
    ]
    return "/".join(str(part) for part in parts if part)


def add_table(lines: list[str], title: str, rows: list[dict[str, Any]], note: str | None = None) -> None:
    lines.extend(["", f"## {title}", ""])
    if note:
        lines.extend([note, ""])

    lines.extend([
        "| Rank | Player | Team | Role | Salary | Score | Value | Tier |",
        "|---:|---|---|---|---:|---:|---:|---|",
    ])

    for index, row in enumerate(rows, 1):
        lines.append(
            f"| {index} | {row.get('playerName')} | {row.get('team')} | {role_text(row)} | "
            f"{row.get('salaryMillions'):.2f} | {row.get('hybridDraftScore'):.2f} | "
            f"{row.get('hybridValueScore'):.2f} | {row.get('confidenceTier')} |"
        )


def build_markdown(payload: dict[str, Any]) -> str:
    lines: list[str] = [
        "# 1968 Role-Balanced Draft Board v0",
        "",
        "Purpose: convert the global hybrid ranking into role-specific draft pools that support legal roster construction.",
        "",
        "This is a human draft-assist report, not an autonomous optimizer.",
        "",
        "## Legal Roster Spine",
        "",
        "| Requirement | Minimum | Available in Board |",
        "|---|---:|---:|",
    ]

    for row in payload["legalRosterSpine"]:
        lines.append(f"| {row['requirement']} | {row['minimum']} | {row['available']} |")

    lines.extend([
        "",
        "## Draft Interpretation",
        "",
        "- Do not draft directly from the global hybrid ranking.",
        "- Use premium hitters and starter-endurance pitchers as the first strategic layers.",
        "- Use catcher, pure-reliever, and closer-qualified buckets to protect legality.",
        "- Use value buckets to fill salary-constrained roster slots.",
        "- Card-backed players are higher-confidence than browser-baseline players.",
    ])

    buckets = payload["buckets"]

    add_table(lines, "Premium Hitters", buckets["premiumHitters"], "Best hitter pool by hybrid score.")
    add_table(lines, "Primary Catchers", buckets["primaryCatchers"], "Catcher pool needed to satisfy the 2-primary-catcher requirement.")
    add_table(lines, "Starter-Endurance Pitchers", buckets["starterEndurancePitchers"], "Pitchers who can satisfy the 5-starter-endurance requirement.")
    add_table(lines, "Pure Relievers", buckets["pureRelievers"], "Relievers with relief endurance and no starter endurance.")
    add_table(lines, "Closer-Qualified Pitchers", buckets["closerQualifiedPitchers"], "Pitchers with closer endurance derived from authenticated card evidence.")
    add_table(lines, "Cheap Hitter Values", buckets["cheapHitterValues"], "Hitters at or below $2M, ranked by value score.")
    add_table(lines, "Cheap Pitcher Values", buckets["cheapPitcherValues"], "Pitchers at or below $2M, ranked by value score.")
    add_table(lines, "Card-Backed Pitchers", buckets["cardBackedPitchers"], "Pitchers with authenticated card probability support.")

    lines.extend([
        "",
        "## v0 Limitation",
        "",
        "This report does not yet assemble a full roster template or enforce a salary cap. That is the next artifact.",
    ])

    return "\n".join(lines) + "\n"


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    board = load_board()
    roster = load_roster_players()
    roster_by_id = {str(player.get("playerId")): player for player in roster}

    rows = [enrich_row(row, roster_by_id) for row in board]

    hitters = [r for r in rows if r["isHitter"]]
    pitchers = [r for r in rows if r["isPitcher"]]
    starter_pitchers = [r for r in rows if r["isStarterEndurancePitcher"]]
    pure_relievers = [r for r in rows if r["isPureReliever"]]
    closer_pitchers = [r for r in rows if r["isCloserEndurancePitcher"]]
    catchers = [r for r in rows if r["isPrimaryCatcher"]]

    buckets = {
        "premiumHitters": take(sort_score([r for r in hitters if not r["isPrimaryCatcher"]]), 40),
        "primaryCatchers": take(sort_score(catchers), 25),
        "starterEndurancePitchers": take(sort_score(starter_pitchers), 40),
        "pureRelievers": take(sort_score(pure_relievers), 35),
        "closerQualifiedPitchers": take(sort_score(closer_pitchers), 30),
        "cheapHitterValues": take(sort_value([r for r in hitters if r["salaryMillions"] <= 2.0]), 35),
        "cheapPitcherValues": take(sort_value([r for r in pitchers if r["salaryMillions"] <= 2.0]), 35),
        "cardBackedPitchers": take(sort_score([r for r in pitchers if r["isCardBacked"]]), 35),
    }

    payload = {
        "schemaVersion": "bie.role-balanced-draft-board.v0",
        "season": int(SEASON),
        "inputs": {
            "draftBoard": str(DRAFT_BOARD_PATH.relative_to(ROOT)).replace("\\", "/"),
            "rosterMetadata": str(ROSTER_METADATA_PATH.relative_to(ROOT)).replace("\\", "/"),
            "cardEvidenceDir": str(CARDS_DIR.relative_to(ROOT)).replace("\\", "/"),
        },
        "counts": {
            "players": len(rows),
            "hitters": len(hitters),
            "pitchers": len(pitchers),
            "primaryCatchers": len(catchers),
            "starterEndurancePitchers": len(starter_pitchers),
            "pureRelievers": len(pure_relievers),
            "closerQualifiedPitchers": len(closer_pitchers),
            "cardBackedPlayers": sum(1 for r in rows if r["isCardBacked"]),
        },
        "legalRosterSpine": [
            {"requirement": "Hitters", "minimum": 13, "available": len(hitters)},
            {"requirement": "Pitchers", "minimum": 11, "available": len(pitchers)},
            {"requirement": "Primary catchers", "minimum": 2, "available": len(catchers)},
            {"requirement": "Starter-endurance pitchers", "minimum": 5, "available": len(starter_pitchers)},
            {"requirement": "Pure relievers", "minimum": 4, "available": len(pure_relievers)},
            {"requirement": "Closer-endurance pitchers", "minimum": 1, "available": len(closer_pitchers)},
        ],
        "buckets": buckets,
        "limitations": [
            "Does not assemble a final roster.",
            "Does not enforce salary cap.",
            "Does not model live draft availability.",
            "Does not yet optimize hitter/pitcher budget split.",
        ],
    }

    JSON_OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    MD_OUT.write_text(build_markdown(payload), encoding="utf-8")

    print("# ROLE-BALANCED BOARD SUMMARY")
    for key, value in payload["counts"].items():
        print(f"{key}: {value}")

    print("\n# BUCKET LEADERS")
    for bucket_name, bucket_rows in buckets.items():
        print(f"\n{bucket_name}:")
        for index, row in enumerate(bucket_rows[:5], 1):
            print(
                f"{index}. {row['playerName']} | {row['team']} | role={role_text(row)} | "
                f"salary={row['salaryMillions']:.2f} | score={row['hybridDraftScore']:.2f} | "
                f"value={row['hybridValueScore']:.2f} | tier={row['confidenceTier']}"
            )

    print("\n# OUTPUT FILES")
    print(JSON_OUT.relative_to(ROOT))
    print(MD_OUT.relative_to(ROOT))

    print("\n# RESULT SUMMARY")
    print("Created 1968 role-balanced draft board v0.")
    print("Paste back:")
    print("1. # ROLE-BALANCED BOARD SUMMARY")
    print("2. # BUCKET LEADERS")
    print("3. # OUTPUT FILES")
    print("4. # BASEBALL GIT STATUS")
    print("5. # RESULT SUMMARY")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
