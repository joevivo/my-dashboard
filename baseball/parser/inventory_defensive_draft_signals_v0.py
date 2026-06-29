from __future__ import annotations

from collections import defaultdict
from pathlib import Path
import json
from typing import Any


DEFENSE_SIGNAL_PATH = Path("data/baseball/parsed/strat365/1980/draft-signals/1980.defensive-draft-signals.json")
SALARY_SIGNAL_PATH = Path("data/baseball/parsed/strat365/1980/draft-signals/1980.salary-adjusted-draft-signals.json")


def score(payload: dict[str, Any] | None) -> float:
    if not payload:
        return -1.0
    return float(payload.get("score", -1.0))


def hitter_def_score(row: dict[str, Any]) -> float:
    best = row.get("bestPosition")
    if not best:
        return -1.0
    return score(best.get("defensiveScore"))


def pitcher_def_score(row: dict[str, Any]) -> float:
    return score(row.get("defensiveScore"))


def player_label(row: dict[str, Any]) -> str:
    player = row.get("player", {})
    return f'{player.get("playerName")} team={player.get("team")}'


def print_hitter_board(title: str, rows: list[dict[str, Any]], *, limit: int = 20) -> None:
    print()
    print(title)
    print("-" * 104)
    print("def     best_pos      pos_ct  player")
    for row in rows[:limit]:
        best = row.get("bestPosition")
        if best:
            best_raw = best.get("raw")
            def_score = hitter_def_score(row)
        else:
            best_raw = "DEFENSE_UNAVAILABLE"
            def_score = -1.0

        print(
            f"{def_score:7.3f} "
            f"{best_raw:>13} "
            f"{row.get('positionCount', 0):>7}  "
            f"{player_label(row)}"
        )


def print_pitcher_board(title: str, rows: list[dict[str, Any]], *, limit: int = 20) -> None:
    print()
    print(title)
    print("-" * 104)
    print("def     pdef hold wp  bk  player")
    for row in rows[:limit]:
        raw = row.get("raw", {})
        print(
            f"{pitcher_def_score(row):7.3f} "
            f"{raw.get('pitcherDefense'):>4} "
            f"{raw.get('hold'):>4} "
            f"{raw.get('wildPitch'):>2} "
            f"{raw.get('balk'):>3}  "
            f"{player_label(row)}"
        )


def main() -> None:
    defense = json.loads(DEFENSE_SIGNAL_PATH.read_text(encoding="utf-8-sig", errors="replace"))
    salary = json.loads(SALARY_SIGNAL_PATH.read_text(encoding="utf-8-sig", errors="replace"))

    hitters = defense.get("hitters", [])
    pitchers = defense.get("pitchers", [])

    salary_hitters_by_id = {
        int(row["player"]["playerId"]): row
        for row in salary.get("hitters", [])
    }

    salary_pitchers_by_id = {
        int(row["player"]["playerId"]): row
        for row in salary.get("pitchers", [])
    }

    hitters_by_position: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in hitters:
        for position in row.get("positions", []):
            copied = dict(row)
            copied["bestPosition"] = position
            hitters_by_position[position["position"]].append(copied)

    top_hitters = sorted(hitters, key=hitter_def_score, reverse=True)
    weak_hitters = sorted(hitters, key=hitter_def_score)

    top_pitchers = sorted(pitchers, key=pitcher_def_score, reverse=True)
    weak_pitchers = sorted(pitchers, key=pitcher_def_score)

    salary_corrections_hitters = []
    for row in hitters:
        player_id = int(row["player"]["playerId"])
        salary_row = salary_hitters_by_id.get(player_id)
        if not salary_row:
            continue

        salary_rank = int(salary_row["salaryAdjustedRank"])
        salary_score = float(salary_row["salaryValue"]["balancedValueScore"]["score"])
        defense_score = hitter_def_score(row)

        if salary_rank <= 50 and defense_score < 35:
            salary_corrections_hitters.append((salary_rank, salary_score, defense_score, row, salary_row))

    salary_corrections_pitchers = []
    for row in pitchers:
        player_id = int(row["player"]["playerId"])
        salary_row = salary_pitchers_by_id.get(player_id)
        if not salary_row:
            continue

        salary_rank = int(salary_row["salaryAdjustedRank"])
        salary_score = float(salary_row["salaryValue"]["balancedValueScore"]["score"])
        defense_score = pitcher_def_score(row)

        if salary_rank <= 50 and defense_score < 35:
            salary_corrections_pitchers.append((salary_rank, salary_score, defense_score, row, salary_row))

    print("BIE Defensive Draft Signal Inventory v0")
    print("=" * 104)
    print(f"Schema: {defense.get('schemaVersion')}")
    print(f"Hitters: {len(hitters)}")
    print(f"Pitchers: {len(pitchers)}")
    print(f"Hitter defense unavailable: {defense.get('counts', {}).get('hitterDefenseUnavailable')}")

    print_hitter_board("Top hitter defensive signals", top_hitters)
    print_hitter_board("Weakest hitter defensive signals", weak_hitters)

    for position in sorted(hitters_by_position):
        rows = sorted(hitters_by_position[position], key=hitter_def_score, reverse=True)
        print_hitter_board(f"Top defensive signals at {position}", rows, limit=10)

    print_pitcher_board("Top pitcher defensive signals", top_pitchers)
    print_pitcher_board("Weakest pitcher defensive signals", weak_pitchers)

    print()
    print("Salary-board hitter correction cases: top-50 salary-adjusted, weak defense")
    print("-" * 104)
    print("s_rank salary_score def_score best_pos player")
    for salary_rank, salary_score, defense_score, row, _salary_row in sorted(salary_corrections_hitters):
        best = row.get("bestPosition")
        best_raw = best.get("raw") if best else "DEFENSE_UNAVAILABLE"
        print(
            f"{salary_rank:>6} "
            f"{salary_score:>12.3f} "
            f"{defense_score:>9.3f} "
            f"{best_raw:>13} "
            f"{player_label(row)}"
        )

    print()
    print("Salary-board pitcher correction cases: top-50 salary-adjusted, weak defense")
    print("-" * 104)
    print("s_rank salary_score def_score pdef hold wp bk player")
    for salary_rank, salary_score, defense_score, row, _salary_row in sorted(salary_corrections_pitchers):
        raw = row.get("raw", {})
        print(
            f"{salary_rank:>6} "
            f"{salary_score:>12.3f} "
            f"{defense_score:>9.3f} "
            f"{raw.get('pitcherDefense'):>4} "
            f"{raw.get('hold'):>4} "
            f"{raw.get('wildPitch'):>2} "
            f"{raw.get('balk'):>2} "
            f"{player_label(row)}"
        )

    print("=" * 104)


if __name__ == "__main__":
    main()
