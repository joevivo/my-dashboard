import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

BATCH = ROOT / "baseball" / "parser" / "batch_observed_player_results_v0.py"
INPUT_DIR = ROOT / "baseball" / "fixtures" / "observed-results"
OUTPUT_DIR = ROOT / "data" / "baseball" / "parsed" / "strat365" / "1980" / "observed-results" / "batch-test"
EXPECTED_OUTPUT = OUTPUT_DIR / "1980.sample-observed-player-results-v0.observed-player-results-v0.json"


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def fail(message):
    print(f"FAIL: {message}")
    raise SystemExit(1)


def main():
    command = [
        sys.executable,
        str(BATCH),
        "--input-dir",
        str(INPUT_DIR),
        "--output-dir",
        str(OUTPUT_DIR),
    ]

    result = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        capture_output=True,
    )

    if result.returncode != 0:
        print(result.stdout)
        print(result.stderr)
        fail(f"Batch parser failed with code {result.returncode}")

    if not EXPECTED_OUTPUT.exists():
        fail(f"Missing expected batch output: {EXPECTED_OUTPUT}")

    data = load_json(EXPECTED_OUTPUT)
    counts = data.get("counts", {})

    if data.get("schemaVersion") != "bie.observed-player-results.v0":
        fail(f"Unexpected schemaVersion: {data.get('schemaVersion')}")

    if counts.get("rows") != 5:
        fail(f"Expected 5 rows, got {counts.get('rows')}")

    if counts.get("hitters") != 3:
        fail(f"Expected 3 hitters, got {counts.get('hitters')}")

    if counts.get("pitchers") != 2:
        fail(f"Expected 2 pitchers, got {counts.get('pitchers')}")

    if counts.get("resolvedPlayers") != 5:
        fail(f"Expected 5 resolved players, got {counts.get('resolvedPlayers')}")

    if counts.get("warnings") != 0:
        fail(f"Expected 0 warnings, got {counts.get('warnings')}")

    print("PASS: observed player results batch v0 verification")
    print("CSV files: 1")
    print("Rows: 5")
    print("Hitters: 3")
    print("Pitchers: 2")
    print("Resolved players: 5")
    print("Warnings: 0")


if __name__ == "__main__":
    main()
