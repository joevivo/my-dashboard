import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

RULES = ROOT / "data/baseball/canonical/rules/strat365_1968_roster_rules_v1.json"
VALIDATOR = ROOT / "baseball/validation/validate_strat365_roster.py"

CASES = [
    {
        "name": "1968 illegal: only four starter-endurance pitchers",
        "roster": ROOT / "data/baseball/fixtures/rosters/1968_illegal_four_starters_v1.json",
        "expectedLegal": False,
        "expectedViolationCodes": ["startingEndurancePitchers.belowMinimum"],
    },
    {
        "name": "1968 legal: minimum pitching requirements satisfied",
        "roster": ROOT / "data/baseball/fixtures/rosters/1968_legal_minimum_pitching_v1.json",
        "expectedLegal": True,
        "expectedViolationCodes": [],
    },
]


def run_case(case):
    completed = subprocess.run(
        [
            sys.executable,
            str(VALIDATOR),
            "--rules",
            str(RULES),
            "--roster",
            str(case["roster"]),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    result = json.loads(completed.stdout)
    actual_legal = result["legal"]
    actual_codes = [v["code"] for v in result["violations"]]

    legal_ok = actual_legal == case["expectedLegal"]
    codes_ok = actual_codes == case["expectedViolationCodes"]

    return {
        "name": case["name"],
        "legalOk": legal_ok,
        "codesOk": codes_ok,
        "actualLegal": actual_legal,
        "actualViolationCodes": actual_codes,
        "expectedLegal": case["expectedLegal"],
        "expectedViolationCodes": case["expectedViolationCodes"],
    }


def main():
    results = [run_case(case) for case in CASES]
    failed = [r for r in results if not r["legalOk"] or not r["codesOk"]]

    for result in results:
        status = "PASS" if result not in failed else "FAIL"
        print(f"{status}: {result['name']}")
        print(f"  legal: expected={result['expectedLegal']} actual={result['actualLegal']}")
        print(f"  violations: expected={result['expectedViolationCodes']} actual={result['actualViolationCodes']}")

    if failed:
        print("\nRegression failure.")
        sys.exit(1)

    print("\nAll roster validation regressions passed.")


if __name__ == "__main__":
    main()
