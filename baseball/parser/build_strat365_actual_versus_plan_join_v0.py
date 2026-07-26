import argparse
import hashlib
import json
from pathlib import Path

def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))

def name_key(value):
    return str(value).strip().casefold()

def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest().upper()

def write_json(path, value):
    target = Path(path)
    text = json.dumps(value, ensure_ascii=False, indent=2) + "\n"
    if target.exists() and target.read_text(encoding="utf-8") == text:
        return 0
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8", newline="\n")
    return 1

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--freeze", required=True)
    parser.add_argument("--forecast", required=True)
    parser.add_argument("--current-roster", required=True)
    parser.add_argument("--output-root", required=True)
    parser.add_argument("--team-name", required=True)
    args = parser.parse_args()

    data = load(args.dataset)
    freeze = load(args.freeze)
    forecast = load(args.forecast)
    current = load(args.current_roster)

    team_forecast = next(
        team for team in forecast["teams"]
        if team["teamName"] == args.team_name
    )

    current_map = {
        name_key(player["canonicalName"]): player
        for player in current["players"]
    }
    freeze_map = {
        name_key(player["canonicalName"]): player
        for player in freeze["roster"]["players"]
    }
    hitter_map = {
        name_key(player["displayName"]): player
        for player in data["teamHitterTotals"]
    }
    pitcher_map = {
        name_key(player["displayName"]): player
        for player in data["teamPitcherTotals"]
    }
    top_hitters = {
        name_key(player["player"]): player
        for player in team_forecast["topHitters"]
    }
    top_starters = {
        name_key(player["player"]): player
        for player in team_forecast["topStarters"]
    }
    top_relievers = {
        name_key(player["player"]): player
        for player in team_forecast["topRelievers"]
    }

    names = sorted(
        set(current_map) | set(hitter_map) | set(pitcher_map)
    )
    rows = []

    for key in names:
        roster = current_map.get(key)
        hitter = hitter_map.get(key)
        pitcher = pitcher_map.get(key)
        name = (
            roster["canonicalName"] if roster else
            hitter["displayName"] if hitter else
            pitcher["displayName"]
        )

        batting = None
        if hitter:
            at_bats = int(hitter["atBats"])
            batting = {
                "gamesWithRow": int(hitter["gamesWithRow"]),
                "atBats": at_bats,
                "hits": int(hitter["hits"]),
                "battingAverage": (
                    round(int(hitter["hits"]) / at_bats, 3)
                    if at_bats else None
                ),
                "runs": int(hitter["runs"]),
                "runsBattedIn": int(hitter["runsBattedIn"]),
                "starterRows": int(hitter["starterRowCount"]),
                "substitutionRows": int(hitter["substitutionRowCount"]),
                "positions": list(hitter["positions"]),
            }

        pitching = None
        if pitcher:
            outs = int(pitcher["inningsPitchedOuts"])
            pitching = {
                "appearances": int(pitcher["appearances"]),
                "starts": int(pitcher["starterRowAppearances"]),
                "reliefAppearances": int(pitcher["reliefRowAppearances"]),
                "inningsPitchedOuts": outs,
                "earnedRuns": int(pitcher["earnedRuns"]),
                "earnedRunAverage": (
                    round(int(pitcher["earnedRuns"]) * 27 / outs, 3)
                    if outs else None
                ),
                "hitsAllowed": int(pitcher["hitsAllowed"]),
                "homeRunsAllowed": int(pitcher["homeRunsAllowed"]),
                "walks": int(pitcher["walks"]),
                "strikeouts": int(pitcher["strikeouts"]),
                "pitchCount": int(pitcher["pitchCount"]),
                "decisions": pitcher["decisions"],
            }

        rows.append({
            "canonicalName": name,
            "playerId": roster.get("playerId") if roster else None,
            "currentRoster": roster is not None,
            "preseasonRoster": key in freeze_map,
            "formerOrUnresolvedObservedPlayer": (
                roster is None and (hitter is not None or pitcher is not None)
            ),
            "role": roster.get("role") if roster else None,
            "salaryDollars": roster.get("salaryDollars") if roster else None,
            "endurance": list(roster.get("endurance", [])) if roster else [],
            "forecastTopHitterScore": (
                top_hitters.get(key, {}).get("score")
            ),
            "forecastTopStarterScore": (
                top_starters.get(key, {}).get("score")
            ),
            "forecastTopRelieverScore": (
                top_relievers.get(key, {}).get("score")
            ),
            "actualObserved": hitter is not None or pitcher is not None,
            "actualHitting": batting,
            "actualPitching": pitching,
        })

    games = data["teamGames"]
    wins = sum(game["result"] == "W" for game in games)
    losses = sum(game["result"] == "L" for game in games)
    runs_for = sum(int(game["runsFor"]) for game in games)
    runs_against = sum(int(game["runsAgainst"]) for game in games)
    game_count = len(games)

    projection = team_forecast["projection"]
    projected_games = int(projection["wins"]) + int(projection["losses"])
    projected_scoring = round(
        float(projection["runsScored"]) / projected_games, 3
    )
    projected_prevention = round(
        float(projection["runsAllowed"]) / projected_games, 3
    )
    actual_scoring = round(runs_for / game_count, 3)
    actual_prevention = round(runs_against / game_count, 3)
    actual_wpct = round(wins / game_count, 3)
    projected_wpct = float(projection["winningPercentage"])

    signals = ["FIFTEEN_GAME_SAMPLE_WARNING"]
    signals.append(
        "WINNING_PERCENTAGE_ABOVE_PROJECTION"
        if actual_wpct > projected_wpct
        else "WINNING_PERCENTAGE_BELOW_PROJECTION"
    )
    signals.append(
        "SCORING_ABOVE_PROJECTION"
        if actual_scoring > projected_scoring
        else "SCORING_BELOW_PROJECTION"
    )
    signals.append(
        "RUN_PREVENTION_ABOVE_PROJECTION"
        if actual_prevention < projected_prevention
        else "RUN_PREVENTION_BELOW_PROJECTION"
    )

    overlap = sum(key in freeze_map for key in current_map)
    if overlap != len(current_map):
        raise ValueError(
            f"Current/preseason roster overlap is {overlap}, "
            f"expected {len(current_map)}."
        )

    league = freeze["league"]
    output_root = Path(args.output_root)
    join_path = output_root / "actual-versus-plan-player-join-v0.json"
    summary_path = output_root / "actual-versus-plan-summary-v0.json"
    manifest_path = output_root / "actual-versus-plan-source-manifest-v0.json"

    join = {
        "schemaVersion": "strat365-actual-versus-plan-player-join-v0",
        "team": args.team_name,
        "leagueId": league["leagueId"],
        "season": league["season"],
        "asOfLeagueDate": max(game["leagueDate"] for game in games),
        "authority": {
            "preseasonRoster": args.freeze,
            "preseasonForecast": args.forecast,
            "currentRoster": args.current_roster,
            "actualPerformance": args.dataset,
        },
        "playerRows": rows,
    }

    summary = {
        "schemaVersion": "strat365-actual-versus-plan-summary-v0",
        "team": args.team_name,
        "sampleGames": game_count,
        "sampleWarning": (
            "Fifteen games are directional evidence, "
            "not a stabilized season sample."
        ),
        "joinCounts": {
            "preseasonFreezePlayers": len(freeze_map),
            "currentRosterPlayers": len(current_map),
            "currentPlayersFoundInFreeze": overlap,
            "joinedPlayerRows": len(rows),
            "currentPlayersObserved": sum(
                row["currentRoster"] and row["actualObserved"]
                for row in rows
            ),
            "formerOrUnresolvedObservedPlayers": sum(
                row["formerOrUnresolvedObservedPlayer"]
                for row in rows
            ),
        },
        "preseasonRatings": team_forecast["ratings"],
        "projectionComparison": {
            "projectedWins": int(projection["wins"]),
            "projectedLosses": int(projection["losses"]),
            "projectedWinningPercentage": projected_wpct,
            "actualWins": wins,
            "actualLosses": losses,
            "actualWinningPercentage": actual_wpct,
            "projectedRunsScoredPerGame": projected_scoring,
            "actualRunsScoredPerGame": actual_scoring,
            "projectedRunsAllowedPerGame": projected_prevention,
            "actualRunsAllowedPerGame": actual_prevention,
            "projectedRunDifferentialPerGame": round(
                float(projection["runDifferential"]) / projected_games, 3
            ),
            "actualRunDifferentialPerGame": round(
                (runs_for - runs_against) / game_count, 3
            ),
            "signals": signals,
        },
    }

    modified = 0
    modified += write_json(join_path, join)
    modified += write_json(summary_path, summary)

    manifest = {
        "schemaVersion": "strat365-actual-versus-plan-manifest-v0",
        "sources": [
            {"path": path, "sha256": sha256(path)}
            for path in (
                args.dataset,
                args.freeze,
                args.forecast,
                args.current_roster,
            )
        ],
        "outputs": [
            {"path": str(join_path), "sha256": sha256(join_path)},
            {"path": str(summary_path), "sha256": sha256(summary_path)},
        ],
    }
    modified += write_json(manifest_path, manifest)

    print(f"FILES_MODIFIED_BY_JOIN_BUILDER: {modified}")
    print(f"JOINED_PLAYER_ROW_COUNT: {len(rows)}")
    print(f"CURRENT_PLAYERS_FOUND_IN_FREEZE: {overlap}")
    print(f"ACTUAL_RECORD: {wins}-{losses}")

if __name__ == "__main__":
    main()