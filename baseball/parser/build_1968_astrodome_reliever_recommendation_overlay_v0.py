from __future__ import annotations

import csv
from pathlib import Path
from typing import Any


INPUT_CSV = Path("data/baseball/parsed/strat365/1968/card-mechanics/1968.pitcher-card-mechanics-v0.csv")
OUT_CSV = Path("data/baseball/parsed/strat365/1968/draft-prep/1968.astrodome-reliever-recommendation-overlay-v0.csv")
OUT_MD = Path("data/baseball/parsed/strat365/1968/draft-prep/1968.astrodome-reliever-recommendation-overlay-v0.md")


RECOMMENDATION_ORDER = {
    "closer_target": 1,
    "core_relief_target": 2,
    "useful_closer_value": 3,
    "useful_relief_value": 4,
    "roster_structure_fallback": 5,
    "depth_review": 6,
    "avoid_or_emergency_only": 7,
}


def to_float(value: Any, default: float = 0.0) -> float:
    try:
        if value in (None, ""):
            return default
        return float(value)
    except Exception:
        return default


def is_pure_reliever(row: dict[str, str]) -> bool:
    browser = row.get("browserEndurance", "")
    starter = to_float(row.get("starterEndurance"))
    relief = to_float(row.get("reliefEndurance"))

    return (relief > 0 or "R" in browser) and starter == 0 and "S" not in browser


def classify(row: dict[str, str]) -> dict[str, str]:
    salary = to_float(row.get("salary"))
    score = to_float(row.get("astrodomeParkAdjustedBrowserScore"))
    oba = to_float(row.get("weightedOnBaseAllowed"))
    hit = to_float(row.get("weightedHitAllowed"))
    hr = to_float(row.get("weightedHRAllowed"))
    walk = to_float(row.get("weightedWalkAllowed"))
    strikeout = to_float(row.get("weightedStrikeout"))
    relief = to_float(row.get("reliefEndurance"))
    closer = to_float(row.get("closerEndurance"))
    ballpark_hr = to_float(row.get("ballparkHRCheckAllowed"))

    warnings: list[str] = []
    strengths: list[str] = []

    if oba <= 0.16:
        strengths.append("on_base_suppression")
    if hit <= 0.10:
        strengths.append("hit_suppression")
    if walk <= 0.03:
        strengths.append("control_plus")
    if strikeout >= 0.24:
        strengths.append("strikeout_plus")
    if relief >= 3:
        strengths.append("multi_inning_relief")
    if closer >= 4:
        strengths.append("closer_endurance")

    if oba >= 0.24:
        warnings.append("on_base_risk")
    if walk >= 0.09:
        warnings.append("walk_risk")
    if strikeout <= 0.10:
        warnings.append("low_strikeouts")
    if hr >= 0.055 or ballpark_hr >= 0.04:
        warnings.append("hr_risk_even_in_astrodome")
    if closer == 0:
        warnings.append("not_closer_qualified")

    if closer >= 4 and score >= 78 and len(warnings) <= 1:
        recommendation = "closer_target"
    elif score >= 74 and len(warnings) <= 2:
        recommendation = "core_relief_target"
    elif closer > 0 and score >= 68 and len(warnings) <= 2:
        recommendation = "useful_closer_value"
    elif score >= 66 and len(warnings) <= 2:
        recommendation = "useful_relief_value"
    elif salary <= 1.0 and score >= 60 and len(warnings) <= 3:
        recommendation = "roster_structure_fallback"
    elif len(warnings) >= 4 or score < 50:
        recommendation = "avoid_or_emergency_only"
    else:
        recommendation = "depth_review"

    return {
        "recommendation": recommendation,
        "playerId": row.get("playerId", ""),
        "playerName": row.get("playerName", ""),
        "team": row.get("team", ""),
        "salary": row.get("salary", ""),
        "browserEndurance": row.get("browserEndurance", ""),
        "reliefEndurance": row.get("reliefEndurance", ""),
        "closerEndurance": row.get("closerEndurance", ""),
        "astrodomeScore": row.get("astrodomeParkAdjustedBrowserScore", ""),
        "weightedOnBaseAllowed": row.get("weightedOnBaseAllowed", ""),
        "weightedHitAllowed": row.get("weightedHitAllowed", ""),
        "weightedHRAllowed": row.get("weightedHRAllowed", ""),
        "weightedWalkAllowed": row.get("weightedWalkAllowed", ""),
        "weightedStrikeout": row.get("weightedStrikeout", ""),
        "ballparkHRCheckAllowed": row.get("ballparkHRCheckAllowed", ""),
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
        "playerId",
        "playerName",
        "team",
        "salary",
        "browserEndurance",
        "reliefEndurance",
        "closerEndurance",
        "astrodomeScore",
        "weightedOnBaseAllowed",
        "weightedHitAllowed",
        "weightedHRAllowed",
        "weightedWalkAllowed",
        "weightedStrikeout",
        "ballparkHRCheckAllowed",
        "strengths",
        "warnings",
    ]

    with OUT_CSV.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_markdown(rows: list[dict[str, str]]) -> None:
    lines: list[str] = [
        "# 1968 Astrodome Reliever Recommendation Overlay",
        "",
        "Generated from full-card pitcher mechanics. Pure relievers only; starter-endurance pitchers excluded.",
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
            "## Top Reliever Recommendations",
            "",
            "| Recommendation | Player | Team | Salary | Endurance | R | C | Score | OBA | HIT | HR | BB | K | Strengths | Warnings |",
            "|---|---|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---|",
        ]
    )

    displayed = [
        row for row in rows
        if row.get("recommendation") != "avoid_or_emergency_only"
    ][:80]

    for row in displayed:
        lines.append(
            "| {recommendation} | {playerName} | {team} | {salary} | {browserEndurance} | "
            "{reliefEndurance} | {closerEndurance} | {astrodomeScore} | {weightedOnBaseAllowed} | "
            "{weightedHitAllowed} | {weightedHRAllowed} | {weightedWalkAllowed} | "
            "{weightedStrikeout} | {strengths} | {warnings} |".format(**row)
        )

    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    if not INPUT_CSV.exists():
        raise FileNotFoundError(f"Missing pitcher mechanics CSV: {INPUT_CSV}")

    with INPUT_CSV.open("r", newline="", encoding="utf-8-sig") as f:
        source_rows = list(csv.DictReader(f))

    rows = [
        classify(row)
        for row in source_rows
        if is_pure_reliever(row)
    ]

    rows = sorted(rows, key=sort_key)

    write_csv(rows)
    write_markdown(rows)

    print("# RESULT SUMMARY")
    print(f"TOTAL_PURE_RELIEVERS: {len(rows)}")
    for rec in RECOMMENDATION_ORDER:
        count = sum(1 for row in rows if row.get("recommendation") == rec)
        print(f"{rec.upper()}: {count}")
    print(f"CSV_OUT: {OUT_CSV}")
    print(f"MD_OUT: {OUT_MD}")
    print("")
    print("# TOP 20")
    for row in rows[:20]:
        print(
            f"{row['recommendation']} | {row['playerName']} | ${row['salary']} | "
            f"{row['browserEndurance']} | R{row['reliefEndurance']} | C{row['closerEndurance']} | "
            f"score={row['astrodomeScore']} | warnings={row['warnings']}"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
