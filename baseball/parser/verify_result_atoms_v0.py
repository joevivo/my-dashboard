from __future__ import annotations

from collections import Counter
from pathlib import Path
import json
from typing import Any


UNIVERSE_PATH = Path("data/baseball/raw/strat365/1980/players/1980_players_universe.json")
ATOM_DIR = Path("data/baseball/parsed/strat365/1980/result-atoms")

EXPECTED_SCHEMA_VERSION = "bie.result-atoms.v0"
EXPECTED_ENTRIES = 47586
EXPECTED_OUTCOME_ROWS = 54748
EXPECTED_DISTINCT_ATOMS = 62

EXPECTED_RANGE_KIND_COUNTS = {
    "none": 42139,
    "d20_closed": 12600,
    "d20_open_high": 9,
}

EXPECTED_ENTRY_MARKER_COUNTS = {
    ">": 2734,
    "#": 1467,
    "$": 1403,
    "@": 1253,
}

EXPECTED_OUTCOME_LABEL_MARKER_COUNTS = {
    "**": 3209,
    "?": 2919,
    "*": 2768,
    "+": 2128,
}


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig", errors="replace"))


def main() -> None:
    universe = read_json(UNIVERSE_PATH)
    players = universe.get("players", [])
    expected_ids = {int(player["playerId"]): player for player in players}

    parsed_paths = list(ATOM_DIR.glob("*.result-atoms.json"))
    parsed_ids = {
        int(path.name.replace(".result-atoms.json", "")): path
        for path in parsed_paths
    }

    missing = sorted(set(expected_ids) - set(parsed_ids))
    extra = sorted(set(parsed_ids) - set(expected_ids))

    role_counts: Counter[str] = Counter()
    atom_counts: Counter[str] = Counter()
    range_kind_counts: Counter[str] = Counter()
    entry_marker_counts: Counter[str] = Counter()
    outcome_label_marker_counts: Counter[str] = Counter()

    total_entries = 0
    total_outcome_rows = 0
    total_warnings = 0
    failures: list[str] = []

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
                token_evidence = entry.get("entryTokenEvidence", {})
                for marker in token_evidence.get("entryTokenMarkers", []):
                    entry_marker_counts[marker] += 1

                for outcome in entry.get("outcomes", []):
                    total_outcome_rows += 1

                    result_atom = outcome.get("resultAtom", {})
                    atom_key = result_atom.get("atomKey")
                    normalized_label = result_atom.get("normalizedLabel")
                    range_kind = result_atom.get("rangeKind")
                    entry_markers = result_atom.get("entryTokenMarkers", [])
                    outcome_markers = result_atom.get("outcomeLabelMarkers", [])

                    if not atom_key:
                        failures.append(
                            f"{player_id}: table[{table.get('tableNumber')}] dice {entry.get('diceRoll')} missing atomKey"
                        )

                    if not normalized_label:
                        failures.append(
                            f"{player_id}: table[{table.get('tableNumber')}] dice {entry.get('diceRoll')} missing normalizedLabel"
                        )

                    if not range_kind:
                        failures.append(
                            f"{player_id}: table[{table.get('tableNumber')}] dice {entry.get('diceRoll')} missing rangeKind"
                        )

                    if entry_markers != token_evidence.get("entryTokenMarkers", []):
                        failures.append(
                            f"{player_id}: table[{table.get('tableNumber')}] dice {entry.get('diceRoll')} entry marker mismatch"
                        )

                    if outcome_markers != outcome.get("outcomeLabelMarkers", []):
                        failures.append(
                            f"{player_id}: table[{table.get('tableNumber')}] dice {entry.get('diceRoll')} outcome marker mismatch"
                        )

                    atom_counts[atom_key] += 1
                    range_kind_counts[range_kind] += 1

                    for marker in outcome_markers:
                        outcome_label_marker_counts[marker] += 1

    print("BIE Result Atom Verification")
    print("=" * 72)
    print(f"Universe players: {len(expected_ids)}")
    print(f"Parsed files: {len(parsed_ids)}")
    print(f"Missing parsed files: {len(missing)}")
    print(f"Extra parsed files: {len(extra)}")
    print(f"Role counts: {dict(role_counts)}")
    print(f"Total entries: {total_entries}")
    print(f"Total outcome rows: {total_outcome_rows}")
    print(f"Total warnings: {total_warnings}")
    print(f"Distinct atoms: {len(atom_counts)}")
    print(f"Range kind counts: {dict(range_kind_counts)}")
    print(f"Entry marker counts: {dict(entry_marker_counts)}")
    print(f"Outcome label marker counts: {dict(outcome_label_marker_counts)}")
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
        and len(atom_counts) == EXPECTED_DISTINCT_ATOMS
        and dict(range_kind_counts) == EXPECTED_RANGE_KIND_COUNTS
        and dict(entry_marker_counts) == EXPECTED_ENTRY_MARKER_COUNTS
        and dict(outcome_label_marker_counts) == EXPECTED_OUTCOME_LABEL_MARKER_COUNTS
        and not failures
    ):
        print("RESULT ATOMS VERIFIED")
    else:
        print("RESULT ATOMS NOT VERIFIED")
        raise SystemExit(1)

    print("=" * 72)


if __name__ == "__main__":
    main()
