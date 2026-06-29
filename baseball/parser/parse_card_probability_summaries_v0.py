from __future__ import annotations

from collections import Counter, defaultdict
from fractions import Fraction
from pathlib import Path
import json
from typing import Any


PROBABILITY_DIR = Path("data/baseball/parsed/strat365/1980/result-probabilities")
OUTPUT_DIR = Path("data/baseball/parsed/strat365/1980/card-probability-summaries")

SCHEMA_VERSION = "bie.card-probability-summary.v0"
PARSER_VERSION = "bie-card-probability-summary-parser-v0.1"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig", errors="replace"))


def fraction_from_payload(payload: dict[str, Any] | None) -> Fraction | None:
    if not payload:
        return None
    numerator = payload.get("numerator")
    denominator = payload.get("denominator")
    if not isinstance(numerator, int) or not isinstance(denominator, int):
        return None
    return Fraction(numerator, denominator)


def fraction_payload(value: Fraction) -> dict[str, Any]:
    return {
        "numerator": value.numerator,
        "denominator": value.denominator,
        "decimal": round(float(value), 12),
    }


def summarize_file(path: Path) -> dict[str, Any]:
    source = read_json(path)

    side_summaries: dict[str, dict[str, Any]] = {}

    for table in source.get("tables", []):
        side = table.get("side")

        if side not in side_summaries:
            side_summaries[side] = {
                "side": side,
                "exactWeightTotal": Fraction(0, 1),
                "hitCandidateWeight": Fraction(0, 1),
                "onBaseCandidateWeight": Fraction(0, 1),
                "outCandidateWeight": Fraction(0, 1),
                "baseOutcomeWeights": defaultdict(Fraction),
                "dependencyWeights": defaultdict(Fraction),
                "probabilityStatusCounts": Counter(),
                "nonProbabilityFlagCounts": Counter(),
                "unresolvedOutcomeRows": [],
            }

        summary = side_summaries[side]

        for entry in table.get("entries", []):
            for outcome in entry.get("outcomes", []):
                probability = outcome.get("resultProbability", {})
                semantics = outcome.get("resultSemantics", {})

                status = probability.get("probabilityStatus")
                summary["probabilityStatusCounts"][status] += 1

                base_outcome = semantics.get("baseOutcomeType")
                final_weight = fraction_from_payload(probability.get("finalWeight"))

                if status == "non_probability_flag":
                    summary["nonProbabilityFlagCounts"][base_outcome] += 1
                    continue

                if status != "exact":
                    summary["unresolvedOutcomeRows"].append(
                        {
                            "status": status,
                            "tableNumber": table.get("tableNumber"),
                            "side": side,
                            "diceRoll": entry.get("diceRoll"),
                            "rawOutcome": outcome.get("rawOutcome"),
                            "atomKey": outcome.get("resultAtom", {}).get("atomKey"),
                        }
                    )
                    continue

                if final_weight is None:
                    raise ValueError("exact probability row missing finalWeight")

                summary["exactWeightTotal"] += final_weight
                summary["baseOutcomeWeights"][base_outcome] += final_weight

                if semantics.get("isHitCandidate"):
                    summary["hitCandidateWeight"] += final_weight

                if semantics.get("isOnBaseCandidate"):
                    summary["onBaseCandidateWeight"] += final_weight

                if semantics.get("isOutCandidate"):
                    summary["outCandidateWeight"] += final_weight

                for dependency in semantics.get("dependencies", []):
                    summary["dependencyWeights"][dependency] += final_weight

    rendered_sides = []

    for side in sorted(side_summaries):
        raw = side_summaries[side]

        rendered_sides.append(
            {
                "side": raw["side"],
                "exactWeightTotal": fraction_payload(raw["exactWeightTotal"]),
                "hitCandidateWeight": fraction_payload(raw["hitCandidateWeight"]),
                "onBaseCandidateWeight": fraction_payload(raw["onBaseCandidateWeight"]),
                "outCandidateWeight": fraction_payload(raw["outCandidateWeight"]),
                "baseOutcomeWeights": {
                    key: fraction_payload(value)
                    for key, value in sorted(raw["baseOutcomeWeights"].items())
                },
                "dependencyWeights": {
                    key: fraction_payload(value)
                    for key, value in sorted(raw["dependencyWeights"].items())
                },
                "probabilityStatusCounts": dict(raw["probabilityStatusCounts"]),
                "nonProbabilityFlagCounts": dict(raw["nonProbabilityFlagCounts"]),
                "unresolvedOutcomeRows": raw["unresolvedOutcomeRows"],
            }
        )

    return {
        "schemaVersion": SCHEMA_VERSION,
        "parserVersion": PARSER_VERSION,
        "sourceSchemaVersion": source.get("schemaVersion"),
        "sourceParserVersion": source.get("parserVersion"),
        "sourceFile": str(path).replace("\\", "/"),
        "player": source.get("player"),
        "role": source.get("role"),
        "probabilityBasis": source.get("probabilityBasis"),
        "sides": rendered_sides,
    }


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    paths = sorted(PROBABILITY_DIR.glob("*.result-probabilities.json"))

    parsed = 0
    failed = 0
    role_counts: Counter[str] = Counter()
    side_count = 0
    side_exact_total_counts: Counter[str] = Counter()
    unresolved_side_count = 0

    for path in paths:
        try:
            summary = summarize_file(path)
            player_id = summary.get("player", {}).get("playerId")
            if not player_id:
                raise ValueError(f"Missing playerId in {path}")

            role_counts[summary.get("role")] += 1

            for side in summary.get("sides", []):
                side_count += 1
                exact = side.get("exactWeightTotal", {})
                side_exact_total_counts[f'{exact.get("numerator")}/{exact.get("denominator")}'] += 1
                if side.get("unresolvedOutcomeRows"):
                    unresolved_side_count += 1

            output_path = OUTPUT_DIR / f"{player_id}.card-probability-summary.json"
            output_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

            parsed += 1
        except Exception as exc:
            failed += 1
            print(f"FAILED {path}: {exc}")

    print("BIE Card Probability Summary Parser v0")
    print("=" * 72)
    print(f"Source files: {len(paths)}")
    print(f"Parsed files: {parsed}")
    print(f"Failed files: {failed}")
    print(f"Role counts: {dict(role_counts)}")
    print(f"Card sides: {side_count}")
    print(f"Unresolved sides: {unresolved_side_count}")
    print(f"Side exact total counts: {dict(side_exact_total_counts)}")
    print(f"Output: {OUTPUT_DIR}")
    print("=" * 72)

    if (
        parsed != 721
        or failed != 0
        or role_counts.get("hitter") != 442
        or role_counts.get("pitcher") != 279
        or side_count != 1442
        or unresolved_side_count != 9
    ):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
