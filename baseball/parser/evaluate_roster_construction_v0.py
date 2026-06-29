import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "data" / "baseball" / "parsed" / "strat365" / "1980"

FIXTURE = ROOT / "baseball" / "fixtures" / "rosters" / "1980.sample-roster-v0.json"
ROSTER_META = BASE / "player-roster-metadata" / "1980.player-roster-metadata.json"
DEFENSE_META = BASE / "player-defense-metadata" / "1980.player-defense-metadata.json"
DEFENSE_AWARE = BASE / "draft-signals" / "1980.defense-aware-draft-signals.json"
BALLPARK_AWARE = BASE / "draft-signals" / "1980.ballpark-aware-draft-signals.json"
OUT_DIR = BASE / "roster-construction"
OUT_PATH = OUT_DIR / "1980.sample-roster-v0.roster-construction-v0.json"

REQUIRED_POSITIONS = ["C", "1B", "2B", "3B", "SS", "LF", "CF", "RF"]
SCARCE_DEFENSIVE_POSITIONS = {"C", "SS", "2B", "CF"}
MIN_TYPICAL_ROSTER_SIZE = 24
MIN_TYPICAL_PITCHERS = 8


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def money(player):
    return player.get("salary", {}).get("millions", {}).get("decimal") or 0.0


def score_value(value):
    if isinstance(value, dict):
        return value.get("score")
    return None


def find_selected_park_fit(park_signal, ballpark_name):
    for fit in park_signal.get("ballparkFits", []):
        if fit.get("ballparkName") == ballpark_name:
            return fit
    return None


def build_evaluation():
    fixture = load_json(FIXTURE)
    roster = load_json(ROSTER_META)
    defense = load_json(DEFENSE_META)
    defense_aware = load_json(DEFENSE_AWARE)
    ballpark_aware = load_json(BALLPARK_AWARE)

    roster_by_id = {p["playerId"]: p for p in roster["players"]}
    defense_by_id = {p["playerId"]: p for p in defense["players"]}

    signal_by_id = {}
    for row in defense_aware["hitters"] + defense_aware["pitchers"]:
        signal_by_id[row["player"]["playerId"]] = row

    park_signal_by_id = {}
    for row in ballpark_aware["hitters"] + ballpark_aware["pitchers"]:
        park_signal_by_id[row["player"]["playerId"]] = row

    players = []
    missing_player_ids = []

    for player_id in fixture["playerIds"]:
        p = roster_by_id.get(player_id)
        if not p:
            missing_player_ids.append(player_id)
            continue
        players.append(p)

    hitters = [p for p in players if p.get("role") == "hitter"]
    pitchers = [p for p in players if p.get("role") == "pitcher"]
    total_salary = round(sum(money(p) for p in players), 2)
    salary_cap = float(fixture["salaryCapMillions"])

    position_coverage = defaultdict(list)
    structural_flags = []

    for p in hitters:
        d = defense_by_id.get(p["playerId"], {})
        hitter_defense = d.get("hitterDefense", {})

        for pos in hitter_defense.get("positions", []):
            position = pos.get("position")
            row = {
                "playerId": p["playerId"],
                "playerName": p["playerName"],
                "position": position,
                "range": pos.get("range"),
                "error": pos.get("error"),
                "arm": pos.get("arm"),
                "raw": pos.get("raw"),
            }
            position_coverage[position].append(row)

            if position in SCARCE_DEFENSIVE_POSITIONS and (pos.get("range") or 9) >= 4:
                structural_flags.append({
                    "severity": "warning",
                    "code": "scarce_position_weak_range",
                    "message": f"{p['playerName']} has weak range at scarce position {position}: range {pos.get('range')}",
                    "playerId": p["playerId"],
                    "position": position,
                })

    missing_positions = [pos for pos in REQUIRED_POSITIONS if not position_coverage.get(pos)]

    if missing_player_ids:
        structural_flags.append({
            "severity": "error",
            "code": "missing_player_ids",
            "message": f"Missing player IDs: {missing_player_ids}",
            "playerIds": missing_player_ids,
        })

    if len(players) < MIN_TYPICAL_ROSTER_SIZE:
        structural_flags.append({
            "severity": "warning",
            "code": "roster_size_below_typical",
            "message": f"Roster size below typical Strat roster: {len(players)} players",
            "count": len(players),
            "minimum": MIN_TYPICAL_ROSTER_SIZE,
        })

    if missing_positions:
        structural_flags.append({
            "severity": "error",
            "code": "missing_required_positions",
            "message": f"Missing required positions: {', '.join(missing_positions)}",
            "positions": missing_positions,
        })

    if len(pitchers) < MIN_TYPICAL_PITCHERS:
        structural_flags.append({
            "severity": "warning",
            "code": "pitching_staff_thin",
            "message": f"Pitching staff likely thin: {len(pitchers)} pitchers",
            "count": len(pitchers),
            "minimum": MIN_TYPICAL_PITCHERS,
        })

    if total_salary > salary_cap:
        structural_flags.append({
            "severity": "error",
            "code": "salary_cap_exceeded",
            "message": f"Salary cap exceeded: ${total_salary:.2f}M / ${salary_cap:.2f}M",
            "salaryMillions": total_salary,
            "salaryCapMillions": salary_cap,
        })

    player_signals = []

    for p in players:
        sig = signal_by_id.get(p["playerId"], {})
        park_sig = park_signal_by_id.get(p["playerId"], {})
        da_rank = sig.get("defenseAwareRank")
        da_score = score_value(sig.get("defenseAwareDraftScore"))

        selected_park = find_selected_park_fit(park_sig, fixture.get("ballparkName"))
        park_rank = None
        park_score = None
        rank_delta = None
        fit_score = None

        if selected_park:
            impact = selected_park.get("ballparkImpact", {})
            park_rank = impact.get("parkAdjustedRank")
            park_score = score_value(impact.get("parkAdjustedDraftScore"))
            fit_score = score_value(impact.get("fitScore"))

            if da_rank is not None and park_rank is not None:
                rank_delta = da_rank - park_rank

        player_signals.append({
            "playerId": p["playerId"],
            "playerName": p["playerName"],
            "team": p.get("team"),
            "role": p.get("role"),
            "salaryMillions": money(p),
            "defenseAwareRank": da_rank,
            "defenseAwareScore": da_score,
            "selectedBallparkRank": park_rank,
            "selectedBallparkScore": park_score,
            "selectedBallparkFitScore": fit_score,
            "selectedBallparkRankDelta": rank_delta,
        })

    evaluation = {
        "schemaVersion": "bie.roster-construction.v0",
        "parserVersion": "evaluate_roster_construction_v0",
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "season": fixture["season"],
        "sourceFiles": {
            "fixture": str(FIXTURE.relative_to(ROOT)).replace("\\", "/"),
            "rosterMetadata": str(ROSTER_META.relative_to(ROOT)).replace("\\", "/"),
            "defenseMetadata": str(DEFENSE_META.relative_to(ROOT)).replace("\\", "/"),
            "defenseAwareSignals": str(DEFENSE_AWARE.relative_to(ROOT)).replace("\\", "/"),
            "ballparkAwareSignals": str(BALLPARK_AWARE.relative_to(ROOT)).replace("\\", "/"),
        },
        "roster": {
            "name": fixture["name"],
            "ballparkName": fixture.get("ballparkName"),
            "salaryCapMillions": salary_cap,
            "playerIds": fixture["playerIds"],
        },
        "counts": {
            "players": len(players),
            "hitters": len(hitters),
            "pitchers": len(pitchers),
            "missingPlayerIds": len(missing_player_ids),
            "structuralFlags": len(structural_flags),
        },
        "salary": {
            "totalMillions": total_salary,
            "capMillions": salary_cap,
            "remainingMillions": round(salary_cap - total_salary, 2),
            "capExceeded": total_salary > salary_cap,
        },
        "positionCoverage": {
            pos: position_coverage.get(pos, [])
            for pos in REQUIRED_POSITIONS
        },
        "missingPositions": missing_positions,
        "structuralFlags": structural_flags,
        "playerSignals": player_signals,
    }

    return evaluation


def print_report(evaluation):
    roster = evaluation["roster"]
    counts = evaluation["counts"]
    salary = evaluation["salary"]

    print("# BIE Roster Construction v0")
    print()
    print(f"Roster: {roster['name']}")
    print(f"Ballpark: {roster.get('ballparkName')}")
    print(f"Players: {counts['players']}")
    print(f"Hitters: {counts['hitters']}")
    print(f"Pitchers: {counts['pitchers']}")
    print(f"Salary: ${salary['totalMillions']:.2f}M / ${salary['capMillions']:.2f}M")
    print(f"Salary remaining: ${salary['remainingMillions']:.2f}M")
    print()

    print("## Position Coverage")
    for pos in REQUIRED_POSITIONS:
        covered = evaluation["positionCoverage"].get(pos, [])
        if not covered:
            print(f"- {pos}: MISSING")
        else:
            names = ", ".join(
                f"{x['playerName']} r{x['range']}e{x['error']}"
                for x in covered
            )
            print(f"- {pos}: {names}")
    print()

    print("## Structural Flags")
    if evaluation["structuralFlags"]:
        for flag in evaluation["structuralFlags"]:
            print(f"- [{flag['severity']}] {flag['message']}")
    else:
        print("- No structural flags")
    print()

    print("## Player Signal Snapshot")
    for p in evaluation["playerSignals"]:
        print(
            f"- {p['playerName']} | {p['role']} | ${p['salaryMillions']:.2f}M"
            f" | DA rank {p['defenseAwareRank']}"
            f" | DA score {p['defenseAwareScore']}"
            f" | park rank {p['selectedBallparkRank']}"
            f" | park delta {p['selectedBallparkRankDelta']}"
        )


def main():
    evaluation = build_evaluation()
    write_json(OUT_PATH, evaluation)
    print_report(evaluation)
    print()
    print(f"Saved {OUT_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
