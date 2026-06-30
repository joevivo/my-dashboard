from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]

DEFAULT_INPUT = ROOT / "data" / "baseball" / "parsed" / "strat365" / "1968" / "draft-signals" / "1968.browser-baseline-draft-signals.json"
DEFAULT_OUT = ROOT / "data" / "baseball" / "parsed" / "strat365" / "1968" / "reports" / "1968.browser-baseline-park-movers.md"

PARKS = [
    "Wrigley Field 1968",
    "Shea Stadium 1968",
    "Tiger Stadium 1968",
    "Astrodome 1968",
    "Dodger Stadium 1968",
    "Busch Stadium 1968",
    "Oakland Coliseum 1968",
    "Forbes Field 1968",
    "Crosley Field 1968",
    "Metro Stadium 1968",
]


def score(payload: dict[str, Any]) -> float:
    return float(payload["score"])


def fit_for(row: dict[str, Any], park_name: str) -> dict[str, Any]:
    return next(fit for fit in row["ballparkFits"] if fit["ballparkName"] == park_name)


def descriptor(row: dict[str, Any]) -> str:
    return row.get("hitter", {}).get("primaryPosition") or row.get("pitcher", {}).get("endurance") or ""


def movement(row: dict[str, Any], park_name: str) -> dict[str, Any]:
    fit = fit_for(row, park_name)
    global_rank = int(row["browserBaselineRank"])
    park_rank = int(fit["parkAdjustedBrowserRank"])
    baseline_score = score(row["browserBaselineDraftScore"])
    park_score = score(fit["parkAdjustedBrowserScore"])

    return {
        "row": row,
        "fit": fit,
        "globalRank": global_rank,
        "parkRank": park_rank,
        "rankDelta": global_rank - park_rank,
        "baselineScore": baseline_score,
        "parkScore": park_score,
        "scoreDelta": park_score - baseline_score,
    }


def player_line(item: dict[str, Any]) -> str:
    row = item["row"]
    player = row["player"]

    rank_delta = item["rankDelta"]
    rank_label = f"+{rank_delta}" if rank_delta >= 0 else str(rank_delta)

    return (
        f"- {player['playerName']} | {player['team']} | {descriptor(row)} | {row['salary']['raw']} | "
        f"global {item['globalRank']} -> park {item['parkRank']} | "
        f"rank {rank_label} | score {item['baselineScore']:.2f} -> {item['parkScore']:.2f} "
        f"({item['scoreDelta']:+.2f})"
    )


def section(lines: list[str], title: str, items: list[dict[str, Any]], limit: int = 10) -> None:
    lines.append("")
    lines.append(f"### {title}")
    lines.append("")

    if not items:
        lines.append("- n/a")
        return

    for item in items[:limit]:
        lines.append(player_line(item))


def role_report(lines: list[str], role: str, rows: list[dict[str, Any]], park_name: str, affordable_limit: float) -> None:
    movements = [movement(row, park_name) for row in rows]

    true_boosts = [
        item for item in movements
        if item["scoreDelta"] >= 2.0
    ]
    true_boosts.sort(key=lambda item: (item["scoreDelta"], item["rankDelta"]), reverse=True)

    affordable_true_boosts = [
        item for item in true_boosts
        if float(item["row"]["salary"]["millions"]) <= affordable_limit
    ]

    relative_only = [
        item for item in movements
        if item["rankDelta"] >= 10 and item["scoreDelta"] < 0
    ]
    relative_only.sort(key=lambda item: (item["rankDelta"], item["scoreDelta"]), reverse=True)

    casualties = [
        item for item in movements
        if item["scoreDelta"] <= -2.0 and item["rankDelta"] <= -10
    ]
    casualties.sort(key=lambda item: (item["scoreDelta"], item["rankDelta"]))

    lines.append("")
    lines.append(f"## {park_name} — {role.title()}")
    lines.append("")

    section(lines, "True park boosts", true_boosts)
    section(lines, f"Affordable true boosts <= ${affordable_limit:.2f}M", affordable_true_boosts)
    section(lines, "Relative-only rank movers", relative_only)
    section(lines, "Park casualties", casualties)


def main() -> int:
    parser = argparse.ArgumentParser(description="Report true park movers from 1968 browser-baseline draft signals.")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    data = json.loads(args.input.read_text(encoding="utf-8"))

    lines: list[str] = [
        "# 1968 Browser-Baseline Park Movers",
        "",
        f"Source: `{args.input.relative_to(ROOT).as_posix()}`",
        "",
        "This report separates true score movement from relative rank movement.",
        "",
        "- **True park boost**: park-adjusted score improves by at least 2.0 points.",
        "- **Relative-only mover**: rank improves by at least 10 spots but score declines.",
        "- **Park casualty**: score declines by at least 2.0 points and rank falls by at least 10 spots.",
        "",
        "Model limitation: this is browser-baseline only. It does not use authenticated card probabilities.",
    ]

    for park_name in PARKS:
        role_report(lines, "hitters", data["hitters"], park_name, affordable_limit=3.00)
        role_report(lines, "pitchers", data["pitchers"], park_name, affordable_limit=2.00)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print("Wrote:", args.out)
    print()
    print("\n".join(lines[:120]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
