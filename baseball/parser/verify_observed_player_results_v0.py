import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "data" / "baseball" / "parsed" / "strat365" / "1980"

REPORT = BASE / "observed-results" / "1980.sample-observed-player-results-v0.json"

EXPECTED_ROWS = 5
EXPECTED_HITTERS = 3
EXPECTED_PITCHERS = 2


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def fail(message):
    print(f"FAIL: {message}")
    raise SystemExit(1)


def main():
    if not REPORT.exists():
        fail(f"Missing observed player results report: {REPORT}")

    data = load_json(REPORT)

    if data.get("schemaVersion") != "bie.observed-player-results.v0":
        fail(f"Unexpected schemaVersion: {data.get('schemaVersion')}")

    if data.get("season") != 1980:
        fail(f"Unexpected season: {data.get('season')}")

    counts = data.get("counts", {})

    if counts.get("rows") != EXPECTED_ROWS:
        fail(f"Expected {EXPECTED_ROWS} rows, got {counts.get('rows')}")

    if counts.get("hitters") != EXPECTED_HITTERS:
        fail(f"Expected {EXPECTED_HITTERS} hitters, got {counts.get('hitters')}")

    if counts.get("pitchers") != EXPECTED_PITCHERS:
        fail(f"Expected {EXPECTED_PITCHERS} pitchers, got {counts.get('pitchers')}")

    if counts.get("resolvedPlayers") != EXPECTED_ROWS:
        fail(f"Expected all players resolved, got {counts.get('resolvedPlayers')}")

    if counts.get("warnings") != 0:
        fail(f"Expected 0 warnings, got {counts.get('warnings')}")

    rows = data.get("rows", [])
    if len(rows) != EXPECTED_ROWS:
        fail(f"Rows array length mismatch: {len(rows)}")

    by_name = {row["player"]["playerName"]: row for row in rows}

    schmidt = by_name.get("Schmidt, Mike")
    if not schmidt:
        fail("Missing Schmidt, Mike")

    if schmidt["observed"]["batting"]["homeRuns"] != 48:
        fail(f"Expected Schmidt 48 HR, got {schmidt['observed']['batting']['homeRuns']}")

    if schmidt["bieSignals"]["selectedBallparkRankDelta"] != 87:
        fail(f"Expected Schmidt Tiger delta 87, got {schmidt['bieSignals']['selectedBallparkRankDelta']}")

    brett = by_name.get("Brett, George")
    if not brett:
        fail("Missing Brett, George")

    if brett["observed"]["batting"]["battingAverage"] != 0.39:
        fail(f"Expected Brett .390 AVG, got {brett['observed']['batting']['battingAverage']}")

    reuss = by_name.get("Reuss, Jerry")
    if not reuss:
        fail("Missing Reuss, Jerry")

    if reuss["observed"]["pitching"]["inningsPitched"] != 229.2:
        fail(f"Expected Reuss 229.2 IP, got {reuss['observed']['pitching']['inningsPitched']}")

    if reuss["observed"]["pitching"]["earnedRuns"] != 74:
        fail(f"Expected Reuss 74 ER, got {reuss['observed']['pitching']['earnedRuns']}")

    print("PASS: observed player results v0 verification")
    print(f"Rows: {counts.get('rows')}")
    print(f"Hitters: {counts.get('hitters')}")
    print(f"Pitchers: {counts.get('pitchers')}")
    print(f"Resolved players: {counts.get('resolvedPlayers')}")
    print("Schmidt Tiger delta: 87")


if __name__ == "__main__":
    main()
