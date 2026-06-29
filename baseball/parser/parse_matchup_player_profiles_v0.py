from __future__ import annotations

from collections import defaultdict
from fractions import Fraction
from pathlib import Path
import json
from typing import Any


MATCHUP_PATH = Path("data/baseball/parsed/strat365/1980/matchup-probabilities/1980.matchup-probabilities.jsonl")
OUTPUT_DIR = Path("data/baseball/parsed/strat365/1980/matchup-player-profiles")
OUTPUT_PATH = OUTPUT_DIR / "1980.matchup-player-profiles.json"

SCHEMA_VERSION = "bie.matchup-player-profiles.v0"
PARSER_VERSION = "bie-matchup-player-profile-parser-v0.1"

METRICS = [
    "onBaseCandidateWeight",
    "hitCandidateWeight",
    "outCandidateWeight",
]


OUTCOMES = [
    "SINGLE",
    "DOUBLE",
    "TRIPLE",
    "HOME_RUN",
    "WALK",
    "HBP",
    "STRIKEOUT",
    "GROUNDBALL",
    "FLYBALL",
    "GROUNDBALL_X",
    "FLYBALL_X",
    "CATCHER_X",
]


def frac(payload: dict[str, Any] | None) -> Fraction:
    if not payload:
        return Fraction(0, 1)
    return Fraction(payload["numerator"], payload["denominator"])


def fraction_payload(value: Fraction) -> dict[str, Any]:
    return {
        "numerator": value.numerator,
        "denominator": value.denominator,
        "decimal": round(float(value), 12),
    }


def blank_profile(player: dict[str, Any], role: str) -> dict[str, Any]:
    return {
        "player": {
            "playerId": player.get("playerId"),
            "playerName": player.get("playerName"),
            "team": player.get("team"),
        },
        "role": role,
        "exactMatchups": 0,
        "partialMatchups": 0,
        "totals": defaultdict(Fraction),
        "outcomeTotals": defaultdict(Fraction),
    }


def add_profile_row(profile: dict[str, Any], row: dict[str, Any]) -> None:
    if row.get("probabilityStatus") != "exact":
        profile["partialMatchups"] += 1
        return

    profile["exactMatchups"] += 1

    weights = row.get("weights", {})

    for metric in METRICS:
        profile["totals"][metric] += frac(weights.get(metric))

    outcomes = weights.get("baseOutcomeWeights", {})

    for outcome in OUTCOMES:
        profile["outcomeTotals"][outcome] += frac(outcomes.get(outcome))


def render_profile(profile: dict[str, Any]) -> dict[str, Any]:
    exact = profile["exactMatchups"]

    averages = {}
    outcome_averages = {}

    for metric in METRICS:
        value = profile["totals"].get(metric, Fraction(0, 1))
        averages[metric] = fraction_payload(value / exact) if exact else fraction_payload(Fraction(0, 1))

    for outcome in OUTCOMES:
        value = profile["outcomeTotals"].get(outcome, Fraction(0, 1))
        outcome_averages[outcome] = fraction_payload(value / exact) if exact else fraction_payload(Fraction(0, 1))

    return {
        "player": profile["player"],
        "role": profile["role"],
        "exactMatchups": exact,
        "partialMatchups": profile["partialMatchups"],
        "averages": averages,
        "outcomeAverages": outcome_averages,
    }


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    hitter_profiles: dict[int, dict[str, Any]] = {}
    pitcher_profiles: dict[int, dict[str, Any]] = {}

    row_count = 0
    exact_rows = 0
    partial_rows = 0

    with MATCHUP_PATH.open("r", encoding="utf-8") as handle:
        for line in handle:
            row_count += 1
            row = json.loads(line)

            hitter = row["hitter"]
            pitcher = row["pitcher"]

            hitter_id = int(hitter["playerId"])
            pitcher_id = int(pitcher["playerId"])

            if hitter_id not in hitter_profiles:
                hitter_profiles[hitter_id] = blank_profile(hitter, "hitter")

            if pitcher_id not in pitcher_profiles:
                pitcher_profiles[pitcher_id] = blank_profile(pitcher, "pitcher")

            add_profile_row(hitter_profiles[hitter_id], row)
            add_profile_row(pitcher_profiles[pitcher_id], row)

            if row.get("probabilityStatus") == "exact":
                exact_rows += 1
            else:
                partial_rows += 1

    output = {
        "schemaVersion": SCHEMA_VERSION,
        "parserVersion": PARSER_VERSION,
        "season": 1980,
        "sourceFile": str(MATCHUP_PATH).replace("\\", "/"),
        "rowCount": row_count,
        "exactRows": exact_rows,
        "partialRows": partial_rows,
        "hitterProfiles": [
            render_profile(profile)
            for _player_id, profile in sorted(hitter_profiles.items())
        ],
        "pitcherProfiles": [
            render_profile(profile)
            for _player_id, profile in sorted(pitcher_profiles.items())
        ],
    }

    OUTPUT_PATH.write_text(json.dumps(output, indent=2), encoding="utf-8")

    print("BIE Matchup Player Profile Parser v0")
    print("=" * 72)
    print(f"Rows: {row_count}")
    print(f"Exact rows: {exact_rows}")
    print(f"Partial rows: {partial_rows}")
    print(f"Hitter profiles: {len(output['hitterProfiles'])}")
    print(f"Pitcher profiles: {len(output['pitcherProfiles'])}")
    print(f"Output: {OUTPUT_PATH}")
    print("=" * 72)

    if (
        row_count != 123318
        or exact_rows != 122011
        or partial_rows != 1307
        or len(output["hitterProfiles"]) != 442
        or len(output["pitcherProfiles"]) != 279
    ):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
