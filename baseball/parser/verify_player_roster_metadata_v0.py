from __future__ import annotations

from fractions import Fraction
from pathlib import Path
import json
from typing import Any


METADATA_PATH = Path("data/baseball/parsed/strat365/1980/player-roster-metadata/1980.player-roster-metadata.json")

EXPECTED_SCHEMA_VERSION = "bie.player-roster-metadata.v0"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig", errors="replace"))


def frac(payload: dict[str, Any] | None) -> Fraction:
    if not payload:
        raise ValueError("missing salary millions payload")

    numerator = payload.get("numerator")
    denominator = payload.get("denominator")

    if not isinstance(numerator, int) or not isinstance(denominator, int):
        raise ValueError(f"invalid fraction payload: {payload}")

    return Fraction(numerator, denominator)


def main() -> None:
    data = read_json(METADATA_PATH)

    players = data.get("players", [])
    hitters = [player for player in players if player.get("role") == "hitter"]
    pitchers = [player for player in players if player.get("role") == "pitcher"]

    failures: list[str] = []

    player_ids = set()

    for player in players:
        player_id = player.get("playerId")
        player_name = player.get("playerName")
        role = player.get("role")
        label = f"{player_id} {player_name}"

        if player_id in player_ids:
            failures.append(f"{label}: duplicate playerId")
        player_ids.add(player_id)

        salary = player.get("salary")

        if not salary:
            failures.append(f"{label}: missing salary")
            continue

        raw_salary = salary.get("raw", "")
        millions = frac(salary.get("millions"))
        dollars = salary.get("dollars")

        if not raw_salary.endswith("M"):
            failures.append(f"{label}: invalid raw salary {raw_salary}")

        if millions <= 0:
            failures.append(f"{label}: non-positive salary {millions}")

        if dollars != int(millions * 1_000_000):
            failures.append(f"{label}: dollar conversion mismatch")

        if role == "hitter":
            hitter = player.get("hitter", {})
            if hitter.get("bats") not in {"L", "R", "S"}:
                failures.append(f"{label}: invalid hitter bats")
            if not hitter.get("primaryPosition"):
                failures.append(f"{label}: missing primary position")

        elif role == "pitcher":
            pitcher = player.get("pitcher", {})
            if pitcher.get("throws") not in {"L", "R"}:
                failures.append(f"{label}: invalid pitcher throws")
            if not pitcher.get("pitchingRole"):
                failures.append(f"{label}: missing pitching role")

        else:
            failures.append(f"{label}: invalid role {role}")

    counts = data.get("counts", {})

    print("BIE Player Roster Metadata Verification")
    print("=" * 72)
    print(f"Schema version: {data.get('schemaVersion')}")
    print(f"Players: {len(players)}")
    print(f"Hitters: {len(hitters)}")
    print(f"Pitchers: {len(pitchers)}")
    print(f"Salary parsed: {counts.get('salaryParsed')}")
    print(f"Salary missing: {counts.get('salaryMissing')}")
    print(f"Warnings: {len(data.get('warnings', []))}")
    print(f"Failures: {len(failures)}")

    if failures:
        print()
        print("Failure examples:")
        for failure in failures[:50]:
            print(failure)

    print("-" * 72)

    if (
        data.get("schemaVersion") == EXPECTED_SCHEMA_VERSION
        and len(players) == 721
        and len(hitters) == 442
        and len(pitchers) == 279
        and counts.get("players") == 721
        and counts.get("hitters") == 442
        and counts.get("pitchers") == 279
        and counts.get("salaryParsed") == 721
        and counts.get("salaryMissing") == 0
        and not data.get("warnings")
        and not failures
    ):
        print("PLAYER ROSTER METADATA VERIFIED")
    else:
        print("PLAYER ROSTER METADATA NOT VERIFIED")
        raise SystemExit(1)

    print("=" * 72)


if __name__ == "__main__":
    main()
