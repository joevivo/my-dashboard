from __future__ import annotations

from pathlib import Path
import json
from typing import Any


PATH = Path("data/baseball/parsed/strat365/1980/draft-signals/1980.defense-aware-draft-signals.json")


def score(payload: dict[str, Any] | None) -> float:
    if not payload:
        return 0.0
    return float(payload.get("score", 0.0))


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


def delta(row: dict[str, Any]) -> int:
    return int(row["salaryAdjustedRank"]) - int(row["defenseAwareRank"])


def print_hitter_bucket(title: str, rows: list[dict[str, Any]], limit: int = 20) -> None:
    print()
    print(title)
    print("-" * 116)
    print("d_rank s_rank delta d_score salary def neutral best_pos player")
    for row in rows[:limit]:
        print(
            f'{row["defenseAwareRank"]:>6} '
            f'{row["salaryAdjustedRank"]:>6} '
            f'{delta(row):>5} '
            f'{score(row["defenseAwareDraftScore"]):>7.3f} '
            f'{score(row["salaryAdjustedScore"]):>6.3f} '
            f'{score(row["defensiveScore"]):>6.3f} '
            f'{score(row["neutralDraftScore"]):>7.3f} '
            f'{best_pos(row):>14} '
            f'{label(row)}'
        )


def print_pitcher_bucket(title: str, rows: list[dict[str, Any]], limit: int = 20) -> None:
    print()
    print(title)
    print("-" * 116)
    print("d_rank s_rank delta d_score salary def neutral raw player")
    for row in rows[:limit]:
        print(
            f'{row["defenseAwareRank"]:>6} '
            f'{row["salaryAdjustedRank"]:>6} '
            f'{delta(row):>5} '
            f'{score(row["defenseAwareDraftScore"]):>7.3f} '
            f'{score(row["salaryAdjustedScore"]):>6.3f} '
            f'{score(row["defensiveScore"]):>6.3f} '
            f'{score(row["neutralDraftScore"]):>7.3f} '
            f'{pitcher_raw(row):>22} '
            f'{label(row)}'
        )


def main() -> None:
    data = json.loads(PATH.read_text(encoding="utf-8-sig", errors="replace"))

    hitters = data["hitters"]
    pitchers = data["pitchers"]

    hitter_core = [r for r in hitters if score(r["defenseAwareDraftScore"]) >= 70]
    hitter_safe_values = [r for r in hitters if score(r["defenseAwareDraftScore"]) >= 65 and score(r["defensiveScore"]) >= 70]
    hitter_glove_risers = [r for r in hitters if delta(r) >= 40]
    hitter_bat_first_risks = [r for r in hitters if int(r["salaryAdjustedRank"]) <= 75 and delta(r) <= -40]

    pitcher_core = [r for r in pitchers if score(r["defenseAwareDraftScore"]) >= 70]
    pitcher_safe_values = [r for r in pitchers if score(r["defenseAwareDraftScore"]) >= 65 and score(r["defensiveScore"]) >= 70]
    pitcher_defense_risers = [r for r in pitchers if delta(r) >= 20]
    pitcher_control_risks = [r for r in pitchers if int(r["salaryAdjustedRank"]) <= 75 and score(r["defensiveScore"]) < 40]

    print("BIE Defense-Aware Candidate Pool Inventory v0")
    print("=" * 116)
    print(f"Schema: {data.get('schemaVersion')}")
    print(f"Rankable hitters: {len(hitters)}")
    print(f"Rankable pitchers: {len(pitchers)}")
    print()
    print("Bucket counts")
    print("-" * 116)
    print(f"hitter_core: {len(hitter_core)}")
    print(f"hitter_safe_values: {len(hitter_safe_values)}")
    print(f"hitter_glove_risers: {len(hitter_glove_risers)}")
    print(f"hitter_bat_first_risks: {len(hitter_bat_first_risks)}")
    print(f"pitcher_core: {len(pitcher_core)}")
    print(f"pitcher_safe_values: {len(pitcher_safe_values)}")
    print(f"pitcher_defense_risers: {len(pitcher_defense_risers)}")
    print(f"pitcher_control_risks: {len(pitcher_control_risks)}")

    print_hitter_bucket("Hitter core defense-aware targets", hitter_core)
    print_hitter_bucket("Hitter safe values: defense-aware score >= 65 and defense >= 70", hitter_safe_values)
    print_hitter_bucket("Hitter glove risers versus salary board", sorted(hitter_glove_risers, key=delta, reverse=True))
    print_hitter_bucket("Hitter bat-first risk cases", sorted(hitter_bat_first_risks, key=delta))

    print_pitcher_bucket("Pitcher core defense-aware targets", pitcher_core)
    print_pitcher_bucket("Pitcher safe values: defense-aware score >= 65 and defense >= 70", pitcher_safe_values)
    print_pitcher_bucket("Pitcher defense/control risers versus salary board", sorted(pitcher_defense_risers, key=delta, reverse=True))
    print_pitcher_bucket("Pitcher control-risk cases", sorted(pitcher_control_risks, key=score_defense))

    print("=" * 116)


def score_defense(row: dict[str, Any]) -> float:
    return score(row["defensiveScore"])


if __name__ == "__main__":
    main()
