from __future__ import annotations

from pathlib import Path
import json
from typing import Any


DEFENSE_PATH = Path("data/baseball/parsed/strat365/1980/player-defense-metadata/1980.player-defense-metadata.json")

EXPECTED_SCHEMA_VERSION = "bie.player-defense-metadata.v0"
EXPECTED_PLAYERS = 721
EXPECTED_HITTERS = 442
EXPECTED_PITCHERS = 279
EXPECTED_HITTER_POSITION_ROWS = 918
EXPECTED_PITCHER_METADATA_ROWS = 279
EXPECTED_DH_DEFENSE_UNAVAILABLE = 2


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig", errors="replace"))


def main() -> None:
    data = read_json(DEFENSE_PATH)

    players = data.get("players", [])
    warnings = data.get("warnings", [])

    hitters = [row for row in players if row.get("role") == "hitter"]
    pitchers = [row for row in players if row.get("role") == "pitcher"]

    hitter_position_rows = sum(
        len(row.get("hitterDefense", {}).get("positions", []))
        for row in hitters
    )

    pitcher_metadata_rows = sum(
        1 for row in pitchers
        if "pitcherDefense" in row
    )

    dh_defense_unavailable = sum(
        1 for row in hitters
        if row.get("hitterDefense", {}).get("defenseUnavailable") is True
    )

    failures: list[str] = []

    if data.get("schemaVersion") != EXPECTED_SCHEMA_VERSION:
        failures.append("schemaVersion mismatch")

    if len(players) != EXPECTED_PLAYERS:
        failures.append(f"players expected {EXPECTED_PLAYERS}, got {len(players)}")

    if len(hitters) != EXPECTED_HITTERS:
        failures.append(f"hitters expected {EXPECTED_HITTERS}, got {len(hitters)}")

    if len(pitchers) != EXPECTED_PITCHERS:
        failures.append(f"pitchers expected {EXPECTED_PITCHERS}, got {len(pitchers)}")

    if hitter_position_rows != EXPECTED_HITTER_POSITION_ROWS:
        failures.append(f"hitter position rows expected {EXPECTED_HITTER_POSITION_ROWS}, got {hitter_position_rows}")

    if pitcher_metadata_rows != EXPECTED_PITCHER_METADATA_ROWS:
        failures.append(f"pitcher metadata rows expected {EXPECTED_PITCHER_METADATA_ROWS}, got {pitcher_metadata_rows}")

    if dh_defense_unavailable != EXPECTED_DH_DEFENSE_UNAVAILABLE:
        failures.append(f"DH unavailable rows expected {EXPECTED_DH_DEFENSE_UNAVAILABLE}, got {dh_defense_unavailable}")

    if warnings:
        failures.append(f"warnings expected 0, got {len(warnings)}")

    for row in hitters:
        label = f'{row.get("playerName")} id={row.get("playerId")}'
        defense = row.get("hitterDefense")

        if not defense:
            failures.append(f"{label}: missing hitterDefense")
            continue

        positions = defense.get("positions", [])
        unavailable = defense.get("defenseUnavailable") is True

        if not positions and not unavailable:
            failures.append(f"{label}: no positions and not defenseUnavailable")

        for position in positions:
            if position.get("position") not in {"1B", "2B", "3B", "SS", "LF", "CF", "RF", "C"}:
                failures.append(f"{label}: invalid position {position}")

            if not isinstance(position.get("range"), int):
                failures.append(f"{label}: invalid range {position}")

            if not isinstance(position.get("error"), int):
                failures.append(f"{label}: invalid error {position}")

    for row in pitchers:
        label = f'{row.get("playerName")} id={row.get("playerId")}'
        defense = row.get("pitcherDefense")

        if not defense:
            failures.append(f"{label}: missing pitcherDefense")
            continue

        for key in ("balk", "wildPitch", "error", "pitcherDefense", "hold"):
            if not isinstance(defense.get(key), int):
                failures.append(f"{label}: invalid pitcher field {key}={defense.get(key)}")

    print("BIE Player Defense Metadata Verification")
    print("=" * 80)
    print(f"Schema version: {data.get('schemaVersion')}")
    print(f"Players: {len(players)}")
    print(f"Hitters: {len(hitters)}")
    print(f"Pitchers: {len(pitchers)}")
    print(f"Hitter defensive position rows: {hitter_position_rows}")
    print(f"Pitcher metadata rows: {pitcher_metadata_rows}")
    print(f"DH defense unavailable rows: {dh_defense_unavailable}")
    print(f"Warnings: {len(warnings)}")
    print(f"Failures: {len(failures)}")

    if failures:
        print()
        print("Failure examples:")
        for failure in failures[:50]:
            print(failure)
        print("-" * 80)
        print("PLAYER DEFENSE METADATA NOT VERIFIED")
        raise SystemExit(1)

    print("-" * 80)
    print("PLAYER DEFENSE METADATA VERIFIED")
    print("=" * 80)


if __name__ == "__main__":
    main()
