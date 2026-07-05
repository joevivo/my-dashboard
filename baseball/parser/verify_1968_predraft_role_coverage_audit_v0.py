from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
AUDIT_SCRIPT = ROOT / "baseball" / "parser" / "report_1968_predraft_role_coverage_audit_v0.py"
AUDIT_JSON = ROOT / "data" / "baseball" / "parsed" / "strat365" / "1968" / "reports" / "1968.predraft-role-coverage-audit.json"


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    raise SystemExit(1)


def check(condition: bool, message: str) -> None:
    if not condition:
        fail(message)
    print(f"PASS: {message}")


def main() -> int:
    print("# VERIFY 1968 PRE-DRAFT ROLE COVERAGE AUDIT")

    check(AUDIT_SCRIPT.exists(), f"audit script exists: {AUDIT_SCRIPT.relative_to(ROOT)}")

    result = subprocess.run(
        [sys.executable, str(AUDIT_SCRIPT)],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )

    if result.stdout:
        print("\n# AUDIT SCRIPT STDOUT")
        print(result.stdout.strip())

    if result.stderr:
        print("\n# AUDIT SCRIPT STDERR")
        print(result.stderr.strip())

    check(result.returncode == 0, "audit script exits successfully")
    check(AUDIT_JSON.exists(), f"audit JSON exists: {AUDIT_JSON.relative_to(ROOT)}")

    payload = json.loads(AUDIT_JSON.read_text(encoding="utf-8"))
    counts = payload.get("counts", {})

    check(counts.get("players") == 537, "1968 audit has 537 players")
    check(counts.get("hitters", 0) >= 13, "full board has at least 13 hitters")
    check(counts.get("pitchers", 0) >= 11, "full board has at least 11 pitchers")
    check(counts.get("primaryCatchers", 0) >= 2, "full board has at least 2 primary catchers")
    check(counts.get("starterEndurancePitchers", 0) >= 5, "full board has at least 5 starter-endurance pitchers")
    check(counts.get("pureRelievers", 0) >= 4, "full board has at least 4 pure relievers")
    check(counts.get("closerEndurancePitchers", 0) >= 1, "full board has at least 1 closer-endurance pitcher")
    check(counts.get("cardBackedPlayers", 0) > 0, "audit includes card-backed players")

    closer_candidates = payload.get("topCloserEndurancePitchers", [])
    check(len(closer_candidates) > 0, "audit emits closer-endurance candidate list")

    first_closer = closer_candidates[0]
    check(first_closer.get("closerEndurance") is not None, "top closer candidate has derived closer endurance")
    check(first_closer.get("cardReliefText") is not None, "top closer candidate cites card relief text")

    legality = payload.get("legalitySignal", [])
    failures = [item for item in legality if str(item).startswith("FAIL")]
    check(not failures, "legality signal contains no FAIL entries")

    print("\n# RESULT SUMMARY")
    print("PASS: 1968 pre-draft role coverage audit verifier passed.")
    print("Paste back:")
    print("1. # VERIFY 1968 PRE-DRAFT ROLE COVERAGE AUDIT")
    print("2. # AUDIT SCRIPT STDOUT")
    print("3. Any FAIL lines, if present")
    print("4. # RESULT SUMMARY")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
