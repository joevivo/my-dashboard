from __future__ import annotations

import json
import subprocess
import sys
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BUILDER = ROOT / "baseball" / "parser" / "build_1968_roster_template_comparison_v0.py"
COMPARISON_JSON = ROOT / "data" / "baseball" / "parsed" / "strat365" / "1968" / "draft-boards" / "1968.roster-template-comparison-v0.json"
COMPARISON_MD = ROOT / "data" / "baseball" / "parsed" / "strat365" / "1968" / "draft-boards" / "1968.roster-template-comparison-v0.md"

EXPECTED_STRATEGIES = {
    "balanced",
    "premium_hitter_heavy",
    "ace_pitcher_heavy",
    "value_heavy",
}


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    raise SystemExit(1)


def check(condition: bool, message: str) -> None:
    if not condition:
        fail(message)
    print(f"PASS: {message}")


def main() -> int:
    print("# VERIFY 1968 ROSTER TEMPLATE COMPARISON")

    check(BUILDER.exists(), f"builder exists: {BUILDER.relative_to(ROOT)}")

    result = subprocess.run(
        [sys.executable, str(BUILDER)],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )

    if result.stdout:
        print("\n# BUILDER STDOUT")
        print(result.stdout.strip())

    if result.stderr:
        print("\n# BUILDER STDERR")
        print(result.stderr.strip())

    check(result.returncode == 0, "builder exits successfully")
    check(COMPARISON_JSON.exists(), f"comparison JSON exists: {COMPARISON_JSON.relative_to(ROOT)}")
    check(COMPARISON_MD.exists(), f"comparison Markdown exists: {COMPARISON_MD.relative_to(ROOT)}")

    payload = json.loads(COMPARISON_JSON.read_text(encoding="utf-8"))
    templates = payload.get("templates", [])

    check(payload.get("schemaVersion") == "bie.roster-template-comparison.v0", "schema version is roster-template comparison v0")
    check(payload.get("season") == 1968, "season is 1968")
    check(payload.get("salaryCapMillions") == 80.0, "salary cap is 80.00M")
    check(len(templates) == 4, "comparison has 4 templates")

    strategy_ids = {template.get("strategyId") for template in templates}
    check(strategy_ids == EXPECTED_STRATEGIES, "all expected strategies are present")

    by_id = {template["strategyId"]: template for template in templates}

    for strategy_id, template in by_id.items():
        counts = template["counts"]
        players = template["players"]
        legality = template["legality"]

        check(template["salaryUsedMillions"] <= 80.0, f"{strategy_id}: salary is at or below cap")
        check(template["pitcherSalaryMillions"] >= template["pitcherSalaryFloorMillions"], f"{strategy_id}: pitcher salary meets floor")
        check(template["pitcherSalaryMillions"] <= template["pitcherSalaryCeilingMillions"], f"{strategy_id}: pitcher salary stays below ceiling")

        check(counts["players"] == 25, f"{strategy_id}: exactly 25 players")
        check(counts["hitters"] == 14, f"{strategy_id}: exactly 14 hitters")
        check(counts["pitchers"] == 11, f"{strategy_id}: exactly 11 pitchers")
        check(counts["primaryCatchers"] >= 2, f"{strategy_id}: at least 2 primary catchers")
        check(counts["starterEndurancePitchers"] >= 5, f"{strategy_id}: at least 5 starter-endurance pitchers")
        check(counts["pureRelievers"] >= 4, f"{strategy_id}: at least 4 pure relievers")
        check(counts["closerEndurancePitchers"] >= 1, f"{strategy_id}: at least 1 closer-endurance pitcher")

        check(all(item["status"] == "PASS" for item in legality), f"{strategy_id}: all legality checks pass")

        player_ids = [str(player.get("playerId")) for player in players]
        check(len(player_ids) == len(set(player_ids)), f"{strategy_id}: no duplicate player IDs")

        positions = Counter(
            player.get("primaryPosition")
            for player in players
            if player.get("role") == "hitter"
        )
        for position in ["C", "1B", "2B", "3B", "SS", "LF", "CF", "RF"]:
            check(positions.get(position, 0) >= 1, f"{strategy_id}: hitter coverage at {position}")

    check(
        by_id["premium_hitter_heavy"]["pitcherSalaryMillions"] < by_id["balanced"]["pitcherSalaryMillions"],
        "premium_hitter_heavy spends less on pitching than balanced",
    )
    check(
        by_id["ace_pitcher_heavy"]["pitcherSalaryMillions"] > by_id["balanced"]["pitcherSalaryMillions"],
        "ace_pitcher_heavy spends more on pitching than balanced",
    )
    check(
        by_id["ace_pitcher_heavy"]["pitcherSalaryMillions"] > by_id["premium_hitter_heavy"]["pitcherSalaryMillions"],
        "ace_pitcher_heavy spends more on pitching than premium_hitter_heavy",
    )

    print("\n# STRATEGY SALARY SHAPES")
    for strategy_id in ["balanced", "premium_hitter_heavy", "ace_pitcher_heavy", "value_heavy"]:
        template = by_id[strategy_id]
        print(
            f"{strategy_id}: total={template['salaryUsedMillions']:.2f} | "
            f"hitting={template['hitterSalaryMillions']:.2f} | "
            f"pitching={template['pitcherSalaryMillions']:.2f} | "
            f"pitcherBand={template['pitcherSalaryFloorMillions']:.2f}-{template['pitcherSalaryCeilingMillions']:.2f}"
        )

    print("\n# RESULT SUMMARY")
    print("PASS: 1968 roster template comparison verifier passed.")
    print("Paste back:")
    print("1. # VERIFY 1968 ROSTER TEMPLATE COMPARISON")
    print("2. # BUILDER STDOUT")
    print("3. # STRATEGY SALARY SHAPES")
    print("4. Any FAIL lines, if present")
    print("5. # RESULT SUMMARY")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
