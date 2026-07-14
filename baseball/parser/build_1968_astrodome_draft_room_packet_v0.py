from __future__ import annotations

import csv
from collections import Counter, defaultdict
from pathlib import Path


SCENARIO_CSV = Path("data/baseball/parsed/strat365/1968/draft-prep/1968.astrodome-overlay-roster-scenarios-v0.csv")
SCENARIO_MD = Path("data/baseball/parsed/strat365/1968/draft-prep/1968.astrodome-overlay-roster-scenarios-v0.md")
OUT_MD = Path("data/baseball/parsed/strat365/1968/draft-prep/1968.astrodome-draft-room-packet-v0.md")

BASELINE_SCENARIO = "balanced_card_score"
PREFERRED_SCENARIO_ORDER = [
    "balanced_card_score",
    "premium_bats_value_pitching",
    "premium_sp_anchor",
    "premium_pitching_and_relief",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(f"Missing required input: {path}")
    with path.open("r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def split_scenario_sections(path: Path) -> dict[str, list[str]]:
    if not path.exists():
        raise FileNotFoundError(f"Missing required input: {path}")

    sections: dict[str, list[str]] = {}
    current_name: str | None = None
    current_lines: list[str] = []

    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("## ") and line.strip() != "## Scenario Summary":
            if current_name:
                sections[current_name] = current_lines
            current_name = line.replace("## ", "", 1).strip()
            current_lines = [line]
        elif current_name:
            current_lines.append(line)

    if current_name:
        sections[current_name] = current_lines

    return sections


def parse_roster_table(section_lines: list[str]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    in_table = False

    for line in section_lines:
        if line.startswith("| Role | Pool | Recommendation | Player | Salary | Position/Endurance | Warnings |"):
            in_table = True
            continue
        if in_table and line.startswith("|---"):
            continue
        if in_table and not line.startswith("|"):
            break
        if in_table and line.startswith("|"):
            parts = [part.strip() for part in line.strip("|").split("|")]
            if len(parts) != 7:
                continue
            role, pool, recommendation, player, salary, pos_endurance, warnings = parts
            rows.append(
                {
                    "role": role,
                    "pool": pool,
                    "recommendation": recommendation,
                    "player": player,
                    "salary": salary,
                    "posEndurance": pos_endurance,
                    "warnings": warnings,
                }
            )

    return rows


def player_name(player_label: str) -> str:
    # Example: "Freehan, Bill (DET '68, $8.21)"
    return player_label.split(" (", 1)[0].strip()


def warning_list(row: dict[str, str]) -> list[str]:
    raw = row.get("warnings", "").strip()
    if not raw:
        return []
    return [item.strip() for item in raw.split(";") if item.strip()]


def tier_for(row: dict[str, str]) -> str:
    role = row.get("role", "")
    pool = row.get("pool", "")
    recommendation = row.get("recommendation", "")

    if pool == "hitter" and role in {"primary_catcher", "clean_cf", "clean_ss", "clean_2b", "clean_3b"}:
        return "Position locks"
    if pool == "hitter" and recommendation in {"core_target", "position_priority", "useful_value"}:
        return "Offensive / bench targets"
    if pool == "starter":
        return "Starter targets"
    if pool == "reliever" and recommendation in {"closer_target", "core_relief_target"}:
        return "Bullpen core"
    if pool == "reliever":
        return "Bullpen depth"
    return "Salary-fit / fallback options"


def sort_priority_key(item: tuple[str, dict[str, str], int]) -> tuple[int, int, float, str]:
    name, row, appearances = item
    tier_order = {
        "Position locks": 0,
        "Bullpen core": 1,
        "Starter targets": 2,
        "Offensive / bench targets": 3,
        "Bullpen depth": 4,
        "Salary-fit / fallback options": 5,
    }
    tier = tier_for(row)
    try:
        salary = float(row.get("salary", "0") or "0")
    except ValueError:
        salary = 0.0
    return (tier_order.get(tier, 99), -appearances, -salary, name)


def scenario_summary_lines(summary: dict[str, str]) -> list[str]:
    return [
        f"- Legal: {summary.get('legal')}",
        f"- Credible: {summary.get('credible')}",
        f"- Salary: ${summary.get('salary')}M",
        f"- Roster: {summary.get('players')} players / {summary.get('hitters')} hitters / {summary.get('pitchers')} pitchers",
        f"- Structure: C {summary.get('primaryCatchers')} / SP {summary.get('starterEndurancePitchers')} / Pure RP {summary.get('pureRelievers')} / Closers {summary.get('closers')}",
        f"- Bench shape: OF-corner {summary.get('ofCornerBatsBeyondCf')} / SS {summary.get('primaryShortstops')} / MI {summary.get('middleInfieldTypes')} / bench no-low-OB {summary.get('benchBatsWithoutLowOb')}",
        f"- Warnings: {summary.get('warningCount')}",
        f"- Failed checks: {summary.get('failedChecks') or 'none'}",
        f"- Failed credibility checks: {summary.get('failedCredibilityChecks') or 'none'}",
    ]


def main() -> None:
    summaries = {row["scenario"]: row for row in read_csv(SCENARIO_CSV)}
    sections = split_scenario_sections(SCENARIO_MD)

    credible_scenarios = [
        name for name, row in summaries.items()
        if row.get("credible") == "yes"
    ]

    selected = [
        name for name in PREFERRED_SCENARIO_ORDER
        if name in credible_scenarios
    ]

    selected += [
        name for name in credible_scenarios
        if name not in selected
    ]

    if not selected:
        raise SystemExit("No credible scenarios found.")

    rosters = {
        name: parse_roster_table(sections[name])
        for name in selected
    }

    by_player: dict[str, dict[str, str]] = {}
    appearances: Counter[str] = Counter()
    scenario_membership: defaultdict[str, list[str]] = defaultdict(list)

    for scenario, rows in rosters.items():
        for row in rows:
            name = player_name(row["player"])
            appearances[name] += 1
            scenario_membership[name].append(scenario)
            by_player.setdefault(name, row)

    priority_items = [
        (name, by_player[name], count)
        for name, count in appearances.items()
    ]
    priority_items.sort(key=sort_priority_key)

    tiered: defaultdict[str, list[tuple[str, dict[str, str], int]]] = defaultdict(list)
    for item in priority_items:
        _, row, _ = item
        tiered[tier_for(row)].append(item)

    shared_players = [
        name for name, count in appearances.items()
        if count == len(selected)
    ]

    scenario_specific = {
        scenario: [
            player_name(row["player"])
            for row in rows
            if appearances[player_name(row["player"])] == 1
        ]
        for scenario, rows in rosters.items()
    }

    lines: list[str] = [
        "# 1968 Astrodome Draft Room Packet v0",
        "",
        "Purpose: produce a human-led draft-room plan from card-backed roster scenarios.",
        "",
        "This is not an autonomous drafter. It is a structured draft-prep artifact: roster shells, target tiers, contingency notes, and risks.",
        "",
        "## Inputs",
        "",
        f"- Scenario summary: `{SCENARIO_CSV}`",
        f"- Scenario report: `{SCENARIO_MD}`",
        "- Credible scenario filter: `credible == yes`",
        f"- Baseline scenario: `{BASELINE_SCENARIO}`",
        f"- Selected scenarios: `{', '.join(selected)}`",
        "",
        "## Executive Recommendation",
        "",
        f"Use `{BASELINE_SCENARIO}` as the current baseline draft-room shell.",
        "",
        "Rationale:",
        "- It is legal and credible.",
        "- It is close to the $80M cap.",
        "- It preserves the strongest offensive spine among the current credible families.",
        "- It passes the bench-composition gates for catcher count, OF/corner depth, SS count, MI count, and non-low-OB bench depth.",
        "",
        "Use the remaining selected credible scenarios as alternate build families. Compare them by protected anchors, salary shape, pitcher spend, and fallback exposure.",
        "",
        "## Credible Scenario Summaries",
        "",
    ]

    for scenario in selected:
        lines.append(f"### {scenario}")
        lines.append("")
        lines.extend(scenario_summary_lines(summaries[scenario]))
        lines.append("")

    lines.extend(
        [
            "## Baseline Roster Shell",
            "",
            f"Scenario: `{BASELINE_SCENARIO}`",
            "",
            "| Role | Pool | Recommendation | Player | Salary | Position/Endurance | Warnings |",
            "|---|---|---|---|---:|---|---|",
        ]
    )
    for row in rosters[BASELINE_SCENARIO]:
        lines.append(
            f"| {row['role']} | {row['pool']} | {row['recommendation']} | {row['player']} | "
            f"{row['salary']} | {row['posEndurance']} | {row['warnings']} |"
        )

    for scenario in selected:
        if scenario == BASELINE_SCENARIO:
            continue

        lines.extend(
            [
                "",
                "## Alternate Roster Shell",
                "",
                f"Scenario: `{scenario}`",
                "",
                "| Role | Pool | Recommendation | Player | Salary | Position/Endurance | Warnings |",
                "|---|---|---|---|---:|---|---|",
            ]
        )
        for row in rosters[scenario]:
            lines.append(
                f"| {row['role']} | {row['pool']} | {row['recommendation']} | {row['player']} | "
                f"{row['salary']} | {row['posEndurance']} | {row['warnings']} |"
            )

    lines.extend(
        [
            "",
            "## Draft Priority Order",
            "",
            "Players appearing across more selected credible scenarios are treated as stronger draft-room targets than scenario-specific players.",
            "",
        ]
    )

    for tier in [
        "Position locks",
        "Bullpen core",
        "Starter targets",
        "Offensive / bench targets",
        "Bullpen depth",
        "Salary-fit / fallback options",
    ]:
        rows = tiered.get(tier, [])
        if not rows:
            continue

        lines.append(f"### {tier}")
        lines.append("")
        lines.append("| Priority | Player | Scenario Count | Role | Recommendation | Salary | Position/Endurance | Warnings |")
        lines.append("|---:|---|---:|---|---|---:|---|---|")
        for idx, (name, row, count) in enumerate(rows, start=1):
            lines.append(
                f"| {idx} | {row['player']} | {count} | {row['role']} | {row['recommendation']} | "
                f"{row['salary']} | {row['posEndurance']} | {row['warnings']} |"
            )
        lines.append("")

    lines.extend(
        [
            "## Shared Targets",
            "",
            "These players appear in every selected credible scenario.",
            "",
        ]
    )
    for name in sorted(shared_players):
        row = by_player[name]
        lines.append(f"- {row['player']} - {tier_for(row)} / {row['recommendation']} / {row['posEndurance']}")
    lines.append("")

    lines.extend(
        [
            "## Scenario-Specific Targets",
            "",
        ]
    )
    for scenario, names in scenario_specific.items():
        lines.append(f"### {scenario}")
        lines.append("")
        if not names:
            lines.append("- No scenario-specific players.")
        else:
            for name in sorted(names):
                row = by_player[name]
                lines.append(f"- {row['player']} - {tier_for(row)} / {row['recommendation']} / {row['posEndurance']}")
        lines.append("")

    lines.extend(
        [
            "## Contingency Notes",
            "",
            "These are draft-room prompts, not final substitutions.",
            "",
            "- If Mays is gone: validate whether the Bonds path remains acceptable or whether the CF/corner-bat overlay needs a separate contingency shell.",
            "- If Freehan is gone: evaluate Sims/Fernandez/Grote/Look combinations while preserving exactly 2-3 catchers.",
            "- If Fregosi is gone: preserve SS quality without exceeding the SS/MI credibility gates.",
            "- If McAuliffe is gone: force a 2B contingency check before spending another SS/MI slot.",
            "- If Santo is gone: preserve 3B coverage and avoid letting salary-fit infielders consume the build.",
            "- If Hoerner/Hamilton/Wilhelm are gone: use the reliever overlay to preserve closer-capable bullpen depth.",
            "- If the value-starter pool is depleted: rerun the scenario builder and check whether a premium-SP shell can survive under cap.",
            "",
            "## Current Risks",
            "",
            "- The selected credible scenarios now include multiple build families, but some shells still share most of the same low-cost support structure.",
            "- Premium-pitching scenario labels correctly fail credibility because no core-target starter survives cap repair.",
            "- Some offensive targets carry dead-HR-park dependency or strikeout/defense warnings; these should remain visible during draft decisions.",
            "- Salary-fit hitters still include low-OB fallback options. They are legal bench pieces, not preferred offensive targets.",
            "",
            "## Next Refinement",
            "",
            "Generate distinct build families:",
            "",
            "1. Balanced baseline",
            "2. Premium bat / value pitching",
            "3. True premium-SP anchor if it can survive cap and roster-shape gates",
            "4. Defense-and-bullpen shell",
            "",
        ]
    )

    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print("# RESULT SUMMARY")
    print(f"OUT_MD: {OUT_MD}")
    print(f"CREDIBLE_SCENARIOS: {len(credible_scenarios)}")
    print(f"SELECTED_SCENARIOS: {', '.join(selected)}")
    print(f"BASELINE: {BASELINE_SCENARIO}")
    print(f"SELECTED_COUNT: {len(selected)}")
    print(f"SHARED_TARGETS: {len(shared_players)}")
    print(f"PRIORITY_PLAYERS: {len(priority_items)}")


if __name__ == "__main__":
    main()
