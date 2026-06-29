from __future__ import annotations

from pathlib import Path
import json
from typing import Any


SIGNAL_PATH = Path("data/baseball/parsed/strat365/1980/draft-signals/1980.salary-adjusted-draft-signals.json")


def player_label(row: dict[str, Any]) -> str:
    player = row.get("player", {})
    salary = row.get("salary", {}).get("raw", "(salary?)")
    return f'{player.get("playerName")} team={player.get("team")} salary={salary}'


def balanced(row: dict[str, Any]) -> float:
    return float(row.get("salaryValue", {}).get("balancedValueScore", {}).get("score", 0))


def neutral(row: dict[str, Any]) -> float:
    return float(row.get("neutralDraftScore", {}).get("score", 0))


def value(row: dict[str, Any]) -> float:
    return float(row.get("salaryValue", {}).get("valuePercentile", {}).get("score", 0))


def per_million(row: dict[str, Any]) -> float:
    return float(row.get("salaryValue", {}).get("signalPerMillion", {}).get("decimal", 0))


def salary_decimal(row: dict[str, Any]) -> float:
    return float(row.get("salary", {}).get("millions", {}).get("decimal", 0))


def print_board(title: str, rows: list[dict[str, Any]], *, limit: int = 15) -> None:
    print()
    print(title)
    print("-" * 104)
    print("bal     neutral value   per_m   salary  s_rank player")
    for row in rows[:limit]:
        print(
            f"{balanced(row):7.3f} "
            f"{neutral(row):7.3f} "
            f"{value(row):7.3f} "
            f"{per_million(row):7.3f} "
            f"{salary_decimal(row):6.2f} "
            f"{row.get('salaryAdjustedRank', ''):6} "
            f"{player_label(row)}"
        )


def print_rank_delta(title: str, rows: list[dict[str, Any]], neutral_rows: list[dict[str, Any]], *, limit: int = 15) -> None:
    neutral_rank = {
        int(row["player"]["playerId"]): index
        for index, row in enumerate(neutral_rows, start=1)
    }

    deltas = []

    for row in rows:
        player_id = int(row["player"]["playerId"])
        s_rank = int(row["salaryAdjustedRank"])
        n_rank = neutral_rank[player_id]
        deltas.append((n_rank - s_rank, n_rank, s_rank, row))

    deltas.sort(reverse=True, key=lambda item: (item[0], value(item[3]), balanced(item[3])))

    print()
    print(title)
    print("-" * 104)
    print("delta  neutral salary  bal     value   salary  player")
    for delta, n_rank, s_rank, row in deltas[:limit]:
        print(
            f"{delta:5} "
            f"{n_rank:7} "
            f"{s_rank:6} "
            f"{balanced(row):7.3f} "
            f"{value(row):7.3f} "
            f"{salary_decimal(row):6.2f} "
            f"{player_label(row)}"
        )


def main() -> None:
    data = json.loads(SIGNAL_PATH.read_text(encoding="utf-8-sig", errors="replace"))

    hitters = data.get("hitters", [])
    pitchers = data.get("pitchers", [])
    unresolved_hitters = data.get("unresolved", {}).get("hitters", [])
    unresolved_pitchers = data.get("unresolved", {}).get("pitchers", [])

    neutral_hitters = sorted(hitters, key=lambda row: neutral(row), reverse=True)
    neutral_pitchers = sorted(pitchers, key=lambda row: neutral(row), reverse=True)

    hitter_bargains = sorted(hitters, key=lambda row: (value(row), neutral(row)), reverse=True)
    pitcher_bargains = sorted(pitchers, key=lambda row: (value(row), neutral(row)), reverse=True)

    hitter_stars = sorted(hitters, key=lambda row: neutral(row), reverse=True)
    pitcher_stars = sorted(pitchers, key=lambda row: neutral(row), reverse=True)

    print("BIE Salary-Adjusted Draft Signal Inventory v0")
    print("=" * 104)
    print(f"Schema: {data.get('schemaVersion')}")
    print(f"Rankable hitters: {len(hitters)}")
    print(f"Unresolved hitters: {len(unresolved_hitters)}")
    print(f"Rankable pitchers: {len(pitchers)}")
    print(f"Unresolved pitchers: {len(unresolved_pitchers)}")

    print_board("Top salary-adjusted hitters", hitters)
    print_board("Top salary-adjusted pitchers", pitchers)

    print_board("Top hitter bargains by value percentile", hitter_bargains)
    print_board("Top pitcher bargains by value percentile", pitcher_bargains)

    print_board("Top neutral hitters, salary-adjusted view", hitter_stars)
    print_board("Top neutral pitchers, salary-adjusted view", pitcher_stars)

    print_rank_delta("Biggest hitter rank gains after salary adjustment", hitters, neutral_hitters)
    print_rank_delta("Biggest pitcher rank gains after salary adjustment", pitchers, neutral_pitchers)

    if unresolved_hitters:
        print()
        print("Unresolved hitters excluded")
        print("-" * 104)
        for row in unresolved_hitters:
            print(f"{player_label(row)} exact={row.get('exactMatchups')} partial={row.get('partialMatchups')}")

    if unresolved_pitchers:
        print()
        print("Unresolved pitchers excluded")
        print("-" * 104)
        for row in unresolved_pitchers:
            print(f"{player_label(row)} exact={row.get('exactMatchups')} partial={row.get('partialMatchups')}")

    print("=" * 104)


if __name__ == "__main__":
    main()
