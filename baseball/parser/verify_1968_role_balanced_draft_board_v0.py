from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BUILDER = ROOT / "baseball" / "parser" / "build_1968_role_balanced_draft_board_v0.py"
BOARD_JSON = ROOT / "data" / "baseball" / "parsed" / "strat365" / "1968" / "draft-boards" / "1968.role-balanced-draft-board-v0.json"
BOARD_MD = ROOT / "data" / "baseball" / "parsed" / "strat365" / "1968" / "draft-boards" / "1968.role-balanced-draft-board-v0.md"


REQUIRED_BUCKETS = [
    "premiumHitters",
    "primaryCatchers",
    "starterEndurancePitchers",
    "pureRelievers",
    "closerQualifiedPitchers",
    "cheapHitterValues",
    "cheapPitcherValues",
    "cardBackedPitchers",
]


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    raise SystemExit(1)


def check(condition: bool, message: str) -> None:
    if not condition:
        fail(message)
    print(f"PASS: {message}")


def main() -> int:
    print("# VERIFY 1968 ROLE-BALANCED DRAFT BOARD")

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
    check(BOARD_JSON.exists(), f"board JSON exists: {BOARD_JSON.relative_to(ROOT)}")
    check(BOARD_MD.exists(), f"board Markdown exists: {BOARD_MD.relative_to(ROOT)}")

    payload = json.loads(BOARD_JSON.read_text(encoding="utf-8"))
    counts = payload.get("counts", {})
    buckets = payload.get("buckets", {})

    check(payload.get("schemaVersion") == "bie.role-balanced-draft-board.v0", "schema version is role-balanced v0")
    check(counts.get("players") == 537, "board has 537 players")
    check(counts.get("hitters", 0) >= 13, "board has enough hitters")
    check(counts.get("pitchers", 0) >= 11, "board has enough pitchers")
    check(counts.get("primaryCatchers", 0) >= 2, "board has enough primary catchers")
    check(counts.get("starterEndurancePitchers", 0) >= 5, "board has enough starter-endurance pitchers")
    check(counts.get("pureRelievers", 0) >= 4, "board has enough pure relievers")
    check(counts.get("closerQualifiedPitchers", 0) >= 1, "board has enough closer-qualified pitchers")
    check(counts.get("cardBackedPlayers", 0) > 0, "board has card-backed players")

    for bucket in REQUIRED_BUCKETS:
        check(bucket in buckets, f"bucket exists: {bucket}")
        check(len(buckets[bucket]) > 0, f"bucket is non-empty: {bucket}")

    check(buckets["primaryCatchers"][0].get("primaryPosition") == "C", "top primary catcher has catcher position")
    check(buckets["starterEndurancePitchers"][0].get("starterEndurance") is not None, "top starter bucket row has starter endurance")
    check(buckets["pureRelievers"][0].get("reliefEndurance") is not None, "top pure reliever has relief endurance")
    check(buckets["pureRelievers"][0].get("starterEndurance") is None, "top pure reliever has no starter endurance")
    check(buckets["closerQualifiedPitchers"][0].get("closerEndurance") is not None, "top closer bucket row has closer endurance")
    check(buckets["cardBackedPitchers"][0].get("confidenceTier") == "card-backed", "top card-backed pitcher is card-backed")

    print("\n# RESULT SUMMARY")
    print("PASS: 1968 role-balanced draft board verifier passed.")
    print("Paste back:")
    print("1. # VERIFY 1968 ROLE-BALANCED DRAFT BOARD")
    print("2. # BUILDER STDOUT")
    print("3. Any FAIL lines, if present")
    print("4. # RESULT SUMMARY")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
