from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
SEASON = "1968"

COMPARISON_BUILDER = ROOT / "baseball" / "parser" / "build_1968_roster_template_comparison_v0.py"
COMPARISON_JSON = ROOT / "data" / "baseball" / "parsed" / "strat365" / SEASON / "draft-boards" / "1968.roster-template-comparison-v0.json"

OUTPUT_DIR = ROOT / "data" / "baseball" / "parsed" / "strat365" / SEASON / "reports"
JSON_OUT = OUTPUT_DIR / "1968.roster-template-distinctness-audit-v0.json"
MD_OUT = OUTPUT_DIR / "1968.roster-template-distinctness-audit-v0.md"

STRATEGY_ORDER = [
    "balanced",
    "premium_hitter_heavy",
    "ace_pitcher_heavy",
    "value_heavy",
]


def load_module(path: Path):
    spec = importlib.util.spec_from_file_location("comparison_builder_v0", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_comparison_builder() -> None:
    result = subprocess.run(
        [sys.executable, str(COMPARISON_BUILDER)],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        print("# COMPARISON BUILDER STDOUT")
        print(result.stdout)
        print("# COMPARISON BUILDER STDERR")
        print(result.stderr)
        raise RuntimeError("Comparison builder failed.")


def role_text(player: dict[str, Any]) -> str:
    parts = [
        player.get("primaryPosition"),
        player.get("starterEndurance"),
        player.get("reliefEndurance"),
        player.get("closerEndurance"),
    ]
    return "/".join(str(part) for part in parts if part)


def player_label(player: dict[str, Any]) -> str:
    return (
        f"{player.get('playerName')} | {player.get('team')} | {role_text(player)} | "
        f"salary={float(player.get('salaryMillions', 0)):.2f}"
    )


def pitcher_function(player: dict[str, Any]) -> str:
    has_starter = bool(player.get("starterEndurance"))
    has_relief = bool(player.get("reliefEndurance"))
    has_closer = bool(player.get("closerEndurance"))

    if has_starter and has_relief:
        return "starter_relief"
    if has_starter:
        return "starter_only"
    if has_closer:
        return "pure_relief_closer"
    if has_relief:
        return "pure_relief"
    return "pitcher_other"


def salary_by_hitter_position(players: list[dict[str, Any]]) -> dict[str, float]:
    totals: dict[str, float] = defaultdict(float)
    for player in players:
        if player.get("role") != "hitter":
            continue
        position = str(player.get("primaryPosition") or "unknown")
        totals[position] += float(player.get("salaryMillions") or 0.0)
    return {key: round(value, 2) for key, value in sorted(totals.items())}


def salary_by_pitcher_function(players: list[dict[str, Any]]) -> dict[str, float]:
    totals: dict[str, float] = defaultdict(float)
    for player in players:
        if player.get("role") != "pitcher":
            continue
        totals[pitcher_function(player)] += float(player.get("salaryMillions") or 0.0)
    return {key: round(value, 2) for key, value in sorted(totals.items())}


def ids_for(template: dict[str, Any]) -> set[str]:
    return {str(player.get("playerId")) for player in template["players"]}


def player_index(templates: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    for template in templates.values():
        for player in template["players"]:
            index[str(player.get("playerId"))] = player
    return index


def build_pairwise_overlap(templates: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for left, right in combinations(STRATEGY_ORDER, 2):
        left_ids = ids_for(templates[left])
        right_ids = ids_for(templates[right])
        shared = left_ids & right_ids
        rows.append({
            "left": left,
            "right": right,
            "sharedPlayers": len(shared),
            "overlapPct": round(len(shared) / 25.0, 3),
            "leftOnly": len(left_ids - right_ids),
            "rightOnly": len(right_ids - left_ids),
        })
    return rows


def build_shared_and_exclusive(templates: dict[str, dict[str, Any]]) -> dict[str, Any]:
    all_id_sets = [ids_for(templates[strategy_id]) for strategy_id in STRATEGY_ORDER]
    universal_ids = set.intersection(*all_id_sets)
    index = player_index(templates)

    appearances: Counter[str] = Counter()
    for id_set in all_id_sets:
        appearances.update(id_set)

    exclusive_by_strategy: dict[str, list[dict[str, Any]]] = {}
    for strategy_id in STRATEGY_ORDER:
        exclusive_ids = [
            player_id
            for player_id in ids_for(templates[strategy_id])
            if appearances[player_id] == 1
        ]
        exclusive_players = [index[player_id] for player_id in exclusive_ids]
        exclusive_by_strategy[strategy_id] = sorted(
            exclusive_players,
            key=lambda player: (-float(player.get("salaryMillions") or 0.0), str(player.get("playerName"))),
        )

    return {
        "universalSharedPlayers": sorted(
            [index[player_id] for player_id in universal_ids],
            key=lambda player: (-float(player.get("salaryMillions") or 0.0), str(player.get("playerName"))),
        ),
        "exclusiveByStrategy": exclusive_by_strategy,
        "appearanceCounts": dict(appearances),
    }


def compact_replacement(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "playerId": row.get("playerId"),
        "playerName": row.get("playerName"),
        "team": row.get("team"),
        "role": row.get("role"),
        "primaryPosition": row.get("primaryPosition"),
        "starterEndurance": row.get("starterEndurance"),
        "reliefEndurance": row.get("reliefEndurance"),
        "closerEndurance": row.get("closerEndurance"),
        "salaryMillions": row.get("salaryMillions"),
        "hybridDraftScore": row.get("hybridDraftScore"),
        "hybridValueScore": row.get("hybridValueScore"),
        "confidenceTier": row.get("confidenceTier"),
    }


def build_replacement_candidates(
    comparison_module,
    templates: dict[str, dict[str, Any]],
) -> dict[str, dict[str, list[dict[str, Any]]]]:
    rows = comparison_module.load_rows()
    replacements: dict[str, dict[str, list[dict[str, Any]]]] = {}

    for strategy_id in STRATEGY_ORDER:
        config = comparison_module.STRATEGIES[strategy_id]
        selected_ids = ids_for(templates[strategy_id])

        pools = {
            "hitters": [row for row in rows if row["isHitter"] and str(row["playerId"]) not in selected_ids],
            "starter_pitchers": [row for row in rows if row["isStarterEndurancePitcher"] and str(row["playerId"]) not in selected_ids],
            "pure_relievers": [row for row in rows if row["isPureReliever"] and str(row["playerId"]) not in selected_ids],
            "closer_pitchers": [row for row in rows if row["isCloserEndurancePitcher"] and str(row["playerId"]) not in selected_ids],
        }

        strategy_replacements: dict[str, list[dict[str, Any]]] = {}
        for pool_name, pool_rows in pools.items():
            ranked = sorted(
                pool_rows,
                key=lambda row: (
                    -comparison_module.strategy_score(row, config),
                    -row["hybridDraftScore"],
                    row["salaryMillions"],
                    str(row.get("playerName")),
                ),
            )
            strategy_replacements[pool_name] = [compact_replacement(row) for row in ranked[:5]]

        replacements[strategy_id] = strategy_replacements

    return replacements


def build_payload() -> dict[str, Any]:
    run_comparison_builder()

    comparison = json.loads(COMPARISON_JSON.read_text(encoding="utf-8"))
    templates = {template["strategyId"]: template for template in comparison["templates"]}

    comparison_module = load_module(COMPARISON_BUILDER)

    pairwise_overlap = build_pairwise_overlap(templates)
    shared_exclusive = build_shared_and_exclusive(templates)

    template_summaries = []
    for strategy_id in STRATEGY_ORDER:
        template = templates[strategy_id]
        players = template["players"]
        template_summaries.append({
            "strategyId": strategy_id,
            "salaryUsedMillions": template["salaryUsedMillions"],
            "hitterSalaryMillions": template["hitterSalaryMillions"],
            "pitcherSalaryMillions": template["pitcherSalaryMillions"],
            "cardBackedPlayers": template["counts"]["cardBackedPlayers"],
            "exclusivePlayers": len(shared_exclusive["exclusiveByStrategy"][strategy_id]),
            "hitterPositionSalary": salary_by_hitter_position(players),
            "pitcherFunctionSalary": salary_by_pitcher_function(players),
        })

    replacements = build_replacement_candidates(comparison_module, templates)

    return {
        "schemaVersion": "bie.roster-template-distinctness-audit.v0",
        "season": 1968,
        "source": str(COMPARISON_JSON.relative_to(ROOT)),
        "strategyOrder": STRATEGY_ORDER,
        "templateSummaries": template_summaries,
        "pairwiseOverlap": pairwise_overlap,
        "universalSharedPlayers": shared_exclusive["universalSharedPlayers"],
        "exclusiveByStrategy": shared_exclusive["exclusiveByStrategy"],
        "replacementCandidates": replacements,
        "interpretation": [
            "High overlap means the current greedy model is relying on common legal/value anchors.",
            "Premium-hitter-heavy and value-heavy are budget-similar in v0 and need additional distinctness constraints later.",
            "Ace-pitcher-heavy is budget-distinct and functions as an extreme pitcher-forward reference.",
        ],
    }


def build_markdown(payload: dict[str, Any]) -> str:
    lines: list[str] = [
        "# 1968 Roster Template Distinctness Audit v0",
        "",
        "Purpose: measure whether the current legal roster templates are materially different from each other.",
        "",
        "## Template Summary",
        "",
        "| Strategy | Total | Hitting | Pitching | Card-backed | Exclusive Players |",
        "|---|---:|---:|---:|---:|---:|",
    ]

    for summary in payload["templateSummaries"]:
        lines.append(
            f"| {summary['strategyId']} | {summary['salaryUsedMillions']:.2f} | "
            f"{summary['hitterSalaryMillions']:.2f} | {summary['pitcherSalaryMillions']:.2f} | "
            f"{summary['cardBackedPlayers']} | {summary['exclusivePlayers']} |"
        )

    lines.extend([
        "",
        "## Pairwise Overlap",
        "",
        "| Left | Right | Shared | Overlap | Left Only | Right Only |",
        "|---|---|---:|---:|---:|---:|",
    ])

    for row in payload["pairwiseOverlap"]:
        lines.append(
            f"| {row['left']} | {row['right']} | {row['sharedPlayers']} | "
            f"{row['overlapPct']:.3f} | {row['leftOnly']} | {row['rightOnly']} |"
        )

    lines.extend([
        "",
        "## Universal Shared Players",
        "",
    ])

    if payload["universalSharedPlayers"]:
        for player in payload["universalSharedPlayers"]:
            lines.append(f"- {player_label(player)}")
    else:
        lines.append("- None")

    lines.extend([
        "",
        "## Salary by Hitter Position",
        "",
    ])

    for summary in payload["templateSummaries"]:
        lines.append(f"### {summary['strategyId']}")
        for position, salary in summary["hitterPositionSalary"].items():
            lines.append(f"- {position}: {salary:.2f}")
        lines.append("")

    lines.extend([
        "## Salary by Pitcher Function",
        "",
    ])

    for summary in payload["templateSummaries"]:
        lines.append(f"### {summary['strategyId']}")
        for function_name, salary in summary["pitcherFunctionSalary"].items():
            lines.append(f"- {function_name}: {salary:.2f}")
        lines.append("")

    lines.extend([
        "## Top Replacement Candidates",
        "",
    ])

    for strategy_id in STRATEGY_ORDER:
        lines.append(f"### {strategy_id}")
        for pool_name, players in payload["replacementCandidates"][strategy_id].items():
            lines.append(f"#### {pool_name}")
            for player in players[:3]:
                lines.append(f"- {player_label(player)}")
        lines.append("")

    lines.extend([
        "## Interpretation",
        "",
    ])

    for item in payload["interpretation"]:
        lines.append(f"- {item}")

    return "\n".join(lines) + "\n"


def print_summary(payload: dict[str, Any]) -> None:
    print("# DISTINCTNESS SUMMARY")
    for summary in payload["templateSummaries"]:
        print(
            f"{summary['strategyId']}: total={summary['salaryUsedMillions']:.2f} | "
            f"hitting={summary['hitterSalaryMillions']:.2f} | "
            f"pitching={summary['pitcherSalaryMillions']:.2f} | "
            f"cardBacked={summary['cardBackedPlayers']} | "
            f"exclusivePlayers={summary['exclusivePlayers']}"
        )

    print("\n# PAIRWISE OVERLAP")
    for row in payload["pairwiseOverlap"]:
        print(
            f"{row['left']} vs {row['right']}: shared={row['sharedPlayers']}/25 | "
            f"overlap={row['overlapPct']:.3f} | leftOnly={row['leftOnly']} | rightOnly={row['rightOnly']}"
        )

    print("\n# UNIVERSAL SHARED PLAYERS")
    if payload["universalSharedPlayers"]:
        for player in payload["universalSharedPlayers"]:
            print(f"- {player_label(player)}")
    else:
        print("None")

    print("\n# PITCHER FUNCTION SALARY")
    for summary in payload["templateSummaries"]:
        functions = ", ".join(
            f"{name}={salary:.2f}"
            for name, salary in summary["pitcherFunctionSalary"].items()
        )
        print(f"{summary['strategyId']}: {functions}")

    print("\n# OUTPUT FILES")
    print(JSON_OUT.relative_to(ROOT))
    print(MD_OUT.relative_to(ROOT))

    print("\n# RESULT SUMMARY")
    print("Created 1968 roster template distinctness audit v0.")
    print("Paste back:")
    print("1. # DISTINCTNESS SUMMARY")
    print("2. # PAIRWISE OVERLAP")
    print("3. # UNIVERSAL SHARED PLAYERS")
    print("4. # PITCHER FUNCTION SALARY")
    print("5. # OUTPUT FILES")
    print("6. # BASEBALL GIT STATUS")
    print("7. # RESULT SUMMARY")


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    payload = build_payload()
    JSON_OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    MD_OUT.write_text(build_markdown(payload), encoding="utf-8")

    print_summary(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
