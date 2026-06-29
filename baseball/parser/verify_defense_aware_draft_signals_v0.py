from __future__ import annotations

from fractions import Fraction
from pathlib import Path
import json
from typing import Any

PATH = Path("data/baseball/parsed/strat365/1980/draft-signals/1980.defense-aware-draft-signals.json")
SCHEMA = "bie.defense-aware-draft-signals.v0"


def sf(payload: dict[str, Any]) -> Fraction:
    frac = payload["scoreFraction"]
    return Fraction(frac["numerator"], frac["denominator"])


def fail(message: str) -> None:
    raise AssertionError(message)


def verify_sorted(rows: list[dict[str, Any]], label: str) -> None:
    previous = None
    for index, row in enumerate(rows, start=1):
        if row.get("defenseAwareRank") != index:
            fail(f"{label} rank mismatch at {index}")
        current = sf(row["defenseAwareDraftScore"])
        if previous is not None and current > previous:
            fail(f"{label} not sorted at {index}")
        previous = current


def verify_formula(rows: list[dict[str, Any]], role: str) -> None:
    for row in rows:
        salary = sf(row["salaryAdjustedScore"])
        defense = sf(row["defensiveScore"])
        actual = sf(row["defenseAwareDraftScore"])

        if role == "hitter":
            expected = salary * Fraction(75, 100) + defense * Fraction(25, 100)
        else:
            expected = salary * Fraction(85, 100) + defense * Fraction(15, 100)

        if actual != expected:
            fail(f"{role} formula mismatch: {row['player']['playerName']}")

        for key in ("salaryAdjustedScore", "defensiveScore", "defenseAwareDraftScore"):
            value = sf(row[key])
            if value < 0 or value > 100:
                fail(f"{role} score out of range: {row['player']['playerName']} {key}")

        if row.get("defenseNeutralized") is True and defense != 50:
            fail(f"{role} neutral defense not 50: {row['player']['playerName']}")


def main() -> None:
    data = json.loads(PATH.read_text(encoding="utf-8-sig", errors="replace"))

    hitters = data["hitters"]
    pitchers = data["pitchers"]
    unresolved_hitters = data["unresolved"]["hitters"]
    unresolved_pitchers = data["unresolved"]["pitchers"]
    counts = data["counts"]

    if data.get("schemaVersion") != SCHEMA:
        fail("schema mismatch")

    if len(hitters) != 440:
        fail("rankable hitter count mismatch")
    if len(unresolved_hitters) != 2:
        fail("unresolved hitter count mismatch")
    if len(pitchers) != 279:
        fail("rankable pitcher count mismatch")
    if len(unresolved_pitchers) != 0:
        fail("unresolved pitcher count mismatch")

    if counts.get("rankableHitters") != 440:
        fail("counts.rankableHitters mismatch")
    if counts.get("unresolvedHitters") != 2:
        fail("counts.unresolvedHitters mismatch")
    if counts.get("rankablePitchers") != 279:
        fail("counts.rankablePitchers mismatch")
    if counts.get("unresolvedPitchers") != 0:
        fail("counts.unresolvedPitchers mismatch")
    if counts.get("defenseNeutralizedHitters") != 2:
        fail("defenseNeutralizedHitters mismatch")
    if counts.get("defenseNeutralizedPitchers") != 0:
        fail("defenseNeutralizedPitchers mismatch")

    verify_sorted(hitters, "hitters")
    verify_sorted(pitchers, "pitchers")
    verify_formula(hitters, "hitter")
    verify_formula(pitchers, "pitcher")

    print("BIE Defense-Aware Draft Signal Verification")
    print("=" * 80)
    print(f"Schema version: {data.get('schemaVersion')}")
    print(f"Rankable hitters: {len(hitters)}")
    print(f"Unresolved hitters: {len(unresolved_hitters)}")
    print(f"Rankable pitchers: {len(pitchers)}")
    print(f"Unresolved pitchers: {len(unresolved_pitchers)}")
    print(f"Top hitter: {hitters[0]['player']['playerName']}")
    print(f"Top pitcher: {pitchers[0]['player']['playerName']}")
    print("-" * 80)
    print("DEFENSE-AWARE DRAFT SIGNALS VERIFIED")
    print("=" * 80)


if __name__ == "__main__":
    main()
