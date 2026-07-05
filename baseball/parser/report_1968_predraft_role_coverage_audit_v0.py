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
REPORT_DIR = BASE / "reports"
JSON_OUT = REPORT_DIR / "1968.predraft-role-coverage-audit.json"
MD_OUT = REPORT_DIR / "1968.predraft-role-coverage-audit.md"


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


def card_source_season(player_id: str) -> Any:
    path = CARDS_DIR / f"{player_id}.parsed-card-evidence.json"
    if not path.exists():
        return None
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    return (data.get("source") or {}).get("season")


def enrich_row(row: dict[str, Any], roster_by_id: dict[str, dict[str, Any]]) -> dict[str, Any]:
    player_id = str(row.get("playerId", "")).strip()
    roster = roster_by_id.get(player_id)
    end = roster_endurance(roster)
    relief_text, card_relief, card_closer = parse_card_relief_text(player_id)

    starter_endurance = parse_starter_endurance(end)
    roster_relief = parse_roster_relief_endurance(end)
    relief_endurance = card_relief or roster_relief

    role = row.get("role", "")
    primary = primary_position(roster)

    source_season = card_source_season(player_id)

    return {
        **row,
        "salaryMillions": fnum(row.get("salaryMillions")),
        "hybridDraftScore": fnum(row.get("hybridDraftScore")),
        "hybridValueScore": fnum(row.get("hybridValueScore")),
        "browserBaselineDraftScore": fnum(row.get("browserBaselineDraftScore")),
        "rawCardScore": fnum(row.get("rawCardScore")),
        "rosterEndurance": end,
        "primaryPosition": primary,
        "starterEndurance": starter_endurance,
        "reliefEndurance": relief_endurance,
        "closerEndurance": card_closer,
        "cardReliefText": relief_text,
        "isStarterEndurancePitcher": role == "pitcher" and starter_endurance is not None,
        "isPureReliever": role == "pitcher" and relief_endurance is not None and starter_endurance is None,
        "isCloserEndurancePitcher": role == "pitcher" and card_closer is not None,
        "isPrimaryCatcher": role == "hitter" and primary == "C",
        "cardSourceSeason": source_season,
        "cardSourceSeasonMismatch": source_season is not None and str(source_season) != SEASON,
    }


def compact_player(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "playerId": row.get("playerId"),
        "playerName": row.get("playerName"),
        "team": row.get("team"),
        "role": row.get("role"),
        "salaryMillions": row.get("salaryMillions"),
        "hybridDraftScore": row.get("hybridDraftScore"),
        "hybridValueScore": row.get("hybridValueScore"),
        "primaryPosition": row.get("primaryPosition"),
        "rosterEndurance": row.get("rosterEndurance"),
        "starterEndurance": row.get("starterEndurance"),
        "reliefEndurance": row.get("reliefEndurance"),
        "closerEndurance": row.get("closerEndurance"),
        "cardReliefText": row.get("cardReliefText"),
        "confidenceTier": row.get("confidenceTier"),
    }


def top(rows: list[dict[str, Any]], limit: int = 25) -> list[dict[str, Any]]:
    ordered = sorted(rows, key=lambda r: (-r["hybridDraftScore"], r["salaryMillions"], str(r.get("playerName"))))
    return [compact_player(r) for r in ordered[:limit]]


def count(rows: list[dict[str, Any]], predicate) -> int:
    return sum(1 for row in rows if predicate(row))


def build_markdown(payload: dict[str, Any]) -> str:
    lines: list[str] = [
        "# 1968 Pre-Draft Role Coverage Audit",
        "",
        "Purpose: verify that BIE can identify legal roster-role coverage before draft recommendations are trusted.",
        "",
        "## Full Board Counts",
        "",
        "| Metric | Count |",
        "|---|---:|",
    ]

    for key, value in payload["counts"].items():
        lines.append(f"| {key} | {value} |")

    lines.extend([
        "",
        "## Top-Slice Coverage by Global Hybrid Score",
        "",
        "| Slice | Hitters | Pitchers | SP Endurance | Pure RP | Closer Endurance | Primary C |",
        "|---:|---:|---:|---:|---:|---:|---:|",
    ])

    for row in payload["topSliceCoverage"]:
        lines.append(
            f"| {row['topN']} | {row['hitters']} | {row['pitchers']} | "
            f"{row['starterEndurancePitchers']} | {row['pureRelievers']} | "
            f"{row['closerEndurancePitchers']} | {row['primaryCatchers']} |"
        )

    def add_table(title: str, rows: list[dict[str, Any]]) -> None:
        lines.extend([
            "",
            f"## {title}",
            "",
            "| Rank | Player | Team | Salary | Score | Value | Pos | Endurance | Derived Role |",
            "|---:|---|---|---:|---:|---:|---|---|---|",
        ])
        for index, row in enumerate(rows, 1):
            derived = "/".join(
                str(x)
                for x in [
                    row.get("starterEndurance"),
                    row.get("reliefEndurance"),
                    row.get("closerEndurance"),
                ]
                if x
            )
            lines.append(
                f"| {index} | {row.get('playerName')} | {row.get('team')} | "
                f"{row.get('salaryMillions'):.2f} | {row.get('hybridDraftScore'):.2f} | "
                f"{row.get('hybridValueScore'):.2f} | {row.get('primaryPosition') or ''} | "
                f"{row.get('rosterEndurance') or ''} | {derived} |"
            )

    add_table("Top Starter-Endurance Pitchers", payload["topStarterEndurancePitchers"])
    add_table("Top Pure Relievers", payload["topPureRelievers"])
    add_table("Top Closer-Endurance Pitchers", payload["topCloserEndurancePitchers"])
    add_table("Top Primary Catchers", payload["topPrimaryCatchers"])

    lines.extend([
        "",
        "## Legality Signal",
        "",
    ])

    for item in payload["legalitySignal"]:
        lines.append(f"- {item}")

    lines.extend([
        "",
        "## Metadata Debt",
        "",
        f"- Card evidence files with source.season mismatch: {payload['metadataDebt']['cardSourceSeasonMismatches']}",
    ])

    return "\n".join(lines) + "\n"


def main() -> int:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    board = load_board()
    roster_players = load_roster_players()
    roster_by_id = {str(player.get("playerId")): player for player in roster_players}

    rows = [enrich_row(row, roster_by_id) for row in board]
    global_rows = sorted(rows, key=lambda r: (-r["hybridDraftScore"], r["salaryMillions"], str(r.get("playerName"))))

    top_slices = []
    for top_n in [25, 40, 60, 80, 100, 120, 160, 200]:
        subset = global_rows[:top_n]
        top_slices.append({
            "topN": top_n,
            "hitters": count(subset, lambda r: r["role"] == "hitter"),
            "pitchers": count(subset, lambda r: r["role"] == "pitcher"),
            "starterEndurancePitchers": count(subset, lambda r: r["isStarterEndurancePitcher"]),
            "pureRelievers": count(subset, lambda r: r["isPureReliever"]),
            "closerEndurancePitchers": count(subset, lambda r: r["isCloserEndurancePitcher"]),
            "primaryCatchers": count(subset, lambda r: r["isPrimaryCatcher"]),
        })

    counts = {
        "players": len(rows),
        "hitters": count(rows, lambda r: r["role"] == "hitter"),
        "pitchers": count(rows, lambda r: r["role"] == "pitcher"),
        "starterEndurancePitchers": count(rows, lambda r: r["isStarterEndurancePitcher"]),
        "pureRelievers": count(rows, lambda r: r["isPureReliever"]),
        "closerEndurancePitchers": count(rows, lambda r: r["isCloserEndurancePitcher"]),
        "primaryCatchers": count(rows, lambda r: r["isPrimaryCatcher"]),
        "cardBackedPlayers": count(rows, lambda r: r.get("confidenceTier") == "card-backed"),
    }

    legality_signal = []
    checks = [
        ("PASS" if counts["hitters"] >= 13 else "FAIL", "full board has at least 13 hitters"),
        ("PASS" if counts["pitchers"] >= 11 else "FAIL", "full board has at least 11 pitchers"),
        ("PASS" if counts["primaryCatchers"] >= 2 else "FAIL", "full board has at least 2 primary catchers"),
        ("PASS" if counts["starterEndurancePitchers"] >= 5 else "FAIL", "full board has at least 5 starter-endurance pitchers"),
        ("PASS" if counts["pureRelievers"] >= 4 else "FAIL", "full board has at least 4 pure relievers"),
        ("PASS" if counts["closerEndurancePitchers"] >= 1 else "FAIL", "full board has at least 1 closer-endurance pitcher"),
    ]

    for status, label in checks:
        legality_signal.append(f"{status}: {label}")

    payload = {
        "schemaVersion": "bie.predraft-role-coverage-audit.v0",
        "season": int(SEASON),
        "inputs": {
            "draftBoard": str(DRAFT_BOARD_PATH.relative_to(ROOT)).replace("\\", "/"),
            "rosterMetadata": str(ROSTER_METADATA_PATH.relative_to(ROOT)).replace("\\", "/"),
            "cardEvidenceDir": str(CARDS_DIR.relative_to(ROOT)).replace("\\", "/"),
        },
        "counts": counts,
        "topSliceCoverage": top_slices,
        "topStarterEndurancePitchers": top([r for r in rows if r["isStarterEndurancePitcher"]]),
        "topPureRelievers": top([r for r in rows if r["isPureReliever"]]),
        "topCloserEndurancePitchers": top([r for r in rows if r["isCloserEndurancePitcher"]]),
        "topPrimaryCatchers": top([r for r in rows if r["isPrimaryCatcher"]]),
        "legalitySignal": legality_signal,
        "metadataDebt": {
            "cardSourceSeasonMismatches": count(rows, lambda r: bool(r["cardSourceSeasonMismatch"])),
        },
    }

    JSON_OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    MD_OUT.write_text(build_markdown(payload), encoding="utf-8")

    print("# 1968 PRE-DRAFT ROLE AUDIT SUMMARY")
    for key, value in counts.items():
        print(f"{key}: {value}")

    print("\n# TOP-SLICE COVERAGE")
    for row in top_slices:
        print(
            f"top{row['topN']}: hitters={row['hitters']}, pitchers={row['pitchers']}, "
            f"SP={row['starterEndurancePitchers']}, pureRP={row['pureRelievers']}, "
            f"closer={row['closerEndurancePitchers']}, primaryC={row['primaryCatchers']}"
        )

    print("\n# TOP CLOSER-ENDURANCE CANDIDATES")
    for index, row in enumerate(payload["topCloserEndurancePitchers"][:15], 1):
        print(
            f"{index:02d}. {row['playerName']} | {row['team']} | "
            f"{row['rosterEndurance']} -> {row['reliefEndurance']}/{row['closerEndurance']} | "
            f"salary={row['salaryMillions']:.2f} | score={row['hybridDraftScore']:.2f} | "
            f"value={row['hybridValueScore']:.2f}"
        )

    print("\n# LEGALITY SIGNAL")
    for item in legality_signal:
        print(item)

    print("\n# OUTPUT FILES")
    print(JSON_OUT.relative_to(ROOT))
    print(MD_OUT.relative_to(ROOT))

    print("\n# RESULT SUMMARY")
    print("Created 1968 pre-draft role coverage audit.")
    print("Paste back:")
    print("1. # 1968 PRE-DRAFT ROLE AUDIT SUMMARY")
    print("2. # TOP-SLICE COVERAGE")
    print("3. # TOP CLOSER-ENDURANCE CANDIDATES")
    print("4. # LEGALITY SIGNAL")
    print("5. # OUTPUT FILES")
    print("6. # BASEBALL GIT STATUS")
    print("7. # RESULT SUMMARY")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
