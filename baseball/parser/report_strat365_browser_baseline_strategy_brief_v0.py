from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]

DEFAULT_INPUT = ROOT / "data" / "baseball" / "parsed" / "strat365" / "1968" / "draft-signals" / "1968.browser-baseline-draft-signals.json"
DEFAULT_OUT = ROOT / "data" / "baseball" / "parsed" / "strat365" / "1968" / "reports" / "1968.browser-baseline-strategy-brief.md"


def score(payload: dict[str, Any]) -> float:
    return float(payload["score"])


def salary(row: dict[str, Any]) -> float:
    return float(row["salary"]["millions"])


def spread(row: dict[str, Any]) -> float:
    return score(row["ballparkProfile"]["fitSpread"])


def best_park(row: dict[str, Any]) -> str:
    return str(row["ballparkProfile"]["bestFit"]["ballparkName"])


def worst_park(row: dict[str, Any]) -> str:
    return str(row["ballparkProfile"]["worstFit"]["ballparkName"])


def descriptor(row: dict[str, Any]) -> str:
    return row.get("hitter", {}).get("primaryPosition") or row.get("pitcher", {}).get("endurance") or ""


def player_line(row: dict[str, Any]) -> str:
    player = row["player"]
    return (
        f"- {player['playerName']} | {player['team']} | {descriptor(row)} | {row['salary']['raw']} | "
        f"rank {row['browserBaselineRank']} | score {score(row['browserBaselineDraftScore']):.2f} | "
        f"spread {spread(row):.2f} | best {best_park(row)} | worst {worst_park(row)}"
    )


def add_section(lines: list[str], title: str, rows: list[dict[str, Any]], limit: int = 12) -> None:
    lines.append("")
    lines.append(f"## {title}")
    lines.append("")

    if not rows:
        lines.append("- n/a")
        return

    for row in rows[:limit]:
        lines.append(player_line(row))


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a 1968 browser-baseline draft strategy brief.")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    data = json.loads(args.input.read_text(encoding="utf-8"))
    hitters = data["hitters"]
    pitchers = data["pitchers"]

    hitter_values = [
        row for row in hitters
        if salary(row) <= 3.0 and score(row["browserBaselineDraftScore"]) >= 40
    ]
    pitcher_values = [
        row for row in pitchers
        if salary(row) <= 2.0 and score(row["browserBaselineDraftScore"]) >= 60
    ]

    hitter_anchors = [
        row for row in hitters
        if salary(row) >= 7.0 and score(row["browserBaselineDraftScore"]) >= 55
    ]
    pitcher_anchors = [
        row for row in pitchers
        if salary(row) >= 6.0 and score(row["browserBaselineDraftScore"]) >= 65
    ]

    high_spread_hitter_anchors = sorted(
        [row for row in hitter_anchors if spread(row) >= 8.0],
        key=lambda row: spread(row),
        reverse=True,
    )
    high_spread_pitcher_anchors = sorted(
        [row for row in pitcher_anchors if spread(row) >= 8.0],
        key=lambda row: spread(row),
        reverse=True,
    )

    low_spread_values = sorted(
        [
            row for row in hitter_values + pitcher_values
            if spread(row) <= 5.0
        ],
        key=lambda row: score(row["browserBaselineDraftScore"]),
        reverse=True,
    )

    cheap_pitcher_core = [
        row for row in pitcher_values
        if score(row["browserBaselineDraftScore"]) >= 65
    ]

    thin_hitter_value = [
        row for row in hitter_values
        if score(row["browserBaselineDraftScore"]) >= 43
    ]

    lines: list[str] = [
        "# 1968 Browser-Baseline Strategy Brief",
        "",
        f"Source: `{args.input.relative_to(ROOT).as_posix()}`",
        "",
        "This is a public-browser-data strategy brief. It is not full card-probability BIE intelligence.",
        "",
        "## Executive Read",
        "",
        "- Cheap pitching appears materially deeper than cheap hitting.",
        "- Expensive hitters are often highly park-sensitive; do not draft them independent of park context.",
        "- Pitcher spend anchors remain strong, but many are materially exposed in Wrigley-style environments.",
        "- Low-spread safe profiles are rare under the current browser-baseline model.",
        "- The immediate practical edge is identifying low-cost pitching and avoiding park-mismatched expensive bats.",
        "",
        "## Draft Hypotheses",
        "",
        "1. In pitcher-protective parks, lean into the deep cheap-pitching pool and reserve salary for scarce offense.",
        "2. In Wrigley-style hitter parks, do not overpay for pitchers whose browser-baseline spread shows material exposure.",
        "3. Treat high-spread expensive hitters as park-dependent assets, not universal anchors.",
        "4. Because cheap hitter value is shallow, useful low-cost bats should be identified early rather than treated as replaceable.",
        "5. Use this as draft triage only until authenticated 1968 card probabilities are available.",
        "",
        "## Summary Counts",
        "",
        f"- Hitter value candidates <= $3.00M and score >= 40: {len(hitter_values)}",
        f"- Pitcher value candidates <= $2.00M and score >= 60: {len(pitcher_values)}",
        f"- High-spread hitter spend anchors: {len(high_spread_hitter_anchors)}",
        f"- High-spread pitcher spend anchors: {len(high_spread_pitcher_anchors)}",
        f"- Low-spread value candidates: {len(low_spread_values)}",
    ]

    add_section(lines, "Cheap Pitcher Core", cheap_pitcher_core, limit=18)
    add_section(lines, "Thin Hitter Value Pool", thin_hitter_value, limit=18)
    add_section(lines, "High-Spread Expensive Hitters", high_spread_hitter_anchors, limit=18)
    add_section(lines, "High-Spread Expensive Pitchers", high_spread_pitcher_anchors, limit=18)
    add_section(lines, "Low-Spread Value Candidates", low_spread_values, limit=18)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print("Wrote:", args.out)
    print()
    print("\n".join(lines[:140]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
