from __future__ import annotations

import json
import subprocess
import sys
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BUILDER = ROOT / "baseball" / "parser" / "build_1968_salary_aware_roster_template_v0.py"
TEMPLATE_JSON = ROOT / "data" / "baseball" / "parsed" / "strat365" / "1968" / "draft-boards" / "1968.salary-aware-roster-template-v0.json"
TEMPLATE_MD = ROOT / "data" / "baseball" / "parsed" / "strat365" / "1968" / "draft-boards" / "1968.salary-aware-roster-template-v0.md"


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    raise SystemExit(1)


def check(condition: bool, message: str) -> None:
    if not condition:
        fail(message)
    print(f"PASS: {message}")


def main() -> int:
    print("# VERIFY 1968 SALARY-AWARE ROSTER TEMPLATE")

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
    check(TEMPLATE_JSON.exists(), f"template JSON exists: {TEMPLATE_JSON.relative_to(ROOT)}")
    check(TEMPLATE_MD.exists(), f"template Markdown exists: {TEMPLATE_MD.relative_to(ROOT)}")

    payload = json.loads(TEMPLATE_JSON.read_text(encoding="utf-8"))
    template = payload.get("template", {})
    counts = template.get("counts", {})
    players = template.get("players", [])
    legality = template.get("legality", [])

    check(payload.get("schemaVersion") == "bie.salary-aware-roster-template.v0", "schema version is salary-aware roster template v0")
    check(template.get("salaryCapMillions") == 80.0, "salary cap is 80.00M")
    check(template.get("salaryUsedMillions", 999.0) <= 80.0, "salary used is at or below cap")
    check(template.get("salaryRemainingMillions", -1.0) >= 0.0, "salary remaining is non-negative")

    check(counts.get("players") == 25, "template has exactly 25 players")
    check(counts.get("hitters") == 14, "template has exactly 14 hitters")
    check(counts.get("pitchers") == 11, "template has exactly 11 pitchers")
    check(counts.get("primaryCatchers", 0) >= 2, "template has at least 2 primary catchers")
    check(counts.get("starterEndurancePitchers", 0) >= 5, "template has at least 5 starter-endurance pitchers")
    check(counts.get("pureRelievers", 0) >= 4, "template has at least 4 pure relievers")
    check(counts.get("closerEndurancePitchers", 0) >= 1, "template has at least 1 closer-endurance pitcher")
    check(counts.get("cardBackedPlayers", 0) > 0, "template includes card-backed players")

    player_ids = [str(player.get("playerId")) for player in players]
    check(len(player_ids) == len(set(player_ids)), "template has no duplicate player IDs")

    failing_legality = [item for item in legality if item.get("status") != "PASS"]
    check(not failing_legality, "all legality checks pass")

    hitter_positions = Counter(
        player.get("primaryPosition")
        for player in players
        if player.get("role") == "hitter"
    )

    required_positions = ["C", "1B", "2B", "3B", "SS", "LF", "CF", "RF"]
    for position in required_positions:
        check(hitter_positions.get(position, 0) >= 1, f"template has hitter coverage at {position}")

    overloaded_positions = {
        position: count
        for position, count in hitter_positions.items()
        if count > 2
    }
    check(not overloaded_positions, "no hitter position has more than 2 rostered players")

    check(any(player.get("closerEndurance") for player in players), "template includes derived closer endurance")
    check(any(player.get("templateReason") == "closer-qualified pure reliever" for player in players), "template explicitly selects a closer-qualified pure reliever")

    print("\n# POSITION COUNTS")
    for position, count in sorted(hitter_positions.items()):
        print(f"{position}: {count}")

    print("\n# RESULT SUMMARY")
    print("PASS: 1968 salary-aware roster template verifier passed.")
    print("Paste back:")
    print("1. # VERIFY 1968 SALARY-AWARE ROSTER TEMPLATE")
    print("2. # BUILDER STDOUT")
    print("3. # POSITION COUNTS")
    print("4. Any FAIL lines, if present")
    print("5. # RESULT SUMMARY")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
