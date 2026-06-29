import json
from pathlib import Path

IN_FILE = Path("data/baseball/parsed/strat365/1980/draft-signals/1980.ballpark-aware-draft-signals.json")

EXPECTED_BALLPARKS = 26
EXPECTED_HITTERS = 440
EXPECTED_PITCHERS = 279


def fail(message):
    raise SystemExit(f"FAIL: {message}")


def verify_group(group_name, rows, expected_rows):
    by_park = {}

    for row in rows:
        name = row.get("player", {}).get("playerName", "UNKNOWN")
        fits = row.get("ballparkFits", [])

        if len(fits) != EXPECTED_BALLPARKS:
            fail(f"{group_name} {name} has {len(fits)} ballpark fits")

        for fit in fits:
            park = fit.get("ballparkName")
            impact = fit.get("ballparkImpact", {})

            adjusted_score = impact.get("parkAdjustedDraftScore", {}).get("score")
            adjusted_rank = impact.get("parkAdjustedRank")

            if adjusted_score is None:
                fail(f"{group_name} {name} missing parkAdjustedDraftScore for {park}")

            if not isinstance(adjusted_rank, int) or adjusted_rank <= 0:
                fail(f"{group_name} {name} missing parkAdjustedRank for {park}")

            by_park.setdefault(park, []).append(adjusted_rank)

    if len(by_park) != EXPECTED_BALLPARKS:
        fail(f"{group_name} has {len(by_park)} ranked parks")

    expected_ranks = list(range(1, expected_rows + 1))
    for park, ranks in by_park.items():
        if sorted(ranks) != expected_ranks:
            fail(f"{group_name} ranks are not contiguous for {park}")

    print(f"PASS: {group_name} per-ballpark ranks contiguous across {len(by_park)} parks")


def main():
    data = json.loads(IN_FILE.read_text(encoding="utf-8"))

    hitters = data.get("hitters", [])
    pitchers = data.get("pitchers", [])

    if len(hitters) != EXPECTED_HITTERS:
        fail(f"Expected {EXPECTED_HITTERS} hitters, found {len(hitters)}")

    if len(pitchers) != EXPECTED_PITCHERS:
        fail(f"Expected {EXPECTED_PITCHERS} pitchers, found {len(pitchers)}")

    verify_group("hitters", hitters, EXPECTED_HITTERS)
    verify_group("pitchers", pitchers, EXPECTED_PITCHERS)

    print("PASS: ballpark-aware draft signals verification")
    print(f"Hitters: {len(hitters)}")
    print(f"Pitchers: {len(pitchers)}")
    print(f"Ballparks per player: {EXPECTED_BALLPARKS}")


if __name__ == "__main__":
    main()
