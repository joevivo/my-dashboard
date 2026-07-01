from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]

DEFAULT_INPUT = ROOT / "data" / "baseball" / "parsed" / "strat365" / "1968" / "draft-signals" / "1968.browser-baseline-draft-signals.json"
DEFAULT_OUT = ROOT / "data" / "baseball" / "parsed" / "strat365" / "1968" / "reports" / "1968.browser-baseline-park-targets.md"

DEFAULT_PARKS = [
    "Wrigley Field 1968",
    "Crosley Field 1968",
    "Dodger Stadium 1968",
    "Astrodome 1968",
    "Busch Stadium 1968",
    "Oakland Coliseum 1968",
]


def score(payload: dict[str, Any]) -> float:
    return float(payload["score"])


def salary(row: dict[str, Any]) -> float:
    return float(row["salary"]["millions"])


def descriptor(row: dict[str, Any]) -> str:
    return row.get("hitter", {}).get("primaryPosition") or row.get("pitcher", {}).get("endurance") or ""


def park_fit(row: dict[str, Any], park_name: str) -> dict[str, Any]:
    for fit in row["ballparkFits"]:
        if fit["ballparkName"] == park_name:
            return fit
    raise KeyError(f"Missing park fit for {park_name}")


def movement_delta(row: dict[str, Any], fit: dict[str, Any]) -> float:
    return score(fit["parkAdjustedBrowserScore"]) - score(row["browserBaselineDraftScore"])


def player_line(row: dict[str, Any], fit: dict[str, Any]) -> str:
    player = row["player"]
    base_score = score(row["browserBaselineDraftScore"])
    park_score = score(fit["parkAdjustedBrowserScore"])
    delta = park_score - base_score

    return (
        f"- {player['playerName']} | {player['team']} | {descriptor(row)} | {row['salary']['raw']} | "
        f"global {row['browserBaselineRank']} -> park {fit['parkAdjustedBrowserRank']} | "
        f"{base_score:.2f} -> {park_score:.2f} ({delta:+.2f})"
    )


def park_rows(rows: list[dict[str, Any]], park_name: str) -> list[tuple[float, dict[str, Any], dict[str, Any]]]:
    output = []
    for row in rows:
        fit = park_fit(row, park_name)
        output.append((score(fit["parkAdjustedBrowserScore"]), row, fit))
    return sorted(output, reverse=True, key=lambda item: item[0])


def add_player_rows(
    lines: list[str],
    title: str,
    rows: list[tuple[float, dict[str, Any], dict[str, Any]]],
    limit: int = 12,
) -> None:
    lines.append("")
    lines.append(f"### {title}")
    lines.append("")

    if not rows:
        lines.append("- n/a")
        return

    for _park_score, row, fit in rows[:limit]:
        lines.append(player_line(row, fit))


def park_summary_label(park_name: str) -> str:
    if park_name in {"Wrigley Field 1968", "Crosley Field 1968"}:
        return "hitter-build"
    if park_name in {"Dodger Stadium 1968", "Astrodome 1968", "Busch Stadium 1968", "Oakland Coliseum 1968"}:
        return "pitcher-build"
    return "conditional"


def main() -> int:
    parser = argparse.ArgumentParser(description="Report 1968 browser-baseline park-specific player targets.")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--parks", nargs="*", default=DEFAULT_PARKS)
    args = parser.parse_args()

    data = json.loads(args.input.read_text(encoding="utf-8"))
    hitters = data["hitters"]
    pitchers = data["pitchers"]

    lines: list[str] = [
        "# 1968 Browser-Baseline Park Targets",
        "",
        f"Source: `{args.input.relative_to(ROOT).as_posix()}`",
        "",
        "This report identifies player target pools for selected 1968 park archetypes.",
        "",
        "Model limitation: this is public-browser-data only. It does not use authenticated card probabilities.",
        "",
        "Target-pool definitions:",
        "",
        "- Top park-adjusted players: highest park-adjusted browser score in that park.",
        "- Cheap park-usable hitter: salary <= $3.00M and park-adjusted score >= 40.",
        "- Cheap park-usable pitcher: salary <= $2.00M and park-adjusted score >= 60.",
        "",
        "## Executive Read",
        "",
        "- Wrigley Field 1968 and Crosley Field 1968 support hitter-first construction.",
        "- Dodger Stadium 1968, Astrodome 1968, Busch Stadium 1968, and Oakland Coliseum 1968 support pitcher-first construction.",
        "- In hitter parks, cheap pitchers can remain usable but often take negative movement.",
        "- In pitcher parks, cheap hitters can remain usable but are usually not boosted.",
        "- This report should guide park-specific draft planning, not final card-probability ranking.",
    ]

    for park in args.parks:
        hitter_rows = park_rows(hitters, park)
        pitcher_rows = park_rows(pitchers, park)

        cheap_hitters = [
            item for item in hitter_rows
            if salary(item[1]) <= 3.0 and score(item[2]["parkAdjustedBrowserScore"]) >= 40
        ]

        cheap_pitchers = [
            item for item in pitcher_rows
            if salary(item[1]) <= 2.0 and score(item[2]["parkAdjustedBrowserScore"]) >= 60
        ]

        positive_cheap_hitters = [
            item for item in cheap_hitters
            if movement_delta(item[1], item[2]) > 0
        ]

        positive_cheap_pitchers = [
            item for item in cheap_pitchers
            if movement_delta(item[1], item[2]) > 0
        ]

        lines.append("")
        lines.append(f"## {park}")
        lines.append("")
        lines.append(f"Archetype: **{park_summary_label(park)}**")
        lines.append("")
        lines.append(f"- Cheap park-usable hitters: {len(cheap_hitters)}")
        lines.append(f"- Cheap park-usable pitchers: {len(cheap_pitchers)}")
        lines.append(f"- Cheap hitters with positive park movement: {len(positive_cheap_hitters)}")
        lines.append(f"- Cheap pitchers with positive park movement: {len(positive_cheap_pitchers)}")

        add_player_rows(lines, "Top Park-Adjusted Hitters", hitter_rows, limit=12)
        add_player_rows(lines, "Top Park-Adjusted Pitchers", pitcher_rows, limit=12)
        add_player_rows(lines, "Cheap Park-Usable Hitters", cheap_hitters, limit=15)
        add_player_rows(lines, "Cheap Park-Usable Pitchers", cheap_pitchers, limit=15)
        add_player_rows(lines, "Cheap Hitters With Positive Park Movement", positive_cheap_hitters, limit=12)
        add_player_rows(lines, "Cheap Pitchers With Positive Park Movement", positive_cheap_pitchers, limit=12)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print("Wrote:", args.out)
    print()
    print("\n".join(lines[:180]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
