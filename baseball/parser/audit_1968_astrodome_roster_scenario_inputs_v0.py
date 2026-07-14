from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path


HITTER_OVERLAY = Path("data/baseball/parsed/strat365/1968/draft-prep/1968.astrodome-hitter-recommendation-overlay-v0.csv")
STARTER_OVERLAY = Path("data/baseball/parsed/strat365/1968/draft-prep/1968.astrodome-starter-recommendation-overlay-v0.csv")
RELIEVER_OVERLAY = Path("data/baseball/parsed/strat365/1968/draft-prep/1968.astrodome-reliever-recommendation-overlay-v0.csv")

OUT_MD = Path("data/baseball/parsed/strat365/1968/draft-prep/1968.astrodome-roster-scenario-input-audit-v0.md")


HITTER_DRAFT_RECS = {
    "core_target",
    "position_priority",
    "useful_value",
    "roster_structure_fallback",
}

STARTER_DRAFT_RECS = {
    "core_target",
    "useful_value",
    "roster_structure_fallback",
}

RELIEVER_DRAFT_RECS = {
    "closer_target",
    "core_relief_target",
    "useful_closer_value",
    "useful_relief_value",
    "roster_structure_fallback",
}


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(f"Missing required input: {path}")
    with path.open("r", newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def to_float(value: str) -> float:
    try:
        return float(value)
    except Exception:
        return 0.0


def to_int(value: str) -> int:
    try:
        return int(float(value))
    except Exception:
        return 0


def has_player_id(row: dict[str, str]) -> bool:
    return bool(row.get("playerId", "").strip())


def player_id_counts(rows: list[dict[str, str]]) -> Counter[str]:
    return Counter(row.get("playerId", "").strip() for row in rows if has_player_id(row))


def count_missing_player_ids(rows: list[dict[str, str]]) -> int:
    return sum(1 for row in rows if not has_player_id(row))


def count_duplicate_player_ids(rows: list[dict[str, str]]) -> int:
    counts = player_id_counts(rows)
    return sum(1 for _, count in counts.items() if count > 1)


def salary_summary(rows: list[dict[str, str]]) -> dict[str, float]:
    salaries = [to_float(row.get("salary", "")) for row in rows]
    if not salaries:
        return {"min": 0.0, "max": 0.0, "avg": 0.0}

    return {
        "min": min(salaries),
        "max": max(salaries),
        "avg": sum(salaries) / len(salaries),
    }


def recommendation_counts(rows: list[dict[str, str]]) -> Counter[str]:
    return Counter(row.get("recommendation", "") for row in rows)


def rows_by_recommendation(rows: list[dict[str, str]], allowed: set[str]) -> list[dict[str, str]]:
    return [row for row in rows if row.get("recommendation") in allowed]


def position_count(rows: list[dict[str, str]], position_group: str) -> int:
    return sum(1 for row in rows if row.get("positionGroup") == position_group)


def primary_position_count(rows: list[dict[str, str]], primary: str) -> int:
    return sum(1 for row in rows if row.get("primaryPosition") == primary)


def pure_reliever_count(rows: list[dict[str, str]]) -> int:
    return sum(
        1 for row in rows
        if to_int(row.get("starterEndurance", "0")) == 0
        and to_int(row.get("reliefEndurance", "0")) > 0
    )


def closer_count(rows: list[dict[str, str]]) -> int:
    return sum(1 for row in rows if to_int(row.get("closerEndurance", "0")) > 0)


def starter_endurance_count(rows: list[dict[str, str]]) -> int:
    return sum(1 for row in rows if to_int(row.get("starterEndurance", "0")) >= 5)


def overlap_player_ids(left: list[dict[str, str]], right: list[dict[str, str]]) -> set[str]:
    left_ids = {row.get("playerId", "").strip() for row in left if has_player_id(row)}
    right_ids = {row.get("playerId", "").strip() for row in right if has_player_id(row)}
    return left_ids & right_ids


def add_counts_table(lines: list[str], title: str, counts: Counter[str]) -> None:
    lines.append(f"## {title}")
    lines.append("")
    lines.append("| Value | Count |")
    lines.append("|---|---|")
    for key, count in sorted(counts.items()):
        lines.append(f"| {key} | {count} |")
    lines.append("")


def add_sample_table(lines: list[str], title: str, rows: list[dict[str, str]], columns: list[str], limit: int = 15) -> None:
    lines.append(f"## {title}")
    lines.append("")
    lines.append("| " + " | ".join(columns) + " |")
    lines.append("|" + "|".join("---" for _ in columns) + "|")
    for row in rows[:limit]:
        lines.append("| " + " | ".join(str(row.get(col, "")) for col in columns) + " |")
    lines.append("")


def main() -> int:
    hitters = read_csv(HITTER_OVERLAY)
    starters = read_csv(STARTER_OVERLAY)
    relievers = read_csv(RELIEVER_OVERLAY)

    hitter_pool = rows_by_recommendation(hitters, HITTER_DRAFT_RECS)
    starter_pool = rows_by_recommendation(starters, STARTER_DRAFT_RECS)
    reliever_pool = rows_by_recommendation(relievers, RELIEVER_DRAFT_RECS)

    starter_reliever_overlap = overlap_player_ids(starter_pool, reliever_pool)

    hitter_salary = salary_summary(hitter_pool)
    starter_salary = salary_summary(starter_pool)
    reliever_salary = salary_summary(reliever_pool)

    pass_fail = {
        "hitter_player_ids_present": count_missing_player_ids(hitter_pool) == 0,
        "starter_player_ids_present": count_missing_player_ids(starter_pool) == 0,
        "reliever_player_ids_present": count_missing_player_ids(reliever_pool) == 0,
        "hitter_pool_has_13_plus": len(hitter_pool) >= 13,
        "starter_pool_has_5_plus": starter_endurance_count(starter_pool) >= 5,
        "reliever_pool_has_4_plus_pure": pure_reliever_count(reliever_pool) >= 4,
        "reliever_pool_has_1_plus_closer": closer_count(reliever_pool) >= 1,
        "catcher_pool_has_2_plus": primary_position_count(hitter_pool, "C") >= 2,
        "clean_cf_pool_has_1_plus": position_count(hitter_pool, "Clean CF") >= 1,
        "clean_ss_pool_has_1_plus": position_count(hitter_pool, "Clean SS") >= 1,
        "clean_2b_pool_has_1_plus": position_count(hitter_pool, "Clean 2B") >= 1,
        "clean_3b_pool_has_1_plus": position_count(hitter_pool, "Clean 3B") >= 1,
        "starter_reliever_overlap_reviewable": True,
    }

    lines: list[str] = [
        "# 1968 Astrodome Roster Scenario Input Audit",
        "",
        "Purpose: validate that hitter, starter, and reliever overlays are structurally ready to feed a legal roster scenario builder.",
        "",
        "## Pass / Review Gates",
        "",
        "| Gate | Result |",
        "|---|---|",
    ]

    for gate, passed in pass_fail.items():
        lines.append(f"| {gate} | {'PASS' if passed else 'FAIL'} |")
    lines.append("")

    lines.extend(
        [
            "## Pool Sizes",
            "",
            "| Pool | Rows | Draft Pool Rows | Missing Player IDs | Duplicate Player IDs |",
            "|---|---:|---:|---:|---:|",
            f"| Hitters | {len(hitters)} | {len(hitter_pool)} | {count_missing_player_ids(hitter_pool)} | {count_duplicate_player_ids(hitter_pool)} |",
            f"| Starters | {len(starters)} | {len(starter_pool)} | {count_missing_player_ids(starter_pool)} | {count_duplicate_player_ids(starter_pool)} |",
            f"| Relievers | {len(relievers)} | {len(reliever_pool)} | {count_missing_player_ids(reliever_pool)} | {count_duplicate_player_ids(reliever_pool)} |",
            "",
            "## Salary Summary",
            "",
            "| Pool | Min | Avg | Max |",
            "|---|---:|---:|---:|",
            f"| Hitters | {hitter_salary['min']:.2f} | {hitter_salary['avg']:.2f} | {hitter_salary['max']:.2f} |",
            f"| Starters | {starter_salary['min']:.2f} | {starter_salary['avg']:.2f} | {starter_salary['max']:.2f} |",
            f"| Relievers | {reliever_salary['min']:.2f} | {reliever_salary['avg']:.2f} | {reliever_salary['max']:.2f} |",
            "",
            "## Legal Roster Supply Signals",
            "",
            "| Requirement | Available In Draft Pools |",
            "|---|---:|",
            f"| Hitters | {len(hitter_pool)} |",
            f"| Starter-endurance pitchers | {starter_endurance_count(starter_pool)} |",
            f"| Pure relievers | {pure_reliever_count(reliever_pool)} |",
            f"| Closer-endurance relievers | {closer_count(reliever_pool)} |",
            f"| Primary catchers | {primary_position_count(hitter_pool, 'C')} |",
            f"| Clean CF | {position_count(hitter_pool, 'Clean CF')} |",
            f"| Clean SS | {position_count(hitter_pool, 'Clean SS')} |",
            f"| Clean 2B | {position_count(hitter_pool, 'Clean 2B')} |",
            f"| Clean 3B | {position_count(hitter_pool, 'Clean 3B')} |",
            f"| Starter/reliever overlay overlap IDs | {len(starter_reliever_overlap)} |",
            "",
        ]
    )

    add_counts_table(lines, "Hitter Recommendation Counts", recommendation_counts(hitters))
    add_counts_table(lines, "Starter Recommendation Counts", recommendation_counts(starters))
    add_counts_table(lines, "Reliever Recommendation Counts", recommendation_counts(relievers))

    add_sample_table(
        lines,
        "Sample Hitter Draft Pool",
        hitter_pool,
        ["recommendation", "positionGroup", "playerId", "playerName", "salary", "primaryPosition", "warnings"],
    )
    add_sample_table(
        lines,
        "Sample Starter Draft Pool",
        starter_pool,
        ["recommendation", "tier", "playerId", "playerName", "salary", "browserEndurance", "warnings"],
    )
    add_sample_table(
        lines,
        "Sample Reliever Draft Pool",
        reliever_pool,
        ["recommendation", "playerId", "playerName", "salary", "browserEndurance", "reliefEndurance", "closerEndurance", "warnings"],
    )

    if starter_reliever_overlap:
        lines.append("## Starter / Reliever Overlay Overlap")
        lines.append("")
        lines.append("These are not automatically errors. They indicate hybrid pitchers that appear in both staff-construction pools and must be deduplicated by the roster scenario builder.")
        lines.append("")
        lines.append("| playerId |")
        lines.append("|---|")
        for player_id in sorted(starter_reliever_overlap):
            lines.append(f"| {player_id} |")
        lines.append("")

    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print("# RESULT SUMMARY")
    print(f"MD_OUT: {OUT_MD}")
    print(f"HITTERS_TOTAL: {len(hitters)}")
    print(f"HITTERS_DRAFT_POOL: {len(hitter_pool)}")
    print(f"STARTERS_TOTAL: {len(starters)}")
    print(f"STARTERS_DRAFT_POOL: {len(starter_pool)}")
    print(f"RELIEVERS_TOTAL: {len(relievers)}")
    print(f"RELIEVERS_DRAFT_POOL: {len(reliever_pool)}")
    print(f"HITTER_MISSING_PLAYERID: {count_missing_player_ids(hitter_pool)}")
    print(f"STARTER_MISSING_PLAYERID: {count_missing_player_ids(starter_pool)}")
    print(f"RELIEVER_MISSING_PLAYERID: {count_missing_player_ids(reliever_pool)}")
    print(f"STARTER_RELIEVER_OVERLAP_IDS: {len(starter_reliever_overlap)}")
    for gate, passed in pass_fail.items():
        print(f"{gate}: {'PASS' if passed else 'FAIL'}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
