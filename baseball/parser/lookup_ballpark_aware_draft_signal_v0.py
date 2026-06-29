import argparse
import json
import re
from pathlib import Path

IN_FILE = Path("data/baseball/parsed/strat365/1980/draft-signals/1980.ballpark-aware-draft-signals.json")


def norm(value):
    return re.sub(r"[^a-z0-9]+", " ", str(value).lower()).strip()


def fit_for(row, park_query):
    wanted = norm(park_query)
    for fit in row.get("ballparkFits", []):
        if wanted in norm(fit.get("ballparkName", "")):
            return fit
    return None


def find_players(data, player_query):
    wanted = norm(player_query)
    rows = data.get("hitters", []) + data.get("pitchers", [])
    return [
        row for row in rows
        if wanted in norm(row.get("player", {}).get("playerName", ""))
    ]


def print_best_worst(row):
    profile = row["ballparkProfile"]
    for label, key in [("Best", "bestFit"), ("Worst", "worstFit")]:
        fit = profile[key]
        impact = fit["ballparkImpact"]
        print(
            f"{label}: {fit['ballparkName']} | "
            f"park rank {impact['parkAdjustedRank']} | "
            f"park score {impact['parkAdjustedDraftScore']['score']} | "
            f"fit {impact['fitScore']['score']}"
        )
    print(f"Spread: {profile['fitSpread']['score']}")


def print_selected_park(row, park_query):
    fit = fit_for(row, park_query)
    if not fit:
        print(f"No matching park found for: {park_query}")
        return

    impact = fit["ballparkImpact"]
    baseline = row.get("defenseAwareRank")
    park_rank = impact.get("parkAdjustedRank")
    delta = baseline - park_rank if baseline and park_rank else None
    delta_text = f"{delta:+}" if delta is not None else "n/a"

    print()
    print(f"## Selected park: {fit['ballparkName']}")
    print(f"Bucket: {fit['bucket']}")
    print(
        f"Factors: SI L/R {fit['factors']['singleLeft']}/{fit['factors']['singleRight']} | "
        f"HR L/R {fit['factors']['homeRunLeft']}/{fit['factors']['homeRunRight']}"
    )
    print(f"Rank movement: {baseline} -> {park_rank} | delta {delta_text}")
    print(f"Park-adjusted score: {impact['parkAdjustedDraftScore']['score']}")
    print(f"Fit score: {impact['fitScore']['score']}")

    print()
    print("Impact details:")
    for key, value in impact.items():
        if key in {"fitScore", "parkAdjustedDraftScore", "parkAdjustedRank"}:
            continue
        print(f"- {key}: {value}")


def print_player(row, park_query=None):
    player = row["player"]
    salary = row.get("salary", {}).get("raw")

    print()
    print(f"# {player['playerName']} ({row['role']})")
    print(f"Player ID: {player['playerId']}")
    print(f"Team: {player.get('team')}")
    print(f"Salary: {salary}")
    print(f"Defense-aware rank: {row.get('defenseAwareRank')}")
    print(f"Defense-aware score: {row.get('defenseAwareDraftScore', {}).get('score')}")
    print()
    print("## Best/Worst park fit")
    print_best_worst(row)

    if park_query:
        print_selected_park(row, park_query)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--player", required=True)
    parser.add_argument("--park", required=False)
    args = parser.parse_args()

    data = json.loads(IN_FILE.read_text(encoding="utf-8"))
    matches = find_players(data, args.player)

    if not matches:
        raise SystemExit(f"No player matched: {args.player}")

    if len(matches) > 1:
        print(f"Matched {len(matches)} players; showing first 10:")
        for row in matches[:10]:
            print(f"- {row['player']['playerName']} ({row['role']})")
        print()

    print_player(matches[0], args.park)


if __name__ == "__main__":
    main()
