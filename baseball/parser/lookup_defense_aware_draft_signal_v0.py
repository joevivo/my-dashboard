from __future__ import annotations

from pathlib import Path
import argparse
import json
from typing import Any


PATH = Path("data/baseball/parsed/strat365/1980/draft-signals/1980.defense-aware-draft-signals.json")


def score(payload: dict[str, Any] | None) -> str:
    if not payload:
        return "n/a"
    value = payload.get("score")
    if value is None:
        return "n/a"
    return f"{float(value):.3f}"


def player_name(row: dict[str, Any]) -> str:
    return str(row.get("player", {}).get("playerName", ""))


def team(row: dict[str, Any]) -> str:
    return str(row.get("player", {}).get("team", ""))


def best_position(row: dict[str, Any]) -> str:
    best = row.get("bestDefensivePosition")
    if not best:
        return "DEFENSE_NEUTRAL"
    return str(best.get("raw", "DEF?"))


def pitcher_raw(row: dict[str, Any]) -> str:
    raw = row.get("pitcherDefenseRaw") or {}
    return (
        f'p-{raw.get("pitcherDefense", "?")} '
        f'hold={raw.get("hold", "?")} '
        f'wp={raw.get("wildPitch", "?")} '
        f'bk={raw.get("balk", "?")}'
    )


def print_hitter(row: dict[str, Any]) -> None:
    print("=" * 96)
    print(f'HITTER: {player_name(row)} team={team(row)}')
    print("-" * 96)
    print(f'Defense-aware rank : {row.get("defenseAwareRank")}')
    print(f'Salary-adjusted rank: {row.get("salaryAdjustedRank")}')
    print(f'Defense-aware score: {score(row.get("defenseAwareDraftScore"))}')
    print(f'Salary score       : {score(row.get("salaryAdjustedScore"))}')
    print(f'Defensive score    : {score(row.get("defensiveScore"))}')
    print(f'Neutral score      : {score(row.get("neutralDraftScore"))}')
    print(f'Best defense       : {best_position(row)}')
    print(f'Position count     : {row.get("defensivePositionCount")}')
    print(f'Defense neutralized: {row.get("defenseNeutralized")}')
    print()


def print_pitcher(row: dict[str, Any]) -> None:
    print("=" * 96)
    print(f'PITCHER: {player_name(row)} team={team(row)}')
    print("-" * 96)
    print(f'Defense-aware rank : {row.get("defenseAwareRank")}')
    print(f'Salary-adjusted rank: {row.get("salaryAdjustedRank")}')
    print(f'Defense-aware score: {score(row.get("defenseAwareDraftScore"))}')
    print(f'Salary score       : {score(row.get("salaryAdjustedScore"))}')
    print(f'Defensive score    : {score(row.get("defensiveScore"))}')
    print(f'Neutral score      : {score(row.get("neutralDraftScore"))}')
    print(f'Pitcher defense    : {pitcher_raw(row)}')
    print(f'Defense neutralized: {row.get("defenseNeutralized")}')
    print()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("query")
    parser.add_argument("--role", choices=["all", "hitter", "pitcher"], default="all")
    parser.add_argument("--limit", type=int, default=25)
    args = parser.parse_args()

    data = json.loads(PATH.read_text(encoding="utf-8-sig", errors="replace"))
    query = args.query.casefold()

    rows: list[tuple[str, dict[str, Any]]] = []

    if args.role in ("all", "hitter"):
        rows.extend(("hitter", row) for row in data.get("hitters", []))

    if args.role in ("all", "pitcher"):
        rows.extend(("pitcher", row) for row in data.get("pitchers", []))

    matches = [
        (role, row)
        for role, row in rows
        if query in player_name(row).casefold()
    ]

    matches.sort(
        key=lambda item: (
            item[0],
            int(item[1].get("defenseAwareRank", 999999)),
        )
    )

    print("BIE Defense-Aware Draft Signal Lookup v0")
    print("=" * 96)
    print(f"Query: {args.query}")
    print(f"Role filter: {args.role}")
    print(f"Matches: {len(matches)}")
    print("=" * 96)

    if not matches:
        return

    for role, row in matches[: args.limit]:
        if role == "hitter":
            print_hitter(row)
        else:
            print_pitcher(row)

    if len(matches) > args.limit:
        print(f"Showing first {args.limit} of {len(matches)} matches.")


if __name__ == "__main__":
    main()
