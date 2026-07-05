from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
SEASON = "1968"
SALARY_CAP = 80.0
PITCHER_COUNT = 11
HITTER_COUNT = 14
TOTAL_PLAYERS = 25
MIN_PLAYER_SALARY = 0.50

BASE_BUILDER_PATH = ROOT / "baseball" / "parser" / "build_1968_salary_aware_roster_template_v0.py"
OUTPUT_DIR = ROOT / "data" / "baseball" / "parsed" / "strat365" / SEASON / "draft-boards"

JSON_OUT = OUTPUT_DIR / "1968.roster-template-comparison-v0.json"
MD_OUT = OUTPUT_DIR / "1968.roster-template-comparison-v0.md"


def load_base_module():
    spec = importlib.util.spec_from_file_location("salary_template_v0", BASE_BUILDER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load base builder: {BASE_BUILDER_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


base = load_base_module()


STRATEGIES: dict[str, dict[str, Any]] = {
    "balanced": {
        "description": "Balanced 80M roster with meaningful investment in both hitting and pitching.",
        "pitcher_salary_floor": 28.0,
        "pitcher_salary_ceiling": 42.0,
        "hitter_score_weight": 1.00,
        "pitcher_score_weight": 1.00,
        "hitter_value_weight": 0.22,
        "pitcher_value_weight": 0.22,
        "hitter_salary_penalty": 1.20,
        "pitcher_salary_penalty": 1.00,
        "card_bonus": 5.0,
    },
    "premium_hitter_heavy": {
        "description": "Hitter-forward build, but with a credible pitching floor.",
        "pitcher_salary_floor": 22.0,
        "pitcher_salary_ceiling": 32.0,
        "hitter_score_weight": 1.24,
        "pitcher_score_weight": 0.84,
        "hitter_value_weight": 0.14,
        "pitcher_value_weight": 0.26,
        "hitter_salary_penalty": 0.72,
        "pitcher_salary_penalty": 1.25,
        "card_bonus": 5.0,
    },
    "ace_pitcher_heavy": {
        "description": "Pitcher-forward build anchored by expensive starter-endurance arms.",
        "pitcher_salary_floor": 45.0,
        "pitcher_salary_ceiling": 60.0,
        "hitter_score_weight": 0.84,
        "pitcher_score_weight": 1.28,
        "hitter_value_weight": 0.34,
        "pitcher_value_weight": 0.10,
        "hitter_salary_penalty": 1.75,
        "pitcher_salary_penalty": 0.58,
        "card_bonus": 5.0,
    },
    "value_heavy": {
        "description": "Value-forward build that still carries a credible pitching spend.",
        "pitcher_salary_floor": 24.0,
        "pitcher_salary_ceiling": 36.0,
        "hitter_score_weight": 0.95,
        "pitcher_score_weight": 0.95,
        "hitter_value_weight": 0.34,
        "pitcher_value_weight": 0.34,
        "hitter_salary_penalty": 1.00,
        "pitcher_salary_penalty": 1.00,
        "card_bonus": 3.0,
    },
}


def load_rows() -> list[dict[str, Any]]:
    board = base.load_board()
    roster_players = base.load_roster_players()
    roster_by_id = {str(player.get("playerId")): player for player in roster_players}
    return [base.enrich_row(row, roster_by_id) for row in board]


def strategy_score(row: dict[str, Any], config: dict[str, Any]) -> float:
    is_hitter = bool(row.get("isHitter"))
    score_weight = config["hitter_score_weight"] if is_hitter else config["pitcher_score_weight"]
    value_weight = config["hitter_value_weight"] if is_hitter else config["pitcher_value_weight"]
    salary_penalty = config["hitter_salary_penalty"] if is_hitter else config["pitcher_salary_penalty"]

    score = float(row["hybridDraftScore"])
    value = min(float(row["hybridValueScore"]), 120.0)
    salary = float(row["salaryMillions"])
    card_bonus = float(config["card_bonus"]) if row.get("isCardBacked") else 0.0

    return score * score_weight + value * value_weight + card_bonus - salary * salary_penalty


def role_text(row: dict[str, Any]) -> str:
    parts = [
        row.get("primaryPosition"),
        row.get("starterEndurance"),
        row.get("reliefEndurance"),
        row.get("closerEndurance"),
    ]
    return "/".join(str(part) for part in parts if part)


def count_roster(roster: list[dict[str, Any]], predicate) -> int:
    return sum(1 for row in roster if predicate(row))


def total_salary(roster: list[dict[str, Any]]) -> float:
    return sum(row["salaryMillions"] for row in roster)


def pitcher_salary(roster: list[dict[str, Any]]) -> float:
    return sum(row["salaryMillions"] for row in roster if row["isPitcher"])


def hitter_salary(roster: list[dict[str, Any]]) -> float:
    return sum(row["salaryMillions"] for row in roster if row["isHitter"])


def select_from_pool(
    pool: list[dict[str, Any]],
    selected_ids: set[str],
    max_pick_salary: float,
    config: dict[str, Any],
) -> dict[str, Any]:
    candidates = [
        row for row in pool
        if row["playerId"] not in selected_ids
        and row["salaryMillions"] <= max_pick_salary + 0.0001
    ]

    if not candidates:
        raise RuntimeError(f"No candidate available. maxPickSalary={max_pick_salary:.2f}")

    return sorted(
        candidates,
        key=lambda row: (
            -strategy_score(row, config),
            -row["hybridDraftScore"],
            row["salaryMillions"],
            str(row.get("playerName")),
        ),
    )[0]


def add_pitcher_pick(
    roster: list[dict[str, Any]],
    selected_ids: set[str],
    pool: list[dict[str, Any]],
    config: dict[str, Any],
    reason: str,
) -> None:
    ceiling = float(config["pitcher_salary_ceiling"])
    remaining_pitcher_slots_after_pick = PITCHER_COUNT - count_roster(roster, lambda r: r["isPitcher"]) - 1
    max_pick_salary = ceiling - pitcher_salary(roster) - (remaining_pitcher_slots_after_pick * MIN_PLAYER_SALARY)

    row = select_from_pool(pool, selected_ids, max_pick_salary, config)
    row["_templateReason"] = reason
    roster.append(row)
    selected_ids.add(row["playerId"])


def add_hitter_pick(
    roster: list[dict[str, Any]],
    selected_ids: set[str],
    pool: list[dict[str, Any]],
    config: dict[str, Any],
    reason: str,
) -> None:
    remaining_total_slots_after_pick = TOTAL_PLAYERS - len(roster) - 1
    max_pick_salary = SALARY_CAP - total_salary(roster) - (remaining_total_slots_after_pick * MIN_PLAYER_SALARY)

    row = select_from_pool(pool, selected_ids, max_pick_salary, config)
    row["_templateReason"] = reason
    roster.append(row)
    selected_ids.add(row["playerId"])


def pitching_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    return {
        "pitchers": len(rows),
        "starterEndurancePitchers": count_roster(rows, lambda r: r["isStarterEndurancePitcher"]),
        "pureRelievers": count_roster(rows, lambda r: r["isPureReliever"]),
        "closerEndurancePitchers": count_roster(rows, lambda r: r["isCloserEndurancePitcher"]),
    }


def pitching_legal(rows: list[dict[str, Any]]) -> bool:
    counts = pitching_counts(rows)
    return (
        counts["pitchers"] == PITCHER_COUNT
        and counts["starterEndurancePitchers"] >= 5
        and counts["pureRelievers"] >= 4
        and counts["closerEndurancePitchers"] >= 1
    )


def upgrade_pitching_to_floor(
    roster: list[dict[str, Any]],
    selected_ids: set[str],
    all_pitchers: list[dict[str, Any]],
    config: dict[str, Any],
) -> None:
    floor = float(config["pitcher_salary_floor"])
    ceiling = float(config["pitcher_salary_ceiling"])

    iterations = 0
    while pitcher_salary(roster) + 0.0001 < floor and iterations < 30:
        iterations += 1
        current_pitchers = [row for row in roster if row["isPitcher"]]
        best_swap: tuple[float, dict[str, Any], dict[str, Any]] | None = None

        for old in current_pitchers:
            for new in all_pitchers:
                if new["playerId"] in selected_ids:
                    continue
                if new["salaryMillions"] <= old["salaryMillions"]:
                    continue

                new_pitch_salary = pitcher_salary(roster) - old["salaryMillions"] + new["salaryMillions"]
                if new_pitch_salary > ceiling + 0.0001:
                    continue

                candidate_pitchers = [row for row in current_pitchers if row["playerId"] != old["playerId"]] + [new]
                if not pitching_legal(candidate_pitchers):
                    continue

                progress = min(new_pitch_salary, floor) - pitcher_salary(roster)
                score_gain = strategy_score(new, config) - strategy_score(old, config)
                swap_score = progress * 100.0 + score_gain

                if best_swap is None or swap_score > best_swap[0]:
                    best_swap = (swap_score, old, new)

        if best_swap is None:
            break

        _, old, new = best_swap
        roster.remove(old)
        selected_ids.remove(old["playerId"])
        new["_templateReason"] = "pitcher budget floor"
        roster.append(new)
        selected_ids.add(new["playerId"])

    if pitcher_salary(roster) + 0.0001 < floor:
        raise RuntimeError(
            f"Could not reach pitcher salary floor. "
            f"floor={floor:.2f}, actual={pitcher_salary(roster):.2f}"
        )


def build_pitching_staff(
    roster: list[dict[str, Any]],
    selected_ids: set[str],
    pools: dict[str, list[dict[str, Any]]],
    config: dict[str, Any],
) -> None:
    while count_roster(roster, lambda r: r["isStarterEndurancePitcher"]) < 5:
        add_pitcher_pick(roster, selected_ids, pools["starter_pitchers"], config, "starter-endurance pitcher")

    if count_roster(roster, lambda r: r["isCloserEndurancePitcher"]) < 1:
        add_pitcher_pick(roster, selected_ids, pools["pure_closers"] or pools["closers"], config, "closer-qualified pure reliever")

    while count_roster(roster, lambda r: r["isPureReliever"]) < 4:
        add_pitcher_pick(roster, selected_ids, pools["pure_relievers"], config, "pure reliever")

    while count_roster(roster, lambda r: r["isPitcher"]) < PITCHER_COUNT:
        add_pitcher_pick(roster, selected_ids, pools["pitchers"], config, "pitcher depth")

    upgrade_pitching_to_floor(roster, selected_ids, pools["pitchers"], config)


def build_hitter_group(
    roster: list[dict[str, Any]],
    selected_ids: set[str],
    pools: dict[str, list[dict[str, Any]]],
    config: dict[str, Any],
) -> None:
    while count_roster(roster, lambda r: r["isPrimaryCatcher"]) < 2:
        add_hitter_pick(roster, selected_ids, pools["catchers"], config, "primary catcher")

    for position in ["1B", "2B", "3B", "SS", "LF", "CF", "RF"]:
        if count_roster(roster, lambda r, p=position: r.get("primaryPosition") == p) == 0:
            pool = [row for row in pools["hitters"] if row.get("primaryPosition") == position]
            add_hitter_pick(roster, selected_ids, pool, config, f"primary position coverage: {position}")

    while count_roster(roster, lambda r: r["isHitter"]) < HITTER_COUNT:
        hitter_depth_pool = [
            row for row in pools["hitters"]
            if count_roster(roster, lambda r, p=row.get("primaryPosition"): r.get("primaryPosition") == p) < 2
        ]
        if not hitter_depth_pool:
            hitter_depth_pool = pools["hitters"]
        add_hitter_pick(roster, selected_ids, hitter_depth_pool, config, "hitter depth")


def compact(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "playerId": row.get("playerId"),
        "playerName": row.get("playerName"),
        "team": row.get("team"),
        "role": row.get("role"),
        "templateReason": row.get("_templateReason"),
        "primaryPosition": row.get("primaryPosition"),
        "rosterEndurance": row.get("rosterEndurance"),
        "starterEndurance": row.get("starterEndurance"),
        "reliefEndurance": row.get("reliefEndurance"),
        "closerEndurance": row.get("closerEndurance"),
        "salaryMillions": row.get("salaryMillions"),
        "hybridDraftScore": row.get("hybridDraftScore"),
        "hybridValueScore": row.get("hybridValueScore"),
        "confidenceTier": row.get("confidenceTier"),
    }


def build_strategy_template(strategy_id: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    config = STRATEGIES[strategy_id]

    pools = {
        "hitters": [row for row in rows if row["isHitter"]],
        "pitchers": [row for row in rows if row["isPitcher"]],
        "catchers": [row for row in rows if row["isPrimaryCatcher"]],
        "starter_pitchers": [row for row in rows if row["isStarterEndurancePitcher"]],
        "pure_relievers": [row for row in rows if row["isPureReliever"]],
        "pure_closers": [row for row in rows if row["isPureReliever"] and row["isCloserEndurancePitcher"]],
        "closers": [row for row in rows if row["isCloserEndurancePitcher"]],
    }

    roster: list[dict[str, Any]] = []
    selected_ids: set[str] = set()

    build_pitching_staff(roster, selected_ids, pools, config)
    build_hitter_group(roster, selected_ids, pools, config)

    if len(roster) != TOTAL_PLAYERS:
        raise RuntimeError(f"{strategy_id}: expected {TOTAL_PLAYERS} players, found {len(roster)}")

    counts = {
        "players": len(roster),
        "hitters": count_roster(roster, lambda r: r["isHitter"]),
        "pitchers": count_roster(roster, lambda r: r["isPitcher"]),
        "primaryCatchers": count_roster(roster, lambda r: r["isPrimaryCatcher"]),
        "starterEndurancePitchers": count_roster(roster, lambda r: r["isStarterEndurancePitcher"]),
        "pureRelievers": count_roster(roster, lambda r: r["isPureReliever"]),
        "closerEndurancePitchers": count_roster(roster, lambda r: r["isCloserEndurancePitcher"]),
        "cardBackedPlayers": count_roster(roster, lambda r: r["isCardBacked"]),
    }

    used_salary = round(total_salary(roster), 2)
    used_hitter_salary = round(hitter_salary(roster), 2)
    used_pitcher_salary = round(pitcher_salary(roster), 2)

    legality = [
        ("players", counts["players"] == 25),
        ("hitters>=13", counts["hitters"] >= 13),
        ("pitchers>=11", counts["pitchers"] >= 11),
        ("primaryCatchers>=2", counts["primaryCatchers"] >= 2),
        ("starterEndurancePitchers>=5", counts["starterEndurancePitchers"] >= 5),
        ("pureRelievers>=4", counts["pureRelievers"] >= 4),
        ("closerEndurancePitchers>=1", counts["closerEndurancePitchers"] >= 1),
        ("salaryCap", used_salary <= SALARY_CAP),
        ("pitcherSalaryFloor", used_pitcher_salary >= float(config["pitcher_salary_floor"])),
        ("pitcherSalaryCeiling", used_pitcher_salary <= float(config["pitcher_salary_ceiling"])),
    ]

    return {
        "strategyId": strategy_id,
        "description": config["description"],
        "salaryCapMillions": SALARY_CAP,
        "salaryUsedMillions": used_salary,
        "salaryRemainingMillions": round(SALARY_CAP - used_salary, 2),
        "hitterSalaryMillions": used_hitter_salary,
        "pitcherSalaryMillions": used_pitcher_salary,
        "pitcherSalaryFloorMillions": float(config["pitcher_salary_floor"]),
        "pitcherSalaryCeilingMillions": float(config["pitcher_salary_ceiling"]),
        "counts": counts,
        "legality": [{"check": name, "status": "PASS" if passed else "FAIL"} for name, passed in legality],
        "players": [compact(row) for row in roster],
    }


def build_markdown(payload: dict[str, Any]) -> str:
    lines: list[str] = [
        "# 1968 Roster Template Comparison v0",
        "",
        "Purpose: compare multiple legal 80M roster-construction concepts generated from the 1968 role-balanced draft pool.",
        "",
        "These are draft-assist templates, not final team recommendations.",
        "",
        "## Strategy Summary",
        "",
        "| Strategy | Salary | Hitter Salary | Pitcher Salary | Pitcher Band | Hitters | Pitchers | Card-backed |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]

    for template in payload["templates"]:
        counts = template["counts"]
        band = f"{template['pitcherSalaryFloorMillions']:.2f}-{template['pitcherSalaryCeilingMillions']:.2f}"
        lines.append(
            f"| {template['strategyId']} | {template['salaryUsedMillions']:.2f} | "
            f"{template['hitterSalaryMillions']:.2f} | {template['pitcherSalaryMillions']:.2f} | "
            f"{band} | {counts['hitters']} | {counts['pitchers']} | {counts['cardBackedPlayers']} |"
        )

    for template in payload["templates"]:
        lines.extend([
            "",
            f"## {template['strategyId']}",
            "",
            template["description"],
            "",
            "### Legality",
            "",
            "| Check | Status |",
            "|---|---|",
        ])

        for item in template["legality"]:
            lines.append(f"| {item['check']} | {item['status']} |")

        lines.extend([
            "",
            "### Roster",
            "",
            "| # | Player | Team | Role | Reason | Salary | Score | Value | Tier |",
            "|---:|---|---|---|---|---:|---:|---:|---|",
        ])

        for index, row in enumerate(template["players"], 1):
            lines.append(
                f"| {index} | {row['playerName']} | {row['team']} | {role_text(row)} | "
                f"{row['templateReason']} | {row['salaryMillions']:.2f} | "
                f"{row['hybridDraftScore']:.2f} | {row['hybridValueScore']:.2f} | {row['confidenceTier']} |"
            )

    return "\n".join(lines) + "\n"


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    rows = load_rows()
    templates = [build_strategy_template(strategy_id, rows) for strategy_id in STRATEGIES]

    payload = {
        "schemaVersion": "bie.roster-template-comparison.v0",
        "season": int(SEASON),
        "salaryCapMillions": SALARY_CAP,
        "templateCount": len(templates),
        "templates": templates,
        "limitations": [
            "Greedy strategy templates, not exhaustive optimization.",
            "No live draft availability modeling.",
            "No ballpark-specific optimization yet.",
            "No platoon or defense substitution model yet.",
        ],
    }

    JSON_OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    MD_OUT.write_text(build_markdown(payload), encoding="utf-8")

    print("# TEMPLATE COMPARISON SUMMARY")
    for template in templates:
        counts = template["counts"]
        legality_status = "PASS" if all(item["status"] == "PASS" for item in template["legality"]) else "FAIL"
        print(
            f"{template['strategyId']}: legality={legality_status} | "
            f"salary={template['salaryUsedMillions']:.2f} | "
            f"hitters={counts['hitters']} | pitchers={counts['pitchers']} | "
            f"hitterSalary={template['hitterSalaryMillions']:.2f} | "
            f"pitcherSalary={template['pitcherSalaryMillions']:.2f} | "
            f"pitcherBand={template['pitcherSalaryFloorMillions']:.2f}-{template['pitcherSalaryCeilingMillions']:.2f} | "
            f"cardBacked={counts['cardBackedPlayers']}"
        )

    print("\n# STRATEGY LEADERS")
    for template in templates:
        print(f"\n{template['strategyId']}")
        for row in template["players"][:8]:
            print(
                f"- {row['playerName']} | {row['team']} | {role_text(row)} | "
                f"reason={row['templateReason']} | salary={row['salaryMillions']:.2f} | "
                f"score={row['hybridDraftScore']:.2f} | tier={row['confidenceTier']}"
            )

    print("\n# OUTPUT FILES")
    print(JSON_OUT.relative_to(ROOT))
    print(MD_OUT.relative_to(ROOT))

    print("\n# RESULT SUMMARY")
    print("Created 1968 roster template comparison v0.")
    print("Paste back:")
    print("1. # TEMPLATE COMPARISON SUMMARY")
    print("2. # STRATEGY LEADERS")
    print("3. # OUTPUT FILES")
    print("4. # BASEBALL GIT STATUS")
    print("5. # RESULT SUMMARY")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
