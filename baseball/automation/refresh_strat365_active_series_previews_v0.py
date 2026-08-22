from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "bie.strat365.active-series-preview-refresh.v0"

DEFAULT_REGISTRY = Path(
    "data/baseball/config/strat365/"
    "strat365-active-team-registry-v0.json"
)

DEFAULT_STATE_ROOT = Path(
    "data/baseball/state/strat365/"
    "league-intelligence-v0"
)

DEFAULT_SERIES_ROOT = Path(
    "data/baseball/state/strat365/"
    "series-preview-v0"
)

DEFAULT_PLAYER_INTELLIGENCE_ROOT = Path(
    "data/baseball/state/strat365/"
    "series-player-intelligence-v1"
)


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)

    if not isinstance(value, dict):
        raise ValueError(
            f"Expected JSON object: {path}"
        )

    return value


def write_text(
    path: Path,
    text: str,
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    path.write_text(
        text,
        encoding="utf-8",
    )


def active_teams(
    registry: Path,
) -> list[dict[str, Any]]:
    payload = read_json(registry)

    rows = payload.get("teams")

    if not isinstance(rows, list):
        raise ValueError(
            "Active-team registry has no teams list."
        )

    teams = [
        row
        for row in rows
        if (
            isinstance(row, dict)
            and row.get("active") is True
        )
    ]

    if not teams:
        raise ValueError(
            "Active-team registry contains no "
            "active teams."
        )

    required = (
        "leagueId",
        "teamId",
        "teamName",
        "season",
        "scheduleUrl",
    )

    for row in teams:
        missing = [
            key
            for key in required
            if not str(
                row.get(key) or ""
            ).strip()
        ]

        if missing:
            raise ValueError(
                "Active-team registry row is "
                "missing required fields "
                f"{missing}: {row}"
            )

    return teams


def run_python(
    *,
    repo_root: Path,
    script: Path,
    arguments: list[str],
) -> subprocess.CompletedProcess[str]:
    command = [
        sys.executable,
        str(script),
        *arguments,
    ]

    result = subprocess.run(
        command,
        cwd=repo_root,
        text=True,
        capture_output=True,
        check=False,
    )

    if result.returncode != 0:
        detail = (
            result.stderr.strip()
            or result.stdout.strip()
            or "no subprocess output"
        )

        raise RuntimeError(
            f"{script.name} failed with "
            f"exit code {result.returncode}: "
            f"{detail[-4000:]}"
        )

    return result


def fetch_schedule(
    *,
    url: str,
    output: Path,
    max_attempts: int = 3,
    base_delay_seconds: float = 2.0,
) -> None:
    if max_attempts < 1:
        raise ValueError(
            "max_attempts must be at least 1"
        )

    for attempt in range(
        1,
        max_attempts + 1,
    ):
        request = urllib.request.Request(
            url,
            headers={
                "User-Agent":
                    "Mozilla/5.0 "
                    "(BIE StratOperations "
                    "Series Preview Refresh)"
            },
        )

        try:
            with urllib.request.urlopen(
                request,
                timeout=30,
            ) as response:
                html = response.read().decode(
                    "utf-8",
                    errors="replace",
                )
        except urllib.error.HTTPError:
            raise
        except (
            urllib.error.URLError,
            TimeoutError,
            ConnectionError,
        ):
            if attempt >= max_attempts:
                raise

            time.sleep(
                base_delay_seconds * attempt
            )
            continue

        if not html.strip():
            raise ValueError(
                f"Empty schedule response: {url}"
            )

        write_text(
            output,
            html,
        )
        return


def schedule_output_path(
    *,
    repo_root: Path,
    team: dict[str, Any],
    league_date: str,
) -> Path:
    return (
        repo_root
        / "data"
        / "baseball"
        / "parsed"
        / "strat365"
        / str(team["season"])
        / "team-schedule"
        / f"league-{team['leagueId']}"
        / f"team-{team['teamId']}"
        / league_date
        / "upcoming-series-v0.json"
    )


def player_intelligence_path(
    *,
    repo_root: Path,
    team: dict[str, Any],
) -> Path:
    return (
        repo_root
        / DEFAULT_PLAYER_INTELLIGENCE_ROOT
        / f"league-{team['leagueId']}"
        / f"team-{team['teamId']}"
        / "series-player-intelligence-v1.json"
    )


def preview_path(
    *,
    repo_root: Path,
    team: dict[str, Any],
) -> Path:
    return (
        repo_root
        / DEFAULT_SERIES_ROOT
        / f"league-{team['leagueId']}"
        / f"team-{team['teamId']}"
        / "series-engine-v0.json"
    )


def normalized_numbers(
    value: Any,
) -> list[int]:
    if not isinstance(value, list):
        return []

    return [
        int(item)
        for item in value
    ]


def build(
    *,
    repo_root: Path,
    registry: Path,
    league_date: str,
    run_root: Path,
    state_root: Path,
    dry_run: bool,
) -> dict[str, Any]:
    teams = active_teams(registry)

    schedule_parser = (
        repo_root
        / "baseball"
        / "analysis"
        / "parse_strat365_team_schedule_v0.py"
    )

    active_cycles = (
        repo_root
        / "baseball"
        / "harvester"
        / "run_strat365_active_league_intelligence_cycles_v0.py"
    )

    player_builder = (
        repo_root
        / "baseball"
        / "analysis"
        / "build_strat365_series_player_intelligence_v1.py"
    )

    preview_builder = (
        repo_root
        / "baseball"
        / "automation"
        / "build_strat365_active_series_previews_v0.py"
    )

    required_scripts = (
        schedule_parser,
        active_cycles,
        player_builder,
        preview_builder,
    )

    for script in required_scripts:
        if not script.exists():
            raise FileNotFoundError(
                f"Required refresh component "
                f"is missing: {script}"
            )

    plan = [
        {
            "teamKey":
                str(team.get("teamKey") or ""),
            "leagueId":
                str(team["leagueId"]),
            "teamId":
                str(team["teamId"]),
            "scheduleUrl":
                str(team["scheduleUrl"]),
            "scheduleOutput":
                str(
                    schedule_output_path(
                        repo_root=repo_root,
                        team=team,
                        league_date=league_date,
                    )
                ),
        }
        for team in teams
    ]

    if dry_run:
        return {
            "schemaVersion": SCHEMA_VERSION,
            "status": "PASS",
            "dryRun": True,
            "activeTeamCount": len(teams),
            "leagueDate": league_date,
            "phase": "pregame",
            "plan": plan,
        }

    raw_schedule_root = (
        run_root
        / "team-schedules"
    )

    parsed_schedules: dict[
        str,
        dict[str, Any],
    ] = {}

    for team in teams:
        league_id = str(
            team["leagueId"]
        )

        team_id = str(
            team["teamId"]
        )

        raw_schedule = (
            raw_schedule_root
            / (
                f"league-{league_id}-"
                f"team-{team_id}.html"
            )
        )

        parsed_schedule = (
            schedule_output_path(
                repo_root=repo_root,
                team=team,
                league_date=league_date,
            )
        )

        fetch_schedule(
            url=str(team["scheduleUrl"]),
            output=raw_schedule,
        )

        run_python(
            repo_root=repo_root,
            script=schedule_parser,
            arguments=[
                "--source",
                str(raw_schedule),
                "--league-id",
                league_id,
                "--team-id",
                team_id,
                "--team-name",
                str(team["teamName"]),
                "--as-of-date",
                league_date,
                "--output",
                str(parsed_schedule),
            ],
        )

        payload = read_json(
            parsed_schedule
        )

        next_series = payload.get(
            "nextSeries"
        )

        if (
            not isinstance(
                next_series,
                dict,
            )
            or next_series.get(
                "status"
            ) != "FOUND"
        ):
            raise ValueError(
                "Current upcoming series was "
                "not resolved for "
                f"{league_id}:{team_id}."
            )

        opponent_team_id = str(
            next_series.get(
                "opponentTeamId"
            )
            or ""
        ).strip()

        if not opponent_team_id:
            raise ValueError(
                "Current upcoming opponent "
                "was not resolved for "
                f"{league_id}:{team_id}."
            )

        parsed_schedules[
            f"{league_id}:{team_id}"
        ] = payload

    intelligence_run_root = (
        run_root
        / "league-intelligence"
    )

    run_python(
        repo_root=repo_root,
        script=active_cycles,
        arguments=[
            "--repo-root",
            str(repo_root),
            "--registry",
            str(registry),
            "--league-date",
            league_date,
            "--phase",
            "pregame",
            "--run-root",
            str(
                intelligence_run_root
            ),
            "--state-root",
            str(state_root),
        ],
    )

    for team in teams:
        league_id = str(
            team["leagueId"]
        )

        team_id = str(
            team["teamId"]
        )

        schedule_payload = (
            parsed_schedules[
                f"{league_id}:{team_id}"
            ]
        )

        next_series = (
            schedule_payload[
                "nextSeries"
            ]
        )

        opponent_team_id = str(
            next_series[
                "opponentTeamId"
            ]
        )

        league_intelligence = (
            state_root
            / f"league-{league_id}"
            / "current-normalized.json"
        )

        if (
            not league_intelligence.exists()
        ):
            raise FileNotFoundError(
                "Pregame league intelligence "
                "was not promoted for "
                f"league {league_id}: "
                f"{league_intelligence}"
            )

        output = (
            player_intelligence_path(
                repo_root=repo_root,
                team=team,
            )
        )

        output.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        run_python(
            repo_root=repo_root,
            script=player_builder,
            arguments=[
                "--league-intelligence",
                str(
                    league_intelligence
                ),
                "--pregame-safe",
                "--team-id",
                team_id,
                "--opponent-team-id",
                opponent_team_id,
                "--output",
                str(output),
            ],
        )

    run_python(
        repo_root=repo_root,
        script=preview_builder,
        arguments=[
            "--repo-root",
            str(repo_root),
            "--registry",
            str(registry),
        ],
    )

    validations = []

    for team in teams:
        league_id = str(
            team["leagueId"]
        )

        team_id = str(
            team["teamId"]
        )

        schedule_payload = (
            parsed_schedules[
                f"{league_id}:{team_id}"
            ]
        )

        preview_file = preview_path(
            repo_root=repo_root,
            team=team,
        )

        if not preview_file.exists():
            raise FileNotFoundError(
                "Series Preview was not "
                "produced for "
                f"{league_id}:{team_id}: "
                f"{preview_file}"
            )

        preview_payload = read_json(
            preview_file
        )

        expected_numbers = (
            normalized_numbers(
                schedule_payload[
                    "nextSeries"
                ].get(
                    "scheduleGameNumbers"
                )
            )
        )

        actual_numbers = (
            normalized_numbers(
                (
                    preview_payload.get(
                        "upcomingSeries"
                    )
                    or {}
                ).get(
                    "scheduleGameNumbers"
                )
            )
        )

        if (
            not expected_numbers
            or expected_numbers
            != actual_numbers
        ):
            raise ValueError(
                "Final Series Preview schedule "
                "identity does not match the "
                "fresh live schedule for "
                f"{league_id}:{team_id}. "
                f"expected={expected_numbers} "
                f"actual={actual_numbers}"
            )

        validations.append(
            {
                "leagueId":
                    league_id,
                "teamId":
                    team_id,
                "scheduleGameNumbersMatch":
                    True,
            }
        )

    return {
        "schemaVersion": SCHEMA_VERSION,
        "status": "PASS",
        "dryRun": False,
        "activeTeamCount": len(teams),
        "leagueDate": league_date,
        "phase": "pregame",
        "runRoot": str(run_root),
        "validation": validations,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Refresh active Strat365 "
            "Series Previews from live, "
            "score-free pregame evidence."
        )
    )

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
        "--league-date",
        default=date.today().isoformat(),
    )

    parser.add_argument(
        "--run-root",
        type=Path,
    )

    parser.add_argument(
        "--state-root",
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

    state_root = (
        args.state_root.resolve()
        if args.state_root is not None
        else (
            repo_root
            / DEFAULT_STATE_ROOT
        ).resolve()
    )

    if args.run_root is not None:
        run_root = (
            args.run_root.resolve()
        )
    else:
        stamp = (
            datetime.now(
                timezone.utc
            )
            .strftime(
                "%Y%m%dT%H%M%SZ"
            )
        )

        run_root = (
            repo_root
            / "data"
            / "baseball"
            / "raw"
            / "strat365"
            / "1968"
            / "one-click-series-preview-refresh"
            / str(args.league_date)
            / f"refresh-{stamp}"
        ).resolve()

    try:
        result = build(
            repo_root=repo_root,
            registry=registry,
            league_date=str(
                args.league_date
            ),
            run_root=run_root,
            state_root=state_root,
            dry_run=bool(
                args.dry_run
            ),
        )
    except Exception as exc:
        result = {
            "schemaVersion":
                SCHEMA_VERSION,
            "status":
                "FAIL",
            "failureType":
                type(exc).__name__,
            "detail":
                str(exc),
            "phase":
                "pregame",
        }

        print(
            json.dumps(
                result,
                indent=2,
                sort_keys=True,
            )
        )

        return 1

    print(
        json.dumps(
            result,
            indent=2,
            sort_keys=True,
        )
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())