from __future__ import annotations

from datetime import datetime, timezone
from html import unescape
from pathlib import Path
import argparse
import json
import re
from typing import Any


PARSER_VERSION = "bie-result-cell-parser-v0.1"
DEFAULT_SEASON = 1980

UNIVERSE_PATH = Path("data/baseball/raw/strat365/1980/players/1980_players_universe.json")
CARDS_DIR = Path("data/baseball/raw/strat365/authenticated/1980/cards")
OUTPUT_DIR = Path("data/baseball/parsed/strat365/1980/result-cells")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig", errors="replace"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def clean_html(value: str) -> str:
    value = re.sub(r"<br\s*/?>", " ", value, flags=re.I)
    value = re.sub(r"<[^>]+>", " ", value)
    value = unescape(value)
    value = re.sub(r"\s+", " ", value).strip()
    return value


def extract_tables(html: str) -> list[str]:
    return re.findall(r"<table\b.*?</table>", html, flags=re.I | re.S)


def extract_rows(table_html: str) -> list[list[str]]:
    rows: list[list[str]] = []

    for row_html in re.findall(r"<tr\b.*?</tr>", table_html, flags=re.I | re.S):
        cells = re.findall(r"<t[dh]\b.*?</t[dh]>", row_html, flags=re.I | re.S)
        cleaned = [clean_html(cell) for cell in cells]

        if any(cell for cell in cleaned):
            rows.append(cleaned)

    return rows


def table_specs(role: str) -> list[dict[str, Any]]:
    if role == "hitter":
        return [
            {"tableNumber": 7, "side": "vs_left_pitcher", "column": 1, "skipHeaderRows": 2},
            {"tableNumber": 8, "side": "vs_left_pitcher", "column": 2, "skipHeaderRows": 0},
            {"tableNumber": 9, "side": "vs_left_pitcher", "column": 3, "skipHeaderRows": 0},
            {"tableNumber": 10, "side": "vs_right_pitcher", "column": 1, "skipHeaderRows": 0},
            {"tableNumber": 11, "side": "vs_right_pitcher", "column": 2, "skipHeaderRows": 0},
            {"tableNumber": 12, "side": "vs_right_pitcher", "column": 3, "skipHeaderRows": 0},
        ]

    if role == "pitcher":
        return [
            {"tableNumber": 6, "side": "vs_left_batter", "column": 4, "skipHeaderRows": 2},
            {"tableNumber": 7, "side": "vs_left_batter", "column": 5, "skipHeaderRows": 0},
            {"tableNumber": 8, "side": "vs_left_batter", "column": 6, "skipHeaderRows": 0},
            {"tableNumber": 9, "side": "vs_right_batter", "column": 4, "skipHeaderRows": 0},
            {"tableNumber": 10, "side": "vs_right_batter", "column": 5, "skipHeaderRows": 0},
            {"tableNumber": 11, "side": "vs_right_batter", "column": 6, "skipHeaderRows": 0},
        ]

    raise ValueError(f"Unsupported role: {role}")


def parse_dice_token(token: str) -> tuple[int | None, str]:
    match = re.match(r"^([#>$@]*)(\d+)-$", token or "")

    if not match:
        return None, ""

    modifiers = match.group(1)
    dice_roll = int(match.group(2))

    return dice_roll, modifiers


def parse_entries(rows: list[list[str]]) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None

    for row_index, row in enumerate(rows):
        token = row[0] if row else ""
        dice_roll, modifiers = parse_dice_token(token)

        if dice_roll is not None:
            current = {
                "diceRoll": dice_roll,
                "rawModifiers": modifiers,
                "rawRows": [
                    {
                        "rowIndex": row_index,
                        "cells": row,
                    }
                ],
                "rawOutcomes": [row[1:]],
            }
            entries.append(current)
            continue

        if current is not None and token == "":
            current["rawRows"].append(
                {
                    "rowIndex": row_index,
                    "cells": row,
                }
            )
            current["rawOutcomes"].append(row[1:])

    return entries


def parse_player(player: dict[str, Any]) -> dict[str, Any]:
    player_id = int(player["playerId"])
    role = player["role"]

    html_path = CARDS_DIR / f"{player_id}.html"
    html = html_path.read_text(encoding="utf-8", errors="replace")
    tables = extract_tables(html)

    parsed_tables: list[dict[str, Any]] = []

    for spec in table_specs(role):
        table_number = spec["tableNumber"]
        rows = extract_rows(tables[table_number - 1])
        rows_to_parse = rows[spec["skipHeaderRows"] :]
        entries = parse_entries(rows_to_parse)

        parsed_tables.append(
            {
                "tableNumber": table_number,
                "sourcePointer": f"table[{table_number}]",
                "side": spec["side"],
                "column": spec["column"],
                "skipHeaderRows": spec["skipHeaderRows"],
                "entryCount": len(entries),
                "entries": entries,
            }
        )

    return {
        "schemaVersion": "bie.result-cells.v0",
        "parserVersion": PARSER_VERSION,
        "parsedAt": utc_now(),
        "source": {
            "provider": "strat365",
            "season": 1980,
            "htmlPath": str(html_path),
        },
        "player": {
            "playerId": player_id,
            "playerName": player.get("playerName"),
            "team": player.get("team"),
        },
        "role": role,
        "tables": parsed_tables,
    }


def configure_paths(season: int) -> None:
    global UNIVERSE_PATH, CARDS_DIR, OUTPUT_DIR

    UNIVERSE_PATH = Path("data/baseball/raw/strat365") / str(season) / "players" / f"{season}_players_universe.json"
    CARDS_DIR = Path("data/baseball/raw/strat365/authenticated") / str(season) / "cards"
    OUTPUT_DIR = Path("data/baseball/parsed/strat365") / str(season) / "result-cells"


def select_players(players: list[dict[str, Any]], player_ids: list[int] | None) -> list[dict[str, Any]]:
    if not player_ids:
        return players

    wanted = {int(player_id) for player_id in player_ids}
    selected = []
    found = set()

    for player in players:
        player_id = int(player["playerId"])
        if player_id in wanted:
            selected.append(player)
            found.add(player_id)

    missing = sorted(wanted - found)
    if missing:
        raise ValueError(f"Player IDs not found in universe: {missing}")

    return selected


def main() -> None:
    parser = argparse.ArgumentParser(description="Parse Strat365 result cells from authenticated card HTML.")
    parser.add_argument(
        "--season",
        type=int,
        default=DEFAULT_SEASON,
        help="Season to parse. Defaults to 1980 to preserve existing behavior.",
    )
    parser.add_argument(
        "--player-ids",
        nargs="+",
        type=int,
        default=None,
        help="Optional targeted player IDs from the selected season universe.",
    )
    args = parser.parse_args()

    configure_paths(args.season)

    universe = read_json(UNIVERSE_PATH)
    players = select_players(universe.get("players", []), args.player_ids)

    parsed_count = 0
    failed_count = 0

    print("BIE Result Cell Parser v0")
    print("=" * 72)
    print(f"Players selected: {len(players)}")

    for player in players:
        player_id = int(player["playerId"])

        try:
            parsed = parse_player(player)
            output_path = OUTPUT_DIR / f"{player_id}.result-cells.json"
            write_json(output_path, parsed)

            table_count = len(parsed["tables"])
            entry_count = sum(table["entryCount"] for table in parsed["tables"])

            print(
                f"PARSED {player_id} {player['playerName']} "
                f"role={parsed['role']} tables={table_count} entries={entry_count}"
            )
            parsed_count += 1

        except Exception as exc:
            print(f"FAILED {player_id} {player.get('playerName')} error={exc}")
            failed_count += 1

    print("-" * 72)
    print(f"Parsed: {parsed_count}")
    print(f"Failed: {failed_count}")
    print(f"Output: {OUTPUT_DIR}")
    print("=" * 72)

    if failed_count:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
