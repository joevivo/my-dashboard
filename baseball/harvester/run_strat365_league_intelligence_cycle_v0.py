from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = (
    "bie.strat365.league-intelligence-cycle.v0"
)

VALID_TRANSACTION_COVERAGE = (
    "NORMALIZED_COMPLETE_PAGINATION"
)

VALID_INJURY_COVERAGE = (
    "NORMALIZED_CURRENT_STATE_SNAPSHOT"
)


def utc_now() -> str:
    return (
        datetime.now(
            timezone.utc
        )
        .isoformat()
        .replace(
            "+00:00",
            "Z",
        )
    )


def load_json(
    path: Path,
) -> dict[str, Any]:
    value = json.loads(
        path.read_text(
            encoding="utf-8"
        )
    )

    if not isinstance(
        value,
        dict,
    ):
        raise ValueError(
            f"Expected JSON object: {path}"
        )

    return value


def write_json(
    path: Path,
    value: dict[str, Any],
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporary = (
        path.parent
        / (
            path.name
            + ".tmp"
        )
    )

    temporary.write_text(
        json.dumps(
            value,
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )

    os.replace(
        temporary,
        path,
    )


def write_bytes_atomic(
    path: Path,
    body: bytes,
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporary = (
        path.parent
        / (
            path.name
            + ".tmp"
        )
    )

    temporary.write_bytes(
        body
    )

    os.replace(
        temporary,
        path,
    )


def sha256_file(
    path: Path,
) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as handle:
        for chunk in iter(
            lambda: handle.read(
                65536
            ),
            b"",
        ):
            digest.update(
                chunk
            )

    return digest.hexdigest()


def run_python(
    script: Path,
    arguments: list[str],
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(script),
            *arguments,
        ],
        text=True,
        capture_output=True,
    )


def state_change_sources_valid(
    normalized: dict[str, Any],
) -> bool:
    coverage = normalized.get(
        "sourceCoverage"
    )

    if not isinstance(
        coverage,
        dict,
    ):
        return False

    if (
        coverage.get(
            "leagueTransactions"
        )
        != VALID_TRANSACTION_COVERAGE
    ):
        return False

    if (
        coverage.get(
            "leagueInjuries"
        )
        != VALID_INJURY_COVERAGE
    ):
        return False

    state = normalized.get(
        "leagueStateChanges"
    )

    if not isinstance(
        state,
        dict,
    ):
        return False

    injuries = state.get(
        "activeInjuries"
    )

    if not isinstance(
        injuries,
        dict,
    ):
        return False

    return (
        injuries.get(
            "snapshotValid"
        )
        is True
    )


def delta_allows_promotion(
    delta: dict[str, Any],
) -> bool:
    status = delta.get(
        "domainStatus"
    )

    if not isinstance(
        status,
        dict,
    ):
        return False

    if delta.get(
        "baseline"
    ) is True:
        return (
            status.get(
                "transactions"
            )
            == "BASELINE_ESTABLISHED"
            and status.get(
                "injuries"
            )
            == "BASELINE_ESTABLISHED"
        )

    return (
        status.get(
            "transactions"
        )
        == "DERIVED"
        and status.get(
            "injuries"
        )
        == "DERIVED"
        and int(
            delta.get(
                "transactionHistoryRegressionCount",
                0,
            )
        )
        == 0
    )


def ensure_empty_run_root(
    run_root: Path,
) -> None:
    if run_root.exists():
        contents = list(
            run_root.iterdir()
        )

        if contents:
            raise ValueError(
                "Run root must be absent or empty: "
                f"{run_root}"
            )

    run_root.mkdir(
        parents=True,
        exist_ok=True,
    )


def build_paths(
    *,
    repo_root: Path,
) -> dict[str, Path]:
    return {
        "builder": (
            repo_root
            / "baseball"
            / "harvester"
            / "build_strat365_league_intelligence_capture_plan_v0.py"
        ),
        "executor": (
            repo_root
            / "baseball"
            / "harvester"
            / "execute_strat365_league_intelligence_capture_plan_v0.py"
        ),
        "normalizer": (
            repo_root
            / "baseball"
            / "parser"
            / "normalize_strat365_league_intelligence_v0.py"
        ),
        "delta": (
            repo_root
            / "baseball"
            / "analysis"
            / "derive_strat365_league_state_change_delta_v0.py"
        ),
    }


def execute_cycle(
    *,
    repo_root: Path,
    registry: Path,
    league_id: str,
    team_id: str,
    league_date: str,
    phase: str,
    run_root: Path,
    state_root: Path,
) -> dict[str, Any]:
    ensure_empty_run_root(
        run_root
    )

    tools = build_paths(
        repo_root=repo_root
    )

    for name, path in tools.items():
        if not path.exists():
            raise FileNotFoundError(
                f"{name} tool missing: {path}"
            )

    if not registry.exists():
        raise FileNotFoundError(
            f"Registry missing: {registry}"
        )

    plan_path = (
        run_root
        / "plan.json"
    )

    capture_root = (
        run_root
        / "capture"
    )

    normalized_path = (
        run_root
        / "normalized.json"
    )

    delta_path = (
        run_root
        / "delta.json"
    )

    result_path = (
        run_root
        / "cycle-result.json"
    )

    league_state_root = (
        state_root
        / f"league-{league_id}"
    )

    current_state_path = (
        league_state_root
        / "current-normalized.json"
    )

    previous_state_path = (
        league_state_root
        / "previous-normalized.json"
    )

    latest_delta_path = (
        league_state_root
        / "latest-delta.json"
    )

    state_manifest_path = (
        league_state_root
        / "state-manifest.json"
    )

    current_before_exists = (
        current_state_path.exists()
    )

    current_before_bytes = (
        current_state_path.read_bytes()
        if current_before_exists
        else None
    )

    current_before_sha256 = (
        sha256_file(
            current_state_path
        )
        if current_before_exists
        else None
    )

    builder = run_python(
        tools["builder"],
        [
            "--registry",
            str(registry),
            "--league-id",
            str(league_id),
            "--team-id",
            str(team_id),
            "--league-date",
            str(league_date),
            "--phase",
            str(phase),
            "--output",
            str(plan_path),
        ],
    )

    if builder.returncode != 0:
        raise RuntimeError(
            "Builder failed: "
            + (
                builder.stderr.strip()
                or builder.stdout.strip()
            )
        )

    executor = run_python(
        tools["executor"],
        [
            "--plan",
            str(plan_path),
            "--output-root",
            str(capture_root),
        ],
    )

    if executor.returncode != 0:
        raise RuntimeError(
            "Executor failed: "
            + (
                executor.stderr.strip()
                or executor.stdout.strip()
            )
        )

    manifest_path = (
        capture_root
        / "league-intelligence-capture-manifest.json"
    )

    manifest = load_json(
        manifest_path
    )

    if (
        manifest.get(
            "captureStatus"
        )
        != "PASS"
    ):
        raise RuntimeError(
            "Required league-intelligence capture failed."
        )

    normalizer = run_python(
        tools["normalizer"],
        [
            "--capture-root",
            str(capture_root),
            "--output",
            str(normalized_path),
        ],
    )

    if normalizer.returncode != 0:
        result = {
            "schemaVersion": (
                SCHEMA_VERSION
            ),
            "status": "FAIL",
            "leagueId": str(
                league_id
            ),
            "teamId": str(
                team_id
            ),
            "leagueDate": str(
                league_date
            ),
            "phase": str(
                phase
            ),
            "promotionStatus": (
                "NOT_ATTEMPTED_NORMALIZER_FAILURE"
            ),
            "stateAdvanced": False,
            "normalizerError": (
                normalizer.stderr.strip()
                or normalizer.stdout.strip()
            ),
            "completedAtUtc": (
                utc_now()
            ),
        }

        write_json(
            result_path,
            result,
        )

        return result

    normalized = load_json(
        normalized_path
    )

    if (
        str(
            normalized.get(
                "leagueId",
                "",
            )
        )
        != str(
            league_id
        )
    ):
        raise ValueError(
            "Normalized league identity mismatch."
        )

    previous_argument = []

    if current_state_path.exists():
        previous_argument = [
            "--previous",
            str(
                current_state_path
            ),
        ]

    delta = run_python(
        tools["delta"],
        [
            *previous_argument,
            "--current",
            str(
                normalized_path
            ),
            "--output",
            str(
                delta_path
            ),
        ],
    )

    if delta.returncode != 0:
        raise RuntimeError(
            "Delta derivation failed: "
            + (
                delta.stderr.strip()
                or delta.stdout.strip()
            )
        )

    delta_payload = load_json(
        delta_path
    )

    sources_valid = (
        state_change_sources_valid(
            normalized
        )
    )

    promotion_allowed = (
        sources_valid
        and delta_allows_promotion(
            delta_payload
        )
    )

    state_advanced = False

    if promotion_allowed:
        league_state_root.mkdir(
            parents=True,
            exist_ok=True,
        )

        if (
            current_before_bytes
            is not None
        ):
            write_bytes_atomic(
                previous_state_path,
                current_before_bytes,
            )

        write_bytes_atomic(
            current_state_path,
            normalized_path.read_bytes(),
        )

        write_bytes_atomic(
            latest_delta_path,
            delta_path.read_bytes(),
        )

        state_manifest = {
            "schemaVersion": (
                "bie.strat365.league-state-persistence.v0"
            ),
            "leagueId": str(
                league_id
            ),
            "teamId": str(
                team_id
            ),
            "leagueDate": str(
                league_date
            ),
            "phase": str(
                phase
            ),
            "updatedAtUtc": (
                utc_now()
            ),
            "currentNormalizedSha256": (
                sha256_file(
                    current_state_path
                )
            ),
            "previousNormalizedSha256": (
                sha256_file(
                    previous_state_path
                )
                if previous_state_path.exists()
                else None
            ),
            "latestDeltaSha256": (
                sha256_file(
                    latest_delta_path
                )
            ),
            "latestDeltaChangeCount": int(
                delta_payload.get(
                    "changeCount",
                    0,
                )
            ),
            "latestDeltaInvalidationSignalCount": int(
                delta_payload.get(
                    "invalidationSignalCount",
                    0,
                )
            ),
        }

        write_json(
            state_manifest_path,
            state_manifest,
        )

        state_advanced = True

        promotion_status = (
            "BASELINE_ESTABLISHED"
            if delta_payload.get(
                "baseline"
            )
            else "ADVANCED"
        )

    else:
        promotion_status = (
            "HELD_INVALID_STATE_CHANGE_EVIDENCE"
        )

    result = {
        "schemaVersion": (
            SCHEMA_VERSION
        ),
        "status": "PASS",
        "leagueId": str(
            league_id
        ),
        "teamId": str(
            team_id
        ),
        "leagueDate": str(
            league_date
        ),
        "phase": str(
            phase
        ),
        "captureStatus": (
            manifest.get(
                "captureStatus"
            )
        ),
        "stateChangeSourcesValid": (
            sources_valid
        ),
        "deltaDomainStatus": (
            delta_payload.get(
                "domainStatus"
            )
        ),
        "deltaChangeCount": int(
            delta_payload.get(
                "changeCount",
                0,
            )
        ),
        "deltaInvalidationSignalCount": int(
            delta_payload.get(
                "invalidationSignalCount",
                0,
            )
        ),
        "transactionHistoryRegressionCount": int(
            delta_payload.get(
                "transactionHistoryRegressionCount",
                0,
            )
        ),
        "promotionStatus": (
            promotion_status
        ),
        "stateAdvanced": (
            state_advanced
        ),
        "previousBaselineSha256": (
            current_before_sha256
        ),
        "currentNormalizedSha256": (
            sha256_file(
                normalized_path
            )
        ),
        "completedAtUtc": (
            utc_now()
        ),
    }

    write_json(
        result_path,
        result,
    )

    return result


def main() -> int:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--repo-root",
        required=True,
    )

    parser.add_argument(
        "--registry",
        required=True,
    )

    parser.add_argument(
        "--league-id",
        required=True,
    )

    parser.add_argument(
        "--team-id",
        required=True,
    )

    parser.add_argument(
        "--league-date",
        required=True,
    )

    parser.add_argument(
        "--phase",
        choices=[
            "pregame",
            "postgame",
        ],
        required=True,
    )

    parser.add_argument(
        "--run-root",
        required=True,
    )

    parser.add_argument(
        "--state-root",
        required=True,
    )

    args = parser.parse_args()

    result = execute_cycle(
        repo_root=Path(
            args.repo_root
        ).resolve(),
        registry=Path(
            args.registry
        ).resolve(),
        league_id=str(
            args.league_id
        ),
        team_id=str(
            args.team_id
        ),
        league_date=str(
            args.league_date
        ),
        phase=str(
            args.phase
        ),
        run_root=Path(
            args.run_root
        ).resolve(),
        state_root=Path(
            args.state_root
        ).resolve(),
    )

    print(
        json.dumps(
            {
                "status": (
                    result[
                        "status"
                    ]
                ),
                "leagueId": (
                    result[
                        "leagueId"
                    ]
                ),
                "promotionStatus": (
                    result[
                        "promotionStatus"
                    ]
                ),
                "stateAdvanced": (
                    result[
                        "stateAdvanced"
                    ]
                ),
            },
            separators=(",", ":"),
        )
    )

    return (
        0
        if result[
            "status"
        ] == "PASS"
        else 1
    )


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
