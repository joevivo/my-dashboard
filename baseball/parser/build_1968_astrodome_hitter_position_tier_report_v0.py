from __future__ import annotations

import csv
from pathlib import Path
from typing import Any


INPUT_CSV = Path("data/baseball/parsed/strat365/1968/card-mechanics/1968.hitter-card-mechanics-v0.csv")
OUT_CSV = Path("data/baseball/parsed/strat365/1968/draft-prep/1968.astrodome-hitter-position-tier-report-v0.csv")
OUT_MD = Path("data/baseball/parsed/strat365/1968/draft-prep/1968.astrodome-hitter-position-tier-report-v0.md")


POSITION_GROUP_ORDER = {
    "C": 1,
    "Clean CF": 2,
    "Clean SS": 3,
    "Clean 2B": 4,
    "Clean 3B": 5,
    "Corner Bat": 6,
    "Other": 9,
}


def to_float(value: Any, default: float = 0.0) -> float:
    try:
        if value in (None, ""):
            return default
        return float(value)
    except Exception:
        return default


def salary_tier(salary: float) -> str:
    if salary >= 9.0:
        return "Premium Bat"
    if salary >= 6.0:
        return "Core Bat"
    if salary >= 2.0:
        return "Value Bat"
    return "Cheap Bat"


def position_group(primary_position: str, defense_text: str) -> str:
    if primary_position == "C":
        return "C"
    if "cf-1" in defense_text or "cf-2" in defense_text:
        return "Clean CF"
    if "ss-1" in defense_text or "ss-2" in defense_text:
        return "Clean SS"
    if "2b-1" in defense_text or "2b-2" in defense_text:
        return "Clean 2B"
    if "3b-1" in defense_text or "3b-2" in defense_text:
        return "Clean 3B"
    if primary_position in {"LF", "RF", "1B"}:
        return "Corner Bat"
    return "Other"


def defense_tag(defense_text: str) -> str:
    premium_tokens = ("c-1", "cf-1", "ss-1", "2b-1", "3b-1", "rf-1", "lf-1")
    plus_tokens = ("cf-2", "ss-2", "2b-2", "3b-2", "rf-2", "lf-2")
    risk_tokens = ("cf-4", "ss-4", "2b-4", "3b-4", "lf-4", "rf-4", "1b-5")

    if any(token in defense_text for token in premium_tokens):
        return "premium_defense"
    if any(token in defense_text for token in plus_tokens):
        return "plus_defense"
    if any(token in defense_text for token in risk_tokens):
        return "defense_risk"
    return "neutral_defense"


def classify(row: dict[str, str]) -> dict[str, str]:
    salary = to_float(row.get("salary"))
    score = to_float(row.get("astrodomeParkAdjustedBrowserScore"))
    ob = to_float(row.get("weightedOB"))
    hr = to_float(row.get("weightedHR"))
    bb = to_float(row.get("weightedBB"))
    gb = to_float(row.get("weightedGB"))
    k = to_float(row.get("weightedK"))
    bp_hr = to_float(row.get("ballparkHRCheck"))

    defense_text = row.get("defenseText", "")
    primary_position = row.get("primaryPosition", "")
    dtag = defense_tag(defense_text)

    strengths: list[str] = []
    warnings: list[str] = []

    if ob >= 0.42:
        strengths.append("ob_engine")
    elif ob < 0.30:
        warnings.append("low_ob")

    if bb >= 0.12:
        strengths.append("walk_engine")

    if hr >= 0.06 and bp_hr >= 0.02:
        warnings.append("hr_dependency_in_dead_hr_park")

    if gb >= 0.45:
        warnings.append("gb_heavy")

    if k >= 0.18:
        warnings.append("strikeout_risk")

    if dtag in {"premium_defense", "plus_defense"}:
        strengths.append(dtag)

    if dtag == "defense_risk":
        warnings.append("defense_risk")

    return {
        "positionGroup": position_group(primary_position, defense_text),
        "salaryTier": salary_tier(salary),
        "playerId": row.get("playerId", ""),
        "playerName": row.get("playerName", ""),
        "team": row.get("team", ""),
        "salary": f"{salary:.2f}",
        "bats": row.get("bats", ""),
        "primaryPosition": primary_position,
        "browserDefense": row.get("browserDefense", ""),
        "defenseText": defense_text,
        "runningText": row.get("runningText", ""),
        "astrodomeScore": f"{score:.4f}",
        "weightedOB": row.get("weightedOB", ""),
        "weightedHit": row.get("weightedHit", ""),
        "weightedHR": row.get("weightedHR", ""),
        "weightedBB": row.get("weightedBB", ""),
        "weightedGB": row.get("weightedGB", ""),
        "weightedK": row.get("weightedK", ""),
        "ballparkHRCheck": row.get("ballparkHRCheck", ""),
        "ballparkSingleCheck": row.get("ballparkSingleCheck", ""),
        "hrDependencyRatio": row.get("hrDependencyRatio", ""),
        "strengths": ";".join(strengths),
        "warnings": ";".join(warnings),
    }


def sort_key(row: dict[str, str]) -> tuple[int, float]:
    return (
        POSITION_GROUP_ORDER.get(row.get("positionGroup", ""), 9),
        -to_float(row.get("astrodomeScore")),
    )


def write_csv(rows: list[dict[str, str]]) -> None:
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "positionGroup",
        "salaryTier",
        "playerId",
        "playerName",
        "team",
        "salary",
        "bats",
        "primaryPosition",
        "browserDefense",
        "defenseText",
        "runningText",
        "astrodomeScore",
        "weightedOB",
        "weightedHit",
        "weightedHR",
        "weightedBB",
        "weightedGB",
        "weightedK",
        "ballparkHRCheck",
        "ballparkSingleCheck",
        "hrDependencyRatio",
        "strengths",
        "warnings",
    ]

    with OUT_CSV.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_markdown(rows: list[dict[str, str]]) -> None:
    lines: list[str] = [
        "# 1968 Astrodome Hitter Position Tier Report",
        "",
        "Generated from full 537-card 1968 hitter mechanics.",
        "",
        "## Position Group Counts",
        "",
    ]

    for group in POSITION_GROUP_ORDER:
        count = sum(1 for row in rows if row.get("positionGroup") == group)
        lines.append(f"- {group}: {count}")

    lines.extend(["", "## Top Hitters by Position Group", ""])

    for group in ["C", "Clean CF", "Clean SS", "Clean 2B", "Clean 3B", "Corner Bat"]:
        lines.extend(
            [
                f"### {group}",
                "",
                "| Player | Team | Salary | Pos | Def | Score | OB | HIT | HR | BB | GB | K | Strengths | Warnings |",
                "|---|---:|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|",
            ]
        )

        group_rows = [
            row for row in rows
            if row.get("positionGroup") == group
        ][:15]

        for row in group_rows:
            lines.append(
                "| {playerName} | {team} | {salary} | {primaryPosition} | {browserDefense} | "
                "{astrodomeScore} | {weightedOB} | {weightedHit} | {weightedHR} | "
                "{weightedBB} | {weightedGB} | {weightedK} | {strengths} | {warnings} |".format(**row)
            )

        lines.append("")

    OUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    if not INPUT_CSV.exists():
        raise FileNotFoundError(f"Missing hitter mechanics CSV: {INPUT_CSV}")

    with INPUT_CSV.open("r", newline="", encoding="utf-8-sig") as f:
        rows = [classify(row) for row in csv.DictReader(f)]

    rows = sorted(rows, key=sort_key)

    write_csv(rows)
    write_markdown(rows)

    print("# RESULT SUMMARY")
    print(f"TOTAL_HITTERS: {len(rows)}")
    for group in POSITION_GROUP_ORDER:
        count = sum(1 for row in rows if row.get("positionGroup") == group)
        print(f"{group.replace(' ', '_').upper()}: {count}")
    print(f"CSV_OUT: {OUT_CSV}")
    print(f"MD_OUT: {OUT_MD}")
    print("")
    print("# TOP POSITION GROUP LEADERS")
    for group in ["C", "Clean CF", "Clean SS", "Clean 2B", "Clean 3B", "Corner Bat"]:
        leaders = [row for row in rows if row.get("positionGroup") == group][:3]
        print(group)
        for row in leaders:
            print(
                f"  {row['playerName']} | ${row['salary']} | {row['primaryPosition']} | "
                f"{row['browserDefense']} | score={row['astrodomeScore']} | warnings={row['warnings']}"
            )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
