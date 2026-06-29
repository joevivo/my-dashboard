import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "data" / "baseball" / "parsed" / "strat365" / "1980"

REPORT = BASE / "roster-construction" / "1980.sample-roster-v0.roster-construction-v0.json"


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def main():
    if not REPORT.exists():
        raise SystemExit(f"Missing roster construction report: {REPORT}")

    data = load_json(REPORT)

    roster = data["roster"]
    counts = data["counts"]
    salary = data["salary"]

    print("# BIE Roster Construction Inventory v0")
    print()
    print(f"Roster: {roster['name']}")
    print(f"Season: {data['season']}")
    print(f"Ballpark: {roster.get('ballparkName')}")
    print(f"Players: {counts['players']} | Hitters: {counts['hitters']} | Pitchers: {counts['pitchers']}")
    print(f"Salary: ${salary['totalMillions']:.2f}M / ${salary['capMillions']:.2f}M")
    print(f"Remaining: ${salary['remainingMillions']:.2f}M")
    print()

    print("## Missing Positions")
    missing_positions = data.get("missingPositions", [])
    if missing_positions:
        for position in missing_positions:
            print(f"- {position}")
    else:
        print("- none")
    print()

    print("## Structural Flags")
    flags = data.get("structuralFlags", [])
    if flags:
        for flag in flags:
            print(f"- [{flag['severity']}] {flag['code']}: {flag['message']}")
    else:
        print("- none")
    print()

    player_signals = data.get("playerSignals", [])

    risers = sorted(
        [p for p in player_signals if isinstance(p.get("selectedBallparkRankDelta"), int)],
        key=lambda p: p["selectedBallparkRankDelta"],
        reverse=True,
    )

    print("## Best Ballpark Risers")
    for row in risers[:5]:
        print(
            f"- {row['playerName']} | {row['role']} | "
            f"DA {row['defenseAwareRank']} -> park {row['selectedBallparkRank']} | "
            f"delta +{row['selectedBallparkRankDelta']}"
        )
    print()

    print("## Worst Ballpark Fits")
    for row in list(reversed(risers))[:5]:
        delta = row["selectedBallparkRankDelta"]
        sign = "+" if delta >= 0 else ""
        print(
            f"- {row['playerName']} | {row['role']} | "
            f"DA {row['defenseAwareRank']} -> park {row['selectedBallparkRank']} | "
            f"delta {sign}{delta}"
        )


if __name__ == "__main__":
    main()
