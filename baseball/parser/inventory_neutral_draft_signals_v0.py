from __future__ import annotations

from pathlib import Path
import json
from typing import Any


SIGNAL_PATH = Path("data/baseball/parsed/strat365/1980/draft-signals/1980.neutral-draft-signals.json")


def score(row: dict[str, Any]) -> float:
    return float(row.get("draftScore", {}).get("score", 0))


def comp(row: dict[str, Any], key: str) -> float:
    return float(row.get("componentScores", {}).get(key, {}).get("score", 0))


def avg(row: dict[str, Any], key: str) -> float:
    return float(row.get("sourceAverages", {}).get(key, {}).get("decimal", 0))


def player_label(row: dict[str, Any]) -> str:
    player = row.get("player", {})
    return f'{player.get("playerName")} team={player.get("team")}'


def print_hitter_board(title: str, rows: list[dict[str, Any]], *, limit: int = 15) -> None:
    print()
    print(title)
    print("-" * 96)
    print("score   ob    hit   pwr   con   ob_avg  hit_avg hr_avg  k_avg   player")
    for row in rows[:limit]:
        print(
            f'{score(row):6.2f} '
            f'{comp(row, "on_base"):5.1f} '
            f'{comp(row, "hit"):5.1f} '
            f'{comp(row, "power"):5.1f} '
            f'{comp(row, "contact"):5.1f} '
            f'{avg(row, "onBaseCandidateWeight"):7.4f} '
            f'{avg(row, "hitCandidateWeight"):7.4f} '
            f'{avg(row, "homeRunWeight"):7.4f} '
            f'{avg(row, "strikeoutWeight"):7.4f} '
            f'{player_label(row)}'
        )


def print_pitcher_board(title: str, rows: list[dict[str, Any]], *, limit: int = 15) -> None:
    print()
    print(title)
    print("-" * 104)
    print("score   obp   hitp  hrp   k     ob_avg  hit_avg hr_avg  k_avg   player")
    for row in rows[:limit]:
        print(
            f'{score(row):6.2f} '
            f'{comp(row, "on_base_prevention"):5.1f} '
            f'{comp(row, "hit_prevention"):5.1f} '
            f'{comp(row, "home_run_prevention"):5.1f} '
            f'{comp(row, "strikeout"):5.1f} '
            f'{avg(row, "onBaseCandidateWeight"):7.4f} '
            f'{avg(row, "hitCandidateWeight"):7.4f} '
            f'{avg(row, "homeRunWeight"):7.4f} '
            f'{avg(row, "strikeoutWeight"):7.4f} '
            f'{player_label(row)}'
        )


def print_component_leaders(title: str, rows: list[dict[str, Any]], component_key: str, *, limit: int = 12, reverse: bool = True) -> None:
    ranked = sorted(rows, key=lambda row: (comp(row, component_key), score(row), player_label(row)), reverse=reverse)

    print()
    print(title)
    print("-" * 72)
    for row in ranked[:limit]:
        print(f'{comp(row, component_key):6.2f} score={score(row):6.2f} {player_label(row)}')


def main() -> None:
    data = json.loads(SIGNAL_PATH.read_text(encoding="utf-8-sig", errors="replace"))

    hitters = data.get("hitters", [])
    pitchers = data.get("pitchers", [])
    unresolved_hitters = data.get("unresolved", {}).get("hitters", [])
    unresolved_pitchers = data.get("unresolved", {}).get("pitchers", [])

    print("BIE Neutral Draft Signal Inventory v0")
    print("=" * 104)
    print(f"Schema: {data.get('schemaVersion')}")
    print(f"Rankable hitters: {len(hitters)}")
    print(f"Unresolved hitters: {len(unresolved_hitters)}")
    print(f"Rankable pitchers: {len(pitchers)}")
    print(f"Unresolved pitchers: {len(unresolved_pitchers)}")

    print_hitter_board("Top neutral hitter draft signals", hitters)
    print_pitcher_board("Top neutral pitcher draft signals", pitchers)

    print_hitter_board("Lowest neutral hitter draft signals", list(reversed(hitters)), limit=12)
    print_pitcher_board("Lowest neutral pitcher draft signals", list(reversed(pitchers)), limit=12)

    print_component_leaders("Hitter component leaders: on-base", hitters, "on_base")
    print_component_leaders("Hitter component leaders: hit", hitters, "hit")
    print_component_leaders("Hitter component leaders: power", hitters, "power")
    print_component_leaders("Hitter component leaders: contact", hitters, "contact")

    print_component_leaders("Pitcher component leaders: on-base prevention", pitchers, "on_base_prevention")
    print_component_leaders("Pitcher component leaders: hit prevention", pitchers, "hit_prevention")
    print_component_leaders("Pitcher component leaders: home-run prevention", pitchers, "home_run_prevention")
    print_component_leaders("Pitcher component leaders: strikeout", pitchers, "strikeout")

    if unresolved_hitters:
        print()
        print("Unresolved hitters excluded from neutral draft board")
        print("-" * 72)
        for row in unresolved_hitters:
            print(f'{player_label(row)} exact={row.get("exactMatchups")} partial={row.get("partialMatchups")}')

    if unresolved_pitchers:
        print()
        print("Unresolved pitchers excluded from neutral draft board")
        print("-" * 72)
        for row in unresolved_pitchers:
            print(f'{player_label(row)} exact={row.get("exactMatchups")} partial={row.get("partialMatchups")}')

    print("=" * 104)


if __name__ == "__main__":
    main()
