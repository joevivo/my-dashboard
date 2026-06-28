from __future__ import annotations

from datetime import datetime, timezone
from html import unescape
from pathlib import Path
import argparse
import json
import re
from typing import Any


PARSER_VERSION = "bie-parser-v0.1"
SCHEMA_VERSION = "bie.parsed-card-evidence.v0"

SAMPLE_PATH = Path("baseball/parser/sample_set_v0.json")
UNIVERSE_PATH = Path("data/baseball/raw/strat365/1980/players/1980_players_universe.json")
CARDS_DIR = Path("data/baseball/raw/strat365/authenticated/1980/cards")
OUTPUT_DIR = Path("data/baseball/parsed/strat365/1980/cards")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig", errors="replace"))


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def strip_tags(value: str) -> str:
    value = re.sub(r"<script\b.*?</script>", " ", value, flags=re.I | re.S)
    value = re.sub(r"<style\b.*?</style>", " ", value, flags=re.I | re.S)
    value = re.sub(r"<[^>]+>", " ", value)
    value = unescape(value)
    return re.sub(r"\s+", " ", value).strip()


def extract_tables(html: str) -> list[str]:
    raw_tables = re.findall(r"<table\b.*?</table>", html, flags=re.I | re.S)
    return [strip_tags(table) for table in raw_tables]


def reject_gated_shell(html: str, metadata: dict[str, Any]) -> None:
    gated_text = "must have purchased and be logged in"
    if gated_text in html.lower():
        raise ValueError("Gated public shell detected")

    if metadata.get("gatedShell") is True:
        raise ValueError("Metadata indicates gated public shell")

    if metadata.get("status") != "validated_authenticated_card":
        raise ValueError(f"Metadata status is not validated_authenticated_card: {metadata.get('status')}")


def parse_balance(table_text: str | None) -> str | None:
    if not table_text:
        return None
    match = re.search(r"Balance:\s*([A-Z0-9]+)", table_text, flags=re.I)
    return match.group(1).upper() if match else None


def parse_hitter_traits(tables: list[str]) -> dict[str, Any]:
    table4 = tables[3] if len(tables) >= 4 else ""
    table5 = tables[4] if len(tables) >= 5 else ""
    combined = f"{table4} {table5}".strip()

    defense_match = re.search(r"Defense:\s*(.*?)(?:\s+running\s+|\s*$)", combined, flags=re.I)
    running_match = re.search(r"\brunning\s+([0-9]+-[0-9]+)", combined, flags=re.I)
    stealing_match = re.search(r"stealing-\s*(.*?)(?:\s+bunting-|\s*$)", combined, flags=re.I)
    bunting_match = re.search(r"bunting-\s*([A-Z])", combined, flags=re.I)
    hitrun_match = re.search(r"hit\s*&\s*run-\s*([A-Z])", combined, flags=re.I)

    return {
        "rawTraitText": combined,
        "defenseText": defense_match.group(1).strip() if defense_match else None,
        "runningText": running_match.group(1).strip() if running_match else None,
        "stealingText": stealing_match.group(1).strip() if stealing_match else None,
        "buntingText": bunting_match.group(1).upper() if bunting_match else None,
        "hitAndRunText": hitrun_match.group(1).upper() if hitrun_match else None,
    }


def parse_pitcher_traits(tables: list[str]) -> dict[str, Any]:
    table4 = tables[3] if len(tables) >= 4 else ""
    table5 = tables[4] if len(tables) >= 5 else ""
    combined = f"{table4} {table5}".strip()

    throws_match = re.search(r"throws\s+(LEFT|RIGHT)", combined, flags=re.I)
    hold_match = re.search(r"hold\s+([+-]?\d+)", combined, flags=re.I)
    starter_match = re.search(r"starter\([^)]+\)", combined, flags=re.I)
    relief_match = re.search(r"relief\([^)]+\)(?:/\d+)?", combined, flags=re.I)
    pitcher_match = re.search(r"pitcher-\d+", combined, flags=re.I)
    bunting_match = re.search(r"bunting-([A-Z])", combined, flags=re.I)
    balk_match = re.search(r"\bbk-\s*\d+", combined, flags=re.I)
    wild_pitch_match = re.search(r"\bwp-\s*\d+", combined, flags=re.I)
    error_match = re.search(r"\be\d+", combined, flags=re.I)

    return {
        "rawTraitText": combined,
        "throws": throws_match.group(1).upper() if throws_match else None,
        "hold": hold_match.group(1) if hold_match else None,
        "starterText": starter_match.group(0) if starter_match else None,
        "reliefText": relief_match.group(0) if relief_match else None,
        "pitcherText": pitcher_match.group(0) if pitcher_match else None,
        "buntingText": bunting_match.group(1).upper() if bunting_match else None,
        "balkText": balk_match.group(0) if balk_match else None,
        "wildPitchText": wild_pitch_match.group(0) if wild_pitch_match else None,
        "errorText": error_match.group(0) if error_match else None,
    }


def result_table_indexes(role: str) -> range:
    if role == "hitter":
        return range(7, 13)   # 1-based tables 7-12
    if role == "pitcher":
        return range(6, 12)   # 1-based tables 6-11
    raise ValueError(f"Unsupported role: {role}")


def build_result_evidence(tables: list[str], role: str) -> list[dict[str, Any]]:
    evidence: list[dict[str, Any]] = []

    for one_based_index in result_table_indexes(role):
        zero_based_index = one_based_index - 1
        if zero_based_index >= len(tables):
            continue

        raw_text = tables[zero_based_index].strip()
        if not raw_text:
            continue

        evidence.append(
            {
                "section": f"{role}_card_result_table_{one_based_index}",
                "column": None,
                "row": None,
                "diceRange": None,
                "rawResultText": raw_text,
                "normalizedLabel": None,
                "source": {
                    "kind": "html_table",
                    "pointer": f"table[{one_based_index}]"
                }
            }
        )

    return evidence


def parse_card(player: dict[str, Any]) -> dict[str, Any]:
    player_id = int(player["playerId"])
    role = player["role"]

    html_path = CARDS_DIR / f"{player_id}.html"
    metadata_path = CARDS_DIR / f"{player_id}.capture.json"

    html = html_path.read_text(encoding="utf-8", errors="replace")
    metadata = read_json(metadata_path)

    reject_gated_shell(html, metadata)

    tables = extract_tables(html)
    balance = parse_balance(tables[2] if len(tables) >= 3 else None)

    warnings: list[str] = []
    if role == "hitter" and len(tables) != 14:
        warnings.append(f"Expected 14 hitter tables, found {len(tables)}")
    if role == "pitcher" and len(tables) != 13:
        warnings.append(f"Expected 13 pitcher tables, found {len(tables)}")

    result_evidence = build_result_evidence(tables, role)
    if len(result_evidence) != 6:
        warnings.append(f"Expected 6 result evidence tables, found {len(result_evidence)}")

    return {
        "schemaVersion": SCHEMA_VERSION,
        "parserVersion": PARSER_VERSION,
        "parsedAt": datetime.now(timezone.utc).isoformat(),
        "source": {
            "provider": "strat365",
            "season": 1980,
            "htmlPath": str(html_path),
            "metadataPath": str(metadata_path),
            "sha256": metadata.get("sha256") or metadata.get("sha") or metadata.get("htmlSha256"),
            "capturedAt": metadata.get("capturedAt"),
            "captureStatus": metadata.get("status"),
        },
        "player": {
            "playerId": player_id,
            "playerName": player["playerName"],
            "team": player.get("team"),
            "bats": metadata.get("bats"),
        },
        "role": role,
        "card": {
            "balance": balance,
            "rawText": strip_tags(html),
            "rawTables": tables,
        },
        "hitterTraits": parse_hitter_traits(tables) if role == "hitter" else None,
        "pitcherTraits": parse_pitcher_traits(tables) if role == "pitcher" else None,
        "resultEvidence": result_evidence,
        "warnings": warnings,
    }


def load_players(parse_all: bool) -> tuple[str, list[dict[str, Any]]]:
    if parse_all:
        universe = read_json(UNIVERSE_PATH)
        return "full-universe", universe.get("players", [])

    sample = read_json(SAMPLE_PATH)
    return sample.get("sampleSetId", "controlled-sample"), sample.get("players", [])


def main() -> None:
    parser = argparse.ArgumentParser(description="Parse Strat365 authenticated card evidence.")
    parser.add_argument(
        "--all",
        action="store_true",
        help="Parse the full discovered player universe instead of the controlled sample.",
    )
    args = parser.parse_args()

    run_id, players = load_players(parse_all=args.all)

    print("BIE Parser v0 Run")
    print("=" * 72)
    print(f"Run: {run_id}")
    print(f"Players selected: {len(players)}")

    parsed_count = 0
    failed_count = 0
    warning_count = 0

    for player in players:
        player_id = int(player["playerId"])
        try:
            parsed = parse_card(player)
            output_path = OUTPUT_DIR / f"{player_id}.parsed-card-evidence.json"
            write_json(output_path, parsed)

            warnings = parsed.get("warnings", [])
            warning_count += len(warnings)

            print(
                f"PARSED {player_id} {player['playerName']} "
                f"role={parsed['role']} "
                f"balance={parsed['card']['balance']} "
                f"results={len(parsed['resultEvidence'])} "
                f"warnings={len(warnings)}"
            )
            parsed_count += 1
        except Exception as exc:
            print(f"FAILED {player_id} {player.get('playerName')} error={exc}")
            failed_count += 1

    print("-" * 72)
    print(f"Parsed: {parsed_count}")
    print(f"Failed: {failed_count}")
    print(f"Warnings: {warning_count}")
    print(f"Output: {OUTPUT_DIR}")
    print("=" * 72)

    if failed_count:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
