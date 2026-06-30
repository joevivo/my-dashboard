import argparse
import json
from pathlib import Path

DEFAULT_INPUT_PATH = Path(
    "data/baseball/parsed/strat365/1980/observed-results/"
    "1980-aquarium-drinkers-observed-player-results.observed-player-results-v0.json"
)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Report observed player calibration against BIE draft and ballpark signals."
    )
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT_PATH)
    parser.add_argument("--top", type=int, default=8)
    return parser.parse_args()


def load_rows(path):
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    return payload["rows"]


def role(row):
    return row.get("player", {}).get("role")


def name(row):
    return row.get("player", {}).get("playerName")


def signals(row):
    bie = row.get("bieSignals", {})
    return (
        bie.get("defenseAwareRank"),
        bie.get("selectedBallparkRank"),
        bie.get("selectedBallparkRankDelta"),
    )


def batting(row):
    return row.get("observed", {}).get("batting", {})


def pitching(row):
    return row.get("observed", {}).get("pitching", {})


def ops(row):
    return batting(row).get("ops")


def era(row):
    return pitching(row).get("era")


def whip(row):
    return pitching(row).get("whip")


def fmt(value, digits):
    if value is None:
        return "n/a"
    return f"{value:.{digits}f}"


def print_row(row):
    da, park, delta = signals(row)
    if role(row) == "hitter":
        print(f"- {name(row)} | OPS {fmt(ops(row), 3)} | DA rank {da} | park rank {park} | delta {delta}")
    else:
        print(f"- {name(row)} | ERA {fmt(era(row), 2)} | WHIP {fmt(whip(row), 2)} | DA rank {da} | park rank {park} | delta {delta}")


def main():
    args = parse_args()
    rows = load_rows(args.input)
    hitters = [row for row in rows if role(row) == "hitter"]
    pitchers = [row for row in rows if role(row) == "pitcher"]

    print("# BIE Observed Player Calibration v0")
    print()
    print(f"Source: {args.input}")
    print(f"Rows: {len(rows)}")
    print(f"Hitters: {len(hitters)}")
    print(f"Pitchers: {len(pitchers)}")
    print()

    print("## Top Actual Hitters by OPS")
    for row in sorted(hitters, key=lambda r: ops(r) or -1, reverse=True)[:args.top]:
        print_row(row)
    print()

    print("## Top Actual Pitchers by ERA")
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