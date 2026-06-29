from __future__ import annotations

from collections import Counter
from pathlib import Path
import json
from typing import Any


UNIVERSE_PATH = Path("data/baseball/raw/strat365/1980/players/1980_players_universe.json")
PROBABILITY_DIR = Path("data/baseball/parsed/strat365/1980/result-probabilities")

EXPECTED_SCHEMA_VERSION = "bie.result-probabilities.v0"
EXPECTED_ENTRIES = 47586
EXPECTED_OUTCOME_ROWS = 54748
EXPECTED_WARNINGS = 9
EXPECTED_STATUS_COUNTS = {
    "exact": 54739,
    "unresolved_open_split": 9,
}


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig", errors="replace"))


def main() -> None:
    universe = read_json(UNIVERSE_PATH)
    players = universe.get("players", [])
    expected_ids = {int(player["playerId"]): player for player in players}

    paths = list(PROBABILITY_DIR.glob("*.result-probabilities.json"))
    parsed_ids = {
        int(path.name.replace(".result-probabilities.json", "")): path
        for path in paths
    }

    missing = sorted(set(expected_ids) - set(parsed_ids))
    extra = sorted(set(parsed_ids) - set(expected_ids))

    role_counts: Counter[str] = Counter()
    status_counts: Counter[str] = Counter()
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
        expected_role = player.get("role")

        if role != expected_role:
            failures.append(f"{player_id}: role mismatch {role} != {expected_role}")

        role_counts[role] += 1
        total_warnings += len(data.get("warnings", []))

        tables = data.get("tables", [])
        if len(tables) != 6:
            failures.append(f"{player_id}: expected 6 tables, found {len(tables)}")

        for table in tables:
            entries = table.get("entries", [])
            if len(entries) != 11:
                failures.append(
                    f"{player_id}: table {table.get('tableNumber')} expected 11 entries, found {len(entries)}"
                )

            total_entries += len(entries)

            for entry in entries:
                dice_roll = entry.get("diceRoll")
                if dice_roll not in range(2, 13):
                    failures.append(f"{player_id}: invalid diceRoll={dice_roll}")

                for outcome in entry.get("outcomes", []):
                    total_outcome_rows += 1

                    probability = outcome.get("resultProbability", {})
                    status = probability.get("probabilityStatus")
                    status_counts[status] += 1

                    if not probability.get("columnWeight"):
                        failures.append(f"{player_id}: missing columnWeight")

                    if not probability.get("dice2d6Weight"):
                        failures.append(f"{player_id}: missing dice2d6Weight")

                    if not probability.get("cellWeightBeforeSplit"):
                        failures.append(f"{player_id}: missing cellWeightBeforeSplit")

                    if not probability.get("splitWeight"):
                        failures.append(f"{player_id}: missing splitWeight")

                    if status == "exact" and probability.get("finalWeight") is None:
                        failures.append(f"{player_id}: exact outcome missing finalWeight")

                    if status == "unresolved_open_split" and probability.get("finalWeight") is not None:
                        failures.append(f"{player_id}: unresolved open split should not have finalWeight")

    print("BIE Result Probability Verification")
    print("=" * 72)
    print(f"Universe players: {len(expected_ids)}")
    print(f"Parsed files: {len(parsed_ids)}")
    print(f"Missing parsed files: {len(missing)}")
    print(f"Extra parsed files: {len(extra)}")
    print(f"Role counts: {dict(role_counts)}")
    print(f"Total entries: {total_entries}")
    print(f"Total outcome rows: {total_outcome_rows}")
    print(f"Total warnings: {total_warnings}")
    print(f"Probability status counts: {dict(status_counts)}")
    print(f"Failures: {len(failures)}")

    if failures:
        print()
        print("Failure examples:")
        for failure in failures[:50]:
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
        and total_warnings == EXPECTED_WARNINGS
        and dict(status_counts) == EXPECTED_STATUS_COUNTS
        and not failures
    ):
        print("RESULT PROBABILITIES VERIFIED")
    else:
        print("RESULT PROBABILITIES NOT VERIFIED")
        raise SystemExit(1)

    print("=" * 72)


if __name__ == "__main__":
    main()
