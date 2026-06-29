from __future__ import annotations

from pathlib import Path
import argparse
import json
import unicodedata
from typing import Any


SIGNAL_PATH = Path("data/baseball/parsed/strat365/1980/draft-signals/1980.salary-adjusted-draft-signals.json")


def normalize(value: str) -> str:
    text = unicodedata.normalize("NFKD", value or "")
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return text.casefold().strip()


def score(payload: dict[str, Any] | None) -> float:
    if not payload:
        return 0.0
    return float(payload.get("score", 0.0))


def decimal(payload: dict[str, Any] | None) -> float:
    if not payload:
        return 0.0
    return float(payload.get("decimal", 0.0))


def salary_raw(row: dict[str, Any]) -> str:
    return str(row.get("salary", {}).get("raw", "(salary?)"))


def build_neutral_ranks(rows: list[dict[str, Any]]) -> dict[int, int]:
    ranked = sorted(
        rows,
        key=lambda row: float(row.get("neutralDraftScore", {}).get("score", 0.0)),
        reverse=True,
    )
    return {
        int(row["player"]["playerId"]): index
        for index, row in enumerate(ranked, start=1)
    }


def print_signal(row: dict[str, Any], neutral_rank: int | None) -> None:
    player = row.get("player", {})
    role = row.get("role")

    print("=" * 72)
    print(f'{player.get("playerName")}  team={player.get("team")}  role={role}')
    print(f'Salary: {salary_raw(row)}')

    if row.get("rankable") is False:
        print("Salary-adjusted rank: unresolved / not rankable")
        print(f'Exact matchups: {row.get("exactMatchups")}')
        print(f'Partial matchups: {row.get("partialMatchups")}')
        print(f'Reason: {row.get("reason")}')
        print("=" * 72)
        return

    salary_value = row.get("salaryValue", {})

    print(f'Neutral rank: {neutral_rank}')
    print(f'Salary-adjusted rank: {row.get("salaryAdjustedRank")}')
    print(f'Neutral draft score: {score(row.get("neutralDraftScore")):.3f}')
    print(f'Balanced value score: {score(salary_value.get("balancedValueScore")):.3f}')
    print(f'Value percentile: {score(salary_value.get("valuePercentile")):.3f}')
    print(f'Signal per million: {decimal(salary_value.get("signalPerMillion")):.3f}')
    print(f'Exact matchups: {row.get("exactMatchups")}')
    print(f'Partial matchups: {row.get("partialMatchups")}')

    print()
    print("Component scores")
    print("-" * 72)
    for key, value in row.get("componentScores", {}).items():
        print(f"{key}: {score(value):.3f}")

    print()
    print("Source averages")
    print("-" * 72)
    for key, value in row.get("sourceAverages", {}).items():
        print(f"{key}: {decimal(value):.4f}")

    print("=" * 72)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("query", help="Player name search, e.g. Brett or Billingham")
    args = parser.parse_args()

    data = json.loads(SIGNAL_PATH.read_text(encoding="utf-8-sig", errors="replace"))
    needle = normalize(args.query)

    neutral_ranks = {
        "hitter": build_neutral_ranks(data.get("hitters", [])),
        "pitcher": build_neutral_ranks(data.get("pitchers", [])),
    }

    matches: list[dict[str, Any]] = []

    for collection_name in ("hitters", "pitchers"):
        for row in data.get(collection_name, []):
            player_name = row.get("player", {}).get("playerName", "")
            if needle in normalize(player_name):
                matches.append(row)

    for collection_name in ("hitters", "pitchers"):
        for row in data.get("unresolved", {}).get(collection_name, []):
            player_name = row.get("player", {}).get("playerName", "")
            if needle in normalize(player_name):
                matches.append(row)

    print("BIE Salary-Adjusted Draft Signal Lookup v0")
    print("=" * 72)
    print(f"Query: {args.query}")
    print(f"Matches: {len(matches)}")

    if not matches:
        print("No matching salary-adjusted draft signals found.")
        print("=" * 72)
        raise SystemExit(1)

    for row in matches:
        player_id = int(row["player"]["playerId"])
        role = row.get("role")
        print_signal(row, neutral_ranks.get(role, {}).get(player_id))


if __name__ == "__main__":
    main()
