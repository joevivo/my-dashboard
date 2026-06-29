from __future__ import annotations

from fractions import Fraction
from pathlib import Path
import json
from typing import Any


NEUTRAL_PATH = Path("data/baseball/parsed/strat365/1980/draft-signals/1980.neutral-draft-signals.json")
ROSTER_PATH = Path("data/baseball/parsed/strat365/1980/player-roster-metadata/1980.player-roster-metadata.json")
OUTPUT_DIR = Path("data/baseball/parsed/strat365/1980/draft-signals")
OUTPUT_PATH = OUTPUT_DIR / "1980.salary-adjusted-draft-signals.json"

SCHEMA_VERSION = "bie.salary-adjusted-draft-signals.v0"
PARSER_VERSION = "bie-salary-adjusted-draft-signal-parser-v0.1"


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


def score_payload(value: Fraction) -> dict[str, Any]:
    return {
        "score": round(float(value), 4),
        "scoreFraction": fraction_payload(value),
    }


def salary_millions(player_metadata: dict[str, Any]) -> Fraction:
    return frac(player_metadata.get("salary", {}).get("millions"))


def neutral_score(row: dict[str, Any]) -> Fraction:
    return frac(row.get("draftScore", {}).get("scoreFraction"))


def percentile_scores(values: list[tuple[int, Fraction]]) -> dict[int, Fraction]:
    n = len(values)

    if n <= 1:
        return {player_id: Fraction(50, 1) for player_id, _value in values}

    scores: dict[int, Fraction] = {}

    for player_id, value in values:
        better_or_equal = sum(1 for _other_id, other_value in values if other_value <= value)
        scores[player_id] = Fraction(100 * (better_or_equal - 1), n - 1)

    return scores


def enrich_rankable_rows(
    rows: list[dict[str, Any]],
    metadata_by_id: dict[int, dict[str, Any]],
    role: str,
) -> list[dict[str, Any]]:
    value_inputs: list[tuple[int, Fraction]] = []

    for row in rows:
        player_id = int(row["player"]["playerId"])
        metadata = metadata_by_id[player_id]
        salary = salary_millions(metadata)
        value_inputs.append((player_id, neutral_score(row) / salary))

    value_percentiles = percentile_scores(value_inputs)

    enriched: list[dict[str, Any]] = []

    for row in rows:
        player_id = int(row["player"]["playerId"])
        metadata = metadata_by_id[player_id]
        salary = salary_millions(metadata)
        base_score = neutral_score(row)
        signal_per_million = base_score / salary
        value_percentile = value_percentiles[player_id]

        balanced_value_score = (
            base_score * Fraction(70, 100)
            + value_percentile * Fraction(30, 100)
        )

        enriched_row = {
            "player": row["player"],
            "role": role,
            "rankable": True,
            "exactMatchups": row.get("exactMatchups"),
            "partialMatchups": row.get("partialMatchups"),
            "salary": metadata.get("salary"),
            "neutralDraftScore": row.get("draftScore"),
            "salaryValue": {
                "signalPerMillion": fraction_payload(signal_per_million),
                "valuePercentile": score_payload(value_percentile),
                "balancedValueScore": score_payload(balanced_value_score),
            },
            "componentScores": row.get("componentScores", {}),
            "sourceAverages": row.get("sourceAverages", {}),
        }

        if role == "hitter":
            enriched_row["hitter"] = metadata.get("hitter", {})

        if role == "pitcher":
            enriched_row["pitcher"] = metadata.get("pitcher", {})

        enriched.append(enriched_row)

    enriched.sort(
        key=lambda row: (
            row["salaryValue"]["balancedValueScore"]["score"],
            row["neutralDraftScore"]["score"],
            row["salaryValue"]["valuePercentile"]["score"],
        ),
        reverse=True,
    )

    for index, row in enumerate(enriched, start=1):
        row["salaryAdjustedRank"] = index

    return enriched


def enrich_unresolved_rows(
    rows: list[dict[str, Any]],
    metadata_by_id: dict[int, dict[str, Any]],
    role: str,
) -> list[dict[str, Any]]:
    enriched: list[dict[str, Any]] = []

    for row in rows:
        player_id = int(row["player"]["playerId"])
        metadata = metadata_by_id[player_id]

        enriched_row = dict(row)
        enriched_row["salary"] = metadata.get("salary")

        if role == "hitter":
            enriched_row["hitter"] = metadata.get("hitter", {})

        if role == "pitcher":
            enriched_row["pitcher"] = metadata.get("pitcher", {})

        enriched.append(enriched_row)

    return enriched


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    neutral = json.loads(NEUTRAL_PATH.read_text(encoding="utf-8-sig", errors="replace"))
    roster = json.loads(ROSTER_PATH.read_text(encoding="utf-8-sig", errors="replace"))

    metadata_by_id = {
        int(player["playerId"]): player
        for player in roster.get("players", [])
    }

    hitters = enrich_rankable_rows(neutral.get("hitters", []), metadata_by_id, "hitter")
    pitchers = enrich_rankable_rows(neutral.get("pitchers", []), metadata_by_id, "pitcher")

    unresolved_hitters = enrich_unresolved_rows(
        neutral.get("unresolved", {}).get("hitters", []),
        metadata_by_id,
        "hitter",
    )
    unresolved_pitchers = enrich_unresolved_rows(
        neutral.get("unresolved", {}).get("pitchers", []),
        metadata_by_id,
        "pitcher",
    )

    output = {
        "schemaVersion": SCHEMA_VERSION,
        "parserVersion": PARSER_VERSION,
        "season": 1980,
        "sourceFiles": {
            "neutralDraftSignals": str(NEUTRAL_PATH).replace("\\", "/"),
            "playerRosterMetadata": str(ROSTER_PATH).replace("\\", "/"),
        },
        "model": {
            "name": "salary_adjusted_draft_signal_v0",
            "balancedValueScore": "70% neutral draft score + 30% salary-value percentile",
            "limitations": [
                "No position scarcity adjustment yet.",
                "No fielding adjustment yet.",
                "No ballpark adjustment yet.",
                "No usage or roster construction adjustment yet.",
            ],
        },
        "counts": {
            "rankableHitters": len(hitters),
            "unresolvedHitters": len(unresolved_hitters),
            "rankablePitchers": len(pitchers),
            "unresolvedPitchers": len(unresolved_pitchers),
        },
        "hitters": hitters,
        "pitchers": pitchers,
        "unresolved": {
            "hitters": unresolved_hitters,
            "pitchers": unresolved_pitchers,
        },
    }

    OUTPUT_PATH.write_text(json.dumps(output, indent=2), encoding="utf-8")

    print("BIE Salary-Adjusted Draft Signal Parser v0")
    print("=" * 72)
    print(f"Rankable hitters: {len(hitters)}")
    print(f"Unresolved hitters: {len(unresolved_hitters)}")
    print(f"Rankable pitchers: {len(pitchers)}")
    print(f"Unresolved pitchers: {len(unresolved_pitchers)}")

    print()
    print("Top salary-adjusted hitter signals")
    print("-" * 72)
    for row in hitters[:15]:
        player = row["player"]
        print(
            f'{row["salaryValue"]["balancedValueScore"]["score"]:7.3f} '
            f'neutral={row["neutralDraftScore"]["score"]:7.3f} '
            f'value={row["salaryValue"]["valuePercentile"]["score"]:7.3f} '
            f'salary={row["salary"]["raw"]:>6} '
            f'{player["playerName"]} team={player["team"]}'
        )

    print()
    print("Top salary-adjusted pitcher signals")
    print("-" * 72)
    for row in pitchers[:15]:
        player = row["player"]
        print(
            f'{row["salaryValue"]["balancedValueScore"]["score"]:7.3f} '
            f'neutral={row["neutralDraftScore"]["score"]:7.3f} '
            f'value={row["salaryValue"]["valuePercentile"]["score"]:7.3f} '
            f'salary={row["salary"]["raw"]:>6} '
            f'{player["playerName"]} team={player["team"]}'
        )

    print(f"\nOutput: {OUTPUT_PATH}")
    print("=" * 72)

    if len(hitters) != 440 or len(unresolved_hitters) != 2 or len(pitchers) != 279 or unresolved_pitchers:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
