from __future__ import annotations

from collections import Counter
from fractions import Fraction
from pathlib import Path
import json
from typing import Any


MATCHUP_PATH = Path("data/baseball/parsed/strat365/1980/matchup-probabilities/1980.matchup-probabilities.jsonl")


def frac(payload: dict[str, Any] | None) -> Fraction:
    if not payload:
        return Fraction(0, 1)
    return Fraction(payload["numerator"], payload["denominator"])


def fmt(value: Fraction) -> str:
    return f"{float(value):.4f}"


def outcome(row: dict[str, Any], label: str) -> Fraction:
    return frac(row.get("weights", {}).get("baseOutcomeWeights", {}).get(label))


def metric(row: dict[str, Any], key: str) -> Fraction:
    return frac(row.get("weights", {}).get(key))


def label(row: dict[str, Any]) -> str:
    hitter = row["hitter"]
    pitcher = row["pitcher"]
    return (
        f'{hitter["playerName"]} ({hitter["bats"]}, {hitter["team"]}) '
        f'vs {pitcher["playerName"]} ({pitcher["throws"]}, {pitcher["team"]})'
    )


def print_top(title: str, rows: list[dict[str, Any]], get_value, limit: int = 12, reverse: bool = True) -> None:
    print()
    print(title)
    print("-" * 72)

    ranked = sorted(rows, key=lambda r: (get_value(r), label(r)), reverse=reverse)

    for row in ranked[:limit]:
        print(f"{fmt(get_value(row))}  {label(row)}  status={row['probabilityStatus']}")


def main() -> None:
    rows: list[dict[str, Any]] = []
    status_counts: Counter[str] = Counter()
    bats_throws_counts: Counter[str] = Counter()
    effective_counts: Counter[str] = Counter()

    with MATCHUP_PATH.open("r", encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            rows.append(row)

            status_counts[row.get("probabilityStatus")] += 1
            bats_throws_counts[f'{row["hitter"]["bats"]}_vs_{row["pitcher"]["throws"]}'] += 1
            effective_counts[f'{row["effectiveBatterSide"]}_batter_vs_{row["pitcher"]["throws"]}_pitcher'] += 1

    exact_rows = [row for row in rows if row.get("probabilityStatus") == "exact"]

    print("BIE Matchup Probability Inventory v0")
    print("=" * 72)
    print(f"Matchup rows: {len(rows)}")
    print(f"Exact rows: {len(exact_rows)}")
    print(f"Probability status counts: {dict(status_counts)}")
    print(f"Bats/throws counts: {dict(bats_throws_counts)}")
    print(f"Effective counts: {dict(effective_counts)}")

    print_top(
        "Top exact matchups by on-base candidate weight",
        exact_rows,
        lambda row: metric(row, "onBaseCandidateWeight"),
    )

    print_top(
        "Top exact matchups by hit candidate weight",
        exact_rows,
        lambda row: metric(row, "hitCandidateWeight"),
    )

    print_top(
        "Top exact matchups by home run weight",
        exact_rows,
        lambda row: outcome(row, "HOME_RUN"),
    )

    print_top(
        "Lowest exact matchups by on-base candidate weight",
        exact_rows,
        lambda row: metric(row, "onBaseCandidateWeight"),
        reverse=False,
    )

    print_top(
        "Top exact matchups by strikeout weight",
        exact_rows,
        lambda row: outcome(row, "STRIKEOUT"),
    )

    print("=" * 72)


if __name__ == "__main__":
    main()
