from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
import uuid
from pathlib import Path
from typing import Any


def sha256(path: Path) -> str:
    algorithm = hashlib.sha256()

    with path.open("rb") as source:
        for chunk in iter(
            lambda: source.read(1024 * 1024),
            b"",
        ):
            algorithm.update(chunk)

    return algorithm.hexdigest().upper()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def json_payload(value: Any) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    ).encode("utf-8")


def relative_to_repo(repo_root: Path, path: Path) -> str:
    return path.resolve().relative_to(repo_root).as_posix()


def game_set_signature(game_files: list[Path]) -> str:
    rows = [
        f"{path.name}:{sha256(path)}"
        for path in sorted(
            game_files,
            key=lambda value: value.name,
        )
    ]

    return hashlib.sha256(
        "\n".join(rows).encode("utf-8")
    ).hexdigest().upper()


def collect_target_files(target: Path) -> dict[str, Path]:
    if not target.is_dir():
        return {}

    return {
        path.relative_to(target).as_posix(): path
        for path in target.rglob("*")
        if path.is_file()
    }


def verify_target(
    target: Path,
    expected_payloads: dict[str, bytes],
) -> tuple[bool, list[str]]:
    failures: list[str] = []

    if not target.is_dir():
        return (
            False,
            [f"Canonical target is missing: {target}"],
        )

    existing_files = collect_target_files(target)
    expected_names = set(expected_payloads)
    existing_names = set(existing_files)

    missing = sorted(expected_names - existing_names)
    extra = sorted(existing_names - expected_names)

    if missing:
        failures.append(
            f"Canonical target is missing files: {missing}"
        )

    if extra:
        failures.append(
            "Canonical target contains unexpected files: "
            f"{extra}"
        )

    for relative_name in sorted(
        expected_names & existing_names
    ):
        actual_payload = existing_files[
            relative_name
        ].read_bytes()

        if actual_payload != expected_payloads[
            relative_name
        ]:
            failures.append(
                f"Canonical file conflicts: {relative_name}"
            )

    return (not failures, failures)


def print_failure(
    failures: list[str],
    canonical_target: str,
    conflict: bool = False,
) -> int:
    print("# RESULT SUMMARY")
    print("ATOMIC_TEAM_NIGHT_PROMOTION: FAIL")
    print(
        "PROMOTION_STATUS: "
        + (
            "CONFLICT_REJECTED"
            if conflict
            else "BLOCKED"
        )
    )
    print(f"CANONICAL_TARGET: {canonical_target}")
    print("FILES_MODIFIED_BY_PROMOTER: 0")
    print(
        "CONFLICT_DETECTED: "
        + ("YES" if conflict else "NO")
    )
    print("LIVE_REQUESTS_EXECUTED: 0")

    for failure in failures[:30]:
        print(f"FAILURE_DETAIL: {failure}")

    return 1


def main() -> int:
    argument_parser = argparse.ArgumentParser()
    argument_parser.add_argument(
        "--repo-root",
        required=True,
    )
    argument_parser.add_argument(
        "--parsed-root",
        required=True,
    )
    argument_parser.add_argument(
        "--team-id",
        required=True,
    )
    argument_parser.add_argument(
        "--canonical-target",
        required=True,
    )
    arguments = argument_parser.parse_args()

    repo_root = Path(arguments.repo_root).resolve()
    parsed_root = Path(arguments.parsed_root).resolve()
    team_id = str(arguments.team_id).strip()
    canonical_target = Path(
        arguments.canonical_target
    ).resolve()

    validation_report_path = (
        parsed_root
        / "complete-night-validation-v0.json"
    )
    league_night_path = (
        parsed_root
        / "league-night-v0.json"
    )
    game_directory = parsed_root / "games"

    failures: list[str] = []

    if re.fullmatch(r"\d+", team_id) is None:
        failures.append(
            f"Team ID is invalid: {team_id}"
        )

    try:
        parsed_relative = relative_to_repo(
            repo_root,
            parsed_root,
        )
    except ValueError:
        parsed_relative = ""
        failures.append(
            "Parsed root is outside the repository."
        )

    parsed_scope_match = re.fullmatch(
        (
            r"data/baseball/parsed/strat365/"
            r"(\d+)/season-ingestion/"
            r"league-(\d+)/"
            r"(\d{4}-\d{2}-\d{2})"
        ),
        parsed_relative,
    )

    season = ""
    league_id = ""
    league_date = ""

    if parsed_scope_match is None:
        failures.append(
            "Parsed root does not match the expected "
            "season-ingestion namespace."
        )
    else:
        (
            season,
            league_id,
            league_date,
        ) = parsed_scope_match.groups()

    expected_scope = (
        f"{season}/league-{league_id}/"
        f"team-{team_id}/{league_date}"
    )

    expected_target_relative = (
        "data/baseball/canonical/strat365/"
        f"{season}/season-ingestion/"
        f"league-{league_id}/"
        f"team-{team_id}/{league_date}"
    )

    expected_target = (
        repo_root / Path(expected_target_relative)
    ).resolve()

    if canonical_target != expected_target:
        failures.append(
            "Canonical target does not match the "
            "authorized team-night namespace."
        )

    for required_path in (
        validation_report_path,
        league_night_path,
        game_directory,
    ):
        if not required_path.exists():
            failures.append(
                f"Required source is missing: {required_path}"
            )

    if failures:
        return print_failure(
            failures,
            expected_target_relative,
        )

    validation_report = load_json(
        validation_report_path
    )
    league_night = load_json(league_night_path)

    scope = validation_report.get("scope", {})
    promotion_decision = validation_report.get(
        "promotionDecision",
        {},
    )
    authoritative_hashes = validation_report.get(
        "authoritativeHashes",
        {},
    )
    counts = validation_report.get("counts", {})
    gates = validation_report.get("gates", {})
    validation_failures = validation_report.get(
        "failures",
        [],
    )

    if (
        validation_report.get("schemaVersion")
        != "strat365-complete-night-validation-v0"
    ):
        failures.append(
            "Validation report schema is invalid."
        )

    if scope.get("scopeType") != "TEAM_NIGHT":
        failures.append(
            "Validation report scope is not TEAM_NIGHT."
        )

    if str(scope.get("teamId", "")) != team_id:
        failures.append(
            "Validation report team ID differs."
        )

    team_name = str(
        scope.get("teamName", "")
    ).strip()

    if not team_name:
        failures.append(
            "Validation report team name is missing."
        )

    if (
        promotion_decision.get("scopeType")
        != "TEAM_NIGHT"
    ):
        failures.append(
            "Promotion-decision scope is not TEAM_NIGHT."
        )

    if (
        promotion_decision.get(
            "canonicalPromotionAuthorized"
        )
        is not True
    ):
        failures.append(
            "Validation report does not authorize promotion."
        )

    if (
        promotion_decision.get("status")
        != "AUTHORIZED_FOR_ATOMIC_CANONICAL_PROMOTION"
    ):
        failures.append(
            "Validation promotion status is invalid."
        )

    if (
        promotion_decision.get("requiresAtomicWrite")
        is not True
    ):
        failures.append(
            "Validation report does not require atomic write."
        )

    if (
        promotion_decision.get(
            "sourceStagingMutationAuthorized"
        )
        is not False
    ):
        failures.append(
            "Validation report permits source mutation."
        )

    if (
        promotion_decision.get("authorizationScope")
        != expected_scope
    ):
        failures.append(
            "Validation authorization scope differs."
        )

    if validation_failures:
        failures.append(
            "Validation report contains failures."
        )

    if (
        not isinstance(gates, dict)
        or len(gates) != 17
        or not all(
            value is True
            for value in gates.values()
        )
    ):
        failures.append(
            "Validation report does not retain "
            "17 passing gates."
        )

    expected_game_count = int(
        counts.get("gameFiles", -1)
    )
    reconciled_game_count = int(
        counts.get("reconciledGames", -1)
    )

    if expected_game_count <= 0:
        failures.append(
            "Validation-report game count is invalid."
        )

    if reconciled_game_count != expected_game_count:
        failures.append(
            "Validation reconciliation count differs."
        )

    game_files = sorted(
        game_directory.glob("game-*-v0.json"),
        key=lambda value: value.name,
    )

    game_ids: set[int] = set()
    tracked_team_game_count = 0

    for game_path in game_files:
        game = load_json(game_path)
        game_id = int(game.get("gameId", -1))
        game_ids.add(game_id)

        if game.get("schemaVersion") != "strat365-game-v0":
            failures.append(
                f"Game {game_id} schema is invalid."
            )

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

        if team_name in game_team_names:
            tracked_team_game_count += 1
        else:
            failures.append(
                f"Game {game_id} does not contain "
                f"the tracked team: {team_name}"
            )

        reconciliation = game.get(
            "reconciliation",
            {},
        )

        if (
            reconciliation.get("resultSourceMatch")
            is not True
        ):
            failures.append(
                f"Game {game_id} result does not reconcile."
            )

        if (
            reconciliation.get("playByPlayAttached")
            is not True
        ):
            failures.append(
                f"Game {game_id} lacks play-by-play."
            )

    if len(game_files) != expected_game_count:
        failures.append(
            "Parsed game-file count differs."
        )

    if len(game_ids) != expected_game_count:
        failures.append(
            "Parsed game IDs are not unique."
        )

    if tracked_team_game_count != len(game_files):
        failures.append(
            "The validation-report team does not appear "
            "in every parsed game."
        )

    if int(league_night.get("gameCount", -1)) != (
        expected_game_count
    ):
        failures.append(
            "League-night game count differs."
        )

    if int(
        league_night.get(
            "structuredGameCount",
            -1,
        )
    ) != expected_game_count:
        failures.append(
            "League-night structured-game count differs."
        )

    reconciliation_summary = league_night.get(
        "reconciliationSummary",
        {},
    )

    if int(
        reconciliation_summary.get(
            "reconciledGameCount",
            -1,
        )
    ) != expected_game_count:
        failures.append(
            "League-night reconciliation count differs."
        )

    parser_path = (
        repo_root
        / "baseball/parser/"
        / "parse_strat365_season_ingestion_v0.py"
    )
    validator_path = (
        repo_root
        / "baseball/parser/"
        / "validate_strat365_season_ingestion_complete_night_v0.py"
    )

    capture_directory = (
        repo_root
        / Path(str(scope.get("captureDirectory", "")))
    ).resolve()

    capture_lock_path = (
        capture_directory
        / "capture-lock-and-promotion-decision-v1.json"
    )
    plan_path = (
        capture_directory
        / "game-capture-plan.json"
    )
    run_manifest_path = (
        capture_directory
        / "run-manifest.json"
    )

    authoritative_paths = {
        "parserSha256": parser_path,
        "captureLockSha256": capture_lock_path,
        "planSha256": plan_path,
        "manifestSha256": run_manifest_path,
        "leagueNightSha256": league_night_path,
    }

    for hash_name, source_path in authoritative_paths.items():
        if not source_path.is_file():
            failures.append(
                f"Authority source is missing: {source_path}"
            )
            continue

        if sha256(source_path) != str(
            authoritative_hashes.get(hash_name, "")
        ):
            failures.append(
                f"Authority hash differs: {hash_name}"
            )

    current_game_set_signature = game_set_signature(
        game_files
    )

    if current_game_set_signature != str(
        authoritative_hashes.get(
            "gameSetSignature",
            "",
        )
    ):
        failures.append(
            "Game-set signature differs."
        )

    validation_report_hash = sha256(
        validation_report_path
    )

    source_payloads: dict[
        str,
        tuple[Path, bytes],
    ] = {
        "league-night-v0.json": (
            league_night_path,
            league_night_path.read_bytes(),
        ),
        "complete-night-validation-v0.json": (
            validation_report_path,
            validation_report_path.read_bytes(),
        ),
    }

    for game_path in game_files:
        relative_name = (
            Path("games") / game_path.name
        ).as_posix()

        source_payloads[relative_name] = (
            game_path,
            game_path.read_bytes(),
        )

    manifest_file_rows: list[dict[str, Any]] = []

    for relative_name in sorted(source_payloads):
        source_path, payload = source_payloads[
            relative_name
        ]

        manifest_file_rows.append(
            {
                "canonicalPath": relative_name,
                "sourcePath": relative_to_repo(
                    repo_root,
                    source_path,
                ),
                "sha256": hashlib.sha256(
                    payload
                ).hexdigest().upper(),
                "byteCount": len(payload),
            }
        )

    manifest = {
        "schemaVersion": (
            "strat365-canonical-team-night-manifest-v0"
        ),
        "season": season,
        "leagueId": league_id,
        "teamId": team_id,
        "teamName": team_name,
        "leagueDate": league_date,
        "scopeType": "TEAM_NIGHT",
        "canonicalTarget": expected_target_relative,
        "promotionStatus": "PROMOTED",
        "promotionAuthority": {
            "validationReport": relative_to_repo(
                repo_root,
                validation_report_path,
            ),
            "validationReportSha256": (
                validation_report_hash
            ),
            "decision": (
                "AUTHORIZED_FOR_ATOMIC_CANONICAL_PROMOTION"
            ),
            "authorizationScope": expected_scope,
            "requiresAtomicWrite": True,
        },
        "sourceAuthority": {
            "parserSha256": sha256(parser_path),
            "validatorSha256": sha256(
                validator_path
            ),
            "captureLockSha256": sha256(
                capture_lock_path
            ),
            "planSha256": sha256(plan_path),
            "runManifestSha256": sha256(
                run_manifest_path
            ),
            "leagueNightSha256": sha256(
                league_night_path
            ),
            "gameSetSignature": (
                current_game_set_signature
            ),
        },
        "counts": {
            "games": len(game_files),
            "payloadFiles": len(source_payloads),
            "packageFiles": len(source_payloads) + 1,
        },
        "payloadFiles": manifest_file_rows,
        "overwritePolicy": {
            "conflictingExistingTarget": "REJECT",
            "identicalExistingTarget": (
                "ACCEPT_IDEMPOTENTLY"
            ),
        },
    }

    expected_payloads = {
        relative_name: payload
        for relative_name, (_, payload)
        in source_payloads.items()
    }

    manifest_name = (
        "canonical-team-night-manifest-v0.json"
    )

    expected_payloads[manifest_name] = json_payload(
        manifest
    )

    if failures:
        return print_failure(
            failures,
            expected_target_relative,
        )

    if canonical_target.exists():
        target_valid, target_failures = verify_target(
            canonical_target,
            expected_payloads,
        )

        if not target_valid:
            return print_failure(
                target_failures,
                expected_target_relative,
                conflict=True,
            )

        print("# RESULT SUMMARY")
        print("ATOMIC_TEAM_NIGHT_PROMOTION: PASS")
        print("PROMOTION_STATUS: ALREADY_PRESENT")
        print(
            f"CANONICAL_TARGET: "
            f"{expected_target_relative}"
        )
        print(
            f"CANONICAL_TARGET_FILE_COUNT: "
            f"{len(expected_payloads)}"
        )
        print(
            f"CANONICAL_GAME_FILE_COUNT: "
            f"{len(game_files)}"
        )
        print(
            f"CANONICAL_MANIFEST_SHA256: "
            f"{sha256(canonical_target / manifest_name)}"
        )
        print("FILES_MODIFIED_BY_PROMOTER: 0")
        print("PROMOTION_IDEMPOTENT: YES")
        print("CONFLICT_DETECTED: NO")
        print("LIVE_REQUESTS_EXECUTED: 0")
        return 0

    canonical_target.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporary_target = (
        canonical_target.parent
        / (
            f".{canonical_target.name}."
            f"promotion-{uuid.uuid4().hex}"
        )
    )

    files_modified = 0

    try:
        temporary_target.mkdir(
            parents=False,
            exist_ok=False,
        )

        for relative_name in sorted(
            expected_payloads
        ):
            destination = (
                temporary_target / relative_name
            )

            destination.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            destination.write_bytes(
                expected_payloads[relative_name]
            )

            files_modified += 1

        temporary_valid, temporary_failures = (
            verify_target(
                temporary_target,
                expected_payloads,
            )
        )

        if not temporary_valid:
            raise RuntimeError(
                "Temporary package failed verification: "
                + " | ".join(temporary_failures)
            )

        os.replace(
            temporary_target,
            canonical_target,
        )

        target_valid, target_failures = verify_target(
            canonical_target,
            expected_payloads,
        )

        if not target_valid:
            raise RuntimeError(
                "Promoted package failed verification: "
                + " | ".join(target_failures)
            )
    finally:
        if temporary_target.exists():
            shutil.rmtree(temporary_target)

    print("# RESULT SUMMARY")
    print("ATOMIC_TEAM_NIGHT_PROMOTION: PASS")
    print("PROMOTION_STATUS: PROMOTED")
    print(
        f"CANONICAL_TARGET: "
        f"{expected_target_relative}"
    )
    print(
        f"CANONICAL_TARGET_FILE_COUNT: "
        f"{len(expected_payloads)}"
    )
    print(
        f"CANONICAL_GAME_FILE_COUNT: "
        f"{len(game_files)}"
    )
    print(
        f"CANONICAL_MANIFEST_SHA256: "
        f"{sha256(canonical_target / manifest_name)}"
    )
    print(
        f"FILES_MODIFIED_BY_PROMOTER: "
        f"{files_modified}"
    )
    print(
        "PROMOTION_IDEMPOTENT: "
        "PENDING_SECOND_RUN"
    )
    print("CONFLICT_DETECTED: NO")
    print("LIVE_REQUESTS_EXECUTED: 0")
    return 0


if __name__ == "__main__":
    sys.exit(main())
