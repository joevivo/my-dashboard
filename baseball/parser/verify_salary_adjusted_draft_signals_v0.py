from __future__ import annotations

from fractions import Fraction
from pathlib import Path
import json
from typing import Any


SIGNAL_PATH = Path("data/baseball/parsed/strat365/1980/draft-signals/1980.salary-adjusted-draft-signals.json")

EXPECTED_SCHEMA_VERSION = "bie.salary-adjusted-draft-signals.v0"
EXPECTED_RANKABLE_HITTERS = 440
EXPECTED_UNRESOLVED_HITTERS = 2
EXPECTED_RANKABLE_PITCHERS = 279
EXPECTED_UNRESOLVED_PITCHERS = 0


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig", errors="replace"))


def frac(payload: dict[str, Any] | None) -> Fraction:
    if not payload:
        raise ValueError("missing fraction payload")

    numerator = payload.get("numerator")
    denominator = payload.get("denominator")

    if not isinstance(numerator, int) or not isinstance(denominator, int):
        raise ValueError(f"invalid fraction payload: {payload}")

    return Fraction(numerator, denominator)


def score_frac(payload: dict[str, Any] | None) -> Fraction:
    if not payload:
        raise ValueError("missing score payload")
    return frac(payload.get("scoreFraction"))


def salary_millions(row: dict[str, Any]) -> Fraction:
    return frac(row.get("salary", {}).get("millions"))


def verify_ranked_rows(rows: list[dict[str, Any]], role: str, failures: list[str]) -> None:
    previous_score: Fraction | None = None

    for expected_rank, row in enumerate(rows, start=1):
        player = row.get("player", {})
        label = f'{role} rank={expected_rank} playerId={player.get("playerId")} name={player.get("playerName")}'

        if row.get("role") != role:
            failures.append(f"{label}: role mismatch")

        if row.get("rankable") is not True:
            failures.append(f"{label}: rankable is not true")

        if row.get("salaryAdjustedRank") != expected_rank:
            failures.append(f"{label}: salaryAdjustedRank mismatch")

        if row.get("exactMatchups", 0) <= 0:
            failures.append(f"{label}: exactMatchups <= 0")

        salary = salary_millions(row)
        neutral = score_frac(row.get("neutralDraftScore"))
        signal_per_million = frac(row.get("salaryValue", {}).get("signalPerMillion"))
        value_percentile = score_frac(row.get("salaryValue", {}).get("valuePercentile"))
        balanced = score_frac(row.get("salaryValue", {}).get("balancedValueScore"))

        if salary <= 0:
            failures.append(f"{label}: non-positive salary")

        if neutral < 0 or neutral > 100:
            failures.append(f"{label}: neutral score out of range")

        if value_percentile < 0 or value_percentile > 100:
            failures.append(f"{label}: value percentile out of range")

        if balanced < 0 or balanced > 100:
            failures.append(f"{label}: balanced score out of range")

        if signal_per_million != neutral / salary:
            failures.append(f"{label}: signalPerMillion mismatch")

        expected_balanced = neutral * Fraction(70, 100) + value_percentile * Fraction(30, 100)

        if balanced != expected_balanced:
            failures.append(f"{label}: balanced score mismatch")

        if previous_score is not None and balanced > previous_score:
            failures.append(f"{label}: balanced scores are not sorted descending")

        previous_score = balanced

        if role == "hitter" and not row.get("hitter", {}).get("primaryPosition"):
            failures.append(f"{label}: missing hitter primary position")

        if role == "pitcher" and not row.get("pitcher", {}).get("pitchingRole"):
            failures.append(f"{label}: missing pitcher role")


def verify_unresolved(rows: list[dict[str, Any]], role: str, failures: list[str]) -> None:
    for row in rows:
        player = row.get("player", {})
        label = f'unresolved {role} playerId={player.get("playerId")} name={player.get("playerName")}'

        if row.get("role") != role:
            failures.append(f"{label}: role mismatch")

        if row.get("rankable") is not False:
            failures.append(f"{label}: rankable is not false")

        if row.get("exactMatchups") != 0:
            failures.append(f"{label}: exactMatchups is not zero")

        if row.get("partialMatchups", 0) <= 0:
            failures.append(f"{label}: partialMatchups <= 0")

        if salary_millions(row) <= 0:
            failures.append(f"{label}: non-positive salary")


def main() -> None:
    data = read_json(SIGNAL_PATH)

    failures: list[str] = []

    hitters = data.get("hitters", [])
    pitchers = data.get("pitchers", [])
    unresolved_hitters = data.get("unresolved", {}).get("hitters", [])
    unresolved_pitchers = data.get("unresolved", {}).get("pitchers", [])
    counts = data.get("counts", {})

    verify_ranked_rows(hitters, "hitter", failures)
    verify_ranked_rows(pitchers, "pitcher", failures)
    verify_unresolved(unresolved_hitters, "hitter", failures)
    verify_unresolved(unresolved_pitchers, "pitcher", failures)

    print("BIE Salary-Adjusted Draft Signal Verification")
    print("=" * 72)
    print(f"Schema version: {data.get('schemaVersion')}")
    print(f"Rankable hitters: {len(hitters)}")
    print(f"Unresolved hitters: {len(unresolved_hitters)}")
    print(f"Rankable pitchers: {len(pitchers)}")
    print(f"Unresolved pitchers: {len(unresolved_pitchers)}")
    print(f"Top hitter: {hitters[0]['player']['playerName'] if hitters else '(none)'}")
    print(f"Top pitcher: {pitchers[0]['player']['playerName'] if pitchers else '(none)'}")
    print(f"Failures: {len(failures)}")

    if failures:
        print()
        print("Failure examples:")
        for failure in failures[:50]:
            print(failure)

    print("-" * 72)

    if (
        data.get("schemaVersion") == EXPECTED_SCHEMA_VERSION
        and counts.get("rankableHitters") == EXPECTED_RANKABLE_HITTERS
        and counts.get("unresolvedHitters") == EXPECTED_UNRESOLVED_HITTERS
        and counts.get("rankablePitchers") == EXPECTED_RANKABLE_PITCHERS
        and counts.get("unresolvedPitchers") == EXPECTED_UNRESOLVED_PITCHERS
        and len(hitters) == EXPECTED_RANKABLE_HITTERS
        and len(unresolved_hitters) == EXPECTED_UNRESOLVED_HITTERS
        and len(pitchers) == EXPECTED_RANKABLE_PITCHERS
        and len(unresolved_pitchers) == EXPECTED_UNRESOLVED_PITCHERS
        and not failures
    ):
        print("SALARY-ADJUSTED DRAFT SIGNALS VERIFIED")
    else:
        print("SALARY-ADJUSTED DRAFT SIGNALS NOT VERIFIED")
        raise SystemExit(1)

    print("=" * 72)


if __name__ == "__main__":
    main()
