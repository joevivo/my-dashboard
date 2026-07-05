from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BUILDER = ROOT / "baseball" / "parser" / "report_1968_roster_template_sanity_review_v0.py"
JSON_OUT = ROOT / "data" / "baseball" / "parsed" / "strat365" / "1968" / "reports" / "1968.roster-template-sanity-review-v0.json"
MD_OUT = ROOT / "data" / "baseball" / "parsed" / "strat365" / "1968" / "reports" / "1968.roster-template-sanity-review-v0.md"

EXPECTED_CLASSIFICATIONS = {
    "balanced": "model_debt",
    "premium_hitter_heavy": "model_debt",
    "ace_pitcher_heavy": "suspicious",
    "value_heavy": "model_debt",
}


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    raise SystemExit(1)


def check(condition: bool, message: str) -> None:
    if not condition:
        fail(message)
    print(f"PASS: {message}")


def main() -> int:
    print("# VERIFY 1968 ROSTER TEMPLATE SANITY REVIEW")

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
    check(JSON_OUT.exists(), f"sanity review JSON exists: {JSON_OUT.relative_to(ROOT)}")
    check(MD_OUT.exists(), f"sanity review Markdown exists: {MD_OUT.relative_to(ROOT)}")

    payload = json.loads(JSON_OUT.read_text(encoding="utf-8"))

    check(payload.get("schemaVersion") == "bie.roster-template-sanity-review.v0", "schema version is sanity review v0")
    check(payload.get("season") == 1968, "season is 1968")
    check(payload.get("decision", {}).get("status") == "continue_with_caution", "decision is continue_with_caution")
    check(payload.get("decision", {}).get("recommendedNextArtifact") == "1968 draft pivot board v0", "recommended next artifact is draft pivot board")

    reviews = payload.get("strategyReviews", [])
    check(len(reviews) == 4, "has 4 strategy reviews")

    by_strategy = {review["strategyId"]: review for review in reviews}
    check(set(by_strategy) == set(EXPECTED_CLASSIFICATIONS), "all expected strategies are present")

    for strategy_id, expected in EXPECTED_CLASSIFICATIONS.items():
        review = by_strategy[strategy_id]
        check(review["classification"] == expected, f"{strategy_id}: classification is {expected}")
        check(len(review.get("findings", [])) >= 2, f"{strategy_id}: has multiple findings")

    check(len(payload.get("anchorReviews", [])) >= 7, "has universal anchor reviews")
    check(len(payload.get("modelDebt", [])) >= 5, "captures model debt findings")
    check(payload.get("draftBlockers", []) == [], "has no draft blockers")

    ace = by_strategy["ace_pitcher_heavy"]
    check(ace["exclusivePlayers"] >= 8, "ace_pitcher_heavy remains meaningfully distinct")
    check(ace["pitcherSalaryMillions"] > ace["hitterSalaryMillions"], "ace_pitcher_heavy spends more on pitching than hitting")

    value = by_strategy["value_heavy"]
    balanced = by_strategy["balanced"]
    check(value["highestOverlapPct"] >= 0.75, "value_heavy high-overlap issue is captured")
    check(balanced["exclusivePlayers"] == 0, "balanced zero-exclusive issue is captured")

    print("\n# SANITY REVIEW INTERPRETATION")
    print("PASS: no draft blockers.")
    print("PASS: outputs are useful for draft prep with caution.")
    print("PASS: strategic identity debt is explicitly captured.")

    print("\n# RESULT SUMMARY")
    print("PASS: 1968 roster template sanity review verifier passed.")
    print("Paste back:")
    print("1. # VERIFY 1968 ROSTER TEMPLATE SANITY REVIEW")
    print("2. # BUILDER STDOUT")
    print("3. # SANITY REVIEW INTERPRETATION")
    print("4. Any FAIL lines, if present")
    print("5. # BASEBALL GIT STATUS")
    print("6. # RESULT SUMMARY")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
