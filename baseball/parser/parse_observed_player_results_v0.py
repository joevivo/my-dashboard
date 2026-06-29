import csv
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "data" / "baseball" / "parsed" / "strat365" / "1980"

INPUT = ROOT / "baseball" / "fixtures" / "observed-results" / "1980.sample-observed-player-results-v0.csv"
ROSTER_META = BASE / "player-roster-metadata" / "1980.player-roster-metadata.json"
BALLPARKS = BASE / "ballparks" / "ballparks_v0.json"
DEFENSE_AWARE = BASE / "draft-signals" / "1980.defense-aware-draft-signals.json"
BALLPARK_AWARE = BASE / "draft-signals" / "1980.ballpark-aware-draft-signals.json"

OUT = BASE / "observed-results" / "1980.sample-observed-player-results-v0.json"


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def text(value):
    if value is None:
        return ""
    return str(value).strip()


def maybe_int(value):
    value = text(value)
    if value == "":
        return None
    return int(value)


def maybe_float(value):
    value = text(value)
    if value == "":
        return None
    return float(value)


def selected_ballpark_fit(row, ballpark_name):
    for fit in row.get("ballparkFits", []):
        if fit.get("ballparkName") == ballpark_name:
            return fit
    return None


def score_value(value):
    if isinstance(value, dict):
        return value.get("score")
    return None


def main():
    if not INPUT.exists():
        raise SystemExit(f"Missing input CSV: {INPUT}")

    roster_meta = load_json(ROSTER_META)
    ballparks = load_json(BALLPARKS)
    defense_aware = load_json(DEFENSE_AWARE)
    ballpark_aware = load_json(BALLPARK_AWARE)

    players_by_id = {p["playerId"]: p for p in roster_meta["players"]}
    ballparks_by_name = {p["ballparkName"]: p for p in ballparks["ballparks"]}

    defense_signal_by_id = {}
    for row in defense_aware["hitters"] + defense_aware["pitchers"]:
        defense_signal_by_id[row["player"]["playerId"]] = row

    ballpark_signal_by_id = {}
    for row in ballpark_aware["hitters"] + ballpark_aware["pitchers"]:
        ballpark_signal_by_id[row["player"]["playerId"]] = row

    rows = []
    warnings = []

    with INPUT.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for index, raw in enumerate(reader, start=1):
            player_id = maybe_int(raw.get("playerId"))
            role = text(raw.get("role"))
            ballpark_name = text(raw.get("ballparkName"))

            player_meta = players_by_id.get(player_id)
            ballpark_meta = ballparks_by_name.get(ballpark_name)
            defense_signal = defense_signal_by_id.get(player_id, {})
            park_signal = ballpark_signal_by_id.get(player_id, {})
            park_fit = selected_ballpark_fit(park_signal, ballpark_name)

            if not player_meta:
                warnings.append({"row": index, "code": "player_not_resolved", "playerId": player_id})

            if not ballpark_meta:
                warnings.append({"row": index, "code": "ballpark_not_resolved", "ballparkName": ballpark_name})

            if player_meta and player_meta.get("role") != role:
                warnings.append({
                    "row": index,
                    "code": "role_mismatch",
                    "playerId": player_id,
                    "csvRole": role,
                    "metadataRole": player_meta.get("role"),
                })

            park_rank = None
            park_delta = None
            if park_fit:
                impact = park_fit.get("ballparkImpact", {})
                park_rank = impact.get("parkAdjustedRank")
                defense_rank = defense_signal.get("defenseAwareRank")
                if defense_rank is not None and park_rank is not None:
                    park_delta = defense_rank - park_rank

            parsed = {
                "sourceRow": index,
                "observedSeasonId": text(raw.get("observedSeasonId")),
                "teamId": text(raw.get("teamId")),
                "teamName": text(raw.get("teamName")),
                "ballparkName": ballpark_name,
                "player": {
                    "playerId": player_id,
                    "playerName": text(raw.get("playerName")),
                    "role": role,
                    "resolved": player_meta is not None,
                    "metadataName": player_meta.get("playerName") if player_meta else None,
                    "metadataTeam": player_meta.get("team") if player_meta else None,
                },
                "observed": {
                    "games": maybe_int(raw.get("games")),
                },
                "bieSignals": {
                    "defenseAwareRank": defense_signal.get("defenseAwareRank"),
                    "defenseAwareScore": score_value(defense_signal.get("defenseAwareDraftScore")),
                    "selectedBallparkRank": park_rank,
                    "selectedBallparkRankDelta": park_delta,
                },
            }

            if role == "hitter":
                parsed["observed"]["batting"] = {
                    "plateAppearances": maybe_int(raw.get("plateAppearances")),
                    "atBats": maybe_int(raw.get("atBats")),
                    "runs": maybe_int(raw.get("runs")),
                    "hits": maybe_int(raw.get("hits")),
                    "doubles": maybe_int(raw.get("doubles")),
                    "triples": maybe_int(raw.get("triples")),
                    "homeRuns": maybe_int(raw.get("homeRuns")),
                    "runsBattedIn": maybe_int(raw.get("runsBattedIn")),
                    "walks": maybe_int(raw.get("walks")),
                    "strikeouts": maybe_int(raw.get("strikeouts")),
                    "stolenBases": maybe_int(raw.get("stolenBases")),
                    "caughtStealing": maybe_int(raw.get("caughtStealing")),
                    "battingAverage": maybe_float(raw.get("battingAverage")),
                    "onBasePercentage": maybe_float(raw.get("onBasePercentage")),
                    "sluggingPercentage": maybe_float(raw.get("sluggingPercentage")),
                    "ops": maybe_float(raw.get("ops")),
                }
            elif role == "pitcher":
                parsed["observed"]["pitching"] = {
                    "inningsPitched": maybe_float(raw.get("inningsPitched")),
                    "wins": maybe_int(raw.get("wins")),
                    "losses": maybe_int(raw.get("losses")),
                    "saves": maybe_int(raw.get("saves")),
                    "hitsAllowed": maybe_int(raw.get("hitsAllowed")),
                    "walksAllowed": maybe_int(raw.get("walksAllowed")),
                    "strikeouts": maybe_int(raw.get("strikeoutsPitching")),
                    "homeRunsAllowed": maybe_int(raw.get("homeRunsAllowed")),
                    "runsAllowed": maybe_int(raw.get("runsAllowed")),
                    "earnedRuns": maybe_int(raw.get("earnedRuns")),
                    "era": maybe_float(raw.get("era")),
                    "whip": maybe_float(raw.get("whip")),
                }
            else:
                warnings.append({"row": index, "code": "unknown_role", "role": role})

            rows.append(parsed)

    hitters = [r for r in rows if r["player"]["role"] == "hitter"]
    pitchers = [r for r in rows if r["player"]["role"] == "pitcher"]

    payload = {
        "schemaVersion": "bie.observed-player-results.v0",
        "parserVersion": "parse_observed_player_results_v0",
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "season": 1980,
        "sourceFiles": {
            "inputCsv": str(INPUT.relative_to(ROOT)).replace("\\", "/"),
            "rosterMetadata": str(ROSTER_META.relative_to(ROOT)).replace("\\", "/"),
            "ballparks": str(BALLPARKS.relative_to(ROOT)).replace("\\", "/"),
            "defenseAwareSignals": str(DEFENSE_AWARE.relative_to(ROOT)).replace("\\", "/"),
            "ballparkAwareSignals": str(BALLPARK_AWARE.relative_to(ROOT)).replace("\\", "/"),
        },
        "counts": {
            "rows": len(rows),
            "hitters": len(hitters),
            "pitchers": len(pitchers),
            "warnings": len(warnings),
            "resolvedPlayers": sum(1 for r in rows if r["player"]["resolved"]),
        },
        "rows": rows,
        "warnings": warnings,
    }

    write_json(OUT, payload)

    print("Saved", OUT.relative_to(ROOT))
    print("Rows:", len(rows))
    print("Hitters:", len(hitters))
    print("Pitchers:", len(pitchers))
    print("Resolved players:", payload["counts"]["resolvedPlayers"])
    print("Warnings:", len(warnings))


if __name__ == "__main__":
    main()
