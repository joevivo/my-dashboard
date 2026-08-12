from __future__ import annotations

import argparse
import importlib
import json
import os
from pathlib import Path
import subprocess
import sys
import uuid
from typing import Any


SCHEMA_VERSION = "bie.strat365.active-series-preview-build.v0"

DEFAULT_REGISTRY = Path(
    "data/baseball/config/strat365/strat365-active-team-registry-v0.json"
)

DEFAULT_SERIES_OUTPUT_ROOT = Path(
    "data/baseball/state/strat365/series-preview-v0"
)

DEFAULT_AGGREGATE_OUTPUT = Path(
    "data/baseball/state/strat365/active-teams-v0/"
    "active-team-aggregate-v0.json"
)


def read_json(path: Path) -> Any:
    return json.loads(
        path.read_text(encoding="utf-8")
    )


def resolve_active_pairs(
    *,
    repo_root: Path,
    registry: Path,
) -> list[tuple[str, str]]:
    harvester_dir = (
        repo_root
        / "baseball"
        / "harvester"
    )

    harvester_text = str(harvester_dir)

    if harvester_text not in sys.path:
        sys.path.insert(
            0,
            harvester_text,
        )

    module = importlib.import_module(
        "run_strat365_active_league_intelligence_cycles_v0"
    )

    payload = read_json(registry)

    pairs = module.resolve_active_leagues(
        payload
    )

    return [
        (
            str(league_id),
            str(team_id),
        )
        for league_id, team_id in pairs
    ]


def latest_file(
    root: Path,
    filename: str,
) -> Path | None:
    if not root.exists():
        return None

    candidates = [
        path
        for path in root.rglob(filename)
        if path.is_file()
    ]

    if not candidates:
        return None

    return max(
        candidates,
        key=lambda path: (
            path.stat().st_mtime_ns,
            path.as_posix(),
        ),
    )


def resolve_inputs(
    *,
    repo_root: Path,
    active_pairs: list[tuple[str, str]],
) -> list[dict[str, Any]]:
    resolved: list[dict[str, Any]] = []

    for league_id, team_id in active_pairs:
        nightly_state = (
            repo_root
            / "data"
            / "baseball"
            / "state"
            / "strat365"
            / "nightly"
            / league_id
            / team_id
            / "nightly-team-state-v0.json"
        )

        schedule_root = (
            repo_root
            / "data"
            / "baseball"
            / "parsed"
            / "strat365"
            / "1968"
            / "team-schedule"
            / f"league-{league_id}"
            / f"team-{team_id}"
        )

        schedule = latest_file(
            schedule_root,
            "upcoming-series-v0.json",
        )

        league_intelligence_root = (
            repo_root
            / "data"
            / "baseball"
            / "parsed"
            / "strat365"
            / "1968"
            / "league-state"
            / f"league-{league_id}"
        )

        league_intelligence = latest_file(
            league_intelligence_root,
            "bie-current-league-intelligence-v0.json",
        )

        resolved.append(
            {
                "leagueId": league_id,
                "teamId": team_id,
                "nightlyState": nightly_state,
                "schedule": schedule,
                "leagueIntelligence": league_intelligence,
            }
        )

    return resolved


def validate_inputs(
    rows: list[dict[str, Any]],
) -> list[str]:
    failures: list[str] = []

    for row in rows:
        identity = (
            f"{row['leagueId']}/"
            f"{row['teamId']}"
        )

        nightly_state = row[
            "nightlyState"
        ]

        if not nightly_state.exists():
            failures.append(
                f"{identity}: nightly state missing: "
                f"{nightly_state}"
            )

        schedule = row["schedule"]

        if schedule is None:
            failures.append(
                f"{identity}: normalized upcoming-series "
                "schedule missing"
            )

    return failures


def run_python(
    *,
    repo_root: Path,
    script: Path,
    arguments: list[str],
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        [
            sys.executable,
            str(script),
            *arguments,
        ],
        cwd=repo_root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )

    if result.returncode != 0:
        detail = (
            result.stderr.strip()
            or result.stdout.strip()
            or "no diagnostic output"
        )

        raise RuntimeError(
            f"{script.name} failed with "
            f"exit code {result.returncode}: "
            f"{detail[:1500]}"
        )

    return result


def temporary_sibling(
    path: Path,
) -> Path:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    return (
        path.parent
        / (
            "."
            + path.name
            + "."
            + uuid.uuid4().hex
            + ".tmp"
        )
    )


def build(
    *,
    repo_root: Path,
    registry: Path,
    output_root: Path,
    aggregate_output: Path,
    dry_run: bool,
) -> dict[str, Any]:
    active_pairs = resolve_active_pairs(
        repo_root=repo_root,
        registry=registry,
    )

    rows = resolve_inputs(
        repo_root=repo_root,
        active_pairs=active_pairs,
    )

    failures = validate_inputs(
        rows
    )

    plan = []

    for row in rows:
        league_id = row["leagueId"]
        team_id = row["teamId"]

        final_series_path = (
            output_root
            / f"league-{league_id}"
            / f"team-{team_id}"
            / "series-engine-v0.json"
        )

        row["finalSeriesPath"] = (
            final_series_path
        )

        plan.append(
            {
                "leagueId": league_id,
                "teamId": team_id,
                "nightlyState": str(
                    row["nightlyState"]
                ),
                "schedule": (
                    str(row["schedule"])
                    if row["schedule"] is not None
                    else None
                ),
                "leagueIntelligence": (
                    str(
                        row[
                            "leagueIntelligence"
                        ]
                    )
                    if row[
                        "leagueIntelligence"
                    ] is not None
                    else None
                ),
                "seriesEngineOutput": str(
                    final_series_path
                ),
            }
        )

    if failures:
        return {
            "schemaVersion": SCHEMA_VERSION,
            "status": "FAIL",
            "activeTeamCount": len(
                active_pairs
            ),
            "plannedSeriesCount": len(
                plan
            ),
            "failureCount": len(
                failures
            ),
            "failures": failures,
            "plan": plan,
            "dryRun": dry_run,
        }

    if dry_run:
        return {
            "schemaVersion": SCHEMA_VERSION,
            "status": "PASS",
            "activeTeamCount": len(
                active_pairs
            ),
            "plannedSeriesCount": len(
                plan
            ),
            "failureCount": 0,
            "failures": [],
            "plan": plan,
            "aggregateOutput": str(
                aggregate_output
            ),
            "dryRun": True,
        }

    series_tool = (
        repo_root
        / "baseball"
        / "analysis"
        / "build_strat365_series_engine_v0.py"
    )

    aggregate_tool = (
        repo_root
        / "baseball"
        / "analysis"
        / "build_strat365_active_team_aggregate_v0.py"
    )

    if not series_tool.exists():
        raise FileNotFoundError(
            f"Series Engine missing: {series_tool}"
        )

    if not aggregate_tool.exists():
        raise FileNotFoundError(
            f"Active Team Aggregate builder missing: "
            f"{aggregate_tool}"
        )

    staged_series: list[
        tuple[Path, Path]
    ] = []

    aggregate_temporary: Path | None = None

    try:
        for row in rows:
            final_path = row[
                "finalSeriesPath"
            ]

            temporary_path = temporary_sibling(
                final_path
            )

            arguments = [
                "--team-readiness",
                str(row["nightlyState"]),
                "--team-schedule",
                str(row["schedule"]),
            ]

            league_intelligence = row[
                "leagueIntelligence"
            ]

            if league_intelligence is not None:
                arguments.extend(
                    [
                        "--league-intelligence",
                        str(
                            league_intelligence
                        ),
                    ]
                )

            player_intelligence = (
                repo_root
                / "data"
                / "baseball"
                / "state"
                / "strat365"
                / "series-player-intelligence-v1"
                / f"league-{row['leagueId']}"
                / f"team-{row['teamId']}"
                / "series-player-intelligence-v1.json"
            )

            if player_intelligence.exists():
                arguments.extend(
                    [
                        "--player-intelligence",
                        str(player_intelligence),
                    ]
                )

            arguments.extend(
                [
                    "--output",
                    str(temporary_path),
                ]
            )

            run_python(
                repo_root=repo_root,
                script=series_tool,
                arguments=arguments,
            )

            staged_series.append(
                (
                    temporary_path,
                    final_path,
                )
            )

        aggregate_temporary = (
            temporary_sibling(
                aggregate_output
            )
        )

        aggregate_arguments = [
            "--registry",
            str(registry),
        ]

        for row in rows:
            aggregate_arguments.extend(
                [
                    "--state",
                    str(row["nightlyState"]),
                ]
            )

        for row, (
            temporary_path,
            _final_path,
        ) in zip(
            rows,
            staged_series,
            strict=True,
        ):
            aggregate_arguments.extend(
                [
                    "--series-engine",
                    (
                        f"{row['teamId']}="
                        f"{temporary_path}"
                    ),
                ]
            )

        for row in rows:
            aggregate_arguments.extend(
                [
                    "--schedule",
                    (
                        f"{row['teamId']}="
                        f"{row['schedule']}"
                    ),
                ]
            )

        league_intelligence_seen: set[
            str
        ] = set()

        for row in rows:
            league_id = row["leagueId"]
            league_intelligence = row[
                "leagueIntelligence"
            ]

            if (
                league_intelligence is None
                or league_id
                in league_intelligence_seen
            ):
                continue

            league_intelligence_seen.add(
                league_id
            )

            aggregate_arguments.extend(
                [
                    "--league-intelligence",
                    (
                        f"{league_id}="
                        f"{league_intelligence}"
                    ),
                ]
            )

        aggregate_arguments.extend(
            [
                "--output",
                str(aggregate_temporary),
            ]
        )

        run_python(
            repo_root=repo_root,
            script=aggregate_tool,
            arguments=aggregate_arguments,
        )

        for temporary_path, final_path in staged_series:
            os.replace(
                temporary_path,
                final_path,
            )

        os.replace(
            aggregate_temporary,
            aggregate_output,
        )

        aggregate_temporary = None

    finally:
        for temporary_path, _final_path in staged_series:
            if temporary_path.exists():
                temporary_path.unlink()

        if (
            aggregate_temporary is not None
            and aggregate_temporary.exists()
        ):
            aggregate_temporary.unlink()

    aggregate_payload = read_json(
        aggregate_output
    )

    return {
        "schemaVersion": SCHEMA_VERSION,
        "status": "PASS",
        "activeTeamCount": len(
            active_pairs
        ),
        "persistedSeriesCount": len(
            staged_series
        ),
        "failureCount": 0,
        "failures": [],
        "aggregateTeamCount": len(
            aggregate_payload.get(
                "teams",
                [],
            )
        ),
        "aggregateOutput": str(
            aggregate_output
        ),
        "plan": plan,
        "dryRun": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path.cwd(),
    )

    parser.add_argument(
        "--registry",
        type=Path,
    )

    parser.add_argument(
        "--output-root",
        type=Path,
    )

    parser.add_argument(
        "--aggregate-output",
        type=Path,
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
    )

    args = parser.parse_args()

    repo_root = (
        args.repo_root.resolve()
    )

    registry = (
        args.registry.resolve()
        if args.registry is not None
        else (
            repo_root
            / DEFAULT_REGISTRY
        ).resolve()
    )

    output_root = (
        args.output_root.resolve()
        if args.output_root is not None
        else (
            repo_root
            / DEFAULT_SERIES_OUTPUT_ROOT
        ).resolve()
    )

    aggregate_output = (
        args.aggregate_output.resolve()
        if args.aggregate_output is not None
        else (
            repo_root
            / DEFAULT_AGGREGATE_OUTPUT
        ).resolve()
    )

    try:
        result = build(
            repo_root=repo_root,
            registry=registry,
            output_root=output_root,
            aggregate_output=aggregate_output,
            dry_run=bool(
                args.dry_run
            ),
        )
    except Exception as exc:
        result = {
            "schemaVersion": SCHEMA_VERSION,
            "status": "FAIL",
            "failureType": type(
                exc
            ).__name__,
            "failureReason": str(
                exc
            ),
            "dryRun": bool(
                args.dry_run
            ),
        }

    print(
        json.dumps(
            result,
            sort_keys=True,
        )
    )

    return (
        0
        if result.get(
            "status"
        ) == "PASS"
        else 1
    )


if __name__ == "__main__":
    raise SystemExit(main())