from __future__ import annotations

from pathlib import Path
import json
from typing import Any


PATH = Path("data/baseball/parsed/strat365/1980/draft-signals/1980.defense-aware-draft-signals.json")


def score(payload: dict[str, Any] | None) -> float:
    if not payload:
        return -1.0
    return float(payload.get("score", -1.0))


def label(row: dict[str, Any]) -> str:
    player = row["player"]
    return f'{player["playerName"]} team={player["team"]}'


def best_pos(row: dict[str, Any]) -> str:
    best = row.get("bestDefensivePosition")
    if not best:
        return "DEFENSE_NEUTRAL"
    return str(best.get("raw", "DEF?"))


def pitcher_raw(row: dict[str, Any]) -> str:
    raw = row.get("pitcherDefenseRaw") or {}
    return f'p-{raw.get("pitcherDefense", "?")} hold={raw.get("hold", "?")} wp={raw.get("wildPitch", "?")} bk={raw.get("balk", "?")}'


def rank_delta(row: dict[str, Any]) -> int:
    return int(row["salaryAdjustedRank"]) - int(row["defenseAwareRank"])


def print_hitter_rows(title: str, rows: list[dict[str, Any]], limit: int = 20) -> None:
    print()
    print(title)
    print("-" * 112)
    print("d_rank s_rank delta d_score salary def    best_pos          player")
    for row in rows[:limit]:
        print(
            f'{row["defenseAwareRank"]:>6} '
            f'{row["salaryAdjustedRank"]:>6} '
            f'{rank_delta(row):>5} '
            f'{score(row["defenseAwareDraftScore"]):>7.3f} '
            f'{score(row["salaryAdjustedScore"]):>6.3f} '
            f'{score(row["defensiveScore"]):>6.3f} '
            f'{best_pos(row):>16}  '
            f'{label(row)}'
        )


def print_pitcher_rows(title: str, rows: list[dict[str, Any]], limit: int = 20) -> None:
    print()
    print(title)
    print("-" * 112)
    print("d_rank s_rank delta d_score salary def    raw                    player")
    for row in rows[:limit]:
        print(
            f'{row["defenseAwareRank"]:>6} '
            f'{row["salaryAdjustedRank"]:>6} '
            f'{rank_delta(row):>5} '
            f'{score(row["defenseAwareDraftScore"]):>7.3f} '
            f'{score(row["salaryAdjustedScore"]):>6.3f} '
            f'{score(row["defensiveScore"]):>6.3f} '
            f'{pitcher_raw(row):>22}  '
            f'{label(row)}'
        )


def main() -> None:
    data = json.loads(PATH.read_text(encoding="utf-8-sig", errors="replace"))

    hitters = data["hitters"]
    pitchers = data["pitchers"]

    hitter_risers = sorted(hitters, key=rank_delta, reverse=True)
    hitter_fallers = sorted(hitters, key=rank_delta)
    pitcher_risers = sorted(pitchers, key=rank_delta, reverse=True)
    pitcher_fallers = sorted(pitchers, key=rank_delta)

    print("BIE Defense-Aware Draft Signal Inventory v0")
    print("=" * 112)
    print(f"Schema: {data.get('schemaVersion')}")
    print(f"Rankable hitters: {len(hitters)}")
    print(f"Rankable pitchers: {len(pitchers)}")
    print(f"Unresolved hitters: {len(data['unresolved']['hitters'])}")
    print(f"Unresolved pitchers: {len(data['unresolved']['pitchers'])}")

    print_hitter_rows("Top defense-aware hitters", hitters)
    print_hitter_rows("Hitter risers versus salary-adjusted board", hitter_risers)
    print_hitter_rows("Hitter fallers versus salary-adjusted board", hitter_fallers)

    print_pitcher_rows("Top defense-aware pitchers", pitchers)
    print_pitcher_rows("Pitcher risers versus salary-adjusted board", pitcher_risers)
    print_pitcher_rows("Pitcher fallers versus salary-adjusted board", pitcher_fallers)

    print()
    print("Top defense-aware hitters by defensive position")
    print("-" * 112)
    seen_positions = sorted({
        (row.get("bestDefensivePosition") or {}).get("position")
        for row in hitters
        if row.get("bestDefensivePosition")
    })

    for position in seen_positions:
        rows = [row for row in hitters if (row.get("bestDefensivePosition") or {}).get("position") == position]
        rows.sort(key=lambda row: row["defenseAwareRank"])
        print(f"\n{position}")
        for row in rows[:8]:
            print(
                f'  #{row["defenseAwareRank"]:>3} '
                f'salary#{row["salaryAdjustedRank"]:>3} '
                f'{score(row["defenseAwareDraftScore"]):>7.3f} '
                f'{best_pos(row):>14} '
                f'{label(row)}'
            )

    print("=" * 112)


if __name__ == "__main__":
    main()
