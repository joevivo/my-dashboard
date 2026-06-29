from __future__ import annotations

from fractions import Fraction
from pathlib import Path
import json
from typing import Any


SALARY_PATH = Path("data/baseball/parsed/strat365/1980/draft-signals/1980.salary-adjusted-draft-signals.json")
DEFENSE_PATH = Path("data/baseball/parsed/strat365/1980/draft-signals/1980.defensive-draft-signals.json")
OUTPUT_DIR = Path("data/baseball/parsed/strat365/1980/draft-signals")
OUTPUT_PATH = OUTPUT_DIR / "1980.defense-aware-draft-signals.json"

SCHEMA_VERSION = "bie.defense-aware-draft-signals.v0"
PARSER_VERSION = "bie-defense-aware-draft-signal-parser-v0.1"


def frac(payload: dict[str, Any] | None) -> Fraction:
    if not payload:
        return Fraction(0, 1)
    return Fraction(payload["numerator"], payload["denominator"])


def score_frac(payload: dict[str, Any] | None) -> Fraction:
    if not payload:
        return Fraction(0, 1)
    return frac(payload.get("scoreFraction"))


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


def player_id(row: dict[str, Any]) -> int:
    return int(row["player"]["playerId"])


def salary_score(row: dict[str, Any]) -> Fraction:
    return score_frac(row.get("salaryValue", {}).get("balancedValueScore"))


def hitter_defense_score(row: dict[str, Any] | None) -> tuple[Fraction, bool]:
    if not row:
        return Fraction(50, 1), True

    best = row.get("bestPosition")
    if not best:
        return Fraction(50, 1), True

    return score_frac(best.get("defensiveScore")), False


def pitcher_defense_score(row: dict[str, Any] | None) -> tuple[Fraction, bool]:
    if not row:
        return Fraction(50, 1), True

    return score_frac(row.get("defensiveScore")), False


def enrich_hitter(row: dict[str, Any], defense_by_id: dict[int, dict[str, Any]]) -> dict[str, Any]:
    defense = defense_by_id.get(player_id(row))
    salary = salary_score(row)
    defensive, defense_neutralized = hitter_defense_score(defense)

    final_score = salary * Fraction(75, 100) + defensive * Fraction(25, 100)

    return {
        "player": row["player"],
        "role": "hitter",
        "rankable": True,
        "salaryAdjustedRank": row.get("salaryAdjustedRank"),
        "salary": row.get("salary"),
        "hitter": row.get("hitter", {}),
        "salaryAdjustedScore": row.get("salaryValue", {}).get("balancedValueScore"),
        "neutralDraftScore": row.get("neutralDraftScore"),
        "defensiveScore": score_payload(defensive),
        "defenseNeutralized": defense_neutralized,
        "bestDefensivePosition": defense.get("bestPosition") if defense else None,
        "defensivePositionCount": defense.get("positionCount", 0) if defense else 0,
        "defenseAwareDraftScore": score_payload(final_score),
        "componentScores": {
            "salaryAdjusted": row.get("salaryValue", {}).get("balancedValueScore"),
            "defense": score_payload(defensive),
        },
        "sourceAverages": row.get("sourceAverages", {}),
        "exactMatchups": row.get("exactMatchups"),
        "partialMatchups": row.get("partialMatchups"),
    }


def enrich_pitcher(row: dict[str, Any], defense_by_id: dict[int, dict[str, Any]]) -> dict[str, Any]:
    defense = defense_by_id.get(player_id(row))
    salary = salary_score(row)
    defensive, defense_neutralized = pitcher_defense_score(defense)

    final_score = salary * Fraction(85, 100) + defensive * Fraction(15, 100)

    return {
        "player": row["player"],
        "role": "pitcher",
        "rankable": True,
        "salaryAdjustedRank": row.get("salaryAdjustedRank"),
        "salary": row.get("salary"),
        "pitcher": row.get("pitcher", {}),
        "salaryAdjustedScore": row.get("salaryValue", {}).get("balancedValueScore"),
        "neutralDraftScore": row.get("neutralDraftScore"),
        "defensiveScore": score_payload(defensive),
        "defenseNeutralized": defense_neutralized,
        "pitcherDefenseRaw": defense.get("raw") if defense else None,
        "defenseAwareDraftScore": score_payload(final_score),
        "componentScores": {
            "salaryAdjusted": row.get("salaryValue", {}).get("balancedValueScore"),
            "defense": score_payload(defensive),
        },
        "sourceAverages": row.get("sourceAverages", {}),
        "exactMatchups": row.get("exactMatchups"),
        "partialMatchups": row.get("partialMatchups"),
    }


def enrich_unresolved(
    rows: list[dict[str, Any]],
    role: str,
    hitter_defense_by_id: dict[int, dict[str, Any]],
    pitcher_defense_by_id: dict[int, dict[str, Any]],
) -> list[dict[str, Any]]:
    output = []

    for row in rows:
        pid = player_id(row)
        copied = dict(row)

        if role == "hitter":
            copied["defense"] = hitter_defense_by_id.get(pid)
        else:
            copied["defense"] = pitcher_defense_by_id.get(pid)

        output.append(copied)

    return output


def rank_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows.sort(
        key=lambda row: (
            row["defenseAwareDraftScore"]["score"],
            row["salaryAdjustedScore"]["score"],
            row["defensiveScore"]["score"],
        ),
        reverse=True,
    )

    for index, row in enumerate(rows, start=1):
        row["defenseAwareRank"] = index

    return rows


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    salary = json.loads(SALARY_PATH.read_text(encoding="utf-8-sig", errors="replace"))
    defense = json.loads(DEFENSE_PATH.read_text(encoding="utf-8-sig", errors="replace"))

    hitter_defense_by_id = {
        player_id(row): row
        for row in defense.get("hitters", [])
    }

    pitcher_defense_by_id = {
        player_id(row): row
        for row in defense.get("pitchers", [])
    }

    hitters = rank_rows([
        enrich_hitter(row, hitter_defense_by_id)
        for row in salary.get("hitters", [])
    ])

    pitchers = rank_rows([
        enrich_pitcher(row, pitcher_defense_by_id)
        for row in salary.get("pitchers", [])
    ])

    unresolved_hitters = enrich_unresolved(
        salary.get("unresolved", {}).get("hitters", []),
        "hitter",
        hitter_defense_by_id,
        pitcher_defense_by_id,
    )

    unresolved_pitchers = enrich_unresolved(
        salary.get("unresolved", {}).get("pitchers", []),
        "pitcher",
        hitter_defense_by_id,
        pitcher_defense_by_id,
    )

    output = {
        "schemaVersion": SCHEMA_VERSION,
        "parserVersion": PARSER_VERSION,
        "season": 1980,
        "sourceFiles": {
            "salaryAdjustedDraftSignals": str(SALARY_PATH).replace("\\", "/"),
            "defensiveDraftSignals": str(DEFENSE_PATH).replace("\\", "/"),
        },
        "model": {
            "name": "defense_aware_draft_signal_v0",
            "hitterScore": "75% salary-adjusted draft score + 25% best-position defensive score.",
            "pitcherScore": "85% salary-adjusted draft score + 15% pitcher defensive score.",
            "defenseUnavailableHandling": "DH-only or missing defensive records receive neutral defensive score of 50 and are marked defenseNeutralized.",
            "limitations": [
                "Does not yet use team-specific GBX/FBX/CATCH-X exposure.",
                "Does not yet apply ballpark fit.",
                "Does not yet enforce roster construction or position scarcity.",
                "Does not yet distinguish starter workload from relief workload.",
            ],
        },
        "counts": {
            "rankableHitters": len(hitters),
            "unresolvedHitters": len(unresolved_hitters),
            "rankablePitchers": len(pitchers),
            "unresolvedPitchers": len(unresolved_pitchers),
            "defenseNeutralizedHitters": sum(1 for row in hitters if row["defenseNeutralized"]),
            "defenseNeutralizedPitchers": sum(1 for row in pitchers if row["defenseNeutralized"]),
        },
        "hitters": hitters,
        "pitchers": pitchers,
        "unresolved": {
            "hitters": unresolved_hitters,
            "pitchers": unresolved_pitchers,
        },
    }

    OUTPUT_PATH.write_text(json.dumps(output, indent=2), encoding="utf-8")

    print("BIE Defense-Aware Draft Signal Parser v0")
    print("=" * 88)
    print(f"Rankable hitters: {len(hitters)}")
    print(f"Unresolved hitters: {len(unresolved_hitters)}")
    print(f"Rankable pitchers: {len(pitchers)}")
    print(f"Unresolved pitchers: {len(unresolved_pitchers)}")
    print(f"Defense-neutralized hitters: {output['counts']['defenseNeutralizedHitters']}")
    print(f"Defense-neutralized pitchers: {output['counts']['defenseNeutralizedPitchers']}")

    print()
    print("Top defense-aware hitters")
    print("-" * 88)
    for row in hitters[:15]:
        best = row.get("bestDefensivePosition") or {}
        print(
            f'{row["defenseAwareDraftScore"]["score"]:7.3f} '
            f'salary={row["salaryAdjustedScore"]["score"]:7.3f} '
            f'def={row["defensiveScore"]["score"]:7.3f} '
            f's_rank={row["salaryAdjustedRank"]:>3} '
            f'{best.get("raw", "DEF?"):>12} '
            f'{row["player"]["playerName"]} team={row["player"]["team"]}'
        )

    print()
    print("Top defense-aware pitchers")
    print("-" * 88)
    for row in pitchers[:15]:
        raw = row.get("pitcherDefenseRaw") or {}
        print(
            f'{row["defenseAwareDraftScore"]["score"]:7.3f} '
            f'salary={row["salaryAdjustedScore"]["score"]:7.3f} '
            f'def={row["defensiveScore"]["score"]:7.3f} '
            f's_rank={row["salaryAdjustedRank"]:>3} '
            f'p-{raw.get("pitcherDefense", "?")} hold={raw.get("hold", "?")} '
            f'{row["player"]["playerName"]} team={row["player"]["team"]}'
        )

    print(f"\nOutput: {OUTPUT_PATH}")
    print("=" * 88)

    if len(hitters) != 440 or len(unresolved_hitters) != 2 or len(pitchers) != 279 or unresolved_pitchers:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
