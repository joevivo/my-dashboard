import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "data" / "baseball" / "parsed" / "strat365" / "1980"

REPORT = BASE / "observed-results" / "1980.sample-observed-player-results-v0.json"


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def main():
    if not REPORT.exists():
        raise SystemExit(f"Missing observed player results report: {REPORT}")

    data = load_json(REPORT)
    counts = data["counts"]
    rows = data["rows"]

    print("# BIE Observed Player Results Inventory v0")
    print()
    print(f"Season: {data['season']}")
    print(f"Rows: {counts['rows']}")
    print(f"Hitters: {counts['hitters']}")
    print(f"Pitchers: {counts['pitchers']}")
    print(f"Resolved players: {counts['resolvedPlayers']}")
    print(f"Warnings: {counts['warnings']}")
    print()

    hitters = [r for r in rows if r["player"]["role"] == "hitter"]
    pitchers = [r for r in rows if r["player"]["role"] == "pitcher"]

    print("## Hitter Results")
    for row in sorted(
        hitters,
        key=lambda r: r["observed"]["batting"].get("ops") or 0,
        reverse=True,
    ):
        batting = row["observed"]["batting"]
        signal = row["bieSignals"]
        print(
            f"- {row['player']['playerName']} | "
            f"OPS {batting.get('ops')} | HR {batting.get('homeRuns')} | "
            f"DA rank {signal.get('defenseAwareRank')} | "
            f"park rank {signal.get('selectedBallparkRank')} | "
            f"park delta {signal.get('selectedBallparkRankDelta')}"
        )
    print()

    print("## Pitcher Results")
    for row in sorted(
        pitchers,
        key=lambda r: r["observed"]["pitching"].get("era") or 999,
    ):
        pitching = row["observed"]["pitching"]
        signal = row["bieSignals"]
        print(
            f"- {row['player']['playerName']} | "
            f"ERA {pitching.get('era')} | WHIP {pitching.get('whip')} | "
            f"IP {pitching.get('inningsPitched')} | "
            f"DA rank {signal.get('defenseAwareRank')} | "
            f"park rank {signal.get('selectedBallparkRank')} | "
            f"park delta {signal.get('selectedBallparkRankDelta')}"
        )
    print()

    print("## Calibration Seeds")
    for row in rows:
        signal = row["bieSignals"]
        delta = signal.get("selectedBallparkRankDelta")
        if isinstance(delta, int) and abs(delta) >= 25:
            print(
                f"- {row['player']['playerName']} has large ballpark rank movement: "
                f"{signal.get('defenseAwareRank')} -> {signal.get('selectedBallparkRank')} "
                f"delta {delta}"
            )


if __name__ == "__main__":
    main()
