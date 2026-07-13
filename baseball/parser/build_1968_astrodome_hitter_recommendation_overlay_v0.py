from __future__ import annotations

import csv
from pathlib import Path
from typing import Any


INPUT_CSV = Path("data/baseball/parsed/strat365/1968/draft-prep/1968.astrodome-hitter-position-tier-report-v0.csv")
OUT_CSV = Path("data/baseball/parsed/strat365/1968/draft-prep/1968.astrodome-hitter-recommendation-overlay-v0.csv")
OUT_MD = Path("data/baseball/parsed/strat365/1968/draft-prep/1968.astrodome-hitter-recommendation-overlay-v0.md")


RECOMMENDATION_ORDER = {
    "core_target": 1,
    "position_priority": 2,
    "useful_value": 3,
    "roster_structure_fallback": 4,
    "depth_review": 5,
    "avoid_or_emergency_only": 6,
}

SCARCE_POSITION_GROUPS = {"C", "Clean CF", "Clean SS", "Clean 2B", "Clean 3B"}


def to_float(value: Any, default: float = 0.0) -> float:
    try:
        if value in (None, ""):
            return default
        return float(value)
    except Exception:
        return default


def split_tags(value: str | None) -> list[str]:
    if not value:
        return []
    return [part for part in value.split(";") if part]


def classify(row: dict[str, str]) -> dict[str, str]:
    score = to_float(row.get("astrodomeScore"))
    salary = to_float(row.get("salary"))
    ob = to_float(row.get("weightedOB"))

    position_group = row.get("positionGroup", "")
    player_name = row.get("playerName", "")
    warnings = split_tags(row.get("warnings"))
    strengths = split_tags(row.get("strengths"))

    is_scarce_position = position_group in SCARCE_POSITION_GROUPS
    is_corner = position_group == "Corner Bat"

    if position_group == "C" and player_name == "Freehan, Bill":
        recommendation = "core_target"
    elif position_group == "Clean CF" and score >= 52 and len(warnings) <= 1:
        recommendation = "core_target"
    elif position_group == "Clean 2B" and score >= 48 and len(warnings) <= 1:
        recommendation = "position_priority"
    elif position_group == "Clean 3B" and score >= 50 and len(warnings) <= 1:
        recommendation = "position_priority"
    elif position_group == "Clean SS" and score >= 36 and len(warnings) <= 1:
        recommendation = "position_priority"
    elif is_corner and score >= 57 and len(warnings) <= 1:
        recommendation = "core_target"
    elif score >= 45 and ob >= 0.36 and len(warnings) <= 2:
        recommendation = "useful_value"
    elif is_scarce_position and salary < 3.0 and len(warnings) <= 2:
        recommendation = "roster_structure_fallback"
    elif len(warnings) >= 3 or (ob < 0.25 and not is_scarce_position):
        recommendation = "avoid_or_emergency_only"
    else:
        recommendation = "depth_review"

    return {
        "recommendation": recommendation,
        "positionGroup": position_group,
        "salaryTier": row.get("salaryTier", ""),
        "playerId": row.get("playerId", ""),
        "playerName": player_name,
        "team": row.get("team", ""),
        "salary": row.get("salary", ""),
        "bats": row.get("bats", ""),
        "primaryPosition": row.get("primaryPosition", ""),
        "browserDefense": row.get("browserDefense", ""),
        "astrodomeScore": row.get("astrodomeScore", ""),
        "weightedOB": row.get("weightedOB", ""),
        "weightedHit": row.get("weightedHit", ""),
        "weightedHR": row.get("weightedHR", ""),
        "weightedBB": row.get("weightedBB", ""),
        "weightedGB": row.get("weightedGB", ""),
        "weightedK": row.get("weightedK", ""),
        "strengths": ";".join(strengths),
        "warnings": ";".join(warnings),
    }


def sort_key(row: dict[str, str]) -> tuple[int, float]:
    return (
        RECOMMENDATION_ORDER.get(row.get("recommendation", ""), 99),
        -to_float(row.get("astrodomeScore")),
    )


def write_csv(rows: list[dict[str, str]]) -> None:
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "recommendation",
        "positionGroup",
        "salaryTier",
        "playerId",
        "playerName",
        "team",
        "salary",
        "bats",
        "primaryPosition",
        "browserDefense",
        "astrodomeScore",
        "weightedOB",
        "weightedHit",
        "weightedHR",
        "weightedBB",
        "weightedGB",
        "weightedK",
        "strengths",
        "warnings",
    ]

    with OUT_CSV.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_markdown(rows: list[dict[str, str]]) -> None:
    lines: list[str] = [
        "# 1968 Astrodome Hitter Recommendation Overlay",
        "",
        "Generated from the hitter position tier report.",
        "",
        "## Recommendation Counts",
        "",
    ]

    for rec in RECOMMENDATION_ORDER:
        count = sum(1 for row in rows if row.get("recommendation") == rec)
        lines.append(f"- {rec}: {count}")

    lines.extend(
        [
            "",
            "## Top Hitter Recommendations",
            "",
            "| Recommendation | Group | Player | Team | Salary | Pos | Def | Score | OB | HIT | HR | BB | GB | K | Strengths | Warnings |",
            "|---|---|---|---:|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|",
        ]
    )

    displayed = [
        row for row in rows
        if row.get("recommendation") != "avoid_or_emergency_only"
    ][:80]

    for row in displayed:
        lines.append(
            "| {recommendation} | {positionGroup} | {playerName} | {team} | {salary} | "
            "{primaryPosition} | {browserDefense} | {astrodomeScore} | {weightedOB} | "
            "{weightedHit} | {weightedHR} | {weightedBB} | {weightedGB} | {weightedK} | "
            "{strengths} | {warnings} |".format(**row)
        )

    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    if not INPUT_CSV.exists():
        raise FileNotFoundError(f"Missing hitter position tier CSV: {INPUT_CSV}")

    with INPUT_CSV.open("r", newline="", encoding="utf-8-sig") as f:
        rows = [classify(row) for row in csv.DictReader(f)]

    rows = sorted(rows, key=sort_key)

    write_csv(rows)
    write_markdown(rows)

    print("# RESULT SUMMARY")
    print(f"TOTAL_HITTERS: {len(rows)}")
    for rec in RECOMMENDATION_ORDER:
        count = sum(1 for row in rows if row.get("recommendation") == rec)
        print(f"{rec.upper()}: {count}")
    print(f"CSV_OUT: {OUT_CSV}")
    print(f"MD_OUT: {OUT_MD}")
    print("")
    print("# TOP 20")
    for row in rows[:20]:
        print(
            f"{row['recommendation']} | {row['positionGroup']} | {row['playerName']} | "
            f"${row['salary']} | {row['primaryPosition']} | {row['browserDefense']} | "
            f"score={row['astrodomeScore']} | warnings={row['warnings']}"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
