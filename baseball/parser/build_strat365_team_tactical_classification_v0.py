from __future__ import annotations
import argparse, hashlib, json, re, sys
from collections import Counter
from pathlib import Path

PATTERNS = {
    "STOLEN_BASE_SUCCESS": re.compile(r"\bstolen base\b|\bstole\b", re.I),
    "CAUGHT_STEALING": re.compile(r"\bcaught stealing\b", re.I),
    "PICKOFF": re.compile(r"\bpickoff\b|\bpicked off\b", re.I),
    "HIT_AND_RUN_EXPLICIT": re.compile(r"\bhit[- ]and[- ]run\b", re.I),
    "SACRIFICE": re.compile(r"\bsacrifice\b|\bsac bunt\b", re.I),
    "DOUBLE_PLAY": re.compile(r"\bdouble play\b", re.I),
    "ERROR": re.compile(r"\berror\b", re.I),
    "WILD_PITCH": re.compile(r"\bwild pitch\b", re.I),
    "PASSED_BALL": re.compile(r"\bpassed ball\b", re.I),
    "BALK": re.compile(r"\bbalk\b", re.I),
    "INJURY": re.compile(r"\binjur(?:y|ed|ies)\b", re.I),
}
TAG_MAP = {
    "stolen_base": "STOLEN_BASE_SUCCESS",
    "caught_stealing": "CAUGHT_STEALING",
    "pickoff": "PICKOFF",
    "hit_and_run": "HIT_AND_RUN_EXPLICIT",
    "sacrifice": "SACRIFICE",
    "double_play": "DOUBLE_PLAY",
    "error": "ERROR",
    "wild_pitch": "WILD_PITCH",
    "passed_ball": "PASSED_BALL",
    "balk": "BALK",
    "injury": "INJURY",
}
TRANSITION = re.compile(r"(?<![A-Za-z0-9])([123bB])-([123HhOo0])")

def sha_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest().upper()

def sha_file(path: Path) -> str:
    return sha_bytes(path.read_bytes())

def json_bytes(value) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")

def jsonl_bytes(rows) -> bytes:
    return ("\n".join(json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":")) for row in rows) + "\n").encode("utf-8")

def write_if_changed(path: Path, payload: bytes) -> int:
    if path.exists() and path.read_bytes() == payload:
        return 0
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_bytes(payload)
    temp.replace(path)
    return 1

def as_int(value) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0

def compact(value) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return " ".join(value.split())
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))

def event_text(row) -> str:
    return " ".join(filter(None, (compact(row.get(name)) for name in (
        "text", "rawText", "result", "miscellaneous", "batter", "baserunners", "details"
    ))))

def transitions(value: str):
    base_value = {"b": 0, "1": 1, "2": 2, "3": 3}
    destination_value = {"1": 1, "2": 2, "3": 3, "h": 4}
    output = []
    for match in TRANSITION.finditer(value):
        origin = match.group(1).lower()
        destination = match.group(2).lower()
        distance = None
        if origin in base_value and destination in destination_value:
            distance = destination_value[destination] - base_value[origin]
        output.append({
            "token": match.group(0),
            "distance": distance,
            "runnerOut": origin in {"1", "2", "3"} and destination in {"o", "0"},
            "multiBaseAdvance": distance is not None and distance >= 2,
        })
    return output

def classifications(row, value, movement_rows):
    found = {TAG_MAP[tag] for tag in row.get("lexicalTags") or [] if tag in TAG_MAP}
    found.update(name for name, pattern in PATTERNS.items() if pattern.search(value))
    control = str(row.get("controlType") or "").upper()
    if control == "SUBSTITUTION":
        found.add("SUBSTITUTION_CONTROL")
    if control == "INJURY":
        found.add("INJURY")
    if any(item["multiBaseAdvance"] for item in movement_rows):
        found.add("MULTI_BASE_TRANSITION")
    if any(item["runnerOut"] for item in movement_rows):
        found.add("RUNNER_OUT_TRANSITION")
    return sorted(found)

def empty_pitching():
    return {"appearances": 0, "inningsPitchedOuts": 0, "earnedRuns": 0, "pitchCount": 0, "decisions": Counter()}

def add_pitching(target, row):
    target["appearances"] += 1
    target["inningsPitchedOuts"] += as_int(row.get("inningsPitchedOuts"))
    target["earnedRuns"] += as_int(row.get("earnedRuns"))
    target["pitchCount"] += as_int(row.get("pitchCount"))
    decision = str(row.get("decision") or "").strip()
    if decision:
        target["decisions"][decision] += 1

def pitch_output(value):
    return {
        "appearances": value["appearances"],
        "inningsPitchedOuts": value["inningsPitchedOuts"],
        "earnedRuns": value["earnedRuns"],
        "pitchCount": value["pitchCount"],
        "decisions": dict(sorted(value["decisions"].items())),
    }

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--event-ledger", required=True)
    parser.add_argument("--output-root", required=True)
    parser.add_argument("--team-name", required=True)
    parser.add_argument("--expected-dataset-sha256", required=True)
    parser.add_argument("--expected-ledger-sha256", required=True)
    args = parser.parse_args()
    try:
        dataset_path = Path(args.dataset).resolve()
        event_path = Path(args.event_ledger).resolve()
        output_root = Path(args.output_root).resolve()
        dataset_hash = sha_file(dataset_path)
        event_hash = sha_file(event_path)
        if dataset_hash != args.expected_dataset_sha256.upper():
            raise ValueError("Review-dataset hash mismatch.")
        if event_hash != args.expected_ledger_sha256.upper():
            raise ValueError("Event-ledger hash mismatch.")
        dataset = json.loads(dataset_path.read_text(encoding="utf-8"))
        counts = dataset.get("counts") or {}
        if (as_int(counts.get("leagueGames")), as_int(counts.get("teamGames")), as_int(counts.get("eventLedgerRows"))) != (90, 15, 9394):
            raise ValueError("Dataset count contract mismatch.")

        rows, seen = [], set()
        league, batting, fielding = Counter(), Counter(), Counter()
        with event_path.open("r", encoding="utf-8") as handle:
            for raw in handle:
                if not raw.strip():
                    continue
                source = json.loads(raw)
                evidence = event_text(source)
                movement_rows = transitions(evidence)
                perspective = str(source.get("teamPerspective") or "none")
                for category in classifications(source, evidence, movement_rows):
                    key = f"{source.get('eventKey')}:{category}"
                    if key in seen:
                        raise ValueError(f"Duplicate classification key: {key}")
                    seen.add(key)
                    league[category] += 1
                    if perspective == "team_batting":
                        batting[category] += 1
                    elif perspective == "team_fielding":
                        fielding[category] += 1
                    rows.append({
                        "schemaVersion": "strat365-tactical-classification-row-v0",
                        "classificationKey": key,
                        "sourceType": "PLAY_BY_PLAY_EVENT",
                        "primaryCategory": category,
                        "leagueDate": source.get("leagueDate"),
                        "gameId": str(source.get("gameId") or ""),
                        "sourceGamePath": source.get("sourceGamePath"),
                        "sourceEventKey": source.get("eventKey"),
                        "sequence": as_int(source.get("sequence")),
                        "inning": as_int(source.get("inning")),
                        "half": str(source.get("half") or ""),
                        "outsBefore": as_int(source.get("outsBefore")),
                        "occupiedBasesBefore": list(source.get("occupiedBasesBefore") or []),
                        "battingTeam": str(source.get("battingTeam") or ""),
                        "fieldingTeam": str(source.get("fieldingTeam") or ""),
                        "teamPerspective": perspective,
                        "recordType": str(source.get("recordType") or ""),
                        "controlType": str(source.get("controlType") or ""),
                        "evidenceText": evidence,
                        "transitions": movement_rows,
                    })

        starters, relievers = empty_pitching(), empty_pitching()
        players = {}
        pitcher_usage_rows = 0
        substitution_rows = 0
        for game in dataset.get("teamGames") or []:
            for index, pitcher in enumerate(game.get("pitcherRows") or []):
                role = "STARTER_APPEARANCE" if index == 0 else "RELIEF_APPEARANCE"
                pitcher_usage_rows += 1
                rows.append({
                    "schemaVersion": "strat365-tactical-classification-row-v0",
                    "classificationKey": f"{game.get('leagueDate')}:{game.get('gameId')}:pitcher:{index}:{role}",
                    "sourceType": "PITCHING_BOX_ROW",
                    "primaryCategory": role,
                    "leagueDate": game.get("leagueDate"),
                    "gameId": str(game.get("gameId") or ""),
                    "sourceGamePath": game.get("sourceGamePath"),
                    "team": args.team_name,
                    "opponent": game.get("opponent"),
                    "displayName": pitcher.get("displayName"),
                    "decision": pitcher.get("decision"),
                    "inningsPitchedOuts": as_int(pitcher.get("inningsPitchedOuts")),
                    "earnedRuns": as_int(pitcher.get("earnedRuns")),
                    "pitchCount": as_int(pitcher.get("pitchCount")),
                })
                target = starters if index == 0 else relievers
                add_pitching(target, pitcher)
                name = str(pitcher.get("displayName") or "")
                player = players.setdefault(name, {"starter": empty_pitching(), "relief": empty_pitching()})
                add_pitching(player["starter" if index == 0 else "relief"], pitcher)

            for index, hitter in enumerate(game.get("hitterRows") or []):
                prefix = str(hitter.get("substitutionPrefix") or "").strip()
                if not prefix:
                    continue
                substitution_rows += 1
                rows.append({
                    "schemaVersion": "strat365-tactical-classification-row-v0",
                    "classificationKey": f"{game.get('leagueDate')}:{game.get('gameId')}:hitter:{index}:BOX_SCORE_SUBSTITUTION_ROW",
                    "sourceType": "HITTING_BOX_ROW",
                    "primaryCategory": "BOX_SCORE_SUBSTITUTION_ROW",
                    "leagueDate": game.get("leagueDate"),
                    "gameId": str(game.get("gameId") or ""),
                    "sourceGamePath": game.get("sourceGamePath"),
                    "team": args.team_name,
                    "opponent": game.get("opponent"),
                    "displayName": hitter.get("displayName"),
                    "position": hitter.get("position"),
                    "substitutionPrefix": prefix,
                })

        rows.sort(key=lambda row: (
            str(row.get("leagueDate") or ""),
            as_int(row.get("gameId")),
            str(row.get("sourceType") or ""),
            as_int(row.get("sequence")),
            str(row.get("classificationKey") or ""),
        ))
        player_rows = [{
            "displayName": name,
            "starter": pitch_output(value["starter"]),
            "relief": pitch_output(value["relief"]),
        } for name, value in sorted(players.items())]

        team_sb, team_cs = batting["STOLEN_BASE_SUCCESS"], batting["CAUGHT_STEALING"]
        opp_sb, opp_cs = fielding["STOLEN_BASE_SUCCESS"], fielding["CAUGHT_STEALING"]
        summary = {
            "schemaVersion": "strat365-team-tactical-classification-summary-v0",
            "scope": {
                "teamName": args.team_name,
                "season": dataset["scope"]["season"],
                "leagueId": dataset["scope"]["leagueId"],
                "throughDate": dataset["scope"]["throughDate"],
                "teamGames": 15,
                "leagueGames": 90,
            },
            "sourceAuthority": {
                "reviewDatasetSha256": dataset_hash,
                "eventLedgerSha256": event_hash,
                "builderScriptSha256": sha_file(Path(__file__).resolve()),
            },
            "counts": {
                "classificationRows": len(rows),
                "playByPlayClassifications": sum(row["sourceType"] == "PLAY_BY_PLAY_EVENT" for row in rows),
                "teamPitcherUsageRows": pitcher_usage_rows,
                "teamBoxScoreSubstitutionRows": substitution_rows,
            },
            "categoryCounts": {
                "league": dict(sorted(league.items())),
                "teamBatting": dict(sorted(batting.items())),
                "teamFielding": dict(sorted(fielding.items())),
            },
            "teamBaserunning": {
                "successfulSteals": team_sb,
                "caughtStealing": team_cs,
                "explicitStealAttempts": team_sb + team_cs,
                "explicitStealSuccessRate": round(team_sb / (team_sb + team_cs), 4) if team_sb + team_cs else None,
                "pickoffsAgainst": batting["PICKOFF"],
                "multiBaseTransitionEvidence": batting["MULTI_BASE_TRANSITION"],
                "runnerOutTransitionEvidence": batting["RUNNER_OUT_TRANSITION"],
            },
            "opponentBaserunningAgainstTeam": {
                "successfulSteals": opp_sb,
                "caughtStealing": opp_cs,
                "explicitStealAttempts": opp_sb + opp_cs,
                "explicitStealSuccessRate": round(opp_sb / (opp_sb + opp_cs), 4) if opp_sb + opp_cs else None,
                "pickoffsByTeam": fielding["PICKOFF"],
            },
            "teamDefenseEventEvidence": {
                "errorsWhileFielding": fielding["ERROR"],
                "opponentErrorsWhileTeamBatted": batting["ERROR"],
                "doublePlaysWhileFielding": fielding["DOUBLE_PLAY"],
                "doublePlaysWhileBatting": batting["DOUBLE_PLAY"],
                "wildPitchesWhileFielding": fielding["WILD_PITCH"],
                "passedBallsWhileFielding": fielding["PASSED_BALL"],
            },
            "explicitTacticalSignals": {
                "hitAndRunTeamBatting": batting["HIT_AND_RUN_EXPLICIT"],
                "hitAndRunTeamFielding": fielding["HIT_AND_RUN_EXPLICIT"],
                "sacrificesTeamBatting": batting["SACRIFICE"],
                "sacrificesTeamFielding": fielding["SACRIFICE"],
                "substitutionControlsTeamBattingContext": batting["SUBSTITUTION_CONTROL"],
                "substitutionControlsTeamFieldingContext": fielding["SUBSTITUTION_CONTROL"],
                "injuryControlsTeamBattingContext": batting["INJURY"],
                "injuryControlsTeamFieldingContext": fielding["INJURY"],
            },
            "teamPitching": {
                "starters": pitch_output(starters),
                "relievers": pitch_output(relievers),
                "pitchers": player_rows,
            },
            "interpretationLimits": [
                "Runner transitions are evidence, not managerial-quality judgments.",
                "The first pitching row is treated as the starter.",
                "Substitution prefixes do not identify the tactical role.",
                "No roster recommendation is made in this layer.",
            ],
        }

        ledger_path = output_root / "tactical-classification-ledger-v0.jsonl"
        summary_path = output_root / "tactical-classification-summary-v0.json"
        manifest_path = output_root / "tactical-classification-source-manifest-v0.json"
        ledger_payload = jsonl_bytes(rows)
        summary_payload = json_bytes(summary)
        manifest = {
            "schemaVersion": "strat365-team-tactical-classification-manifest-v0",
            "inputs": {
                "reviewDataset": {"path": str(dataset_path), "sha256": dataset_hash},
                "eventLedger": {"path": str(event_path), "sha256": event_hash},
            },
            "builder": {"path": str(Path(__file__).resolve()), "sha256": sha_file(Path(__file__).resolve())},
            "outputs": {
                "classificationLedger": {"path": str(ledger_path), "sha256": sha_bytes(ledger_payload), "rowCount": len(rows)},
                "classificationSummary": {"path": str(summary_path), "sha256": sha_bytes(summary_payload)},
            },
        }
        manifest_payload = json_bytes(manifest)
        modified = (
            write_if_changed(ledger_path, ledger_payload)
            + write_if_changed(summary_path, summary_payload)
            + write_if_changed(manifest_path, manifest_payload)
        )
        print("# RESULT SUMMARY")
        print("TACTICAL_CLASSIFICATION_BUILD: PASS")
        print(f"CLASSIFICATION_ROW_COUNT: {len(rows)}")
        print(f"PLAY_BY_PLAY_CLASSIFICATION_COUNT: {summary['counts']['playByPlayClassifications']}")
        print(f"TEAM_PITCHER_USAGE_ROW_COUNT: {pitcher_usage_rows}")
        print(f"TEAM_BOX_SCORE_SUBSTITUTION_ROW_COUNT: {substitution_rows}")
        print(f"FILES_MODIFIED_BY_CLASSIFIER: {modified}")
        print("FAILURE_COUNT: 0")
        print("FAILURE_DETAIL: none")
        print("LIVE_REQUESTS_EXECUTED: 0")
        return 0
    except Exception as error:
        print("# RESULT SUMMARY")
        print("TACTICAL_CLASSIFICATION_BUILD: FAIL")
        print("CLASSIFICATION_ROW_COUNT: 0")
        print("PLAY_BY_PLAY_CLASSIFICATION_COUNT: 0")
        print("TEAM_PITCHER_USAGE_ROW_COUNT: 0")
        print("TEAM_BOX_SCORE_SUBSTITUTION_ROW_COUNT: 0")
        print("FILES_MODIFIED_BY_CLASSIFIER: 0")
        print("FAILURE_COUNT: 1")
        print(f"FAILURE_DETAIL: {error}")
        print("LIVE_REQUESTS_EXECUTED: 0")
        return 1

if __name__ == "__main__":
    sys.exit(main())
