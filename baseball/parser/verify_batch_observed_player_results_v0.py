import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

BATCH = ROOT / "baseball" / "parser" / "batch_observed_player_results_v0.py"
INPUT_DIR = ROOT / "baseball" / "fixtures" / "observed-results"
OUTPUT_DIR = ROOT / "data" / "baseball" / "parsed" / "strat365" / "1980" / "observed-results" / "batch-test"
MANIFEST = OUTPUT_DIR / "manifest.json"
EXPECTED_OUTPUT = OUTPUT_DIR / "1980.sample-observed-player-results-v0.observed-player-results-v0.json"


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def fail(message):
    print(f"FAIL: {message}")
    raise SystemExit(1)


def expect(actual, expected, label):
    if actual != expected:
        fail(f"Expected {label} {expected}, got {actual}")


def main():
    command = [
        sys.executable,
        str(BATCH),
        "--input-dir",
        str(INPUT_DIR),
        "--output-dir",
        str(OUTPUT_DIR),
        "--manifest-output",
        str(MANIFEST),
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

    if not MANIFEST.exists():
        fail(f"Missing expected batch manifest: {MANIFEST}")

    data = load_json(EXPECTED_OUTPUT)
    counts = data.get("counts", {})

    expect(data.get("schemaVersion"), "bie.observed-player-results.v0", "result schemaVersion")
    expect(counts.get("rows"), 5, "result rows")
    expect(counts.get("hitters"), 3, "result hitters")
    expect(counts.get("pitchers"), 2, "result pitchers")
    expect(counts.get("resolvedPlayers"), 5, "result resolvedPlayers")
    expect(counts.get("warnings"), 0, "result warnings")

    manifest = load_json(MANIFEST)
    manifest_counts = manifest.get("counts", {})

    expect(
        manifest.get("schemaVersion"),
        "bie.observed-player-results-batch-manifest.v0",
        "manifest schemaVersion",
    )
    expect(manifest.get("season"), 1980, "manifest season")
    expect(manifest_counts.get("csvFiles"), 1, "manifest csvFiles")
    expect(manifest_counts.get("parsedFiles"), 1, "manifest parsedFiles")
    expect(manifest_counts.get("failures"), 0, "manifest failures")
    expect(manifest_counts.get("rows"), 5, "manifest rows")
    expect(manifest_counts.get("hitters"), 3, "manifest hitters")
    expect(manifest_counts.get("pitchers"), 2, "manifest pitchers")
    expect(manifest_counts.get("resolvedPlayers"), 5, "manifest resolvedPlayers")
    expect(manifest_counts.get("warnings"), 0, "manifest warnings")

    files = manifest.get("files", [])
    expect(len(files), 1, "manifest file count")
    expect(manifest.get("failures"), [], "manifest failures list")

    print("PASS: observed player results batch v0 verification")
    print("CSV files: 1")
    print("Parsed files: 1")
    print("Rows: 5")
    print("Hitters: 3")
    print("Pitchers: 2")
    print("Resolved players: 5")
    print("Warnings: 0")
    print("Manifest verified")


if __name__ == "__main__":
    main()
