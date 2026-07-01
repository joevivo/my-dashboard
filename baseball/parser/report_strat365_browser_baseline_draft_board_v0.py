from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]

DEFAULT_INPUT = ROOT / "data" / "baseball" / "parsed" / "strat365" / "1968" / "draft-signals" / "1968.browser-baseline-draft-signals.json"
DEFAULT_OUT = ROOT / "data" / "baseball" / "parsed" / "strat365" / "1968" / "reports" / "1968.browser-baseline-draft-board.md"


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
        f"global {row['browserBaselineRank']} | score {score(row['browserBaselineDraftScore']):.2f} | "
        f"spread {spread(row):.2f} | best {best_park(row)} | worst {worst_park(row)}"
    )


def add_section(lines: list[str], title: str, rows: list[dict[str, Any]], limit: int | None = None) -> None:
    lines.append("")
    lines.append(f"## {title}")
    lines.append("")

    selected = rows if limit is None else rows[:limit]
    if not selected:
        lines.append("- n/a")
        return

    for row in selected:
        lines.append(player_line(row))


def main() -> int:
    parser = argparse.ArgumentParser(description="Report 1968 browser-baseline draft-board tiers.")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    data = json.loads(args.input.read_text(encoding="utf-8"))
    hitters = data["hitters"]
    pitchers = data["pitchers"]

    hitter_spend_anchors = [row for row in hitters if salary(row) >= 7.0]
    pitcher_spend_anchors = [row for row in pitchers if salary(row) >= 6.0]

    hitter_values = [
        row for row in hitters
        if salary(row) <= 3.0 and score(row["browserBaselineDraftScore"]) >= 40
    ]
    pitcher_values = [
        row for row in pitchers
        if salary(row) <= 2.0 and score(row["browserBaselineDraftScore"]) >= 60
    ]

    hitter_traps = sorted(
        [row for row in hitters if spread(row) >= 8 and salary(row) >= 5.0],
        key=lambda row: spread(row),
        reverse=True,
    )
    pitcher_traps = sorted(
        [row for row in pitchers if spread(row) >= 8 and salary(row) >= 4.0],
        key=lambda row: spread(row),
        reverse=True,
    )

    safer_hitters = [
        row for row in hitters
        if score(row["browserBaselineDraftScore"]) >= 50 and spread(row) <= 5
    ]
    safer_pitchers = [
        row for row in pitchers
        if score(row["browserBaselineDraftScore"]) >= 65 and spread(row) <= 5
    ]

    lines: list[str] = [
        "# 1968 Browser-Baseline Draft Board",
        "",
        f"Source: `{args.input.relative_to(ROOT).as_posix()}`",
        "",
        "This report turns the browser-baseline draft signals into draft-board tiers.",
        "",
        "Model limitation: this is public-browser-data only. It does not use authenticated card probabilities.",
        "",
        "Interpretation rules:",
        "",
        "- **Spend anchors** are expensive players who may justify major salary allocation.",
        "- **Value candidates** are lower-cost players with useful baseline scores.",
        "- **Park-sensitive draft traps** are expensive players whose value changes materially by park.",
        "- **Low-spread safer players** are less park-dependent under the current browser model.",
        "",
        "Thresholds:",
        "",
        "- Hitter spend anchor: salary >= $7.00M.",
        "- Pitcher spend anchor: salary >= $6.00M.",
        "- Hitter value candidate: salary <= $3.00M and baseline score >= 40.",
        "- Pitcher value candidate: salary <= $2.00M and baseline score >= 60.",
        "- Draft trap: fit spread >= 8 with hitter salary >= $5.00M or pitcher salary >= $4.00M.",
    ]

    add_section(lines, "Hitter Spend Anchors >= $7.00M", hitter_spend_anchors)
    add_section(lines, "Pitcher Spend Anchors >= $6.00M", pitcher_spend_anchors)
    add_section(lines, "Hitter Value Candidates <= $3.00M and score >= 40", hitter_values)
    add_section(lines, "Pitcher Value Candidates <= $2.00M and score >= 60", pitcher_values)
    add_section(lines, "Hitter Park-Sensitive Draft Traps", hitter_traps, limit=40)
    add_section(lines, "Pitcher Park-Sensitive Draft Traps", pitcher_traps, limit=40)
    add_section(lines, "Low-Spread Safer Hitters", safer_hitters)
    add_section(lines, "Low-Spread Safer Pitchers", safer_pitchers)

    lines.append("")
    lines.append("## Summary Counts")
    lines.append("")
    lines.append(f"- Hitter spend anchors: {len(hitter_spend_anchors)}")
    lines.append(f"- Pitcher spend anchors: {len(pitcher_spend_anchors)}")
    lines.append(f"- Hitter value candidates: {len(hitter_values)}")
    lines.append(f"- Pitcher value candidates: {len(pitcher_values)}")
    lines.append(f"- Hitter park-sensitive draft traps: {len(hitter_traps)}")
    lines.append(f"- Pitcher park-sensitive draft traps: {len(pitcher_traps)}")
    lines.append(f"- Low-spread safer hitters: {len(safer_hitters)}")
    lines.append(f"- Low-spread safer pitchers: {len(safer_pitchers)}")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print("Wrote:", args.out)
    print()
    print("\n".join(lines[:140]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
