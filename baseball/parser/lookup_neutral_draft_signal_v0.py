from __future__ import annotations

from pathlib import Path
import argparse
import json
import unicodedata
from typing import Any


SIGNAL_PATH = Path("data/baseball/parsed/strat365/1980/draft-signals/1980.neutral-draft-signals.json")


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


def print_signal(row: dict[str, Any], rank: int | None) -> None:
    player = row.get("player", {})
    role = row.get("role")

    print("=" * 72)
    print(f'{player.get("playerName")}  team={player.get("team")}  role={role}')

    if rank is not None:
        print(f"Neutral draft rank: {rank}")
        print(f'Draft score: {score(row.get("draftScore")):.3f}')
    else:
        print("Neutral draft rank: unresolved / not rankable")

    print(f'Exact matchups: {row.get("exactMatchups")}')
    print(f'Partial matchups: {row.get("partialMatchups")}')

    if row.get("rankable") is False:
        print(f'Reason: {row.get("reason")}')
        print("=" * 72)
        return

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

    matches: list[tuple[dict[str, Any], int | None]] = []

    for collection_name in ("hitters", "pitchers"):
        for index, row in enumerate(data.get(collection_name, []), start=1):
            player_name = row.get("player", {}).get("playerName", "")
            if needle in normalize(player_name):
                matches.append((row, index))

    for collection_name in ("hitters", "pitchers"):
        for row in data.get("unresolved", {}).get(collection_name, []):
            player_name = row.get("player", {}).get("playerName", "")
            if needle in normalize(player_name):
                matches.append((row, None))

    print("BIE Neutral Draft Signal Lookup v0")
    print("=" * 72)
    print(f"Query: {args.query}")
    print(f"Matches: {len(matches)}")

    if not matches:
        print("No matching draft signals found.")
        print("=" * 72)
        raise SystemExit(1)

    for row, rank in matches:
        print_signal(row, rank)


if __name__ == "__main__":
    main()
