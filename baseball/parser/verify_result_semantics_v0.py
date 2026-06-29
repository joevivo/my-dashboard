from __future__ import annotations

from collections import Counter
from pathlib import Path
import json
from typing import Any


UNIVERSE_PATH = Path("data/baseball/raw/strat365/1980/players/1980_players_universe.json")
SEMANTICS_DIR = Path("data/baseball/parsed/strat365/1980/result-semantics")

EXPECTED_SCHEMA_VERSION = "bie.result-semantics.v0"
EXPECTED_ENTRIES = 47586
EXPECTED_OUTCOME_ROWS = 54748
EXPECTED_MAPPED_ROWS = 54748

EXPECTED_DEPENDENCIES = {
    "base_out_state": 12839,
    "split_roll_d20": 12609,
    "split_roll_closed_range": 12600,
    "runner_advancement_state": 7018,
    "legacy_baserunning_marker": 5977,
    "defensive_x_chart": 5862,
    "flyball_runner_third_may_attempt_score": 2919,
    "ballpark_single_check": 2734,
    "ballpark_home_run_check": 2173,
    "contextual_plus_marker": 2128,
    "clutch_context_reversal": 1403,
    "pitcher_fatigue_marker_ignored_in_365": 1253,
    "injury_check": 862,
    "catcher_defensive_chart": 558,
    "split_roll_open_high_range": 9,
}


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig", errors="replace"))


def main() -> None:
    universe = read_json(UNIVERSE_PATH)
    players = universe.get("players", [])
    expected_ids = {int(player["playerId"]): player for player in players}

    paths = list(SEMANTICS_DIR.glob("*.result-semantics.json"))
    parsed_ids = {
        int(path.name.replace(".result-semantics.json", "")): path
        for path in paths
    }

    missing = sorted(set(expected_ids) - set(parsed_ids))
    extra = sorted(set(parsed_ids) - set(expected_ids))

    role_counts: Counter[str] = Counter()
    status_counts: Counter[str] = Counter()
    dependency_counts: Counter[str] = Counter()

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
                    f"{player_id}: table {table.get('tableNumber')} expected 11 entries, found {len(entries)}"
                )

            total_entries += len(entries)

            for entry in entries:
                for outcome in entry.get("outcomes", []):
                    total_outcome_rows += 1

                    semantics = outcome.get("resultSemantics", {})
                    status = semantics.get("semanticStatus")
                    status_counts[status] += 1

                    if status != "mapped":
                        failures.append(
                            f"{player_id}: table {table.get('tableNumber')} dice {entry.get('diceRoll')} semanticStatus={status}"
                        )

                    if not semantics.get("atomKey"):
                        failures.append(
                            f"{player_id}: table {table.get('tableNumber')} dice {entry.get('diceRoll')} missing atomKey"
                        )

                    if not semantics.get("baseOutcomeType"):
                        failures.append(
                            f"{player_id}: table {table.get('tableNumber')} dice {entry.get('diceRoll')} missing baseOutcomeType"
                        )

                    for dep in semantics.get("dependencies", []):
                        dependency_counts[dep] += 1

    print("BIE Result Semantics Verification")
    print("=" * 72)
    print(f"Universe players: {len(expected_ids)}")
    print(f"Parsed files: {len(parsed_ids)}")
    print(f"Missing parsed files: {len(missing)}")
    print(f"Extra parsed files: {len(extra)}")
    print(f"Role counts: {dict(role_counts)}")
    print(f"Total entries: {total_entries}")
    print(f"Total outcome rows: {total_outcome_rows}")
    print(f"Total warnings: {total_warnings}")
    print(f"Semantic status counts: {dict(status_counts)}")
    print(f"Dependency counts: {dict(dependency_counts)}")
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
        and total_warnings == 0
        and status_counts.get("mapped") == EXPECTED_MAPPED_ROWS
        and dict(dependency_counts) == EXPECTED_DEPENDENCIES
        and not failures
    ):
        print("RESULT SEMANTICS VERIFIED")
    else:
        print("RESULT SEMANTICS NOT VERIFIED")
        raise SystemExit(1)

    print("=" * 72)


if __name__ == "__main__":
    main()
