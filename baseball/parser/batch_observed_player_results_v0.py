import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INPUT_DIR = ROOT / "data" / "baseball" / "raw" / "strat365" / "1980" / "observed-results"
DEFAULT_OUTPUT_DIR = ROOT / "data" / "baseball" / "parsed" / "strat365" / "1980" / "observed-results"
DEFAULT_MANIFEST = DEFAULT_OUTPUT_DIR / "observed-player-results-batch-v0.manifest.json"
PARSER = ROOT / "baseball" / "parser" / "parse_observed_player_results_v0.py"


def parse_args():
    parser = argparse.ArgumentParser(
        description="Batch parse observed Strat player results CSV files into BIE observed-results JSON."
    )
    parser.add_argument(
        "--input-dir",
        default=str(DEFAULT_INPUT_DIR),
        help="Directory containing observed player results CSV files.",
    )
    parser.add_argument(
        "--output-dir",
        default=str(DEFAULT_OUTPUT_DIR),
        help="Directory for parsed observed player results JSON files.",
    )
    parser.add_argument(
        "--manifest-output",
        default=str(DEFAULT_MANIFEST),
        help="Output JSON manifest summarizing the batch parse.",
    )
    parser.add_argument(
        "--pattern",
        default="*.csv",
        help="CSV filename pattern to parse.",
    )
    return parser.parse_args()


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def rel(path):
    return str(path.relative_to(ROOT)).replace("\\", "/")


def main():
    args = parse_args()
    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    manifest_output = Path(args.manifest_output)

    if not input_dir.is_absolute():
        input_dir = ROOT / input_dir

    if not output_dir.is_absolute():
        output_dir = ROOT / output_dir

    if not manifest_output.is_absolute():
        manifest_output = ROOT / manifest_output

    if not input_dir.exists():
        raise SystemExit(f"Missing input directory: {input_dir}")

    csv_files = sorted(input_dir.glob(args.pattern))
    if not csv_files:
        raise SystemExit(f"No CSV files matched {args.pattern} in {input_dir}")

    output_dir.mkdir(parents=True, exist_ok=True)

    parsed = []
    failures = []

    for csv_path in csv_files:
        output_path = output_dir / f"{csv_path.stem}.observed-player-results-v0.json"

        command = [
            sys.executable,
            str(PARSER),
            "--input",
            str(csv_path),
            "--output",
            str(output_path),
        ]

        result = subprocess.run(
            command,
            cwd=ROOT,
            text=True,
            capture_output=True,
        )

        if result.returncode != 0:
            failures.append({
                "inputCsv": rel(csv_path),
                "returnCode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
            })
            continue

        report = load_json(output_path)
        parsed.append({
            "inputCsv": rel(csv_path),
            "outputJson": rel(output_path),
            "rows": report["counts"]["rows"],
            "hitters": report["counts"]["hitters"],
            "pitchers": report["counts"]["pitchers"],
            "resolvedPlayers": report["counts"]["resolvedPlayers"],
            "warnings": report["counts"]["warnings"],
        })

    total_rows = sum(item["rows"] for item in parsed)
    total_hitters = sum(item["hitters"] for item in parsed)
    total_pitchers = sum(item["pitchers"] for item in parsed)
    total_resolved = sum(item["resolvedPlayers"] for item in parsed)
    total_warnings = sum(item["warnings"] for item in parsed)

    manifest = {
        "schemaVersion": "bie.observed-player-results-batch-manifest.v0",
        "parserVersion": "batch_observed_player_results_v0",
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "season": 1980,
        "source": {
            "inputDirectory": rel(input_dir),
            "outputDirectory": rel(output_dir),
            "manifestOutput": rel(manifest_output),
            "pattern": args.pattern,
        },
        "counts": {
            "csvFiles": len(csv_files),
            "parsedFiles": len(parsed),
            "failures": len(failures),
            "rows": total_rows,
            "hitters": total_hitters,
            "pitchers": total_pitchers,
            "resolvedPlayers": total_resolved,
            "warnings": total_warnings,
        },
        "files": parsed,
        "failures": failures,
    }

    write_json(manifest_output, manifest)

    print("# BIE Observed Player Results Batch v0")
    print()
    print(f"Input directory: {rel(input_dir)}")
    print(f"Output directory: {rel(output_dir)}")
    print(f"Manifest: {rel(manifest_output)}")
    print(f"CSV files: {len(csv_files)}")
    print(f"Parsed: {len(parsed)}")
    print(f"Failures: {len(failures)}")
    print()

    print("Totals:")
    print(f"- Rows: {total_rows}")
    print(f"- Hitters: {total_hitters}")
    print(f"- Pitchers: {total_pitchers}")
    print(f"- Resolved players: {total_resolved}")
    print(f"- Warnings: {total_warnings}")
    print()

    print("Files:")
    for item in parsed:
        print(
            f"- {item['inputCsv']} -> {item['outputJson']} | "
            f"rows {item['rows']} | warnings {item['warnings']}"
        )

    if failures:
        print()
        print("Failures:")
        for failure in failures:
            print(f"- {failure['inputCsv']} failed with code {failure['returnCode']}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
