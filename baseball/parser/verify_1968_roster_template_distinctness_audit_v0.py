from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BUILDER = ROOT / "baseball" / "parser" / "report_1968_roster_template_distinctness_audit_v0.py"
JSON_OUT = ROOT / "data" / "baseball" / "parsed" / "strat365" / "1968" / "reports" / "1968.roster-template-distinctness-audit-v0.json"
MD_OUT = ROOT / "data" / "baseball" / "parsed" / "strat365" / "1968" / "reports" / "1968.roster-template-distinctness-audit-v0.md"

EXPECTED_STRATEGIES = [
    "balanced",
    "premium_hitter_heavy",
    "ace_pitcher_heavy",
    "value_heavy",
]


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    raise SystemExit(1)


def check(condition: bool, message: str) -> None:
    if not condition:
        fail(message)
    print(f"PASS: {message}")


def pair_key(row: dict) -> tuple[str, str]:
    return (row["left"], row["right"])


def main() -> int:
    print("# VERIFY 1968 ROSTER TEMPLATE DISTINCTNESS AUDIT")

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
    check(JSON_OUT.exists(), f"distinctness JSON exists: {JSON_OUT.relative_to(ROOT)}")
    check(MD_OUT.exists(), f"distinctness Markdown exists: {MD_OUT.relative_to(ROOT)}")

    payload = json.loads(JSON_OUT.read_text(encoding="utf-8"))

    check(payload.get("schemaVersion") == "bie.roster-template-distinctness-audit.v0", "schema version is distinctness audit v0")
    check(payload.get("season") == 1968, "season is 1968")
    check(payload.get("strategyOrder") == EXPECTED_STRATEGIES, "strategy order is expected")

    summaries = payload.get("templateSummaries", [])
    check(len(summaries) == 4, "has 4 template summaries")

    by_strategy = {summary["strategyId"]: summary for summary in summaries}
    check(set(by_strategy) == set(EXPECTED_STRATEGIES), "all expected strategies have summaries")

    pairwise = payload.get("pairwiseOverlap", [])
    check(len(pairwise) == 6, "has 6 pairwise overlap rows")

    pairwise_by_key = {pair_key(row): row for row in pairwise}

    check(
        pairwise_by_key[("balanced", "value_heavy")]["sharedPlayers"] >= 18,
        "balanced and value_heavy high-overlap condition is captured",
    )
    check(
        pairwise_by_key[("ace_pitcher_heavy", "value_heavy")]["sharedPlayers"] <= 10,
        "ace_pitcher_heavy and value_heavy low-overlap condition is captured",
    )
    check(
        by_strategy["ace_pitcher_heavy"]["exclusivePlayers"] >= 8,
        "ace_pitcher_heavy has strong exclusive-player count",
    )
    check(
        by_strategy["balanced"]["exclusivePlayers"] == 0,
        "balanced has no exclusive players in v0",
    )

    universal = payload.get("universalSharedPlayers", [])
    check(len(universal) >= 5, "has at least 5 universal shared players")

    replacements = payload.get("replacementCandidates", {})
    check(set(replacements) == set(EXPECTED_STRATEGIES), "replacement candidates exist for all strategies")

    for strategy_id in EXPECTED_STRATEGIES:
        pools = replacements[strategy_id]
        for pool_name in ["hitters", "starter_pitchers", "pure_relievers", "closer_pitchers"]:
            check(pool_name in pools, f"{strategy_id}: replacement pool exists for {pool_name}")
            check(len(pools[pool_name]) >= 3, f"{strategy_id}: at least 3 replacement candidates for {pool_name}")

    print("\n# DISTINCTNESS INTERPRETATION")
    print("PASS: ace_pitcher_heavy is meaningfully distinct.")
    print("PASS: balanced/value/premium overlap is captured as v0 model debt.")
    print("PASS: replacement candidate pools are available for next-step draft pivots.")

    print("\n# RESULT SUMMARY")
    print("PASS: 1968 roster template distinctness audit verifier passed.")
    print("Paste back:")
    print("1. # VERIFY 1968 ROSTER TEMPLATE DISTINCTNESS AUDIT")
    print("2. # BUILDER STDOUT")
    print("3. # DISTINCTNESS INTERPRETATION")
    print("4. Any FAIL lines, if present")
    print("5. # BASEBALL GIT STATUS")
    print("6. # RESULT SUMMARY")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
