from __future__ import annotations

from fractions import Fraction
from pathlib import Path
import json
from typing import Any


PROFILE_PATH = Path("data/baseball/parsed/strat365/1980/matchup-player-profiles/1980.matchup-player-profiles.json")

EXPECTED_SCHEMA_VERSION = "bie.matchup-player-profiles.v0"
EXPECTED_ROWS = 123318
EXPECTED_EXACT_ROWS = 122011
EXPECTED_PARTIAL_ROWS = 1307
EXPECTED_HITTER_PROFILES = 442
EXPECTED_PITCHER_PROFILES = 279


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


def verify_profile(profile: dict[str, Any], failures: list[str]) -> None:
    player = profile.get("player", {})
    label = f'{profile.get("role")} {player.get("playerId")} {player.get("playerName")}'

    exact = profile.get("exactMatchups")
    partial = profile.get("partialMatchups")

    if not isinstance(exact, int) or exact < 0:
        failures.append(f"{label}: invalid exactMatchups={exact}")

    if not isinstance(partial, int) or partial < 0:
        failures.append(f"{label}: invalid partialMatchups={partial}")

    averages = profile.get("averages", {})

    on_base = frac(averages.get("onBaseCandidateWeight"))
    hit = frac(averages.get("hitCandidateWeight"))
    out = frac(averages.get("outCandidateWeight"))

    if hit > on_base:
        failures.append(f"{label}: hit average > on-base average")

    if on_base + out > 1:
        failures.append(f"{label}: on-base + out average > 1")

    if hit + out > 1:
        failures.append(f"{label}: hit + out average > 1")

    for section_name in ("averages", "outcomeAverages"):
        section = profile.get(section_name, {})
        for key, value in section.items():
            metric = frac(value)
            if metric < 0 or metric > 1:
                failures.append(f"{label}: {section_name}.{key} out of range: {metric}")


def main() -> None:
    data = read_json(PROFILE_PATH)

    failures: list[str] = []

    hitter_profiles = data.get("hitterProfiles", [])
    pitcher_profiles = data.get("pitcherProfiles", [])

    for profile in hitter_profiles:
        verify_profile(profile, failures)

    for profile in pitcher_profiles:
        verify_profile(profile, failures)

    hitter_exact = sum(profile.get("exactMatchups", 0) for profile in hitter_profiles)
    hitter_partial = sum(profile.get("partialMatchups", 0) for profile in hitter_profiles)
    pitcher_exact = sum(profile.get("exactMatchups", 0) for profile in pitcher_profiles)
    pitcher_partial = sum(profile.get("partialMatchups", 0) for profile in pitcher_profiles)

    print("BIE Matchup Player Profile Verification")
    print("=" * 72)
    print(f"Schema version: {data.get('schemaVersion')}")
    print(f"Rows: {data.get('rowCount')}")
    print(f"Exact rows: {data.get('exactRows')}")
    print(f"Partial rows: {data.get('partialRows')}")
    print(f"Hitter profiles: {len(hitter_profiles)}")
    print(f"Pitcher profiles: {len(pitcher_profiles)}")
    print(f"Hitter exact sum: {hitter_exact}")
    print(f"Hitter partial sum: {hitter_partial}")
    print(f"Pitcher exact sum: {pitcher_exact}")
    print(f"Pitcher partial sum: {pitcher_partial}")
    print(f"Failures: {len(failures)}")

    if failures:
        print()
        print("Failure examples:")
        for failure in failures[:50]:
            print(failure)

    print("-" * 72)

    if (
        data.get("schemaVersion") == EXPECTED_SCHEMA_VERSION
        and data.get("rowCount") == EXPECTED_ROWS
        and data.get("exactRows") == EXPECTED_EXACT_ROWS
        and data.get("partialRows") == EXPECTED_PARTIAL_ROWS
        and len(hitter_profiles) == EXPECTED_HITTER_PROFILES
        and len(pitcher_profiles) == EXPECTED_PITCHER_PROFILES
        and hitter_exact == EXPECTED_EXACT_ROWS
        and hitter_partial == EXPECTED_PARTIAL_ROWS
        and pitcher_exact == EXPECTED_EXACT_ROWS
        and pitcher_partial == EXPECTED_PARTIAL_ROWS
        and not failures
    ):
        print("MATCHUP PLAYER PROFILES VERIFIED")
    else:
        print("MATCHUP PLAYER PROFILES NOT VERIFIED")
        raise SystemExit(1)

    print("=" * 72)


if __name__ == "__main__":
    main()
