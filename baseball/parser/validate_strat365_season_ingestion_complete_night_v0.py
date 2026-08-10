from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any


SUPPORTED_PARSER_SHA256 = {
    '9CFE7586AD7077113DB00B52468A2CB1F5884E6DAD58F38889DC4377A564ACDB',
    '78B7F6BACB0690FBFA6F7D622C3C105EE1138B32F208B17DFD8FD0DAD2894899',
    'BA1845643850A68F20751547C15193C499AEFE4ECA292CE834494D6F8D851193',
}

REQUIRED_GAME_SOURCE_FAMILIES = {
    "gamePlayByPlay",
    "gameRecap",
    "gameReplay",
}
REQUIRED_RECONCILIATION_TRUE_FIELDS = {
    "finalHeaderMatch",
    "teamOrderMatch",
    "awayTeamLineMatch",
    "homeTeamLineMatch",
    "decisionSummaryExactMatch",
    "leagueScoreMatch",
    "leagueResultOutcomeMatch",
    "recapReplayOrientationMatch",
    "playByPlayAttached",
    "playByPlayInningsMatch",
    "unknownControlFree",
}


def sha256(path: Path) -> str:
    algorithm = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            algorithm.update(chunk)
    return algorithm.hexdigest().upper()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_if_changed(path: Path, payload: bytes) -> int:
    if path.exists() and path.read_bytes() == payload:
        return 0

    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_suffix(path.suffix + ".tmp")
    temporary_path.write_bytes(payload)
    temporary_path.replace(path)
    return 1


def game_set_signature(game_files: list[Path]) -> str:
    pairs = [
        f"{path.name}:{sha256(path)}"
        for path in sorted(game_files, key=lambda value: value.name)
    ]
    return hashlib.sha256("\n".join(pairs).encode("utf-8")).hexdigest().upper()


def resolve_repo_path(repo_root: Path, value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path.resolve()
    return (repo_root / path).resolve()


def add_gate(
    gates: dict[str, bool],
    failures: list[str],
    name: str,
    condition: bool,
    failure: str,
) -> None:
    gates[name] = bool(condition)
    if not condition:
        failures.append(failure)


def main() -> int:
    argument_parser = argparse.ArgumentParser()
    argument_parser.add_argument("--repo-root", required=True)
    argument_parser.add_argument("--run-directory", required=True)
    argument_parser.add_argument("--parsed-root", required=True)
    arguments = argument_parser.parse_args()

    repo_root = Path(arguments.repo_root).resolve()
    run_directory = Path(arguments.run_directory).resolve()
    parsed_root = Path(arguments.parsed_root).resolve()

    parser_path = (
        repo_root
        / "baseball"
        / "parser"
        / "parse_strat365_season_ingestion_v0.py"
    )
    capture_lock_path = (
        run_directory
        / "capture-lock-and-promotion-decision-v1.json"
    )
    plan_path = run_directory / "game-capture-plan.json"
    manifest_path = run_directory / "run-manifest.json"
    metadata_directory = run_directory / "metadata"
    league_night_path = parsed_root / "league-night-v0.json"
    game_directory = parsed_root / "games"
    report_path = parsed_root / "complete-night-validation-v0.json"

    failures: list[str] = []
    gates: dict[str, bool] = {}

    capture_lock = load_json(capture_lock_path)
    capture_lock_identity = capture_lock.get("runIdentity", {})
    capture_lock_evidence = capture_lock.get("evidence", {})
    plan = load_json(plan_path)
    league_night = load_json(league_night_path)

    season = str(capture_lock_identity.get("season", ""))
    league_id = str(capture_lock_identity.get("leagueId", ""))
    league_date = str(capture_lock_identity.get("leagueDate", ""))

    league_authorization_scope = (
        f"{season}/league-{league_id}/{league_date}"
    )
    authorization_scope = league_authorization_scope
    scope_type = "LEAGUE_NIGHT"
    team_id = ""
    team_name = ""

    plan_game_request_ids = [
        str(request.get("requestId", ""))
        for request in plan.get("requests", [])
        if (
            str(request.get("requestId", "")).startswith("game-")
            and str(request.get("requestId", "")).endswith(
                (
                    "-recap",
                    "-play-by-play",
                    "-replay",
                )
            )
        )
    ]

    expected_game_ids = {
        int(request_id.split("-")[1])
        for request_id in plan_game_request_ids
    }

    capture_lock_state = capture_lock.get("captureLock", {})

    actual_run_directory = run_directory.relative_to(
        repo_root
    ).as_posix()

    expected_game_count = len(expected_game_ids)
    expected_game_source_count = len(plan_game_request_ids)

    plan_request_counts_by_game = {
        game_id: sum(
            request_id.startswith(f"game-{game_id}-")
            for request_id in plan_game_request_ids
        )
        for game_id in expected_game_ids
    }

    expected_metadata_count = int(
        capture_lock_evidence.get(
            "metadataFileCount",
            -1,
        )
    )

    expected_manifest_request_count = int(
        capture_lock_evidence.get(
            "manifestTotalRequestCount",
            -1,
        )
    )

    expected_source_family_counts = {
        "gamePlayByPlay": sum(
            request.get("sourceFamily") == "gamePlayByPlay"
            for request in plan.get("requests", [])
        ),
        "gameRecap": sum(
            request.get("sourceFamily") == "gameRecap"
            for request in plan.get("requests", [])
        ),
        "gameReplay": sum(
            request.get("sourceFamily") == "gameReplay"
            for request in plan.get("requests", [])
        ),
        "leagueScores": int(
            capture_lock_evidence.get(
                "manifestLeagueRequestCount",
                -1,
            )
        ),
    }

    parser_hash = sha256(parser_path)
    capture_lock_hash = sha256(capture_lock_path)
    plan_hash = sha256(plan_path)
    manifest_hash = sha256(manifest_path)
    league_night_hash = sha256(league_night_path)

    add_gate(
        gates,
        failures,
        "parserHashMatch",
        parser_hash in SUPPORTED_PARSER_SHA256,
        f"Parser hash mismatch: {parser_hash}",
    )
    add_gate(
        gates,
        failures,
        "captureLockStateMatch",
        (
            capture_lock_state.get("status") == "LOCKED"
            and capture_lock_state.get("authorized") is True
            and capture_lock_state.get(
                "rawEvidenceImmutable"
            )
            is True
            and capture_lock_state.get(
                "liveRecaptureAuthorized"
            )
            is False
        ),
        "Capture lock is not in its required immutable state.",
    )

    add_gate(
        gates,
        failures,
        "captureLockRunIdentityMatch",
        (
            str(capture_lock_identity.get("season", ""))
            == season
            and str(
                capture_lock_identity.get(
                    "leagueId",
                    "",
                )
            )
            == league_id
            and str(
                capture_lock_identity.get(
                    "leagueDate",
                    "",
                )
            )
            == league_date
            and str(
                capture_lock_identity.get(
                    "runDirectory",
                    "",
                )
            )
            == actual_run_directory
        ),
        "Capture-lock identity differs from the active run.",
    )

    add_gate(
        gates,
        failures,
        "captureLockEvidenceHashMatch",
        (
            plan_hash
            == str(
                capture_lock_evidence.get(
                    "planSha256",
                    "",
                )
            ).upper()
            and manifest_hash
            == str(
                capture_lock_evidence.get(
                    "manifestSha256",
                    "",
                )
            ).upper()
        ),
        "Capture-lock plan or manifest hash differs.",
    )

    add_gate(
        gates,
        failures,
        "captureLockCoverageMatch",
        (
            expected_game_count > 0
            and expected_game_source_count
            == expected_game_count * 3
            and all(
                count == 3
                for count in plan_request_counts_by_game.values()
            )
            and int(
                capture_lock_evidence.get(
                    "planGameRequestCount",
                    -1,
                )
            )
            == expected_game_source_count
            and int(
                capture_lock_evidence.get(
                    "manifestGameRequestCount",
                    -1,
                )
            )
            == expected_game_source_count
            and int(
                capture_lock_evidence.get(
                    "completeGameCount",
                    -1,
                )
            )
            == expected_game_count
            and expected_metadata_count
            == expected_manifest_request_count
            and int(
                capture_lock_evidence.get(
                    "capturedResponseCount",
                    -1,
                )
            )
            == expected_metadata_count
            and int(
                capture_lock_evidence.get(
                    "artifactFailureCount",
                    -1,
                )
            )
            == 0
            and int(
                capture_lock_evidence.get(
                    "validationFailureCount",
                    -1,
                )
            )
            == 0
            and int(
                capture_lock_evidence.get(
                    "gameCoverageFailureCount",
                    -1,
                )
            )
            == 0
        ),
        "Capture-lock evidence does not prove a complete night.",
    )
    add_gate(
        gates,
        failures,
        "leagueNightIdentityMatch",
        (
            str(league_night.get("season", ""))
            == season
            and str(
                league_night.get(
                    "leagueId",
                    "",
                )
            )
            == league_id
            and str(
                league_night.get(
                    "leagueDate",
                    "",
                )
            )
            == league_date
        ),
        "League-night identity differs from the capture lock.",
    )

    metadata_files = sorted(metadata_directory.glob("*.json"))
    metadata_family_counts: dict[str, int] = {}
    metadata_body_paths: set[str] = set()
    metadata_by_name: dict[str, dict[str, Any]] = {}

    for metadata_path in metadata_files:
        metadata = load_json(metadata_path)
        metadata_by_name[metadata_path.name] = metadata

        family = str(metadata.get("sourceFamily", ""))
        logical_family = (
            "leagueScores"
            if family == "teamSchedule"
            else family
        )
        metadata_family_counts[logical_family] = (
            metadata_family_counts.get(logical_family, 0) + 1
        )

        raw_response_value = str(metadata.get("rawResponsePath", ""))
        if raw_response_value:
            raw_response_path = resolve_repo_path(
                repo_root,
                raw_response_value,
            )
            metadata_body_paths.add(str(raw_response_path))

            if not raw_response_path.is_file():
                failures.append(
                    f"Metadata body path is missing: {raw_response_path}"
                )
        else:
            failures.append(
                f"Metadata lacks rawResponsePath: {metadata_path.name}"
            )

    add_gate(
        gates,
        failures,
        "metadataFileCountMatch",
        len(metadata_files) == expected_metadata_count,
        (
            "Metadata file count differs: "
            f"expected={expected_metadata_count}, "
            f"actual={len(metadata_files)}."
        ),
    )
    add_gate(
        gates,
        failures,
        "metadataFamilyCountsMatch",
        metadata_family_counts == expected_source_family_counts,
        (
            "Metadata family counts differ: "
            f"{metadata_family_counts}"
        ),
    )
    add_gate(
        gates,
        failures,
        "uniqueMetadataBodyPathCountMatch",
        len(metadata_body_paths) == expected_metadata_count,
        (
            "Unique metadata body-path count differs: "
            f"expected={expected_metadata_count}, "
            f"actual={len(metadata_body_paths)}."
        ),
    )

    game_files = sorted(
        game_directory.glob("game-*-v0.json"),
        key=lambda value: value.name,
    )
    actual_game_set_signature = game_set_signature(game_files)

    add_gate(
        gates,
        failures,
        "gameFileCountMatch",
        len(game_files) == expected_game_count,
        (
            "Parsed game-file count differs: "
            f"expected={expected_game_count}, "
            f"actual={len(game_files)}."
        ),
    )
    add_gate(
        gates,
        failures,
        "gameSetSignaturePresent",
        (
            len(actual_game_set_signature) == 64
            and all(
                character in "0123456789ABCDEF"
                for character in actual_game_set_signature
            )
        ),
        (
            "Game-set signature is invalid: "
            f"{actual_game_set_signature}"
        ),
    )

    game_ids: set[int] = set()
    games_by_id: dict[int, dict[str, Any]] = {}

    hitter_row_count = 0
    pitcher_row_count = 0
    substitution_row_count = 0
    extra_inning_game_count = 0

    inning_marker_count = 0
    event_row_count = 0
    control_row_count = 0
    unknown_control_count = 0
    ordered_record_count = 0

    reconciled_game_count = 0
    winner_mention_count = 0
    winner_omission_accepted_count = 0
    loser_mention_count = 0

    loser_omission_accepted_count = 0
    score_match_count = 0
    decision_match_count = 0
    promotion_blocked_game_count = 0

    verified_game_source_count = 0
    verified_source_paths: set[str] = set()
    verified_metadata_names: set[str] = set()

    for game_path in game_files:
        filename_match = re.fullmatch(
            r"game-(?P<game_id>\d+)-v0\.json",
            game_path.name,
        )
        if filename_match is None:
            failures.append(f"Invalid game filename: {game_path.name}")
            continue

        filename_game_id = int(filename_match.group("game_id"))
        game = load_json(game_path)
        game_id = int(game.get("gameId", -1))

        if game_id != filename_game_id:
            failures.append(
                f"Game ID mismatch in {game_path.name}: {game_id}"
            )

        game_ids.add(game_id)
        games_by_id[game_id] = game

        if game.get("schemaVersion") != "strat365-game-v0":
            failures.append(
                f"Game {game_id} has an invalid schema version."
            )

        if str(game.get("season")) != season:
            failures.append(f"Game {game_id} has an invalid season.")

        if str(game.get("leagueId")) != league_id:
            failures.append(f"Game {game_id} has an invalid league ID.")

        if str(game.get("leagueDate")) != league_date:
            failures.append(f"Game {game_id} has an invalid league date.")

        innings = int(game.get("innings", 0))
        away_team = game["awayTeam"]
        home_team = game["homeTeam"]

        if len(away_team["inningRuns"]) != innings:
            failures.append(
                f"Game {game_id} away inning count differs."
            )

        if len(home_team["inningRuns"]) != innings:
            failures.append(
                f"Game {game_id} home inning count differs."
            )

        away_calculated_runs = sum(
            value
            for value in away_team["inningRuns"]
            if value is not None
        )
        home_calculated_runs = sum(
            value
            for value in home_team["inningRuns"]
            if value is not None
        )

        if away_calculated_runs != int(away_team["runs"]):
            failures.append(
                f"Game {game_id} away runs do not reconcile."
            )

        if home_calculated_runs != int(home_team["runs"]):
            failures.append(
                f"Game {game_id} home runs do not reconcile."
            )

        if int(away_team["runs"]) == int(home_team["runs"]):
            failures.append(f"Game {game_id} has a tied final score.")

        expected_winner = (
            away_team["name"]
            if int(away_team["runs"]) > int(home_team["runs"])
            else home_team["name"]
        )
        expected_loser = (
            home_team["name"]
            if expected_winner == away_team["name"]
            else away_team["name"]
        )

        if game.get("winnerTeam") != expected_winner:
            failures.append(f"Game {game_id} winner is inconsistent.")

        if game.get("loserTeam") != expected_loser:
            failures.append(f"Game {game_id} loser is inconsistent.")

        if bool(game.get("extraInnings")):
            extra_inning_game_count += 1

        hitters = (
            list(game.get("awayHitters", []))
            + list(game.get("homeHitters", []))
        )
        pitchers = (
            list(game.get("awayPitchers", []))
            + list(game.get("homePitchers", []))
        )
        all_players = hitters + pitchers

        hitter_row_count += len(hitters)
        pitcher_row_count += len(pitchers)
        substitution_row_count += sum(
            1
            for player in all_players
            if player.get("substitutionPrefix") is not None
        )

        play_by_play = game.get("playByPlay", {})
        records = list(play_by_play.get("orderedRecords", []))

        inning_marker_count += int(
            play_by_play.get("inningMarkerCount", 0)
        )
        event_row_count += int(play_by_play.get("eventCount", 0))
        control_row_count += int(play_by_play.get("controlCount", 0))
        unknown_control_count += int(
            play_by_play.get("unknownControlCount", 0)
        )
        ordered_record_count += int(
            play_by_play.get("orderedRecordCount", 0)
        )

        if len(records) != int(
            play_by_play.get("orderedRecordCount", -1)
        ):
            failures.append(
                f"Game {game_id} ordered-record count differs."
            )

        expected_sequences = list(range(1, len(records) + 1))
        actual_sequences = [
            int(record.get("sequence", -1))
            for record in records
        ]

        if actual_sequences != expected_sequences:
            failures.append(
                f"Game {game_id} sequence is not contiguous."
            )

        record_type_counts = {
            "INNING_MARKER": 0,
            "EVENT": 0,
            "CONTROL": 0,
        }

        for record in records:
            record_type = str(record.get("recordType", ""))
            if record_type in record_type_counts:
                record_type_counts[record_type] += 1
            else:
                failures.append(
                    f"Game {game_id} has unknown record type "
                    f"{record_type!r}."
                )

        if record_type_counts["INNING_MARKER"] != int(
            play_by_play.get("inningMarkerCount", -1)
        ):
            failures.append(
                f"Game {game_id} inning-marker total differs."
            )

        if record_type_counts["EVENT"] != int(
            play_by_play.get("eventCount", -1)
        ):
            failures.append(
                f"Game {game_id} event total differs."
            )

        if record_type_counts["CONTROL"] != int(
            play_by_play.get("controlCount", -1)
        ):
            failures.append(
                f"Game {game_id} control total differs."
            )

        if not bool(play_by_play.get("expectedInningsMatch")):
            failures.append(
                f"Game {game_id} play-by-play innings do not match."
            )

        if int(play_by_play.get("maximumInning", 0)) != innings:
            failures.append(
                f"Game {game_id} maximum inning differs."
            )

        reconciliation = game.get("reconciliation", {})

        if reconciliation.get("status") == "RECONCILED":
            reconciled_game_count += 1
        else:
            failures.append(
                f"Game {game_id} is not reconciled."
            )

        for field_name in REQUIRED_RECONCILIATION_TRUE_FIELDS:
            if reconciliation.get(field_name) is not True:
                failures.append(
                    f"Game {game_id} reconciliation field "
                    f"{field_name} is not true."
                )

        winner_mentioned = (
            reconciliation.get("leagueWinnerMention") is True
        )
        winner_omission_accepted = (
            reconciliation.get(
                "leagueWinnerOmissionAccepted"
            )
            is True
        )

        if winner_mentioned:
            winner_mention_count += 1

        if winner_omission_accepted:
            winner_omission_accepted_count += 1

            if (
                reconciliation.get(
                    "leagueWinnerOmissionReason"
                )
                != "NARRATIVE_HEADLINE_OMITS_WINNER_TEAM"
            ):
                failures.append(
                    f"Game {game_id} has an invalid winner-omission reason."
                )

        if not winner_mentioned and not winner_omission_accepted:
            failures.append(
                f"Game {game_id} lacks accepted winner evidence."
            )

        loser_mentioned = (
            reconciliation.get("leagueLoserMention") is True
        )
        loser_omission_accepted = (
            reconciliation.get(
                "leagueLoserOmissionAccepted"
            )
            is True
        )

        if loser_mentioned:
            loser_mention_count += 1

        if loser_omission_accepted:
            loser_omission_accepted_count += 1

        if not loser_mentioned and not loser_omission_accepted:
            failures.append(
                f"Game {game_id} lacks accepted loser evidence."
            )

        if reconciliation.get("leagueScoreMatch") is True:
            score_match_count += 1

        if reconciliation.get(
            "decisionSummaryExactMatch"
        ) is True:
            decision_match_count += 1

        if reconciliation.get(
            "canonicalPromotionAuthorized"
        ) is False:
            promotion_blocked_game_count += 1
        else:
            failures.append(
                f"Game {game_id} was prematurely authorized."
            )

        source_bundle = game.get("sources", {})

        if set(source_bundle) != REQUIRED_GAME_SOURCE_FAMILIES:
            failures.append(
                f"Game {game_id} source-family set differs: "
                f"{sorted(source_bundle)}"
            )
        else:
            for family in sorted(REQUIRED_GAME_SOURCE_FAMILIES):
                source = source_bundle[family]
                body_path = resolve_repo_path(
                    repo_root,
                    str(source["bodyPath"]),
                )
                metadata_name = str(source["metadataFile"])
                expected_body_hash = str(
                    source["bodySha256"]
                ).upper()

                if not body_path.is_file():
                    failures.append(
                        f"Game {game_id} source body is missing: "
                        f"{body_path}"
                    )
                    continue

                actual_body_hash = sha256(body_path)

                if actual_body_hash != expected_body_hash:
                    failures.append(
                        f"Game {game_id} {family} body hash differs."
                    )

                if metadata_name not in metadata_by_name:
                    failures.append(
                        f"Game {game_id} metadata is missing: "
                        f"{metadata_name}"
                    )
                    continue

                metadata = metadata_by_name[metadata_name]

                if metadata.get("sourceFamily") != family:
                    failures.append(
                        f"Game {game_id} metadata family differs "
                        f"for {metadata_name}."
                    )

                if int(metadata.get("gameId", -1)) != game_id:
                    failures.append(
                        f"Game {game_id} metadata game ID differs "
                        f"for {metadata_name}."
                    )

                metadata_body_path = resolve_repo_path(
                    repo_root,
                    str(metadata.get("rawResponsePath", "")),
                )

                if metadata_body_path != body_path:
                    failures.append(
                        f"Game {game_id} metadata body path differs "
                        f"for {metadata_name}."
                    )

                verified_game_source_count += 1
                verified_source_paths.add(str(body_path))
                verified_metadata_names.add(metadata_name)

    add_gate(
        gates,
        failures,
        "gameIdCoverageMatch",
        game_ids == expected_game_ids,
        f"Game ID coverage differs: {sorted(game_ids)}",
    )
    add_gate(
        gates,
        failures,
        "recapAggregateCountsMatch",
        (
            hitter_row_count
            == sum(
                len(game.get("awayHitters", []))
                + len(game.get("homeHitters", []))
                for game in games_by_id.values()
            )
            and pitcher_row_count
            == sum(
                len(game.get("awayPitchers", []))
                + len(game.get("homePitchers", []))
                for game in games_by_id.values()
            )
            and 0 <= substitution_row_count <= hitter_row_count
            and extra_inning_game_count
            == sum(
                1
                for game in games_by_id.values()
                if bool(game.get("extraInnings"))
            )
        ),
        (
            "Recap aggregate derivation differs: "
            f"hitters={hitter_row_count}, "
            f"pitchers={pitcher_row_count}, "
            f"substitutions={substitution_row_count}, "
            f"extraInnings={extra_inning_game_count}."
        ),
    )
    add_gate(
        gates,
        failures,
        "playByPlayAggregateCountsMatch",
        (
            inning_marker_count > 0
            and event_row_count > 0
            and control_row_count >= 0
            and unknown_control_count == 0
            and ordered_record_count
            == (
                inning_marker_count
                + event_row_count
                + control_row_count
            )
        ),
        (
            "Play-by-play aggregate integrity differs: "
            f"markers={inning_marker_count}, "
            f"events={event_row_count}, "
            f"controls={control_row_count}, "
            f"unknownControls={unknown_control_count}, "
            f"orderedRecords={ordered_record_count}."
        ),
    )
    add_gate(
        gates,
        failures,
        "reconciliationAggregateCountsMatch",
        (
            reconciled_game_count == expected_game_count
            and (
                winner_mention_count
                + winner_omission_accepted_count
            )
            == expected_game_count
            and (
                loser_mention_count
                + loser_omission_accepted_count
            )
            == expected_game_count
            and score_match_count == expected_game_count
            and decision_match_count == expected_game_count
            and promotion_blocked_game_count
            == expected_game_count
        ),
        (
            "Reconciliation aggregate counts differ: "
            f"reconciled={reconciled_game_count}, "
            f"winnerMentions={winner_mention_count}, "
            f"winnerOmissions={winner_omission_accepted_count}, "
            f"loserMentions={loser_mention_count}, "
            f"loserOmissions={loser_omission_accepted_count}, "
            f"scoreMatches={score_match_count}, "
            f"decisionMatches={decision_match_count}, "
            f"promotionBlocked={promotion_blocked_game_count}."
        ),
    )
    add_gate(
        gates,
        failures,
        "rawGameSourceReferencesMatch",
        (
            verified_game_source_count
            == expected_game_source_count
            and len(verified_source_paths)
            == expected_game_source_count
            and len(verified_metadata_names)
            == expected_game_source_count
        ),
        (
            "Verified raw game-source references differ: "
            f"expected={expected_game_source_count}, "
            f"verified={verified_game_source_count}, "
            f"paths={len(verified_source_paths)}, "
            f"metadata={len(verified_metadata_names)}."
        ),
    )

    league_night = load_json(league_night_path)
    game_summaries = list(league_night.get("gameSummaries", []))
    game_summary_ids = {
        int(summary.get("gameId", -1))
        for summary in game_summaries
    }

    league_game_files = {
        str(value)
        for value in league_night.get("gameFiles", [])
    }
    expected_game_file_paths = {
        path.relative_to(repo_root).as_posix()
        for path in game_files
    }

    league_play_by_play_summary = league_night.get(
        "playByPlaySummary",
        {},
    )
    league_reconciliation_summary = league_night.get(
        "reconciliationSummary",
        {},
    )

    league_summary_match = (
        int(league_night.get("gameCount", -1))
        == expected_game_count
        and int(
            league_night.get(
                "structuredGameCount",
                -1,
            )
        )
        == expected_game_count
        and len(game_summaries) == expected_game_count
        and game_summary_ids == expected_game_ids
        and league_game_files == expected_game_file_paths
        and int(
            league_play_by_play_summary.get(
                "inningMarkerCount",
                -1,
            )
        )
        == inning_marker_count
        and int(
            league_play_by_play_summary.get(
                "eventCount",
                -1,
            )
        )
        == event_row_count
        and int(
            league_play_by_play_summary.get(
                "controlCount",
                -1,
            )
        )
        == control_row_count
        and int(
            league_play_by_play_summary.get(
                "unknownControlCount",
                -1,
            )
        )
        == unknown_control_count
        and int(
            league_play_by_play_summary.get(
                "orderedRecordCount",
                -1,
            )
        )
        == ordered_record_count
        and int(
            league_reconciliation_summary.get(
                "reconciledGameCount",
                -1,
            )
        )
        == reconciled_game_count
        and int(
            league_reconciliation_summary.get(
                "leagueWinnerMentionCount",
                -1,
            )
        )
        == winner_mention_count
        and int(
            league_reconciliation_summary.get(
                "leagueWinnerOmissionAcceptedCount",
                -1,
            )
        )
        == winner_omission_accepted_count
        and int(
            league_reconciliation_summary.get(
                "leagueLoserMentionCount",
                -1,
            )
        )
        == loser_mention_count
        and int(
            league_reconciliation_summary.get(
                "leagueScoreMatchCount",
                -1,
            )
        )
        == score_match_count
        and int(
            league_reconciliation_summary.get(
                "decisionSummaryExactMatchCount",
                -1,
            )
        )
        == decision_match_count
        and league_reconciliation_summary.get(
            "completeNightReady"
        )
        is True
        and league_reconciliation_summary.get(
            "canonicalPromotionAuthorized"
        )
        is False
    )

    add_gate(
        gates,
        failures,
        "leagueNightSummaryMatch",
        league_summary_match,
        "League-night aggregate summary differs from game staging.",
    )

    metadata_team_ids: set[str] = set()

    for metadata_path in sorted(
        metadata_directory.glob("*.json"),
        key=lambda value: value.name,
    ):
        metadata_payload = load_json(metadata_path)
        metadata_team_id = str(
            metadata_payload.get("teamId", "")
        ).strip()

        if metadata_team_id:
            metadata_team_ids.add(metadata_team_id)

    if expected_game_count > 0 and expected_game_count != 18:
        scope_type = "TEAM_NIGHT"

        if len(metadata_team_ids) != 1:
            failures.append(
                "Team-night metadata does not contain exactly "
                "one authoritative team ID: "
                f"{sorted(metadata_team_ids)}"
            )
        else:
            team_id = next(iter(metadata_team_ids))

        if team_id:
            team_state_path = (
                repo_root
                / "data/baseball/state/strat365/nightly"
                / league_id
                / team_id
                / "nightly-team-state-v0.json"
            )

            if not team_state_path.is_file():
                failures.append(
                    "The sealed team-state authority is missing: "
                    f"{team_state_path}"
                )
            else:
                team_state = load_json(team_state_path)

                if str(
                    team_state.get("leagueId", "")
                ) != league_id:
                    failures.append(
                        "The sealed team-state league ID differs."
                    )

                if str(
                    team_state.get("teamId", "")
                ) != team_id:
                    failures.append(
                        "The sealed team-state team ID differs."
                    )

                team_name = str(
                    team_state.get("teamName", "")
                ).strip()

                if not team_name:
                    failures.append(
                        "The sealed team-state team name is missing."
                    )

            tracked_team_game_count = 0

            for game_id, game in games_by_id.items():
                home_name = str(
                    game.get("homeTeam", {}).get("name", "")
                ).strip()
                away_name = str(
                    game.get("awayTeam", {}).get("name", "")
                ).strip()

                game_team_names = {
                    value
                    for value in (home_name, away_name)
                    if value
                }

                if len(game_team_names) != 2:
                    failures.append(
                        f"Game {game_id} does not contain "
                        "two distinct team names."
                    )

                if team_name and team_name in game_team_names:
                    tracked_team_game_count += 1
                elif team_name:
                    failures.append(
                        f"Game {game_id} does not contain "
                        f"the tracked team: {team_name}"
                    )

            if (
                team_name
                and tracked_team_game_count
                != expected_game_count
            ):
                failures.append(
                    "The tracked team does not appear in "
                    "every team-night game."
                )

            authorization_scope = (
                f"{season}/league-{league_id}/"
                f"team-{team_id}/{league_date}"
            )

    promotion_authorized = not failures and all(gates.values())

    report = {
        "schemaVersion": (
            "strat365-complete-night-validation-v0"
        ),
        "season": season,
        "leagueId": league_id,
        "leagueDate": league_date,
        "scope": {
            "scopeType": scope_type,
            "teamId": team_id,
            "teamName": team_name,
            "parsedRoot": parsed_root.relative_to(
                repo_root
            ).as_posix(),
            "leagueNightFile": league_night_path.relative_to(
                repo_root
            ).as_posix(),
            "gameDirectory": game_directory.relative_to(
                repo_root
            ).as_posix(),
            "captureDirectory": run_directory.relative_to(
                repo_root
            ).as_posix(),
        },
        "authoritativeHashes": {
            "parserSha256": parser_hash,
            "captureLockSha256": capture_lock_hash,
            "planSha256": plan_hash,
            "manifestSha256": manifest_hash,
            "leagueNightSha256": league_night_hash,
            "gameSetSignature": actual_game_set_signature,
        },
        "counts": {
            "metadataFiles": len(metadata_files),
            "gameFiles": len(game_files),
            "gameSourcesVerified": verified_game_source_count,
            "hitterRows": hitter_row_count,
            "pitcherRows": pitcher_row_count,
            "substitutionRows": substitution_row_count,
            "extraInningGames": extra_inning_game_count,
            "inningMarkers": inning_marker_count,
            "playByPlayEvents": event_row_count,
            "controlRows": control_row_count,
            "unknownControls": unknown_control_count,
            "orderedRecords": ordered_record_count,
            "reconciledGames": reconciled_game_count,
            "winnerMentions": winner_mention_count,
            "acceptedWinnerOmissions": (
                winner_omission_accepted_count
            ),
        },
        "gates": gates,
        "promotionDecision": {
            "scopeType": scope_type,
            "status": (
                "AUTHORIZED_FOR_ATOMIC_CANONICAL_PROMOTION"
                if promotion_authorized
                else "BLOCKED"
            ),
            "canonicalPromotionAuthorized": (
                promotion_authorized
            ),
            "authorizationScope": authorization_scope,
            "requiresAtomicWrite": True,
            "liveRecaptureAuthorized": False,
            "sourceStagingMutationAuthorized": False,
        },
        "failures": failures,
    }

    report_payload = (
        json.dumps(
            report,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    ).encode("utf-8")

    files_modified = write_if_changed(
        report_path,
        report_payload,
    )
    report_hash = sha256(report_path)

    print("# RESULT SUMMARY")
    print(
        "COMPLETE_NIGHT_INDEPENDENT_VALIDATION: "
        f"{'PASS' if promotion_authorized else 'FAIL'}"
    )
    print(f"PARSER_SHA256: {parser_hash}")
    print(f"CAPTURE_LOCK_SHA256: {capture_lock_hash}")
    print(f"LEAGUE_NIGHT_SHA256: {league_night_hash}")
    print(
        "GAME_SET_SIGNATURE: "
        f"{actual_game_set_signature}"
    )
    print(f"METADATA_FILE_COUNT: {len(metadata_files)}")
    print(f"PARSED_GAME_FILE_COUNT: {len(game_files)}")
    print(
        "VERIFIED_GAME_SOURCE_COUNT: "
        f"{verified_game_source_count}"
    )
    print(f"RECONCILED_GAME_COUNT: {reconciled_game_count}")
    print(f"PLAY_BY_PLAY_EVENT_COUNT: {event_row_count}")
    print(f"CONTROL_ROW_COUNT: {control_row_count}")
    print(f"UNKNOWN_CONTROL_COUNT: {unknown_control_count}")
    print(
        "WINNER_OMISSION_ACCEPTED_COUNT: "
        f"{winner_omission_accepted_count}"
    )
    print(
        "VALIDATION_GATE_COUNT: "
        f"{len(gates)}"
    )
    print(
        "PASSED_VALIDATION_GATE_COUNT: "
        f"{sum(1 for value in gates.values() if value)}"
    )
    print(
        "CANONICAL_PROMOTION_AUTHORIZED: "
        f"{'YES' if promotion_authorized else 'NO'}"
    )
    print(
        "PROMOTION_DECISION: "
        f"{report['promotionDecision']['status']}"
    )
    print(
        "VALIDATION_REPORT: "
        f"{report_path.relative_to(repo_root).as_posix()}"
    )
    print(f"VALIDATION_REPORT_SHA256: {report_hash}")
    print(f"FAILURE_COUNT: {len(failures)}")

    for failure in failures[:30]:
        print(f"FAILURE_DETAIL: {failure}")

    if not failures:
        print("FAILURE_DETAIL: none")

    print(
        "FILES_MODIFIED_BY_VALIDATOR: "
        f"{files_modified}"
    )
    print("CANONICAL_FILES_MODIFIED: 0")
    print("LIVE_REQUESTS_EXECUTED: 0")

    return 0 if promotion_authorized else 1


if __name__ == "__main__":
    raise SystemExit(main())
