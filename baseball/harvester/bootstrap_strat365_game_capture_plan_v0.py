from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


EXPECTED_TRANSPORT_SHA256 = (
    "F139D1457598489F989EDBE8EF5503C617C8CB8E5A6EF4D67BF56FD413439133"
)

EXPECTED_PLAN_BUILDER_SHA256 = (
    "B971716470E9B35438AC2AFDDE7279107B355F874E01D419ED5050FF2F1D910E"
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def atomic_write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    payload = (
        json.dumps(
            value,
            indent=4,
            ensure_ascii=False,
        )
        + "\n"
    ).encode("utf-8")

    temporary = path.with_name(
        f".{path.name}.{os.getpid()}.{next(tempfile._get_candidate_names())}.tmp"
    )

    temporary.write_bytes(payload)
    os.replace(temporary, path)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as stream:
        while True:
            chunk = stream.read(1024 * 1024)

            if not chunk:
                break

            digest.update(chunk)

    return digest.hexdigest().upper()


def repository_relative(path: Path, repo_root: Path) -> str:
    return path.resolve().relative_to(repo_root.resolve()).as_posix()


def resolve_under_repository(
    value: str,
    repo_root: Path,
) -> Path:
    candidate = Path(value)

    if not candidate.is_absolute():
        candidate = repo_root / candidate

    resolved = candidate.resolve()
    resolved.relative_to(repo_root.resolve())

    return resolved


def parse_result_summary(output: str) -> dict[str, str]:
    values: dict[str, str] = {}

    for line in output.splitlines():
        match = re.match(
            r"^\s*([A-Z][A-Z0-9_]*):\s*(.*)\s*$",
            line,
        )

        if match:
            values[match.group(1)] = match.group(2)

    return values


def parse_headers(
    path: Path,
) -> tuple[int, str]:
    text = path.read_text(
        encoding="utf-8",
        errors="replace",
    )

    status_matches = re.findall(
        r"(?mi)^HTTP/\S+\s+(\d{3})\b",
        text,
    )

    if not status_matches:
        raise ValueError(
            "Response headers do not contain an HTTP status."
        )

    content_type_matches = re.findall(
        r"(?mi)^content-type:\s*(.+?)\s*$",
        text,
    )

    content_type = (
        content_type_matches[-1].strip()
        if content_type_matches
        else "text/html"
    )

    return int(status_matches[-1]), content_type


def validate_scores_body(
    body_path: Path,
    league_id: str,
    expected_game_count: int,
) -> dict[str, Any]:
    html_text = body_path.read_text(
        encoding="utf-8",
        errors="replace",
    )

    game_pattern = re.compile(
        rf'''href\s*=\s*["']
        [^"']*?/game/{re.escape(league_id)}/
        (?P<game_id>\d+)
        (?:[/?#][^"']*)?
        ["']''',
        re.IGNORECASE | re.VERBOSE,
    )

    game_ids = [
        match.group("game_id")
        for match in game_pattern.finditer(html_text)
    ]

    unique_game_ids = sorted(
        set(game_ids),
        key=int,
    )

    final_candidates = [
        (
            "game_result_hidden",
            len(
                re.findall(
                    r"(?i)game\s+result\s+hidden",
                    html_text,
                )
            ),
        ),
        (
            "final_css_class",
            len(
                re.findall(
                    r'''(?i)class\s*=\s*["'][^"']*\bfinal\b[^"']*["']''',
                    html_text,
                )
            ),
        ),
        (
            "final_word",
            len(
                re.findall(
                    r"(?i)\bfinal\b",
                    html_text,
                )
            ),
        ),
    ]

    selected_final_method = None
    selected_final_count = -1

    for method, count in final_candidates:
        if count == expected_game_count:
            selected_final_method = method
            selected_final_count = count
            break

    if len(unique_game_ids) != expected_game_count:
        raise ValueError(
            "League-scores unique game count mismatch: "
            f"expected {expected_game_count}; "
            f"found {len(unique_game_ids)}."
        )

    if selected_final_method is None:
        candidate_text = ", ".join(
            f"{method}={count}"
            for method, count in final_candidates
        )

        raise ValueError(
            "Could not validate the expected number of final games. "
            f"Candidates: {candidate_text}"
        )

    return {
        "gameLinkCount": len(game_ids),
        "uniqueGameCount": len(unique_game_ids),
        "expectedGameCount": expected_game_count,
        "duplicateGameLinkCount": (
            len(game_ids) - len(unique_game_ids)
        ),
        "finalIndicatorCount": selected_final_count,
        "expectedFinalIndicatorCount": expected_game_count,
        "finalIndicatorMethod": selected_final_method,
        "gameIds": unique_game_ids,
    }


def copy_for_adoption(
    source_body: Path,
    source_headers: Path,
    staged_body: Path,
    staged_headers: Path,
) -> tuple[int, str, str, int]:
    if not source_body.is_file():
        raise ValueError(
            f"Adoption body is missing: {source_body}"
        )

    if not source_headers.is_file():
        raise ValueError(
            f"Adoption headers are missing: {source_headers}"
        )

    staged_body.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    shutil.copyfile(
        source_body,
        staged_body,
    )

    shutil.copyfile(
        source_headers,
        staged_headers,
    )

    http_status, content_type = parse_headers(
        staged_headers
    )

    return (
        http_status,
        content_type,
        "",
        0,
    )


def capture_live(
    transport_path: Path,
    requested_url: str,
    staged_body: Path,
    staged_headers: Path,
    request_timeout_seconds: int,
) -> tuple[int, str, str, int]:
    staged_body.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    command = [
        "powershell.exe",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(transport_path),
        "-RequestedUrl",
        requested_url,
        "-BodyPath",
        str(staged_body),
        "-HeadersPath",
        str(staged_headers),
        "-RequestTimeoutSeconds",
        str(request_timeout_seconds),
    ]

    completed = subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=False,
    )

    combined_output = (
        completed.stdout
        + ("\n" if completed.stdout and completed.stderr else "")
        + completed.stderr
    )

    result = parse_result_summary(
        combined_output
    )

    if completed.returncode != 0:
        raise ValueError(
            "Transport helper failed: "
            + combined_output.replace("\n", " | ")
        )

    if result.get("TRANSPORT_VALIDATION") != "PASS":
        raise ValueError(
            "Transport helper did not report PASS: "
            + combined_output.replace("\n", " | ")
        )

    if result.get("HTTP_REQUESTS_EXECUTED") != "1":
        raise ValueError(
            "Transport helper did not report exactly one request."
        )

    if not staged_body.is_file():
        raise ValueError(
            "Transport helper did not create the response body."
        )

    if not staged_headers.is_file():
        raise ValueError(
            "Transport helper did not create response headers."
        )

    http_status = int(
        result.get("HTTP_STATUS", "0")
    )

    content_type = result.get(
        "CONTENT_TYPE",
        "text/html",
    )

    effective_url = result.get(
        "EFFECTIVE_URL",
        requested_url,
    )

    return (
        http_status,
        content_type,
        effective_url,
        1,
    )


def build_scores_metadata(
    *,
    run_relative: str,
    run_spec_relative: str,
    manifest_relative: str,
    requested_url: str,
    effective_url: str,
    league_id: str,
    league_date: str,
    captured_at_utc: str,
    http_status: int,
    content_type: str,
    byte_count: int,
    body_sha256: str,
    body_relative: str,
    headers_relative: str,
    validation: dict[str, Any],
    helper_exit_code: int,
) -> dict[str, Any]:
    return {
        "schemaVersion":
            "strat365-raw-response-metadata-v0",
        "sourceFamily": "leagueScores",
        "sourceRouteClassification":
            "leagueScoresDated",
        "requestedUrl": requested_url,
        "effectiveUrl": effective_url,
        "leagueId": league_id,
        "leagueDate": league_date,
        "teamId": None,
        "gameId": None,
        "attemptNumber": 1,
        "capturedAtUtc": captured_at_utc,
        "httpStatus": http_status,
        "contentType": content_type,
        "byteCount": byte_count,
        "sha256": body_sha256,
        "rawResponsePath": body_relative,
        "responseHeadersPath": headers_relative,
        "transportResult": "PASS",
        "validation": {
            "helperExitCode": helper_exit_code,
            "helperByteCount": str(byte_count),
            "helperSha256": body_sha256,
            "rawBodyPresent": True,
            "responseHeadersPresent": True,
            "rawBodyHashMatch": True,
            "gameLinkCount":
                validation["gameLinkCount"],
            "uniqueGameCount":
                validation["uniqueGameCount"],
            "expectedGameCount":
                validation["expectedGameCount"],
            "duplicateGameLinkCount":
                validation["duplicateGameLinkCount"],
            "finalIndicatorCount":
                validation["finalIndicatorCount"],
            "expectedFinalIndicatorCount":
                validation[
                    "expectedFinalIndicatorCount"
                ],
            "finalIndicatorMethod":
                validation["finalIndicatorMethod"],
            "sourceValidation": "PASS",
            "nightCandidateSignal":
                "GAME_AND_FINAL_COUNTS_PASS_SERIES_PENDING",
        },
        "provenance": {
            "runManifest": manifest_relative,
            "runSpec": run_spec_relative,
            "transportHelper":
                "baseball/harvester/"
                "invoke_strat365_raw_get_v0.ps1",
            "governingContract":
                "docs/baseball/"
                "strat365-league-season-ingestion-"
                "source-contract-v0.md",
        },
    }


def build_scores_row(
    *,
    requested_url: str,
    effective_url: str,
    body_relative: str,
    headers_relative: str,
    metadata_relative: str,
    byte_count: int,
    body_sha256: str,
) -> dict[str, Any]:
    return {
        "sourceFamily": "leagueScores",
        "requestedUrl": requested_url,
        "effectiveUrl": effective_url,
        "attemptNumber": 1,
        "requestStatus": "captured",
        "rawResponsePath": body_relative,
        "responseHeadersPath": headers_relative,
        "metadataPath": metadata_relative,
        "byteCount": byte_count,
        "sha256": body_sha256,
    }


def checkpoint_scores_manifest(
    manifest: dict[str, Any],
    *,
    run_relative: str,
    scores_row: dict[str, Any],
    requested_url: str,
    validation: dict[str, Any],
) -> dict[str, Any]:
    manifest["runDirectory"] = run_relative
    manifest["runState"] = "scores_captured"
    manifest["capturePlanFrozen"] = False
    manifest["plannedRequestCount"] = 1
    manifest["attemptedRequestCount"] = 1
    manifest["capturedResponseCount"] = 1
    manifest["failedRequestCount"] = 0
    manifest["httpRequestCount"] = 1
    manifest["canonicalPromotionEligibility"] = "NO"
    manifest["requests"] = [scores_row]

    manifest["scoresDiscovery"] = {
        "status": "captured",
        "requestedUrl": requested_url,
        "expectedGameCount":
            validation["expectedGameCount"],
        "discoveredGameCount":
            validation["uniqueGameCount"],
        "duplicateGameLinkCount":
            validation["duplicateGameLinkCount"],
        "finalIndicatorCount":
            validation["finalIndicatorCount"],
        "sourceValidation": "PASS",
        "seriesCoverageStatus": "PENDING",
    }

    return manifest


def finalize_manifest(
    manifest: dict[str, Any],
    *,
    run_relative: str,
    scores_row: dict[str, Any],
    plan: dict[str, Any],
    plan_relative: str,
    plan_sha256: str,
) -> dict[str, Any]:
    ledger_rows: list[dict[str, Any]] = [
        scores_row
    ]

    for request in plan["requests"]:
        row = dict(request)
        row["requestStatus"] = "planned"
        row["attemptCount"] = 0
        ledger_rows.append(row)

    if len(ledger_rows) != 55:
        raise ValueError(
            "Final ledger must contain 55 requests."
        )

    manifest["runDirectory"] = run_relative
    manifest["runState"] = "game_capture_plan_frozen"
    manifest["capturePlanFrozen"] = True
    manifest["plannedRequestCount"] = 55
    manifest["attemptedRequestCount"] = 1
    manifest["capturedResponseCount"] = 1
    manifest["failedRequestCount"] = 0
    manifest["httpRequestCount"] = 1
    manifest["canonicalPromotionEligibility"] = "NO"
    manifest["requests"] = ledger_rows

    manifest["gameCapturePlan"] = {
        "planPath": plan_relative,
        "planSha256": plan_sha256,
        "planState": "frozen",
        "frozenAtUtc": plan["frozenAtUtc"],
        "plannedGameRequestCount":
            plan["plannedRequestCount"],
        "requiredGameRequestCount":
            plan["requiredRequestCount"],
        "sourceScoresResponse":
            plan["sourceScoresResponse"],
    }

    existing_execution = (
        manifest.get("gameCaptureExecution")
        or {}
    )

    recovery_events = list(
        existing_execution.get("recoveryEvents")
        or []
    )

    manifest["gameCaptureExecution"] = {
        "capturedGameRequestCount": 0,
        "pendingGameRequestCount": 54,
        "failedGameRequestCount": 0,
        "lastCompletedGameId": None,
        "executionLedger":
            "run-manifest.json requests",
        "frozenPlanImmutable": True,
        "planMutationAllowed": False,
        "recoveryEvents": recovery_events,
    }

    return manifest


def validate_existing_scores_checkpoint(
    *,
    metadata_path: Path,
    body_path: Path,
    headers_path: Path,
    expected_game_count: int,
    league_id: str,
) -> tuple[
    dict[str, Any],
    dict[str, Any],
]:
    metadata = load_json(metadata_path)

    if metadata.get("transportResult") != "PASS":
        raise ValueError(
            "Existing scores metadata transportResult is not PASS."
        )

    if not body_path.is_file():
        raise ValueError(
            "Existing scores body is missing."
        )

    if not headers_path.is_file():
        raise ValueError(
            "Existing scores headers are missing."
        )

    body_sha256 = sha256_file(body_path)

    if (
        body_sha256
        != str(metadata.get("sha256", "")).upper()
    ):
        raise ValueError(
            "Existing scores body hash does not match metadata."
        )

    validation = validate_scores_body(
        body_path=body_path,
        league_id=league_id,
        expected_game_count=expected_game_count,
    )

    return metadata, validation


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Capture or adopt one Strat365 league-scores "
            "response, checkpoint its provenance, freeze the "
            "54-request game plan, and initialize the executor ledger."
        )
    )

    parser.add_argument(
        "--repo-root",
        required=True,
    )

    parser.add_argument(
        "--run-directory",
        required=True,
    )

    parser.add_argument(
        "--request-timeout-seconds",
        type=int,
        default=60,
    )

    mode = parser.add_mutually_exclusive_group(
        required=True
    )

    mode.add_argument(
        "--dry-run",
        action="store_true",
    )

    mode.add_argument(
        "--live",
        action="store_true",
    )

    mode.add_argument(
        "--adopt-body",
    )

    parser.add_argument(
        "--adopt-headers",
    )

    return parser.parse_args()


def main() -> int:
    args = parse_args()

    repo_root = Path(
        args.repo_root
    ).resolve()

    run_directory = resolve_under_repository(
        args.run_directory,
        repo_root,
    )

    if not run_directory.is_dir():
        raise ValueError(
            f"Run directory does not exist: {run_directory}"
        )

    if args.adopt_body and not args.adopt_headers:
        raise ValueError(
            "--adopt-headers is required with --adopt-body."
        )

    if args.adopt_headers and not args.adopt_body:
        raise ValueError(
            "--adopt-body is required with --adopt-headers."
        )

    run_spec_path = (
        run_directory / "run-spec.json"
    )

    manifest_path = (
        run_directory / "run-manifest.json"
    )

    plan_path = (
        run_directory / "game-capture-plan.json"
    )

    if not run_spec_path.is_file():
        raise ValueError(
            f"Missing run spec: {run_spec_path}"
        )

    if not manifest_path.is_file():
        raise ValueError(
            f"Missing run manifest: {manifest_path}"
        )

    transport_path = (
        repo_root
        / "baseball"
        / "harvester"
        / "invoke_strat365_raw_get_v0.ps1"
    )

    plan_builder_path = (
        repo_root
        / "baseball"
        / "harvester"
        / "build_strat365_game_capture_plan_v0.py"
    )

    if sha256_file(transport_path) != EXPECTED_TRANSPORT_SHA256:
        raise ValueError(
            "Transport-helper SHA-256 mismatch."
        )

    if (
        sha256_file(plan_builder_path)
        != EXPECTED_PLAN_BUILDER_SHA256
    ):
        raise ValueError(
            "Plan-builder SHA-256 mismatch."
        )

    run_spec = load_json(run_spec_path)
    manifest = load_json(manifest_path)

    league_id = str(run_spec["leagueId"])
    league_date = str(run_spec["leagueDate"])
    base_uri = str(run_spec["baseUri"]).rstrip("/")

    expected_game_count = int(
        run_spec["expectedCounts"]["gameCount"]
    )

    if expected_game_count != 18:
        raise ValueError(
            "This bootstrap contract requires 18 games."
        )

    run_relative = repository_relative(
        run_directory,
        repo_root,
    )

    run_spec_relative = repository_relative(
        run_spec_path,
        repo_root,
    )

    manifest_relative = repository_relative(
        manifest_path,
        repo_root,
    )

    requested_url = (
        f"{base_uri}/league/scores/"
        f"{league_id}/{league_date}"
    )

    body_path = (
        run_directory
        / "responses"
        / "league"
        / f"league-scores-{league_date}.html"
    )

    headers_path = (
        run_directory
        / "responses"
        / "league"
        / f"league-scores-{league_date}.headers.txt"
    )

    metadata_path = (
        run_directory
        / "metadata"
        / f"league-scores-{league_date}.attempt-1.json"
    )

    body_relative = repository_relative(
        body_path,
        repo_root,
    )

    headers_relative = repository_relative(
        headers_path,
        repo_root,
    )

    metadata_relative = repository_relative(
        metadata_path,
        repo_root,
    )

    plan_relative = repository_relative(
        plan_path,
        repo_root,
    )

    scores_rows = [
        row
        for row in list(manifest.get("requests") or [])
        if row.get("sourceFamily") == "leagueScores"
    ]

    all_scores_artifacts_exist = all(
        path.is_file()
        for path in (
            body_path,
            headers_path,
            metadata_path,
        )
    )

    any_scores_artifact_exists = any(
        path.exists()
        for path in (
            body_path,
            headers_path,
            metadata_path,
        )
    )

    if args.dry_run:
        if plan_path.exists():
            raise ValueError(
                "Frozen game-capture plan already exists."
            )

        if any_scores_artifact_exists:
            if not all_scores_artifacts_exist:
                raise ValueError(
                    "Partial league-scores artifacts exist."
                )

            if len(scores_rows) != 1:
                raise ValueError(
                    "Existing scores artifacts lack one ledger row."
                )

            mode = "RESUME_EXISTING_SCORES"
        else:
            if scores_rows:
                raise ValueError(
                    "Manifest contains a scores row without artifacts."
                )

            mode = "NEW_SCORES_CAPTURE"

        print(
            json.dumps(
                {
                    "status": "PASS",
                    "mode": "DRY_RUN",
                    "nextMode": mode,
                    "leagueId": league_id,
                    "leagueDate": league_date,
                    "requestedUrl": requested_url,
                    "httpRequestsExecuted": 0,
                    "canonicalPromotionEligibility": "NO",
                },
                separators=(",", ":"),
            )
        )

        return 0

    http_requests_executed = 0
    captured_at_utc = utc_now()

    if plan_path.exists():
        raise ValueError(
            "Frozen game-capture plan already exists."
        )

    if all_scores_artifacts_exist:
        if len(scores_rows) != 1:
            raise ValueError(
                "Existing scores artifacts lack one manifest ledger row."
            )

        existing_row = scores_rows[0]

        if existing_row.get("requestStatus") != "captured":
            raise ValueError(
                "Existing scores ledger row is not captured."
            )

        metadata, validation = (
            validate_existing_scores_checkpoint(
                metadata_path=metadata_path,
                body_path=body_path,
                headers_path=headers_path,
                expected_game_count=expected_game_count,
                league_id=league_id,
            )
        )

        effective_url = str(
            metadata.get(
                "effectiveUrl",
                requested_url,
            )
        )

        http_status = int(
            metadata.get("httpStatus", 0)
        )

        content_type = str(
            metadata.get(
                "contentType",
                "text/html",
            )
        )

        byte_count = body_path.stat().st_size
        body_sha256 = sha256_file(body_path)
        scores_row = dict(existing_row)
        execution_mode = "RESUME_EXISTING_SCORES"

    else:
        if any_scores_artifact_exists:
            raise ValueError(
                "Partial league-scores artifacts exist."
            )

        if scores_rows:
            raise ValueError(
                "Manifest contains a scores row without artifacts."
            )

        staging_directory = (
            run_directory
            / (
                ".scores-bootstrap-"
                + next(tempfile._get_candidate_names())
            )
        )

        staged_body = (
            staging_directory / "body.html"
        )

        staged_headers = (
            staging_directory / "headers.txt"
        )

        try:
            if args.live:
                (
                    http_status,
                    content_type,
                    effective_url,
                    http_requests_executed,
                ) = capture_live(
                    transport_path=transport_path,
                    requested_url=requested_url,
                    staged_body=staged_body,
                    staged_headers=staged_headers,
                    request_timeout_seconds=(
                        args.request_timeout_seconds
                    ),
                )

                execution_mode = "LIVE"
                helper_exit_code = 0
            else:
                adoption_body = Path(
                    args.adopt_body
                ).resolve()

                adoption_headers = Path(
                    args.adopt_headers
                ).resolve()

                (
                    http_status,
                    content_type,
                    _,
                    http_requests_executed,
                ) = copy_for_adoption(
                    source_body=adoption_body,
                    source_headers=adoption_headers,
                    staged_body=staged_body,
                    staged_headers=staged_headers,
                )

                effective_url = requested_url
                execution_mode = "ADOPT_EXISTING"
                helper_exit_code = 0

            if http_status != 200:
                raise ValueError(
                    "League-scores HTTP status is not 200: "
                    f"{http_status}"
                )

            validation = validate_scores_body(
                body_path=staged_body,
                league_id=league_id,
                expected_game_count=expected_game_count,
            )

            byte_count = staged_body.stat().st_size
            body_sha256 = sha256_file(staged_body)

            body_path.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            metadata_path.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            os.replace(
                staged_body,
                body_path,
            )

            os.replace(
                staged_headers,
                headers_path,
            )

            metadata = build_scores_metadata(
                run_relative=run_relative,
                run_spec_relative=run_spec_relative,
                manifest_relative=manifest_relative,
                requested_url=requested_url,
                effective_url=effective_url,
                league_id=league_id,
                league_date=league_date,
                captured_at_utc=captured_at_utc,
                http_status=http_status,
                content_type=content_type,
                byte_count=byte_count,
                body_sha256=body_sha256,
                body_relative=body_relative,
                headers_relative=headers_relative,
                validation=validation,
                helper_exit_code=helper_exit_code,
            )

            atomic_write_json(
                metadata_path,
                metadata,
            )

            scores_row = build_scores_row(
                requested_url=requested_url,
                effective_url=effective_url,
                body_relative=body_relative,
                headers_relative=headers_relative,
                metadata_relative=metadata_relative,
                byte_count=byte_count,
                body_sha256=body_sha256,
            )

            checkpoint_scores_manifest(
                manifest,
                run_relative=run_relative,
                scores_row=scores_row,
                requested_url=requested_url,
                validation=validation,
            )

            atomic_write_json(
                manifest_path,
                manifest,
            )
        finally:
            shutil.rmtree(
                staging_directory,
                ignore_errors=True,
            )

    temporary_plan_path = (
        run_directory
        / (
            ".game-capture-plan."
            + next(tempfile._get_candidate_names())
            + ".json"
        )
    )

    plan_command = [
        sys.executable,
        "-B",
        str(plan_builder_path),
        "--repo-root",
        str(repo_root),
        "--run-directory",
        str(run_directory),
        "--output-path",
        str(temporary_plan_path),
        "--frozen-at-utc",
        utc_now(),
    ]

    completed_plan = subprocess.run(
        plan_command,
        capture_output=True,
        text=True,
        check=False,
    )

    plan_output = (
        completed_plan.stdout
        + (
            "\n"
            if completed_plan.stdout
            and completed_plan.stderr
            else ""
        )
        + completed_plan.stderr
    )

    if completed_plan.returncode != 0:
        raise ValueError(
            "Plan builder failed after scores checkpoint: "
            + plan_output.replace("\n", " | ")
        )

    if not temporary_plan_path.is_file():
        raise ValueError(
            "Plan builder did not create a plan."
        )

    plan = load_json(
        temporary_plan_path
    )

    if int(plan["discoveredGameCount"]) != 18:
        raise ValueError(
            "Generated plan did not discover 18 games."
        )

    if int(plan["discoveredSeriesCount"]) != 6:
        raise ValueError(
            "Generated plan did not discover six series."
        )

    if int(plan["plannedRequestCount"]) != 54:
        raise ValueError(
            "Generated plan does not contain 54 requests."
        )

    if int(plan["duplicateRequestIdCount"]) != 0:
        raise ValueError(
            "Generated plan contains duplicate request IDs."
        )

    if int(plan["duplicateUrlCount"]) != 0:
        raise ValueError(
            "Generated plan contains duplicate URLs."
        )

    if plan["gameIdContiguitySignal"] != "PASS":
        raise ValueError(
            "Generated plan game IDs are not contiguous."
        )

    os.replace(
        temporary_plan_path,
        plan_path,
    )

    plan_sha256 = sha256_file(
        plan_path
    )

    final_manifest = load_json(
        manifest_path
    )

    finalize_manifest(
        final_manifest,
        run_relative=run_relative,
        scores_row=scores_row,
        plan=plan,
        plan_relative=plan_relative,
        plan_sha256=plan_sha256,
    )

    atomic_write_json(
        manifest_path,
        final_manifest,
    )

    final_manifest_sha256 = sha256_file(
        manifest_path
    )

    print(
        json.dumps(
            {
                "status": "PASS",
                "mode": execution_mode,
                "leagueId": league_id,
                "leagueDate": league_date,
                "httpStatus": http_status,
                "scoresByteCount": byte_count,
                "scoresSha256": body_sha256,
                "discoveredGameCount":
                    plan["discoveredGameCount"],
                "discoveredSeriesCount":
                    plan["discoveredSeriesCount"],
                "plannedGameRequestCount":
                    plan["plannedRequestCount"],
                "ledgerRequestCount": 55,
                "capturedScoresRowCount": 1,
                "pendingGameRequestCount": 54,
                "planSha256": plan_sha256,
                "manifestSha256":
                    final_manifest_sha256,
                "httpRequestsExecuted":
                    http_requests_executed,
                "canonicalPromotionEligibility":
                    "NO",
            },
            separators=(",", ":"),
        )
    )

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(
            json.dumps(
                {
                    "status": "FAIL",
                    "error": str(exc),
                },
                separators=(",", ":"),
            )
        )

        raise SystemExit(1)
