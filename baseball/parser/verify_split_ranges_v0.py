from __future__ import annotations

from collections import Counter
from pathlib import Path
import json
from typing import Any


UNIVERSE_PATH = Path("data/baseball/raw/strat365/1980/players/1980_players_universe.json")
SPLIT_RANGE_DIR = Path("data/baseball/parsed/strat365/1980/split-ranges")

EXPECTED_SCHEMA_VERSION = "bie.result-split-ranges.v0"
EXPECTED_OUTCOME_ROWS = 54748
EXPECTED_ENTRIES = 47586
EXPECTED_NONE_ROWS = 42139
EXPECTED_D20_CLOSED_ROWS = 12600
EXPECTED_D20_OPEN_HIGH_ROWS = 9


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig", errors="replace"))


def main() -> None:
    universe = read_json(UNIVERSE_PATH)
    players = universe.get("players", [])
    expected_ids = {int(player["playerId"]): player for player in players}

    parsed_paths = list(SPLIT_RANGE_DIR.glob("*.split-ranges.json"))
    parsed_ids = {
        int(path.name.replace(".split-ranges.json", "")): path
        for path in parsed_paths
    }

    missing = sorted(set(expected_ids) - set(parsed_ids))
    extra = sorted(set(parsed_ids) - set(expected_ids))

    role_counts: Counter[str] = Counter()
    range_kind_counts: Counter[str] = Counter()
    failures: list[str] = []

    total_entries = 0
    total_outcome_rows = 0
    total_warnings = 0

    for player_id, player in sorted(expected_ids.items()):
        path = parsed_ids.get(player_id)
        if not path:
            continue

        data = read_json(path)

        if data.get("schemaVersion") != EXPECTED_SCHEMA_VERSION:
            failures.append(f"{player_id}: schemaVersion={data.get('schemaVersion')}")

        role = data.get("role")
        if role != player.get("role"):
            failures.append(f"{player_id}: role mismatch {role} != {player.get('role')}")

        if data.get("player", {}).get("playerId") != player_id:
            failures.append(f"{player_id}: playerId mismatch")

        warnings = data.get("warnings", [])
        total_warnings += len(warnings)
        if warnings:
            failures.append(f"{player_id}: warnings={len(warnings)}")

        role_counts[role] += 1

        tables = data.get("tables", [])
        if len(tables) != 6:
            failures.append(f"{player_id}: expected 6 tables, found {len(tables)}")

        for table in tables:
            entries = table.get("entries", [])
            if len(entries) != 11:
                failures.append(
                    f"{player_id}: table[{table.get('tableNumber')}] expected 11 entries, found {len(entries)}"
                )

            total_entries += len(entries)

            for entry in entries:
                for outcome in entry.get("outcomes", []):
                    total_outcome_rows += 1

                    split_range = outcome.get("splitRange", {})
                    kind = split_range.get("rangeKind")
                    range_kind_counts[kind] += 1

                    if not kind:
                        failures.append(
                            f"{player_id}: table[{table.get('tableNumber')}] dice {entry.get('diceRoll')} missing rangeKind"
                        )

                    if kind == "d20_closed":
                        low = split_range.get("low")
                        high = split_range.get("high")
                        width = split_range.get("width")

                        if not isinstance(low, int) or not isinstance(high, int):
                            failures.append(
                                f"{player_id}: table[{table.get('tableNumber')}] dice {entry.get('diceRoll')} invalid closed range bounds"
                            )
                        elif low < 1 or high > 20 or low > high:
                            failures.append(
                                f"{player_id}: table[{table.get('tableNumber')}] dice {entry.get('diceRoll')} out-of-bounds closed range {low}-{high}"
                            )

                        if width != high - low + 1:
                            failures.append(
                                f"{player_id}: table[{table.get('tableNumber')}] dice {entry.get('diceRoll')} width mismatch"
                            )

                    elif kind == "d20_open_high":
                        if split_range.get("rangeText") != "1-":
                            failures.append(
                                f"{player_id}: table[{table.get('tableNumber')}] dice {entry.get('diceRoll')} unexpected open-high range {split_range.get('rangeText')}"
                            )

                    elif kind == "none":
                        if outcome.get("rangeText") is not None:
                            failures.append(
                                f"{player_id}: table[{table.get('tableNumber')}] dice {entry.get('diceRoll')} none range has rangeText"
                            )

                    else:
                        failures.append(
                            f"{player_id}: table[{table.get('tableNumber')}] dice {entry.get('diceRoll')} unexpected rangeKind={kind}"
                        )

    print("BIE Split Range Verification")
    print("=" * 72)
    print(f"Universe players: {len(expected_ids)}")
    print(f"Parsed files: {len(parsed_ids)}")
    print(f"Missing parsed files: {len(missing)}")
    print(f"Extra parsed files: {len(extra)}")
    print(f"Role counts: {dict(role_counts)}")
    print(f"Total entries: {total_entries}")
    print(f"Total outcome rows: {total_outcome_rows}")
    print(f"Total warnings: {total_warnings}")
    print(f"Range kind counts: {dict(range_kind_counts)}")
    print(f"Failures: {len(failures)}")

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
        and role_counts.get("hitter") == 442
        and role_counts.get("pitcher") == 279
        and total_entries == EXPECTED_ENTRIES
        and total_outcome_rows == EXPECTED_OUTCOME_ROWS
        and total_warnings == 0
        and range_kind_counts.get("none") == EXPECTED_NONE_ROWS
        and range_kind_counts.get("d20_closed") == EXPECTED_D20_CLOSED_ROWS
        and range_kind_counts.get("d20_open_high") == EXPECTED_D20_OPEN_HIGH_ROWS
        and not failures
    ):
        print("SPLIT RANGES VERIFIED")
    else:
        print("SPLIT RANGES NOT VERIFIED")
        raise SystemExit(1)

    print("=" * 72)


if __name__ == "__main__":
    main()
