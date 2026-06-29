from __future__ import annotations

from fractions import Fraction
from pathlib import Path
import json
from typing import Any


SIGNAL_PATH = Path("data/baseball/parsed/strat365/1980/draft-signals/1980.defensive-draft-signals.json")

EXPECTED_SCHEMA_VERSION = "bie.defensive-draft-signals.v0"
EXPECTED_HITTERS = 442
EXPECTED_PITCHERS = 279
EXPECTED_HITTER_POSITION_ROWS = 918
EXPECTED_DEFENSE_UNAVAILABLE = 2


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig", errors="replace"))


def frac(payload: dict[str, Any] | None) -> Fraction:
    if not payload:
        raise ValueError("missing fraction payload")
    return Fraction(payload["numerator"], payload["denominator"])


def score_frac(payload: dict[str, Any] | None) -> Fraction:
    if not payload:
        raise ValueError("missing score payload")
    return frac(payload.get("scoreFraction"))


def assert_score_range(label: str, value: Fraction, failures: list[str]) -> None:
    if value < 0 or value > 100:
        failures.append(f"{label}: score out of range {value}")


def verify_sorted(rows: list[dict[str, Any]], label: str, failures: list[str]) -> None:
    previous: Fraction | None = None

    for row in rows:
        if label == "hitter":
            best = row.get("bestPosition")
            current = score_frac(best["defensiveScore"]) if best else Fraction(-1, 1)
        else:
            current = score_frac(row.get("defensiveScore"))

        if previous is not None and current > previous:
            failures.append(f"{label}: rows not sorted descending")

        previous = current


def main() -> None:
    data = read_json(SIGNAL_PATH)

    hitters = data.get("hitters", [])
    pitchers = data.get("pitchers", [])
    counts = data.get("counts", {})

    failures: list[str] = []

    if data.get("schemaVersion") != EXPECTED_SCHEMA_VERSION:
        failures.append("schemaVersion mismatch")

    if len(hitters) != EXPECTED_HITTERS:
        failures.append(f"hitters expected {EXPECTED_HITTERS}, got {len(hitters)}")

    if len(pitchers) != EXPECTED_PITCHERS:
        failures.append(f"pitchers expected {EXPECTED_PITCHERS}, got {len(pitchers)}")

    hitter_position_rows = sum(len(row.get("positions", [])) for row in hitters)
    defense_unavailable = sum(1 for row in hitters if row.get("defenseUnavailable") is True)

    if hitter_position_rows != EXPECTED_HITTER_POSITION_ROWS:
        failures.append(f"hitter position rows expected {EXPECTED_HITTER_POSITION_ROWS}, got {hitter_position_rows}")

    if defense_unavailable != EXPECTED_DEFENSE_UNAVAILABLE:
        failures.append(f"defense unavailable expected {EXPECTED_DEFENSE_UNAVAILABLE}, got {defense_unavailable}")

    if counts.get("hitters") != EXPECTED_HITTERS:
        failures.append("counts.hitters mismatch")

    if counts.get("pitchers") != EXPECTED_PITCHERS:
        failures.append("counts.pitchers mismatch")

    if counts.get("hitterDefenseUnavailable") != EXPECTED_DEFENSE_UNAVAILABLE:
        failures.append("counts.hitterDefenseUnavailable mismatch")

    verify_sorted(hitters, "hitter", failures)
    verify_sorted(pitchers, "pitcher", failures)

    for row in hitters:
        player = row.get("player", {})
        label = f'hitter {player.get("playerName")} id={player.get("playerId")}'

        if row.get("role") != "hitter":
            failures.append(f"{label}: role mismatch")

        positions = row.get("positions", [])
        best = row.get("bestPosition")

        if row.get("defenseUnavailable") is True:
            if positions:
                failures.append(f"{label}: defense unavailable but has positions")
            if best is not None:
                failures.append(f"{label}: defense unavailable but has bestPosition")
            continue

        if not positions:
            failures.append(f"{label}: missing positions")
            continue

        if not best:
            failures.append(f"{label}: missing bestPosition")
            continue

        if row.get("positionCount") != len(positions):
            failures.append(f"{label}: positionCount mismatch")

        best_score = score_frac(best["defensiveScore"])
        assert_score_range(f"{label} bestPosition", best_score, failures)

        for position in positions:
            position_label = f'{label} {position.get("raw")}'

            for key in ("rangeScore", "errorScore", "defensiveScore"):
                assert_score_range(position_label + f" {key}", score_frac(position[key]), failures)

            if position.get("armScore") is not None:
                assert_score_range(position_label + " armScore", score_frac(position["armScore"]), failures)

    for row in pitchers:
        player = row.get("player", {})
        label = f'pitcher {player.get("playerName")} id={player.get("playerId")}'

        if row.get("role") != "pitcher":
            failures.append(f"{label}: role mismatch")

        raw = row.get("raw", {})
        for key in ("balk", "wildPitch", "error", "pitcherDefense", "hold"):
            if not isinstance(raw.get(key), int):
                failures.append(f"{label}: raw {key} invalid")

        for key in ("pitcherDefenseScore", "holdScore", "wildPitchScore", "balkScore", "defensiveScore"):
            assert_score_range(label + f" {key}", score_frac(row[key]), failures)

        expected = (
            score_frac(row["pitcherDefenseScore"]) * Fraction(45, 100)
            + score_frac(row["holdScore"]) * Fraction(30, 100)
            + score_frac(row["wildPitchScore"]) * Fraction(15, 100)
            + score_frac(row["balkScore"]) * Fraction(10, 100)
        )

        actual = score_frac(row["defensiveScore"])

        if actual != expected:
            failures.append(f"{label}: defensiveScore formula mismatch")

    print("BIE Defensive Draft Signal Verification")
    print("=" * 80)
    print(f"Schema version: {data.get('schemaVersion')}")
    print(f"Hitters: {len(hitters)}")
    print(f"Pitchers: {len(pitchers)}")
    print(f"Hitter position rows: {hitter_position_rows}")
    print(f"Hitter defense unavailable: {defense_unavailable}")
    print(f"Top hitter: {hitters[0]['player']['playerName'] if hitters else '(none)'}")
    print(f"Top pitcher: {pitchers[0]['player']['playerName'] if pitchers else '(none)'}")
    print(f"Failures: {len(failures)}")

    if failures:
        print()
        print("Failure examples:")
        for failure in failures[:50]:
            print(failure)
        print("-" * 80)
        print("DEFENSIVE DRAFT SIGNALS NOT VERIFIED")
        raise SystemExit(1)

    print("-" * 80)
    print("DEFENSIVE DRAFT SIGNALS VERIFIED")
    print("=" * 80)


if __name__ == "__main__":
    main()
