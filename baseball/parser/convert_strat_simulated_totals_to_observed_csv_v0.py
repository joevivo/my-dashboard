import argparse
import csv
import json
import re
from pathlib import Path

SEASON = 1980

DEFAULT_INPUT_PATH = Path("data/baseball/raw/strat365/1980/observed-results/raw-player-total-lines-sample.txt")
DEFAULT_OUTPUT_PATH = Path("data/baseball/raw/strat365/1980/observed-results/1980-aquarium-drinkers-observed-player-results.csv")
DEFAULT_METADATA_PATH = Path("data/baseball/parsed/strat365/1980/player-roster-metadata/1980.player-roster-metadata.json")

FIELDS = [
    "observedSeasonId", "teamId", "teamName", "ballparkName",
    "playerId", "playerName", "role", "games",
    "plateAppearances", "atBats", "runs", "hits", "doubles", "triples",
    "homeRuns", "runsBattedIn", "walks", "strikeouts", "stolenBases",
    "caughtStealing", "battingAverage", "onBasePercentage", "sluggingPercentage",
    "ops", "inningsPitched", "wins", "losses", "saves", "hitsAllowed",
    "walksAllowed", "strikeoutsPitching", "homeRunsAllowed", "runsAllowed",
    "earnedRuns", "era", "whip",
]


def parse_args():
    parser = argparse.ArgumentParser(
        description="Convert copied Strat 365 simulated player totals into BIE observed-results CSV v0."
    )
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--metadata", type=Path, default=DEFAULT_METADATA_PATH)
    parser.add_argument("--observed-season-id", default="aquarium-drinkers-1980")
    parser.add_argument("--team-id", default="AQUARIUM-DRINKERS")
    parser.add_argument("--team-name", default="Aquarium Drinkers")
    parser.add_argument("--ballpark-name", default="Comiskey Park 1980")
    parser.add_argument("--pitcher-count", type=int, default=10)
    return parser.parse_args()


def load_players(metadata_path):
    payload = json.loads(metadata_path.read_text(encoding="utf-8-sig"))
    if isinstance(payload, list):
        return payload
    return payload.get("players") or payload.get("rows") or []


def resolve_player(players, abbreviated_name):
    match = re.match(r"^([^,]+),\s+([A-Z])\.$", abbreviated_name)
    if not match:
        raise ValueError(f"Could not parse abbreviated name: {abbreviated_name}")

    last_name, first_initial = match.groups()
    matches = [
        player
        for player in players
        if player.get("playerName", "").split(",")[0] == last_name
        and player.get("playerName", "").split(",", 1)[1].strip().startswith(first_initial)
    ]

    if len(matches) != 1:
        names = ", ".join(player.get("playerName", "") for player in matches) or "none"
        raise ValueError(f"Expected one match for {abbreviated_name}; found {len(matches)}: {names}")

    return matches[0]


def blank_row(player, role, args):
    row = {field: "" for field in FIELDS}
    row.update({
        "observedSeasonId": args.observed_season_id,
        "teamId": args.team_id,
        "teamName": args.team_name,
        "ballparkName": args.ballpark_name,
        "playerId": player["playerId"],
        "playerName": player["playerName"],
        "role": role,
    })
    return row


def parse_line(line):
    match = re.match(r"^([^,]+,\s+[A-Z]\.)\s+(.*)$", line)
    if not match:
        raise ValueError(f"Could not parse line: {line}")
    return match.group(1), match.group(2).split()


def parse_pitcher(player, tokens, args):
    row = blank_row(player, "pitcher", args)
    row.update({
        "wins": tokens[2],
        "losses": tokens[3],
        "saves": tokens[4],
        "inningsPitched": tokens[6],
        "hitsAllowed": tokens[7],
        "runsAllowed": tokens[8],
        "earnedRuns": tokens[9],
        "walksAllowed": tokens[10],
        "strikeoutsPitching": tokens[11],
        "homeRunsAllowed": tokens[12],
        "era": tokens[17],
        "whip": tokens[18],
    })
    return row


def parse_hitter(player, tokens, args):
    row = blank_row(player, "hitter", args)
    row.update({
        "atBats": tokens[3],
        "runs": tokens[4],
        "hits": tokens[5],
        "doubles": tokens[6],
        "triples": tokens[7],
        "homeRuns": tokens[8],
        "runsBattedIn": tokens[9],
        "walks": tokens[10],
        "strikeouts": tokens[11],
        "stolenBases": tokens[13],
        "caughtStealing": tokens[14],
        "battingAverage": tokens[18],
        "onBasePercentage": tokens[19],
        "sluggingPercentage": tokens[20],
    })

    try:
        row["ops"] = f"{float(row['onBasePercentage']) + float(row['sluggingPercentage']):.3f}".lstrip("0")
    except ValueError:
        row["ops"] = ""

    return row


def main():
    args = parse_args()
    players = load_players(args.metadata)
    lines = [line for line in args.input.read_text(encoding="utf-8-sig").splitlines() if line.strip()]

    rows = []
    for index, line in enumerate(lines):
        abbreviated_name, tokens = parse_line(line)
        player = resolve_player(players, abbreviated_name)

        if index < args.pitcher_count:
            rows.append(parse_pitcher(player, tokens, args))
        else:
            rows.append(parse_hitter(player, tokens, args))

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Saved {args.output}")
    print(f"Rows: {len(rows)}")
    print(f"Pitchers: {sum(1 for row in rows if row['role'] == 'pitcher')}")
    print(f"Hitters: {sum(1 for row in rows if row['role'] == 'hitter')}")


if __name__ == "__main__":
    main()