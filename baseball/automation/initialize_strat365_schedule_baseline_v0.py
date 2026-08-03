#!/usr/bin/env python3
"""Initialize a spoiler-safe historical schedule baseline for one active team."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import re
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REGISTRY_RELATIVE = Path(
    "data/baseball/config/strat365/"
    "strat365-active-team-registry-v0.json"
)

CONTRACT_RELATIVE = Path(
    "data/baseball/config/strat365/"
    "strat365-nightly-team-state-contract-v0.json"
)


class BaselineFailure(Exception):
    """Raised when a schedule baseline invariant fails."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise BaselineFailure(message)


def utc_now_text() -> str:
    return (
        datetime.now(timezone.utc)
        .isoformat(timespec="milliseconds")
        .replace("+00:00", "Z")
    )


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)

    return digest.hexdigest().upper()


def load_json(path: Path) -> dict[str, Any]:
    require(
        path.is_file(),
        f"Required JSON file is missing: {path}",
    )

    try:
        with path.open("r", encoding="utf-8") as handle:
            value = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        raise BaselineFailure(
            f"Unable to parse JSON file {path}: {exc}"
        ) from exc

    require(
        isinstance(value, dict),
        f"Expected a JSON object at {path}",
    )

    return value


def repository_path(
    repo_root: Path,
    supplied_path: str,
) -> Path:
    candidate = Path(supplied_path)

    if not candidate.is_absolute():
        candidate = repo_root / candidate

    resolved = candidate.resolve()

    try:
        resolved.relative_to(repo_root)
    except ValueError as exc:
        raise BaselineFailure(
            f"Path is outside the repository: {resolved}"
        ) from exc

    return resolved


def repository_relative(
    repo_root: Path,
    path: Path,
) -> str:
    return path.resolve().relative_to(repo_root).as_posix()


def numeric_game_sort(value: str) -> int:
    return int(value)


def discover_game_ids(
    html_text: str,
    league_id: str,
) -> tuple[list[str], int]:
    league_pattern = re.compile(
        (
            r"(?:https?://365\.strat-o-matic\.com)?"
            r"/game/"
            + re.escape(league_id)
            + r"/(?P<game_id>\d+)"
        ),
        re.IGNORECASE,
    )

    all_game_pattern = re.compile(
        (
            r"(?:https?://365\.strat-o-matic\.com)?"
            r"/game/(?P<league_id>\d+)/(?P<game_id>\d+)"
        ),
        re.IGNORECASE,
    )

    game_ids = sorted(
        {
            match.group("game_id")
            for match in league_pattern.finditer(html_text)
        },
        key=numeric_game_sort,
    )

    cross_league_count = sum(
        1
        for match in all_game_pattern.finditer(html_text)
        if match.group("league_id") != league_id
    )

    return game_ids, cross_league_count


def atomic_write_json(
    destination: Path,
    value: dict[str, Any],
) -> None:
    destination.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    serialized = (
        json.dumps(
            value,
            indent=2,
            ensure_ascii=False,
        )
        + "\n"
    )

    temporary_path: Path | None = None

    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="\n",
            dir=destination.parent,
            prefix=f".{destination.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            handle.write(serialized)
            temporary_path = Path(handle.name)

        os.replace(
            temporary_path,
            destination,
        )
    finally:
        if (
            temporary_path is not None
            and temporary_path.exists()
        ):
            temporary_path.unlink()


def build_proposed_state(
    *,
    current_state: dict[str, Any],
    game_ids: list[str],
    fixture_sha256: str,
    captured_at_utc: str,
    run_id: str,
) -> dict[str, Any]:
    proposed = copy.deepcopy(current_state)

    proposed["stateRevision"] = (
        int(current_state["stateRevision"]) + 1
    )

    proposed["scheduleBaseline"].update(
        {
            "status": "READY",
            "capturedAtUtc": captured_at_utc,
            "scheduleSha256": fixture_sha256,
            "historicalGameIds": game_ids,
            "historicalGameCount": len(game_ids),
            "baselineRunId": run_id,
        }
    )

    proposed["discovery"].update(
        {
            "status": "NO_NEW_GAMES",
            "lastCheckedAtUtc": captured_at_utc,
            "knownGameIds": game_ids,
            "newlyDiscoveredGameIds": [],
            "pendingCaptureGameIds": [],
            "lastDiscoveredGameId": game_ids[-1],
            "scheduleUnchanged": None,
        }
    )

    proposed["audit"].update(
        {
            "lastTransitionAtUtc": captured_at_utc,
            "lastTransitionAction": (
                "INITIAL_SCHEDULE_BASELINE_READY"
            ),
            "lastRunId": run_id,
            "transitionCount": (
                int(
                    current_state["audit"]
                    .get("transitionCount", 0)
                )
                + 1
            ),
        }
    )

    transition_history = list(
        current_state["audit"].get(
            "transitionHistory",
            [],
        )
    )

    transition_history.append(
        {
            "timestampUtc": captured_at_utc,
            "action": "INITIAL_SCHEDULE_BASELINE_READY",
            "priorState": (
                "PENDING_INITIAL_SCHEDULE_BASELINE"
            ),
            "nextState": "READY",
            "runId": run_id,
        }
    )

    proposed["audit"]["transitionHistory"] = (
        transition_history
    )

    proposed["validation"].update(
        {
            "pendingBaselineBeforeDiscovery": False,
            "initialQueuesEmpty": False,
            "registryTeamIdentityMatch": True,
            "gameResultsStoredInState": False,
            "status": "PASS",
        }
    )

    return proposed


def validate_proposed_state(
    *,
    proposed: dict[str, Any],
    game_ids: list[str],
    expected_team_key: str,
) -> None:
    require(
        proposed.get("teamKey") == expected_team_key,
        "Proposed state team identity changed.",
    )

    require(
        proposed["scheduleBaseline"]["status"]
        == "READY",
        "Proposed baseline status is not READY.",
    )

    require(
        proposed["scheduleBaseline"]["historicalGameIds"]
        == game_ids,
        "Proposed historical game IDs do not match discovery.",
    )

    require(
        proposed["scheduleBaseline"]["historicalGameCount"]
        == len(game_ids),
        "Proposed historical game count is incorrect.",
    )

    require(
        proposed["discovery"]["knownGameIds"]
        == game_ids,
        "Proposed known game IDs do not match baseline.",
    )

    require(
        proposed["discovery"]["newlyDiscoveredGameIds"]
        == [],
        "Initial baseline must not classify games as new.",
    )

    require(
        proposed["discovery"]["pendingCaptureGameIds"]
        == [],
        "Initial baseline must not queue historical games.",
    )

    require(
        proposed["capture"]["capturedGameIds"]
        == [],
        "Initial baseline must not mark games captured.",
    )

    require(
        proposed["series"]["gameIds"] == [],
        "Initial baseline must not activate a series.",
    )

    require(
        proposed["spoilerControl"]["state"]
        == "SEALED",
        "Initial baseline must remain sealed.",
    )

    require(
        proposed["spoilerControl"][
            "automaticOutcomeDisclosure"
        ]
        is False,
        "Automatic outcome disclosure must remain disabled.",
    )


def initialize_baseline(
    *,
    repo_root: Path,
    team_key: str,
    fixture_path: Path,
    dry_run: bool,
    apply: bool,
    run_id: str,
) -> dict[str, Any]:
    registry = load_json(
        repo_root / REGISTRY_RELATIVE
    )

    contract = load_json(
        repo_root / CONTRACT_RELATIVE
    )

    active_teams = [
        team
        for team in registry.get("teams", [])
        if isinstance(team, dict)
        and team.get("active") is True
    ]

    matches = [
        team
        for team in active_teams
        if str(team.get("teamKey", "")) == team_key
    ]

    require(
        len(matches) == 1,
        (
            "Expected exactly one active registry team "
            f"for {team_key}; found {len(matches)}."
        ),
    )

    team = matches[0]
    league_id = str(team["leagueId"])
    team_id = str(team["teamId"])

    root_template = str(
        contract["storagePolicy"]["rootTemplate"]
    )

    state_relative = Path(
        root_template.format(
            leagueId=league_id,
            teamId=team_id,
        )
    ) / str(contract["storagePolicy"]["fileName"])

    state_path = repo_root / state_relative
    state = load_json(state_path)

    require(
        state.get("teamKey") == team_key,
        "Registry and state team keys do not match.",
    )

    require(
        state.get("leagueId") == league_id,
        "Registry and state league IDs do not match.",
    )

    require(
        state.get("teamId") == team_id,
        "Registry and state team IDs do not match.",
    )

    require(
        state["scheduleBaseline"]["status"]
        == "PENDING_INITIAL_SCHEDULE_BASELINE",
        "State is not pending its initial schedule baseline.",
    )

    require(
        state["discovery"]["status"] == "NOT_RUN",
        "Discovery already ran before baseline.",
    )

    require(
        state["capture"]["status"] == "NOT_RUN",
        "Capture already ran before baseline.",
    )

    require(
        state["stateRevision"] == 0,
        "Initial baseline requires state revision 0.",
    )

    require(
        fixture_path.is_file(),
        f"Saved schedule fixture is missing: {fixture_path}",
    )

    html_text = fixture_path.read_text(
        encoding="utf-8",
        errors="replace",
    )

    game_ids, cross_league_count = discover_game_ids(
        html_text,
        league_id,
    )

    require(
        game_ids,
        "No target-league game IDs were discovered.",
    )

    require(
        cross_league_count == 0,
        (
            "Cross-league game links were discovered: "
            f"{cross_league_count}"
        ),
    )

    fixture_sha256 = sha256_file(fixture_path)
    captured_at_utc = utc_now_text()

    proposed = build_proposed_state(
        current_state=state,
        game_ids=game_ids,
        fixture_sha256=fixture_sha256,
        captured_at_utc=captured_at_utc,
        run_id=run_id,
    )

    validate_proposed_state(
        proposed=proposed,
        game_ids=game_ids,
        expected_team_key=team_key,
    )

    state_write_count = 0

    if apply:
        atomic_write_json(
            state_path,
            proposed,
        )

        state_write_count = 1

    return {
        "status": "PASS",
        "mode": "APPLY" if apply else "DRY_RUN",
        "teamKey": team_key,
        "leagueId": league_id,
        "teamId": team_id,
        "fixturePath": repository_relative(
            repo_root,
            fixture_path,
        ),
        "fixtureSha256": fixture_sha256,
        "fixtureByteCount": fixture_path.stat().st_size,
        "crossLeagueGameLinkCount": cross_league_count,
        "discoveredGameCount": len(game_ids),
        "discoveredGameIds": game_ids,
        "currentBaselineStatus": (
            state["scheduleBaseline"]["status"]
        ),
        "proposedBaselineStatus": (
            proposed["scheduleBaseline"]["status"]
        ),
        "currentStateRevision": state["stateRevision"],
        "proposedStateRevision": (
            proposed["stateRevision"]
        ),
        "historicalGameCountProposed": len(game_ids),
        "newlyDiscoveredGameCountProposed": 0,
        "pendingCaptureGameCountProposed": 0,
        "stateWriteCount": state_write_count,
        "spoilerStatus": (
            proposed["spoilerControl"]["state"]
        ),
        "outcomeFieldsPrinted": 0,
        "runId": run_id,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Initialize one team's spoiler-safe "
            "historical schedule baseline."
        )
    )

    parser.add_argument(
        "--repo-root",
        required=True,
    )

    parser.add_argument(
        "--team-key",
        required=True,
    )

    parser.add_argument(
        "--fixture-path",
        required=True,
    )

    parser.add_argument(
        "--run-id",
        required=True,
    )

    mode = parser.add_mutually_exclusive_group(
        required=True
    )

    mode.add_argument(
        "--dry-run",
        action="store_true",
    )

    mode.add_argument(
        "--apply",
        action="store_true",
    )

    args = parser.parse_args()

    try:
        repo_root = Path(
            args.repo_root
        ).resolve()

        fixture_path = repository_path(
            repo_root,
            args.fixture_path,
        )

        result = initialize_baseline(
            repo_root=repo_root,
            team_key=args.team_key,
            fixture_path=fixture_path,
            dry_run=args.dry_run,
            apply=args.apply,
            run_id=args.run_id,
        )
    except BaselineFailure as exc:
        print(
            json.dumps(
                {
                    "status": "FAIL",
                    "failureDetail": str(exc),
                },
                separators=(",", ":"),
            )
        )

        return 1

    print(
        json.dumps(
            result,
            separators=(",", ":"),
        )
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
