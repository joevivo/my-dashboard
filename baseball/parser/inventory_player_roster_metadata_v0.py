from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
import json
from typing import Any


METADATA_PATH = Path("data/baseball/parsed/strat365/1980/player-roster-metadata/1980.player-roster-metadata.json")


def salary(player: dict[str, Any]) -> float:
    return float(player.get("salary", {}).get("millions", {}).get("decimal", 0))


def label(player: dict[str, Any]) -> str:
    parts = [
        f'{player.get("playerName")}',
        f'team={player.get("team")}',
        f'role={player.get("role")}',
        f'salary={salary(player):.2f}M',
    ]

    if player.get("role") == "hitter":
        hitter = player.get("hitter", {})
        parts.append(f'pos={hitter.get("primaryPosition")}')
        parts.append(f'bats={hitter.get("bats")}')

    if player.get("role") == "pitcher":
        pitcher = player.get("pitcher", {})
        parts.append(f'pitchingRole={pitcher.get("pitchingRole")}')
        parts.append(f'throws={pitcher.get("throws")}')

    return " ".join(parts)


def print_top(title: str, players: list[dict[str, Any]], *, limit: int = 20, reverse: bool = True) -> None:
    print()
    print(title)
    print("-" * 72)

    for player in sorted(players, key=lambda p: (salary(p), p.get("playerName", "")), reverse=reverse)[:limit]:
        print(label(player))


def main() -> None:
    data = json.loads(METADATA_PATH.read_text(encoding="utf-8-sig", errors="replace"))

    players = data.get("players", [])
    hitters = [player for player in players if player.get("role") == "hitter"]
    pitchers = [player for player in players if player.get("role") == "pitcher"]

    position_counts = Counter(player.get("hitter", {}).get("primaryPosition") for player in hitters)
    bats_counts = Counter(player.get("hitter", {}).get("bats") for player in hitters)
    throws_counts = Counter(player.get("pitcher", {}).get("throws") for player in pitchers)
    pitching_role_counts = Counter(player.get("pitcher", {}).get("pitchingRole") for player in pitchers)

    salary_buckets = defaultdict(int)

    for player in players:
        value = salary(player)
        if value < 1:
            salary_buckets["under_1M"] += 1
        elif value < 3:
            salary_buckets["1M_to_3M"] += 1
        elif value < 5:
            salary_buckets["3M_to_5M"] += 1
        elif value < 8:
            salary_buckets["5M_to_8M"] += 1
        else:
            salary_buckets["8M_plus"] += 1

    print("BIE Player Roster Metadata Inventory v0")
    print("=" * 72)
    print(f"Players: {len(players)}")
    print(f"Hitters: {len(hitters)}")
    print(f"Pitchers: {len(pitchers)}")
    print(f"Salary buckets: {dict(sorted(salary_buckets.items()))}")
    print(f"Position counts: {dict(position_counts)}")
    print(f"Bats counts: {dict(bats_counts)}")
    print(f"Throws counts: {dict(throws_counts)}")

    print()
    print("Pitching role counts")
    print("-" * 72)
    for role, count in pitching_role_counts.most_common():
        print(f"{role}: {count}")

    print_top("Highest salary hitters", hitters)
    print_top("Lowest salary hitters", hitters, reverse=False)
    print_top("Highest salary pitchers", pitchers)
    print_top("Lowest salary pitchers", pitchers, reverse=False)

    print("=" * 72)


if __name__ == "__main__":
    main()
