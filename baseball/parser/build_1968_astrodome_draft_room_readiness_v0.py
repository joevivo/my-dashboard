from __future__ import annotations

import csv
from pathlib import Path


HITTER_OVERLAY = Path("data/baseball/parsed/strat365/1968/draft-prep/1968.astrodome-hitter-recommendation-overlay-v0.csv")
STARTER_OVERLAY = Path("data/baseball/parsed/strat365/1968/draft-prep/1968.astrodome-starter-recommendation-overlay-v0.csv")
RELIEVER_OVERLAY = Path("data/baseball/parsed/strat365/1968/draft-prep/1968.astrodome-reliever-recommendation-overlay-v0.csv")
OUT_MD = Path("data/baseball/parsed/strat365/1968/draft-prep/1968.astrodome-draft-room-readiness-v0.md")


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(f"Missing required input: {path}")

    with path.open("r", newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def add_table(lines: list[str], title: str, rows: list[dict[str, str]], columns: list[str]) -> None:
    lines.append(f"## {title}")
    lines.append("")
    lines.append("| " + " | ".join(columns) + " |")
    lines.append("|" + "|".join("---" for _ in columns) + "|")

    for row in rows:
        values = [str(row.get(col, "")) for col in columns]
        lines.append("| " + " | ".join(values) + " |")

    lines.append("")


def count_rows(rows: list[dict[str, str]], recommendation: str) -> int:
    return sum(1 for row in rows if row.get("recommendation") == recommendation)


def main() -> int:
    hitters = read_csv(HITTER_OVERLAY)
    starters = read_csv(STARTER_OVERLAY)
    relievers = read_csv(RELIEVER_OVERLAY)

    premium_hitters = [
        row for row in hitters
        if row.get("recommendation") == "core_target"
    ][:20]

    scarcity_hitters = [
        row for row in hitters
        if row.get("recommendation") == "position_priority"
    ][:20]

    useful_hitters = [
        row for row in hitters
        if row.get("recommendation") == "useful_value"
    ][:20]

    core_starters = [
        row for row in starters
        if row.get("recommendation") == "core_target"
    ][:20]

    value_starters = [
        row for row in starters
        if row.get("recommendation") == "useful_value"
    ][:25]

    fallback_starters = [
        row for row in starters
        if row.get("recommendation") == "roster_structure_fallback"
    ][:20]

    closer_targets = [
        row for row in relievers
        if row.get("recommendation") == "closer_target"
    ][:20]

    core_relievers = [
        row for row in relievers
        if row.get("recommendation") == "core_relief_target"
    ][:20]

    useful_closers = [
        row for row in relievers
        if row.get("recommendation") == "useful_closer_value"
    ][:20]

    useful_relievers = [
        row for row in relievers
        if row.get("recommendation") == "useful_relief_value"
    ][:20]

    lines: list[str] = [
        "# 1968 Astrodome Draft Room Readiness",
        "",
        "Generated from card-backed hitter, starter, and reliever recommendation overlays.",
        "",
        "## Readiness Summary",
        "",
        f"- Hitter overlay rows: {len(hitters)}",
        f"- Starter overlay rows: {len(starters)}",
        f"- Reliever overlay rows: {len(relievers)}",
        f"- Hitter core targets: {count_rows(hitters, 'core_target')}",
        f"- Hitter position priorities: {count_rows(hitters, 'position_priority')}",
        f"- Hitter useful values: {count_rows(hitters, 'useful_value')}",
        f"- Starter core targets: {count_rows(starters, 'core_target')}",
        f"- Starter useful values: {count_rows(starters, 'useful_value')}",
        f"- Starter structure fallbacks: {count_rows(starters, 'roster_structure_fallback')}",
        f"- Closer targets: {count_rows(relievers, 'closer_target')}",
        f"- Core relief targets: {count_rows(relievers, 'core_relief_target')}",
        f"- Useful closer values: {count_rows(relievers, 'useful_closer_value')}",
        f"- Useful relief values: {count_rows(relievers, 'useful_relief_value')}",
        "",
        "## Draft Posture",
        "",
        "BIE is ready to support a human-led 1968 Astrodome draft plan. It is not making autonomous picks. It provides card-backed target pools, warnings, scarcity signals, and roster-structure options.",
        "",
    ]

    hitter_columns = [
        "recommendation",
        "positionGroup",
        "playerName",
        "team",
        "salary",
        "primaryPosition",
        "browserDefense",
        "astrodomeScore",
        "warnings",
    ]

    starter_columns = [
        "recommendation",
        "tier",
        "playerName",
        "team",
        "salary",
        "browserEndurance",
        "astrodomeScore",
        "warnings",
    ]

    reliever_columns = [
        "recommendation",
        "playerName",
        "team",
        "salary",
        "browserEndurance",
        "reliefEndurance",
        "closerEndurance",
        "astrodomeScore",
        "warnings",
    ]

    add_table(lines, "Premium Hitter Targets", premium_hitters, hitter_columns)
    add_table(lines, "Position Priority Hitters", scarcity_hitters, hitter_columns)
    add_table(lines, "Useful Hitter Values", useful_hitters, hitter_columns)
    add_table(lines, "Core Starter Targets", core_starters, starter_columns)
    add_table(lines, "Useful Starter Values", value_starters, starter_columns)
    add_table(lines, "Starter Structure Fallbacks", fallback_starters, starter_columns)
    add_table(lines, "Closer Targets", closer_targets, reliever_columns)
    add_table(lines, "Core Relief Targets", core_relievers, reliever_columns)
    add_table(lines, "Useful Closer Values", useful_closers, reliever_columns)
    add_table(lines, "Useful Relief Values", useful_relievers, reliever_columns)

    lines.extend(
        [
            "## Remaining Draft-Readiness Checks",
            "",
            "- Rebuild one legal roster scenario using hitter, starter, and reliever overlays.",
            "- Confirm at least 2 primary catchers.",
            "- Confirm at least 5 starter-endurance pitchers.",
            "- Confirm at least 4 pure relievers.",
            "- Confirm at least 1 closer-endurance pitcher.",
            "- Confirm bench coverage at C, SS/2B, CF/OF, and corner bat.",
            "- Produce final human-readable draft-room cheat sheet.",
            "",
        ]
    )

    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print("# RESULT SUMMARY")
    print(f"MD_OUT: {OUT_MD}")
    print(f"HITTERS: {len(hitters)}")
    print(f"STARTERS: {len(starters)}")
    print(f"RELIEVERS: {len(relievers)}")
    print(f"PREMIUM_HITTER_TARGETS: {len(premium_hitters)}")
    print(f"POSITION_PRIORITY_HITTERS: {len(scarcity_hitters)}")
    print(f"USEFUL_HITTER_VALUES: {len(useful_hitters)}")
    print(f"CORE_STARTER_TARGETS: {len(core_starters)}")
    print(f"USEFUL_STARTER_VALUES: {len(value_starters)}")
    print(f"STARTER_STRUCTURE_FALLBACKS_SHOWN: {len(fallback_starters)}")
    print(f"STARTER_STRUCTURE_FALLBACKS_TOTAL: {count_rows(starters, 'roster_structure_fallback')}")
    print(f"CLOSER_TARGETS: {len(closer_targets)}")
    print(f"CORE_RELIEF_TARGETS: {len(core_relievers)}")
    print(f"USEFUL_CLOSER_VALUES: {len(useful_closers)}")
    print(f"USEFUL_RELIEF_VALUES: {len(useful_relievers)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
