from __future__ import annotations

import csv
from pathlib import Path
from typing import Any


INPUT_CSV = Path("data/baseball/parsed/strat365/1968/draft-prep/1968.astrodome-starter-tier-report-v0.csv")
OUT_CSV = Path("data/baseball/parsed/strat365/1968/draft-prep/1968.astrodome-starter-recommendation-overlay-v0.csv")
OUT_MD = Path("data/baseball/parsed/strat365/1968/draft-prep/1968.astrodome-starter-recommendation-overlay-v0.md")


RECOMMENDATION_ORDER = {
    "core_target": 1,
    "useful_value": 2,
    "roster_structure_fallback": 3,
    "depth_review": 4,
    "avoid_or_emergency_only": 5,
}


def to_float(value: Any, default: float = 0.0) -> float:
    try:
        if value in (None, ""):
            return default
        return float(value)
    except Exception:
        return default


def to_int(value: Any, default: int = 0) -> int:
    try:
        if value in (None, ""):
            return default
        return int(float(value))
    except Exception:
        return default


def classify(row: dict[str, str]) -> dict[str, str]:
    salary = to_float(row.get("salary"))
    score = to_float(row.get("astrodomeScore"))
    oba = to_float(row.get("weightedOnBaseAllowed"))
    hr = to_float(row.get("weightedHRAllowed"))
    bb = to_float(row.get("weightedWalkAllowed"))
    k = to_float(row.get("weightedStrikeout"))
    bp_hr = to_float(row.get("ballparkHRCheckAllowed"))
    starter = to_int(row.get("starterEndurance"))
    hybrid = row.get("hybridSPRP") == "yes"

    strengths: list[str] = []
    warnings: list[str] = []

    if starter >= 8:
        strengths.append("workhorse_endurance")
    elif starter >= 7:
        strengths.append("strong_starter_endurance")
    elif starter <= 5:
        warnings.append("low_starter_endurance")

    if hybrid:
        strengths.append("hybrid_sp_rp")

    if oba <= 0.20:
        strengths.append("excellent_oba_allowed")
    elif oba >= 0.30:
        warnings.append("high_oba_allowed")

    if bb <= 0.035:
        strengths.append("low_walks")
    elif bb >= 0.10:
        warnings.append("walk_risk")

    if hr <= 0.006:
        strengths.append("low_card_hr")
    elif hr >= 0.03:
        warnings.append("hr_risk_even_in_astrodome")

    if bp_hr <= 0.006:
        strengths.append("low_ballpark_hr_dependency")
    elif bp_hr >= 0.02:
        warnings.append("ballpark_hr_dependency")

    if k >= 0.25:
        strengths.append("strikeout_plus")
    elif k <= 0.10:
        warnings.append("low_strikeouts")

    if score >= 80 and len(warnings) <= 1:
        recommendation = "core_target"
    elif score >= 68 and len(warnings) <= 2:
        recommendation = "useful_value"
    elif salary < 2.0 and starter >= 6 and len(warnings) <= 2:
        recommendation = "roster_structure_fallback"
    elif len(warnings) >= 3:
        recommendation = "avoid_or_emergency_only"
    else:
        recommendation = "depth_review"

    out = dict(row)
    out["recommendation"] = recommendation
    out["pitcherDefense"] = f"{row.get('pitcherFieldingRating', '')}/e{row.get('pitcherError', '')}"
    out["strengths"] = ";".join(strengths)
    out["warnings"] = ";".join(warnings)
    return out


def sorted_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return sorted(
        rows,
        key=lambda row: (
            RECOMMENDATION_ORDER.get(row.get("recommendation", ""), 9),
            -to_float(row.get("astrodomeScore")),
        ),
    )


def write_csv(rows: list[dict[str, str]]) -> None:
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "recommendation",
        "tier",
        "playerName",
        "team",
        "salary",
        "browserEndurance",
        "starterEndurance",
        "reliefEndurance",
        "closerEndurance",
        "hybridSPRP",
        "astrodomeScore",
        "weightedOnBaseAllowed",
        "weightedHitAllowed",
        "weightedHRAllowed",
        "weightedWalkAllowed",
        "weightedStrikeout",
        "ballparkHRCheckAllowed",
        "defensiveXChartDependency",
        "pitcherDefense",
        "strengths",
        "warnings",
    ]

    with OUT_CSV.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_markdown(rows: list[dict[str, str]]) -> None:
    lines: list[str] = [
        "# 1968 Astrodome Starter Recommendation Overlay",
        "",
        "Generated from the full-card starter tier report.",
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
            "## Top Starter Recommendations",
            "",
            "| Recommendation | Player | Tier | Team | Salary | Endurance | Score | OBA | BB | HR | K | Strengths | Warnings |",
            "|---|---|---|---:|---:|---|---:|---:|---:|---:|---:|---|---|",
        ]
    )

    displayed = [
        row for row in sorted_rows(rows)
        if row.get("recommendation") != "avoid_or_emergency_only"
    ][:50]

    for row in displayed:
        lines.append(
            "| {recommendation} | {playerName} | {tier} | {team} | {salary} | "
            "{browserEndurance} | {astrodomeScore} | {weightedOnBaseAllowed} | "
            "{weightedWalkAllowed} | {weightedHRAllowed} | {weightedStrikeout} | "
            "{strengths} | {warnings} |".format(**row)
        )

    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    if not INPUT_CSV.exists():
        raise FileNotFoundError(f"Missing starter tier report: {INPUT_CSV}")

    with INPUT_CSV.open("r", newline="", encoding="utf-8-sig") as f:
        rows = [classify(row) for row in csv.DictReader(f)]

    rows = sorted_rows(rows)
    write_csv(rows)
    write_markdown(rows)

    print("# RESULT SUMMARY")
    print(f"TOTAL_STARTERS: {len(rows)}")
    for rec in RECOMMENDATION_ORDER:
        count = sum(1 for row in rows if row.get("recommendation") == rec)
        print(f"{rec.upper()}: {count}")
    print(f"CSV_OUT: {OUT_CSV}")
    print(f"MD_OUT: {OUT_MD}")
    print("")
    print("# TOP 15")
    for row in rows[:15]:
        print(
            f"{row['recommendation']} | {row['playerName']} | {row['tier']} | "
            f"${row['salary']} | {row['browserEndurance']} | score={row['astrodomeScore']} | "
            f"warnings={row['warnings']}"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
