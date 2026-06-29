import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "data" / "baseball" / "parsed" / "strat365" / "1980"

REPORT = BASE / "roster-construction" / "1980.sample-roster-v0.roster-construction-v0.json"

EXPECTED_REQUIRED_POSITIONS = {"C", "1B", "2B", "3B", "SS", "LF", "CF", "RF"}
EXPECTED_MISSING_POSITIONS = {"C", "2B", "LF", "CF"}
EXPECTED_PLAYERS = 9
EXPECTED_HITTERS = 6
EXPECTED_PITCHERS = 3


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def fail(message):
    print(f"FAIL: {message}")
    raise SystemExit(1)


def main():
    if not REPORT.exists():
        fail(f"Missing roster construction report: {REPORT}")

    data = load_json(REPORT)

    if data.get("schemaVersion") != "bie.roster-construction.v0":
        fail(f"Unexpected schemaVersion: {data.get('schemaVersion')}")

    if data.get("season") != 1980:
        fail(f"Unexpected season: {data.get('season')}")

    roster = data.get("roster", {})
    if roster.get("name") != "sample-roster-v0":
        fail(f"Unexpected roster name: {roster.get('name')}")

    if roster.get("ballparkName") != "Tiger Stadium 1980":
        fail(f"Unexpected ballpark: {roster.get('ballparkName')}")

    counts = data.get("counts", {})
    if counts.get("players") != EXPECTED_PLAYERS:
        fail(f"Expected {EXPECTED_PLAYERS} players, got {counts.get('players')}")

    if counts.get("hitters") != EXPECTED_HITTERS:
        fail(f"Expected {EXPECTED_HITTERS} hitters, got {counts.get('hitters')}")

    if counts.get("pitchers") != EXPECTED_PITCHERS:
        fail(f"Expected {EXPECTED_PITCHERS} pitchers, got {counts.get('pitchers')}")

    salary = data.get("salary", {})
    if salary.get("capExceeded") is not False:
        fail("Sample roster should not exceed salary cap")

    if round(float(salary.get("totalMillions", 0)), 2) != 71.62:
        fail(f"Unexpected salary total: {salary.get('totalMillions')}")

    coverage = data.get("positionCoverage", {})
    if set(coverage.keys()) != EXPECTED_REQUIRED_POSITIONS:
        fail(f"Unexpected position coverage keys: {sorted(coverage.keys())}")

    missing_positions = set(data.get("missingPositions", []))
    if missing_positions != EXPECTED_MISSING_POSITIONS:
        fail(f"Expected missing positions {sorted(EXPECTED_MISSING_POSITIONS)}, got {sorted(missing_positions)}")

    flags = data.get("structuralFlags", [])
    flag_codes = {flag.get("code") for flag in flags}

    expected_flag_codes = {
        "roster_size_below_typical",
        "missing_required_positions",
        "pitching_staff_thin",
    }

    if flag_codes != expected_flag_codes:
        fail(f"Unexpected structural flag codes: {sorted(flag_codes)}")

    player_signals = data.get("playerSignals", [])
    if len(player_signals) != EXPECTED_PLAYERS:
        fail(f"Expected {EXPECTED_PLAYERS} player signals, got {len(player_signals)}")

    by_name = {row.get("playerName"): row for row in player_signals}

    schmidt = by_name.get("Schmidt, Mike")
    if not schmidt:
        fail("Missing Schmidt, Mike player signal")

    if schmidt.get("selectedBallparkRankDelta") != 87:
        fail(f"Expected Schmidt Tiger delta 87, got {schmidt.get('selectedBallparkRankDelta')}")

    brett = by_name.get("Brett, George")
    if not brett:
        fail("Missing Brett, George player signal")

    if brett.get("selectedBallparkRank") != 1:
        fail(f"Expected Brett Tiger park rank 1, got {brett.get('selectedBallparkRank')}")

    print("PASS: roster construction v0 verification")
    print(f"Roster: {roster.get('name')}")
    print(f"Players: {counts.get('players')}")
    print(f"Missing positions: {', '.join(sorted(missing_positions))}")
    print(f"Structural flags: {len(flags)}")
    print("Schmidt Tiger delta: 87")


if __name__ == "__main__":
    main()
