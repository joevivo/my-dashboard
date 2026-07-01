from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]

DEFAULT_INPUT = ROOT / "data" / "baseball" / "parsed" / "strat365" / "1968" / "draft-signals" / "1968.browser-baseline-draft-signals.json"
DEFAULT_OUT = ROOT / "data" / "baseball" / "parsed" / "strat365" / "1968" / "reports" / "1968.browser-baseline-park-archetypes.md"


def score(payload: dict[str, Any]) -> float:
    return float(payload["score"])


def salary(row: dict[str, Any]) -> float:
    return float(row["salary"]["millions"])


def descriptor(row: dict[str, Any]) -> str:
    return row.get("hitter", {}).get("primaryPosition") or row.get("pitcher", {}).get("endurance") or ""


def movement_delta(row: dict[str, Any], fit: dict[str, Any]) -> float:
    return score(fit["parkAdjustedBrowserScore"]) - score(row["browserBaselineDraftScore"])


def movement_line(row: dict[str, Any], fit: dict[str, Any]) -> str:
    player = row["player"]
    base_score = score(row["browserBaselineDraftScore"])
    park_score = score(fit["parkAdjustedBrowserScore"])
    delta = park_score - base_score

    return (
        f"- {player['playerName']} | {player['team']} | {descriptor(row)} | {row['salary']['raw']} | "
        f"global {row['browserBaselineRank']} -> park {fit['parkAdjustedBrowserRank']} | "
        f"{base_score:.2f} -> {park_score:.2f} ({delta:+.2f})"
    )


def park_label(bucket: dict[str, Any]) -> str:
    hitter_net = bucket["hitter_true_boosts"] - bucket["hitter_casualties"]
    pitcher_net = bucket["pitcher_true_boosts"] - bucket["pitcher_casualties"]

    if hitter_net >= 100 and pitcher_net < 0:
        return "extreme hitter-build"
    if hitter_net >= 25 and pitcher_net < 0:
        return "selective hitter-build"
    if pitcher_net >= 100 and hitter_net < 0:
        return "extreme pitcher-build"
    if pitcher_net >= 25 and hitter_net <= 0:
        return "selective pitcher-build"
    if hitter_net == 0 and pitcher_net == 0:
        return "neutral/low-signal"
    return "mixed/conditional"


def build_buckets(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    parks: dict[str, dict[str, Any]] = defaultdict(lambda: {
        "hitter_true_boosts": 0,
        "pitcher_true_boosts": 0,
        "hitter_casualties": 0,
        "pitcher_casualties": 0,
        "cheap_hitter_boosts": [],
        "cheap_pitcher_boosts": [],
    })

    for row in rows:
        role = row["role"]
        base_rank = int(row["browserBaselineRank"])

        for fit in row["ballparkFits"]:
            park = fit["ballparkName"]
            delta = movement_delta(row, fit)
            rank_delta = base_rank - int(fit["parkAdjustedBrowserRank"])
            bucket = parks[park]

            if role == "hitter":
                if delta >= 2.0:
                    bucket["hitter_true_boosts"] += 1
                    if salary(row) <= 3.0:
                        bucket["cheap_hitter_boosts"].append((delta, row, fit))
                if delta <= -2.0 and rank_delta <= -10:
                    bucket["hitter_casualties"] += 1

            if role == "pitcher":
                if delta >= 2.0:
                    bucket["pitcher_true_boosts"] += 1
                    if salary(row) <= 2.0:
                        bucket["cheap_pitcher_boosts"].append((delta, row, fit))
                if delta <= -2.0 and rank_delta <= -10:
                    bucket["pitcher_casualties"] += 1

    return parks


def add_player_section(
    lines: list[str],
    title: str,
    bucket_key: str,
    parks: dict[str, dict[str, Any]],
    limit_parks: int,
    limit_players: int,
) -> None:
    lines.append("")
    lines.append(f"## {title}")
    lines.append("")

    selected_parks = sorted(
        parks.items(),
        key=lambda item: len(item[1][bucket_key]),
        reverse=True,
    )[:limit_parks]

    for park, bucket in selected_parks:
        rows = sorted(bucket[bucket_key], key=lambda item: item[0], reverse=True)
        lines.append(f"### {park} - {bucket_key.replace('_', ' ')}: {len(rows)}")
        lines.append("")

        if not rows:
            lines.append("- n/a")
            lines.append("")
            continue

        for _delta, row, fit in rows[:limit_players]:
            lines.append(movement_line(row, fit))
        lines.append("")


def main() -> int:
    parser = argparse.ArgumentParser(description="Report 1968 browser-baseline park archetypes.")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    data = json.loads(args.input.read_text(encoding="utf-8"))
    rows = data["hitters"] + data["pitchers"]
    parks = build_buckets(rows)

    summary = []
    for park, bucket in parks.items():
        hitter_net = bucket["hitter_true_boosts"] - bucket["hitter_casualties"]
        pitcher_net = bucket["pitcher_true_boosts"] - bucket["pitcher_casualties"]
        summary.append((hitter_net, pitcher_net, park, bucket))

    lines: list[str] = [
        "# 1968 Browser-Baseline Park Archetypes",
        "",
        f"Source: `{args.input.relative_to(ROOT).as_posix()}`",
        "",
        "This report classifies 1968 parks by how they move browser-baseline hitter and pitcher draft scores.",
        "",
        "Model limitation: this is public-browser-data only. It does not use authenticated card probabilities.",
        "",
        "Movement thresholds:",
        "",
        "- True boost: park-adjusted score improves by at least 2.0 points.",
        "- Casualty: park-adjusted score declines by at least 2.0 points and rank falls by at least 10 spots.",
        "- Cheap hitter boost: true hitter boost with salary <= $3.00M.",
        "- Cheap pitcher boost: true pitcher boost with salary <= $2.00M.",
        "",
        "## Executive Read",
        "",
        "- Wrigley Field 1968 is the extreme hitter-build park.",
        "- Crosley Field 1968 is the secondary hitter-build park.",
        "- Dodger Stadium 1968, Astrodome 1968, Busch Stadium 1968, D.C. Stadium 1968, and Oakland Coliseum 1968 are the clearest pitcher-build parks.",
        "- Park choice materially determines whether the cheap-pitching edge is exploitable or exposed.",
        "",
        "## Park Summary",
        "",
    ]

    for hitter_net, pitcher_net, park, bucket in sorted(summary, reverse=True):
        lines.append(
            f"- {park} | {park_label(bucket)} | "
            f"hitter boosts {bucket['hitter_true_boosts']} / casualties {bucket['hitter_casualties']} / net {hitter_net} | "
            f"pitcher boosts {bucket['pitcher_true_boosts']} / casualties {bucket['pitcher_casualties']} / net {pitcher_net} | "
            f"cheap hitter boosts {len(bucket['cheap_hitter_boosts'])} | cheap pitcher boosts {len(bucket['cheap_pitcher_boosts'])}"
        )

    add_player_section(lines, "Best Cheap-Hitter Boost Parks", "cheap_hitter_boosts", parks, 8, 10)
    add_player_section(lines, "Best Cheap-Pitcher Boost Parks", "cheap_pitcher_boosts", parks, 8, 10)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print("Wrote:", args.out)
    print()
    print("\n".join(lines[:150]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
