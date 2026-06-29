from __future__ import annotations

from collections import Counter, defaultdict
from fractions import Fraction
from pathlib import Path
import json
from typing import Any


PROBABILITY_DIR = Path("data/baseball/parsed/strat365/1980/result-probabilities")


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


def fmt(value: Fraction) -> str:
    return f"{value.numerator}/{value.denominator} ({float(value):.6f})"


def main() -> None:
    paths = sorted(PROBABILITY_DIR.glob("*.result-probabilities.json"))

    role_counts: Counter[str] = Counter()
    status_counts: Counter[str] = Counter()
    side_exact_total_counts: Counter[str] = Counter()
    side_unresolved_counts: Counter[int] = Counter()
    side_flag_counts: Counter[int] = Counter()

    base_outcome_weight = defaultdict(Fraction)

    total_entries = 0
    total_outcome_rows = 0
    total_warnings = 0
    exact_weight_total = Fraction(0, 1)

    for path in paths:
        data = read_json(path)
        role = data.get("role")
        role_counts[role] += 1
        total_warnings += len(data.get("warnings", []))

        side_totals = defaultdict(Fraction)
        side_unresolved = Counter()
        side_flags = Counter()

        for table in data.get("tables", []):
            side = table.get("side")
            side_key = (data.get("player", {}).get("playerId"), role, side)

            for entry in table.get("entries", []):
                total_entries += 1

                for outcome in entry.get("outcomes", []):
                    total_outcome_rows += 1

                    probability = outcome.get("resultProbability", {})
                    status = probability.get("probabilityStatus")
                    status_counts[status] += 1

                    final_weight = fraction_from_payload(probability.get("finalWeight"))
                    base_outcome = outcome.get("resultSemantics", {}).get("baseOutcomeType")

                    if final_weight is not None:
                        exact_weight_total += final_weight
                        side_totals[side_key] += final_weight
                        base_outcome_weight[base_outcome] += final_weight
                    elif status == "unresolved_open_split":
                        side_unresolved[side_key] += 1
                    elif status == "non_probability_flag":
                        side_flags[side_key] += 1

        all_side_keys = set(side_totals) | set(side_unresolved) | set(side_flags)

        for side_key in all_side_keys:
            side_exact_total_counts[str(side_totals[side_key])] += 1
            side_unresolved_counts[side_unresolved[side_key]] += 1
            side_flag_counts[side_flags[side_key]] += 1

    print("BIE Result Probability Inventory v0")
    print("=" * 72)
    print(f"Result-probability files: {len(paths)}")
    print(f"Role counts: {dict(role_counts)}")
    print(f"Total entries: {total_entries}")
    print(f"Total outcome rows: {total_outcome_rows}")
    print(f"Warnings: {total_warnings}")
    print(f"Probability status counts: {dict(status_counts)}")
    print(f"Exact final weight total: {fmt(exact_weight_total)}")
    print()

    print("Card-side exact total distribution:")
    for key, count in sorted(side_exact_total_counts.items()):
        print(f"  {key}: {count}")

    print()
    print("Card-side unresolved open split distribution:")
    for key, count in sorted(side_unresolved_counts.items()):
        print(f"  {key}: {count}")

    print()
    print("Card-side non-probability flag distribution:")
    for key, count in sorted(side_flag_counts.items()):
        print(f"  {key}: {count}")

    print()
    print("Exact base outcome weight totals:")
    for key, value in sorted(base_outcome_weight.items(), key=lambda kv: kv[1], reverse=True):
        print(f"  {key}: {fmt(value)}")

    print("=" * 72)


if __name__ == "__main__":
    main()
