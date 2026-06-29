from __future__ import annotations

from collections import Counter
from fractions import Fraction
from pathlib import Path
import json
from typing import Any


SUMMARY_DIR = Path("data/baseball/parsed/strat365/1980/card-probability-summaries")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig", errors="replace"))


def frac(payload: dict[str, Any] | None) -> Fraction:
    if not payload:
        return Fraction(0, 1)
    return Fraction(payload["numerator"], payload["denominator"])


def fmt(value: Fraction) -> str:
    return f"{float(value):.4f}"


def outcome(side: dict[str, Any], label: str) -> Fraction:
    return frac(side.get("baseOutcomeWeights", {}).get(label))


def row(data: dict[str, Any], side: dict[str, Any]) -> dict[str, Any]:
    player = data.get("player", {})
    return {
        "playerId": player.get("playerId"),
        "playerName": player.get("playerName"),
        "team": player.get("team"),
        "role": data.get("role"),
        "side": side.get("side"),
        "exact": frac(side.get("exactWeightTotal")),
        "onBase": frac(side.get("onBaseCandidateWeight")),
        "hit": frac(side.get("hitCandidateWeight")),
        "out": frac(side.get("outCandidateWeight")),
        "single": outcome(side, "SINGLE"),
        "double": outcome(side, "DOUBLE"),
        "triple": outcome(side, "TRIPLE"),
        "homeRun": outcome(side, "HOME_RUN"),
        "walk": outcome(side, "WALK"),
        "strikeout": outcome(side, "STRIKEOUT"),
        "gbx": outcome(side, "GROUNDBALL_X"),
        "fbx": outcome(side, "FLYBALL_X"),
        "unresolvedRows": len(side.get("unresolvedOutcomeRows", [])),
        "flags": sum(side.get("nonProbabilityFlagCounts", {}).values()),
    }


def print_top(title: str, rows: list[dict[str, Any]], metric: str, limit: int = 12, reverse: bool = True) -> None:
    print()
    print(title)
    print("-" * 72)

    ranked = sorted(rows, key=lambda r: (r[metric], r["playerName"] or ""), reverse=reverse)

    for item in ranked[:limit]:
        print(
            f'{fmt(item[metric])}  {item["playerName"]}  '
            f'role={item["role"]} side={item["side"]} team={item["team"]}'
        )


def main() -> None:
    paths = sorted(SUMMARY_DIR.glob("*.card-probability-summary.json"))

    role_counts: Counter[str] = Counter()
    side_total_counts: Counter[str] = Counter()
    rows: list[dict[str, Any]] = []

    for path in paths:
        data = read_json(path)
        role_counts[data.get("role")] += 1

        for side in data.get("sides", []):
            item = row(data, side)
            rows.append(item)
            side_total_counts[str(item["exact"])] += 1

    hitter_rows = [r for r in rows if r["role"] == "hitter"]
    pitcher_rows = [r for r in rows if r["role"] == "pitcher"]

    print("BIE Card Probability Summary Inventory v0")
    print("=" * 72)
    print(f"Summary files: {len(paths)}")
    print(f"Role counts: {dict(role_counts)}")
    print(f"Card sides: {len(rows)}")
    print(f"Side exact total counts: {dict(side_total_counts)}")
    print(f"Unresolved sides: {sum(1 for r in rows if r['unresolvedRows'])}")
    print(f"Non-probability flag sides: {sum(1 for r in rows if r['flags'])}")

    print_top("Top hitter sides by on-base candidate weight", hitter_rows, "onBase")
    print_top("Top hitter sides by hit candidate weight", hitter_rows, "hit")
    print_top("Top hitter sides by home run weight", hitter_rows, "homeRun")

    print_top("Top pitcher sides by strikeout weight", pitcher_rows, "strikeout")
    print_top("Lowest pitcher sides by on-base candidate weight", pitcher_rows, "onBase", reverse=False)

    print("=" * 72)


if __name__ == "__main__":
    main()
