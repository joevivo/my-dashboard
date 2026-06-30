import argparse
import json
from pathlib import Path

from report_observed_player_calibration_v0 import era, ops, print_row, role, signals

DEFAULT_MANIFEST_PATH = Path(
    "data/baseball/parsed/strat365/1980/observed-results/"
    "observed-player-results-batch-v0.manifest.json"
)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Report observed player calibration across a batch manifest."
    )
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST_PATH)
    parser.add_argument("--top", type=int, default=10)
    return parser.parse_args()


def load_manifest(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def load_batch_rows(manifest):
    rows = []
    for file_entry in manifest.get("files", []):
        output_path = Path(file_entry["outputJson"])
        payload = json.loads(output_path.read_text(encoding="utf-8-sig"))
        for row in payload.get("rows", []):
            item = dict(row)
            item["_batchSourceJson"] = str(output_path)
            rows.append(item)
    return rows


def main():
    args = parse_args()
    manifest = load_manifest(args.manifest)
    rows = load_batch_rows(manifest)
    hitters = [row for row in rows if role(row) == "hitter"]
    pitchers = [row for row in rows if role(row) == "pitcher"]

    print("# BIE Observed Player Batch Calibration v0")
    print()
    print(f"Manifest: {args.manifest}")
    print(f"CSV files: {manifest.get('counts', {}).get('csvFiles')}")
    print(f"Parsed files: {manifest.get('counts', {}).get('parsedFiles')}")
    print(f"Player-seasons: {len(rows)}")
    print(f"Hitters: {len(hitters)}")
    print(f"Pitchers: {len(pitchers)}")
    print(f"Warnings: {manifest.get('counts', {}).get('warnings')}")
    print()

    print("## Top Actual Hitter Player-Seasons by OPS")
    for row in sorted(hitters, key=lambda r: ops(r) or -1, reverse=True)[:args.top]:
        print_row(row)
    print()

    print("## Top Actual Pitcher Player-Seasons by ERA")
    for row in sorted(pitchers, key=lambda r: era(r) if era(r) is not None else 999)[:args.top]:
        print_row(row)
    print()

    print("## Largest Positive Ballpark Movement")
    for row in sorted(rows, key=lambda r: signals(r)[2] or 0, reverse=True)[:args.top]:
        print_row(row)
    print()

    print("## Largest Negative Ballpark Movement")
    for row in sorted(rows, key=lambda r: signals(r)[2] or 0)[:args.top]:
        print_row(row)


if __name__ == "__main__":
    main()
