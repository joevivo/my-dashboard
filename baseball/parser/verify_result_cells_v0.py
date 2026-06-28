from __future__ import annotations

from collections import Counter
from pathlib import Path
import json
from typing import Any


UNIVERSE_PATH = Path("data/baseball/raw/strat365/1980/players/1980_players_universe.json")
RESULT_CELLS_DIR = Path("data/baseball/parsed/strat365/1980/result-cells")

EXPECTED_SCHEMA_VERSION = "bie.result-cells.v0"
EXPECTED_DICE = list(range(2, 13))


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig", errors="replace"))


def expected_table_specs(role: str) -> list[dict[str, Any]]:
    if role == "hitter":
        return [
            {"tableNumber": 7, "side": "vs_left_pitcher", "column": 1},
            {"tableNumber": 8, "side": "vs_left_pitcher", "column": 2},
            {"tableNumber": 9, "side": "vs_left_pitcher", "column": 3},
            {"tableNumber": 10, "side": "vs_right_pitcher", "column": 1},
            {"tableNumber": 11, "side": "vs_right_pitcher", "column": 2},
            {"tableNumber": 12, "side": "vs_right_pitcher", "column": 3},
        ]

    if role == "pitcher":
        return [
            {"tableNumber": 6, "side": "vs_left_batter", "column": 4},
            {"tableNumber": 7, "side": "vs_left_batter", "column": 5},
            {"tableNumber": 8, "side": "vs_left_batter", "column": 6},
            {"tableNumber": 9, "side": "vs_right_batter", "column": 4},
            {"tableNumber": 10, "side": "vs_right_batter", "column": 5},
            {"tableNumber": 11, "side": "vs_right_batter", "column": 6},
        ]

    raise ValueError(f"Unsupported role: {role}")


def main() -> None:
    universe = read_json(UNIVERSE_PATH)
    players = universe.get("players", [])
    expected_ids = {int(player["playerId"]): player for player in players}

    parsed_paths = list(RESULT_CELLS_DIR.glob("*.result-cells.json"))
    parsed_ids = {
        int(path.name.replace(".result-cells.json", "")): path
        for path in parsed_paths
    }

    missing = sorted(set(expected_ids) - set(parsed_ids))
    extra = sorted(set(parsed_ids) - set(expected_ids))

    role_counts: Counter[str] = Counter()
    table_counts: Counter[str] = Counter()
    entry_counts: Counter[str] = Counter()
    failures: list[str] = []

    for player_id, player in sorted(expected_ids.items()):
        path = parsed_ids.get(player_id)
        if not path:
            continue

        data = read_json(path)

        if data.get("schemaVersion") != EXPECTED_SCHEMA_VERSION:
            failures.append(f"{player_id}: schemaVersion={data.get('schemaVersion')}")

        if data.get("role") != player.get("role"):
            failures.append(f"{player_id}: role mismatch {data.get('role')} != {player.get('role')}")

        if data.get("player", {}).get("playerId") != player_id:
            failures.append(f"{player_id}: playerId mismatch")

        role = data.get("role")
        role_counts[role] += 1

        tables = data.get("tables", [])
        if len(tables) != 6:
            failures.append(f"{player_id}: expected 6 tables, found {len(tables)}")

        expected_specs = expected_table_specs(role)
        for idx, expected in enumerate(expected_specs):
            if idx >= len(tables):
                continue

            table = tables[idx]
            table_number = table.get("tableNumber")
            key = f"{role}:table[{table_number}]"

            table_counts[key] += 1
            entry_counts[key] += table.get("entryCount", 0)

            if table_number != expected["tableNumber"]:
                failures.append(f"{player_id}: table index {idx} expected table {expected['tableNumber']}, found {table_number}")

            if table.get("side") != expected["side"]:
                failures.append(f"{player_id}: table[{table_number}] side mismatch {table.get('side')} != {expected['side']}")

            if table.get("column") != expected["column"]:
                failures.append(f"{player_id}: table[{table_number}] column mismatch {table.get('column')} != {expected['column']}")

            entries = table.get("entries", [])
            if table.get("entryCount") != 11 or len(entries) != 11:
                failures.append(f"{player_id}: table[{table_number}] expected 11 entries, found entryCount={table.get('entryCount')} len={len(entries)}")

            dice = [entry.get("diceRoll") for entry in entries]
            if dice != EXPECTED_DICE:
                failures.append(f"{player_id}: table[{table_number}] dice mismatch {dice}")

            for entry in entries:
                if not entry.get("rawRows"):
                    failures.append(f"{player_id}: table[{table_number}] dice {entry.get('diceRoll')} missing rawRows")
                if not entry.get("rawOutcomes"):
                    failures.append(f"{player_id}: table[{table_number}] dice {entry.get('diceRoll')} missing rawOutcomes")

    print("BIE Result Cell Parser Verification")
    print("=" * 72)
    print(f"Universe players: {len(expected_ids)}")
    print(f"Parsed files: {len(parsed_ids)}")
    print(f"Missing parsed files: {len(missing)}")
    print(f"Extra parsed files: {len(extra)}")
    print(f"Role counts: {dict(role_counts)}")
    print(f"Failures: {len(failures)}")
    print()
    print("Table counts:")
    for key in sorted(table_counts):
        print(f"  {key}: {table_counts[key]}")
    print()
    print("Entry totals:")
    for key in sorted(entry_counts):
        print(f"  {key}: {entry_counts[key]}")

    if missing:
        print()
        print("Missing examples:")
        print(missing[:25])

    if extra:
        print()
        print("Extra examples:")
        print(extra[:25])

    if failures:
        print()
        print("Failure examples:")
        for failure in failures[:100]:
            print(failure)

    print("-" * 72)

    if (
        len(expected_ids) == 721
        and len(parsed_ids) == 721
        and not missing
        and not extra
        and not failures
        and role_counts.get("hitter") == 442
        and role_counts.get("pitcher") == 279
    ):
        print("RESULT CELL PARSER VERIFIED")
    else:
        print("RESULT CELL PARSER NOT VERIFIED")
        raise SystemExit(1)

    print("=" * 72)


if __name__ == "__main__":
    main()
