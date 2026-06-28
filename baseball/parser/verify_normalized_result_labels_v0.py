from __future__ import annotations

from collections import Counter
from pathlib import Path
import json
from typing import Any


UNIVERSE_PATH = Path("data/baseball/raw/strat365/1980/players/1980_players_universe.json")
NORMALIZED_DIR = Path("data/baseball/parsed/strat365/1980/normalized-result-labels")

EXPECTED_SCHEMA_VERSION = "bie.normalized-result-labels.v0"
EXPECTED_OUTCOME_ROWS = 54748


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig", errors="replace"))


def main() -> None:
    universe = read_json(UNIVERSE_PATH)
    players = universe.get("players", [])
    expected_ids = {int(player["playerId"]): player for player in players}

    parsed_paths = list(NORMALIZED_DIR.glob("*.normalized-result-labels.json"))
    parsed_ids = {
        int(path.name.replace(".normalized-result-labels.json", "")): path
        for path in parsed_paths
    }

    missing = sorted(set(expected_ids) - set(parsed_ids))
    extra = sorted(set(parsed_ids) - set(expected_ids))

    role_counts: Counter[str] = Counter()
    normalized_counts: Counter[str] = Counter()
    failures: list[str] = []

    total_entries = 0
    total_outcome_rows = 0
    unmatched_outcome_rows = 0

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
                normalized_outcomes = entry.get("normalizedOutcomes", [])
                raw_outcomes = entry.get("rawOutcomes", [])

                if len(normalized_outcomes) != len(raw_outcomes):
                    failures.append(
                        f"{player_id}: table[{table.get('tableNumber')}] dice {entry.get('diceRoll')} "
                        f"normalized/raw outcome count mismatch"
                    )

                for outcome in normalized_outcomes:
                    total_outcome_rows += 1

                    normalized = outcome.get("normalized", {})
                    label = normalized.get("normalizedLabel")
                    normalized_counts[label] += 1

                    if not label:
                        failures.append(
                            f"{player_id}: table[{table.get('tableNumber')}] dice {entry.get('diceRoll')} missing normalized label"
                        )

                    if label == "UNMATCHED":
                        unmatched_outcome_rows += 1

                    raw_outcome = outcome.get("rawOutcome", [])
                    range_text = outcome.get("rangeText")
                    if range_text is not None and (len(raw_outcome) < 2 or raw_outcome[1] != range_text):
                        failures.append(
                            f"{player_id}: table[{table.get('tableNumber')}] dice {entry.get('diceRoll')} range mismatch"
                        )

    print("BIE Normalized Result Label Verification")
    print("=" * 72)
    print(f"Universe players: {len(expected_ids)}")
    print(f"Parsed files: {len(parsed_ids)}")
    print(f"Missing parsed files: {len(missing)}")
    print(f"Extra parsed files: {len(extra)}")
    print(f"Role counts: {dict(role_counts)}")
    print(f"Total entries: {total_entries}")
    print(f"Total outcome rows: {total_outcome_rows}")
    print(f"Unmatched outcome rows: {unmatched_outcome_rows}")
    print(f"Failures: {len(failures)}")
    print()
    print("Normalized counts:")
    for label, count in normalized_counts.most_common():
        print(f"  {label}: {count}")

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
        and total_outcome_rows == EXPECTED_OUTCOME_ROWS
        and unmatched_outcome_rows == 0
        and not failures
    ):
        print("NORMALIZED RESULT LABELS VERIFIED")
    else:
        print("NORMALIZED RESULT LABELS NOT VERIFIED")
        raise SystemExit(1)

    print("=" * 72)


if __name__ == "__main__":
    main()
