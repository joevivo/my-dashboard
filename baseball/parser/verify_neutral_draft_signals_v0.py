from __future__ import annotations

from fractions import Fraction
from pathlib import Path
import json
from typing import Any


SIGNAL_PATH = Path("data/baseball/parsed/strat365/1980/draft-signals/1980.neutral-draft-signals.json")

EXPECTED_SCHEMA_VERSION = "bie.neutral-draft-signals.v0"
EXPECTED_RANKABLE_HITTERS = 440
EXPECTED_UNRESOLVED_HITTERS = 2
EXPECTED_RANKABLE_PITCHERS = 279
EXPECTED_UNRESOLVED_PITCHERS = 0

HITTER_WEIGHTS = {
    "on_base": Fraction(40, 100),
    "hit": Fraction(25, 100),
    "power": Fraction(20, 100),
    "contact": Fraction(15, 100),
}

PITCHER_WEIGHTS = {
    "on_base_prevention": Fraction(35, 100),
    "hit_prevention": Fraction(25, 100),
    "home_run_prevention": Fraction(20, 100),
    "strikeout": Fraction(20, 100),
}

SOURCE_AVERAGE_KEYS = {
    "onBaseCandidateWeight",
    "hitCandidateWeight",
    "outCandidateWeight",
    "homeRunWeight",
    "strikeoutWeight",
}


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


def verify_ranked_signals(
    rows: list[dict[str, Any]],
    role: str,
    expected_component_keys: set[str],
    weights: dict[str, Fraction],
    failures: list[str],
) -> None:
    previous_score: Fraction | None = None

    for index, row in enumerate(rows, start=1):
        player = row.get("player", {})
        label = f"{role} rank={index} playerId={player.get('playerId')} name={player.get('playerName')}"

        if row.get("role") != role:
            failures.append(f"{label}: role mismatch")

        if row.get("rankable") is not True:
            failures.append(f"{label}: rankable is not true")

        if row.get("exactMatchups", 0) <= 0:
            failures.append(f"{label}: exactMatchups <= 0")

        score = score_frac(row.get("draftScore"))

        if score < 0 or score > 100:
            failures.append(f"{label}: draft score out of range {score}")

        if previous_score is not None and score > previous_score:
            failures.append(f"{label}: draft scores are not sorted descending")

        previous_score = score

        components = row.get("componentScores", {})
        component_keys = set(components.keys())

        if component_keys != expected_component_keys:
            failures.append(f"{label}: component keys mismatch {component_keys}")

        recomputed = Fraction(0, 1)

        for key, weight in weights.items():
            component_score = score_frac(components.get(key))

            if component_score < 0 or component_score > 100:
                failures.append(f"{label}: component score out of range {key}={component_score}")

            recomputed += component_score * weight

        if recomputed != score:
            failures.append(f"{label}: draft score does not match weighted components")

        source_keys = set(row.get("sourceAverages", {}).keys())

        if source_keys != SOURCE_AVERAGE_KEYS:
            failures.append(f"{label}: source average keys mismatch {source_keys}")

        for key, value in row.get("sourceAverages", {}).items():
            source_average = frac(value)
            if source_average < 0 or source_average > 1:
                failures.append(f"{label}: source average out of range {key}={source_average}")


def verify_unresolved(rows: list[dict[str, Any]], role: str, failures: list[str]) -> None:
    for row in rows:
        player = row.get("player", {})
        label = f"unresolved {role} playerId={player.get('playerId')} name={player.get('playerName')}"

        if row.get("role") != role:
            failures.append(f"{label}: role mismatch")

        if row.get("rankable") is not False:
            failures.append(f"{label}: rankable is not false")

        if row.get("exactMatchups") != 0:
            failures.append(f"{label}: exactMatchups is not zero")

        if row.get("partialMatchups", 0) <= 0:
            failures.append(f"{label}: partialMatchups <= 0")


def main() -> None:
    data = read_json(SIGNAL_PATH)

    failures: list[str] = []

    hitters = data.get("hitters", [])
    pitchers = data.get("pitchers", [])
    unresolved_hitters = data.get("unresolved", {}).get("hitters", [])
    unresolved_pitchers = data.get("unresolved", {}).get("pitchers", [])
    counts = data.get("counts", {})

    verify_ranked_signals(
        hitters,
        "hitter",
        set(HITTER_WEIGHTS.keys()),
        HITTER_WEIGHTS,
        failures,
    )

    verify_ranked_signals(
        pitchers,
        "pitcher",
        set(PITCHER_WEIGHTS.keys()),
        PITCHER_WEIGHTS,
        failures,
    )

    verify_unresolved(unresolved_hitters, "hitter", failures)
    verify_unresolved(unresolved_pitchers, "pitcher", failures)

    print("BIE Neutral Draft Signal Verification")
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
        print("NEUTRAL DRAFT SIGNALS VERIFIED")
    else:
        print("NEUTRAL DRAFT SIGNALS NOT VERIFIED")
        raise SystemExit(1)

    print("=" * 72)


if __name__ == "__main__":
    main()
