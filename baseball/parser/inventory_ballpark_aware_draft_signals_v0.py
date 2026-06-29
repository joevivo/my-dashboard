import json
from pathlib import Path

IN_FILE = Path("data/baseball/parsed/strat365/1980/draft-signals/1980.ballpark-aware-draft-signals.json")


PARKS_TO_REPORT = [
    "Tiger Stadium 1980",
    "Comiskey Park 1980",
    "Riverfront Stdm 1980",
    "Astrodome 1980",
    "Yankee Stadium 1980",
    "Wrigley Field 1980",
]


def fit_for(row, park_name):
    for fit in row.get("ballparkFits", []):
        if fit.get("ballparkName") == park_name:
            return fit
    return None


def park_rank_delta(row, park_name):
    fit = fit_for(row, park_name)
    if not fit:
        return None

    baseline = row.get("defenseAwareRank")
    park_rank = fit.get("ballparkImpact", {}).get("parkAdjustedRank")
    if baseline is None or park_rank is None:
        return None

    return baseline - park_rank


def print_row(row, park_name):
    fit = fit_for(row, park_name)
    impact = fit["ballparkImpact"]
    delta = park_rank_delta(row, park_name)

    print(
        f"- {row['player']['playerName']} | "
        f"DA {row.get('defenseAwareRank')} -> park {impact['parkAdjustedRank']} | "
        f"delta {delta:+} | "
        f"parkScore {impact['parkAdjustedDraftScore']['score']} | "
        f"fit {impact['fitScore']['score']}"
    )


def report_park(title, rows, park_name, n=12):
    print()
    print(f"## {title}: {park_name}")

    movers = [
        row for row in rows
        if park_rank_delta(row, park_name) is not None
    ]

    risers = sorted(
        movers,
        key=lambda row: (park_rank_delta(row, park_name), fit_for(row, park_name)["ballparkImpact"]["parkAdjustedDraftScore"]["score"]),
        reverse=True,
    )[:n]

    fallers = sorted(
        movers,
        key=lambda row: (park_rank_delta(row, park_name), fit_for(row, park_name)["ballparkImpact"]["parkAdjustedDraftScore"]["score"]),
    )[:n]

    print()
    print("### Biggest risers")
    for row in risers:
        print_row(row, park_name)

    print()
    print("### Biggest fallers")
    for row in fallers:
        print_row(row, park_name)


def main():
    data = json.loads(IN_FILE.read_text(encoding="utf-8"))
    hitters = data["hitters"]
    pitchers = data["pitchers"]

    print("# Ballpark-Aware Draft Signals Inventory v0")
    print()
    print(f"Hitters: {len(hitters)}")
    print(f"Pitchers: {len(pitchers)}")
    print(f"Ballparks: {data['counts']['ballparks']}")

    for park_name in PARKS_TO_REPORT:
        report_park("Hitter park-specific movement", hitters, park_name)
        report_park("Pitcher park-specific movement", pitchers, park_name)


if __name__ == "__main__":
    main()
