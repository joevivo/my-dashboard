from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
import json
from typing import Any


DEFENSE_PATH = Path("data/baseball/parsed/strat365/1980/player-defense-metadata/1980.player-defense-metadata.json")


def player_label(row: dict[str, Any]) -> str:
    return f'{row.get("playerName")} team={row.get("team")}'


def print_position_leaders(position: str, rows: list[dict[str, Any]], *, best: bool, limit: int = 10) -> None:
    title = "Best" if best else "Weakest"
    print()
    print(f"{title} {position} defenders")
    print("-" * 96)

    sorted_rows = sorted(
        rows,
        key=lambda item: (
            item["range"],
            item["error"],
            item["arm"] if item["arm"] is not None else 99,
        ),
        reverse=not best,
    )

    print("range  error  arm    player")
    for item in sorted_rows[:limit]:
        arm = item["arm"] if item["arm"] is not None else "-"
        print(
            f'{item["range"]:>5} '
            f'{item["error"]:>6} '
            f'{str(arm):>4}   '
            f'{player_label(item["player"])} raw={item["raw"]}'
        )


def print_pitcher_leaders(title: str, rows: list[dict[str, Any]], key: str, *, low_is_good: bool, limit: int = 15) -> None:
    print()
    print(title)
    print("-" * 96)

    sorted_rows = sorted(
        rows,
        key=lambda item: item["pitcherDefense"][key],
        reverse=not low_is_good,
    )

    print(f"{key:>14}  player")
    for row in sorted_rows[:limit]:
        print(f'{row["pitcherDefense"][key]:>14}  {player_label(row)}')


def main() -> None:
    data = json.loads(DEFENSE_PATH.read_text(encoding="utf-8-sig", errors="replace"))

    players = data.get("players", [])
    hitters = [row for row in players if row.get("role") == "hitter"]
    pitchers = [row for row in players if row.get("role") == "pitcher"]

    position_rows: list[dict[str, Any]] = []
    position_counts: Counter[str] = Counter()
    range_counts: dict[str, Counter[int]] = defaultdict(Counter)
    error_counts: dict[str, Counter[int]] = defaultdict(Counter)
    arm_counts: dict[str, Counter[int]] = defaultdict(Counter)
    multi_position_hitters: list[dict[str, Any]] = []

    for hitter in hitters:
        positions = hitter.get("hitterDefense", {}).get("positions", [])

        if len(positions) > 1:
            multi_position_hitters.append(hitter)

        for position in positions:
            item = dict(position)
            item["player"] = hitter
            position_rows.append(item)

            pos = item["position"]
            position_counts[pos] += 1
            range_counts[pos][item["range"]] += 1
            error_counts[pos][item["error"]] += 1

            if item["arm"] is not None:
                arm_counts[pos][item["arm"]] += 1

    by_position: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in position_rows:
        by_position[item["position"]].append(item)

    pitcher_defense_counts = Counter(row["pitcherDefense"]["pitcherDefense"] for row in pitchers)
    pitcher_hold_counts = Counter(row["pitcherDefense"]["hold"] for row in pitchers)
    pitcher_wp_counts = Counter(row["pitcherDefense"]["wildPitch"] for row in pitchers)
    pitcher_bk_counts = Counter(row["pitcherDefense"]["balk"] for row in pitchers)
    pitcher_bunting_counts = Counter(row["pitcherDefense"]["bunting"] for row in pitchers)

    print("BIE Player Defense Metadata Inventory v0")
    print("=" * 96)
    print(f"Schema: {data.get('schemaVersion')}")
    print(f"Players: {len(players)}")
    print(f"Hitters: {len(hitters)}")
    print(f"Pitchers: {len(pitchers)}")
    print(f"Hitter defensive position rows: {len(position_rows)}")
    print(f"Warnings: {len(data.get('warnings', []))}")

    print()
    print("Hitter defensive position counts")
    print("-" * 96)
    for position, count in sorted(position_counts.items()):
        print(f"{position}: {count}")

    print()
    print("Range distribution by position")
    print("-" * 96)
    for position in sorted(range_counts):
        print(f"{position}: {dict(sorted(range_counts[position].items()))}")

    print()
    print("Outfield / catcher arm distribution")
    print("-" * 96)
    for position in sorted(arm_counts):
        print(f"{position}: {dict(sorted(arm_counts[position].items()))}")

    print()
    print("Multi-position hitters")
    print("-" * 96)
    for hitter in sorted(multi_position_hitters, key=lambda row: (-len(row.get("hitterDefense", {}).get("positions", [])), row.get("playerName", "")))[:40]:
        positions = " / ".join(pos["raw"] for pos in hitter.get("hitterDefense", {}).get("positions", []))
        print(f'{player_label(hitter)} positions={positions}')

    for position in sorted(by_position):
        print_position_leaders(position, by_position[position], best=True)
        print_position_leaders(position, by_position[position], best=False)

    print()
    print("Pitcher defense rating distribution")
    print("-" * 96)
    print(dict(sorted(pitcher_defense_counts.items())))

    print()
    print("Pitcher hold distribution")
    print("-" * 96)
    print(dict(sorted(pitcher_hold_counts.items())))

    print()
    print("Pitcher wild pitch distribution")
    print("-" * 96)
    print(dict(sorted(pitcher_wp_counts.items())))

    print()
    print("Pitcher balk distribution")
    print("-" * 96)
    print(dict(sorted(pitcher_bk_counts.items())))

    print()
    print("Pitcher bunting distribution")
    print("-" * 96)
    print(dict(sorted(pitcher_bunting_counts.items())))

    print_pitcher_leaders("Best pitcher fielding ratings", pitchers, "pitcherDefense", low_is_good=True)
    print_pitcher_leaders("Weakest pitcher fielding ratings", pitchers, "pitcherDefense", low_is_good=False)
    print_pitcher_leaders("Best pitcher holds", pitchers, "hold", low_is_good=True)
    print_pitcher_leaders("Worst pitcher holds", pitchers, "hold", low_is_good=False)
    print_pitcher_leaders("Lowest wild pitch ratings", pitchers, "wildPitch", low_is_good=True)
    print_pitcher_leaders("Highest wild pitch ratings", pitchers, "wildPitch", low_is_good=False)

    print("=" * 96)


if __name__ == "__main__":
    main()
