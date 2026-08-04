from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class DiscoveryFailure(RuntimeError):
    pass


FORBIDDEN_OUTPUT_KEYS = {
    "score",
    "scores",
    "winner",
    "winners",
    "record",
    "records",
    "linescore",
    "linescores",
    "decisiveplay",
    "decisiveplays",
    "seriesoutcome",
    "seriesoutcomes",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise DiscoveryFailure(message)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)

    return digest.hexdigest().upper()


def utc_now_text() -> str:
    return (
        datetime.now(timezone.utc)
        .isoformat(timespec="milliseconds")
        .replace("+00:00", "Z")
    )


def numeric_game_sort(game_ids: list[str]) -> list[str]:
    return sorted(set(game_ids), key=lambda value: int(value))


def normalize_game_ids(value: Any, field_name: str) -> list[str]:
    require(
        isinstance(value, list),
        f"{field_name} must be an array.",
    )

    normalized: list[str] = []

    for item in value:
        text = str(item)

        require(
            re.fullmatch(r"\d+", text) is not None,
            f"{field_name} contains a nonnumeric game ID.",
        )

        normalized.append(text)

    require(
        len(normalized) == len(set(normalized)),
        f"{field_name} contains duplicate game IDs.",
    )

    return numeric_game_sort(normalized)


def repository_path(repo_root: Path, supplied_path: str) -> Path:
    path = Path(supplied_path)

    if not path.is_absolute():
        path = repo_root / path

    resolved = path.resolve()

    try:
        resolved.relative_to(repo_root)
    except ValueError as exc:
        raise DiscoveryFailure(
            f"Path is outside the repository: {supplied_path}"
        ) from exc

    return resolved


def repository_relative(repo_root: Path, path: Path) -> str:
    return path.resolve().relative_to(repo_root).as_posix()


def atomic_write_json(path: Path, value: Any) -> None:
    text = (
        json.dumps(
            value,
            ensure_ascii=True,
            indent=2,
        )
        + "\n"
    )

    path.parent.mkdir(parents=True, exist_ok=True)

    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=path.parent,
    )

    temporary_path = Path(temporary_name)

    try:
        with os.fdopen(
            descriptor,
            "w",
            encoding="utf-8",
            newline="\n",
        ) as output:
            output.write(text)
            output.flush()
            os.fsync(output.fileno())

        os.replace(temporary_path, path)
    finally:
        if temporary_path.exists():
            temporary_path.unlink()


def discover_game_ids(
    html_text: str,
    expected_league_id: str,
) -> tuple[list[str], list[str]]:
    pattern = re.compile(
        r"(?:https?://365\.strat-o-matic\.com)?"
        r"/game/(?P<league_id>\d+)/(?P<game_id>\d+)",
        re.IGNORECASE,
    )

    expected_game_ids: list[str] = []
    cross_league_links: list[str] = []

    for match in pattern.finditer(html_text):
        league_id = match.group("league_id")
        game_id = match.group("game_id")

        if league_id == expected_league_id:
            expected_game_ids.append(game_id)
        else:
            cross_league_links.append(
                f"{league_id}:{game_id}"
            )

    return (
        numeric_game_sort(expected_game_ids),
        sorted(set(cross_league_links)),
    )


def find_registry_team(
    registry: dict[str, Any],
    team_key: str,
) -> dict[str, Any]:
    teams = registry.get("teams")

    require(
        isinstance(teams, list),
        "Registry teams must be an array.",
    )

    matches = [
        team
        for team in teams
        if isinstance(team, dict)
        and str(team.get("teamKey")) == team_key
    ]

    require(
        len(matches) == 1,
        f"Registry must contain exactly one team for {team_key}.",
    )

    return matches[0]


def validate_metadata(
    *,
    repo_root: Path,
    fixture_path: Path,
    metadata_path: Path,
    metadata: dict[str, Any],
    registry_team: dict[str, Any],
    team_key: str,
    league_id: str,
    team_id: str,
    discovered_game_ids: list[str],
) -> None:
    validation = metadata.get("validation")

    require(
        isinstance(validation, dict),
        "Capture metadata validation must be an object.",
    )

    require(
        metadata.get("schemaVersion")
        == "strat365-nightly-schedule-capture-v0",
        "Unexpected schedule-capture schema version.",
    )
    require(
        metadata.get("artifactType")
        == "strat365-nightly-schedule-capture",
        "Unexpected schedule-capture artifact type.",
    )
    require(
        metadata.get("sourceFamily") == "teamSchedule",
        "Schedule source family must be teamSchedule.",
    )
    require(
        str(metadata.get("teamKey")) == team_key,
        "Capture metadata teamKey does not match.",
    )
    require(
        str(metadata.get("leagueId")) == league_id,
        "Capture metadata leagueId does not match.",
    )
    require(
        str(metadata.get("teamId")) == team_id,
        "Capture metadata teamId does not match.",
    )
    require(
        metadata.get("requestStatus") == "captured",
        "Capture metadata requestStatus must be captured.",
    )
    require(
        metadata.get("transportResult") == "PASS",
        "Capture metadata transportResult must be PASS.",
    )
    require(
        int(metadata.get("httpStatus")) == 200,
        "Capture metadata HTTP status must be 200.",
    )
    require(
        validation.get("sourceValidation") == "PASS",
        "Capture source validation must be PASS.",
    )
    require(
        validation.get("leagueRouteIdentity") is True,
        "Capture league-route identity must be true.",
    )
    require(
        int(validation.get("crossLeagueGameLinkCount")) == 0,
        "Capture contains cross-league game links.",
    )
    require(
        validation.get("spoilerSafeCapture") is True,
        "Capture is not marked spoiler-safe.",
    )
    require(
        str(metadata.get("requestedUrl"))
        == str(registry_team.get("scheduleUrl")),
        "Capture schedule URL does not match the registry.",
    )
    require(
        str(metadata.get("sha256")).upper()
        == sha256_file(fixture_path),
        "Capture body SHA-256 does not match metadata.",
    )
    require(
        repository_relative(repo_root, fixture_path)
        == str(metadata.get("rawResponsePath")),
        "Capture rawResponsePath does not match the fixture.",
    )
    require(
        repository_relative(repo_root, metadata_path)
        == str(metadata.get("metadataPath")),
        "Capture metadataPath does not match.",
    )

    metadata_game_ids = normalize_game_ids(
        validation.get("discoveredGameIds"),
        "metadata.validation.discoveredGameIds",
    )

    require(
        int(validation.get("uniqueGameCount"))
        == len(discovered_game_ids),
        "Capture uniqueGameCount does not match parsed game IDs.",
    )
    require(
        metadata_game_ids == discovered_game_ids,
        "Capture discoveredGameIds do not match parsed game IDs.",
    )


def validate_state_identity(
    state: dict[str, Any],
    *,
    team_key: str,
    league_id: str,
    team_id: str,
    schedule_url: str,
) -> None:
    require(
        str(state.get("teamKey")) == team_key,
        "State teamKey does not match.",
    )
    require(
        str(state.get("leagueId")) == league_id,
        "State leagueId does not match.",
    )
    require(
        str(state.get("teamId")) == team_id,
        "State teamId does not match.",
    )
    require(
        state.get("active") is True,
        "State team is not active.",
    )

    baseline = state.get("scheduleBaseline")
    discovery = state.get("discovery")
    capture = state.get("capture")
    spoiler = state.get("spoilerControl")
    audit = state.get("audit")

    require(
        isinstance(baseline, dict),
        "scheduleBaseline must be an object.",
    )
    require(
        isinstance(discovery, dict),
        "discovery must be an object.",
    )
    require(
        isinstance(capture, dict),
        "capture must be an object.",
    )
    require(
        isinstance(spoiler, dict),
        "spoilerControl must be an object.",
    )
    require(
        isinstance(audit, dict),
        "audit must be an object.",
    )

    require(
        baseline.get("status") == "READY",
        "Initial schedule baseline is not READY.",
    )
    require(
        str(baseline.get("scheduleUrl")) == schedule_url,
        "State schedule URL does not match the registry.",
    )
    require(
        spoiler.get("state") == "SEALED",
        "Discovery requires a sealed state.",
    )
    require(
        spoiler.get("automaticOutcomeDisclosure") is False,
        "Automatic outcome disclosure must remain disabled.",
    )
    require(
        spoiler.get("explicitGameUnlockRequired") is True,
        "Explicit game unlock must remain required.",
    )
    require(
        spoiler.get("unlockOneGameAtATime") is True,
        "One-game-at-a-time unlock must remain enabled.",
    )
    require(
        isinstance(state.get("stateRevision"), int)
        and int(state.get("stateRevision")) >= 1,
        "State revision must be at least 1.",
    )
    require(
        isinstance(audit.get("transitionHistory"), list),
        "audit.transitionHistory must be an array.",
    )
    require(
        int(audit.get("transitionCount"))
        == len(audit.get("transitionHistory")),
        "Audit transition count does not match history length.",
    )


def state_summary(
    state: dict[str, Any],
) -> dict[str, Any]:
    discovery = state["discovery"]
    capture = state["capture"]

    return {
        "stateRevision": int(state["stateRevision"]),
        "discoveryStatus": str(discovery["status"]),
        "knownGameCount": len(discovery["knownGameIds"]),
        "newlyDiscoveredGameCount": len(
            discovery["newlyDiscoveredGameIds"]
        ),
        "pendingCaptureGameCount": len(
            discovery["pendingCaptureGameIds"]
        ),
        "captureStatus": str(capture["status"]),
        "spoilerState": str(state["spoilerControl"]["state"]),
    }


def build_transition_entry(
    *,
    run_id: str,
    transitioned_at_utc: str,
    prior_state: dict[str, Any],
    next_state: dict[str, Any],
    new_game_ids: list[str],
    fixture_path: str,
    metadata_path: str,
    schedule_sha256: str,
) -> dict[str, Any]:
    return {
        "runId": run_id,
        "transitionedAtUtc": transitioned_at_utc,
        "action": "DISCOVER_NEW_GAMES",
        "priorState": state_summary(prior_state),
        "nextState": state_summary(next_state),
        "newlyDiscoveredGameIds": new_game_ids,
        "fixturePath": fixture_path,
        "metadataPath": metadata_path,
        "scheduleSha256": schedule_sha256,
    }


def build_proposed_state(
    *,
    current_state: dict[str, Any],
    current_schedule_game_ids: list[str],
    new_game_ids: list[str],
    run_id: str,
    checked_at_utc: str,
    fixture_relative: str,
    metadata_relative: str,
    schedule_sha256: str,
) -> dict[str, Any]:
    proposed = copy.deepcopy(current_state)

    discovery = proposed["discovery"]
    capture = proposed["capture"]
    audit = proposed["audit"]

    known_game_ids = normalize_game_ids(
        discovery.get("knownGameIds"),
        "discovery.knownGameIds",
    )
    pending_game_ids = normalize_game_ids(
        discovery.get("pendingCaptureGameIds"),
        "discovery.pendingCaptureGameIds",
    )

    next_known_game_ids = numeric_game_sort(
        known_game_ids + new_game_ids
    )
    next_pending_game_ids = numeric_game_sort(
        pending_game_ids + new_game_ids
    )

    proposed["stateRevision"] = int(
        current_state["stateRevision"]
    ) + 1

    discovery["status"] = "NEW_GAMES_DISCOVERED"
    discovery["knownGameIds"] = next_known_game_ids
    discovery["newlyDiscoveredGameIds"] = new_game_ids
    discovery["pendingCaptureGameIds"] = next_pending_game_ids
    discovery["lastCheckedAtUtc"] = checked_at_utc
    discovery["lastDiscoveredGameId"] = (
        numeric_game_sort(new_game_ids)[-1]
    )
    discovery["scheduleUnchanged"] = False

    if capture.get("status") in {"NOT_RUN", "COMPLETE"}:
        capture["status"] = "PENDING"

    audit["lastRunId"] = run_id
    audit["lastTransitionAction"] = "DISCOVER_NEW_GAMES"
    audit["lastTransitionAtUtc"] = checked_at_utc
    audit["transitionCount"] = int(
        audit["transitionCount"]
    ) + 1

    transition = build_transition_entry(
        run_id=run_id,
        transitioned_at_utc=checked_at_utc,
        prior_state=current_state,
        next_state=proposed,
        new_game_ids=new_game_ids,
        fixture_path=fixture_relative,
        metadata_path=metadata_relative,
        schedule_sha256=schedule_sha256,
    )

    audit["transitionHistory"] = (
        list(audit["transitionHistory"])
        + [transition]
    )

    require(
        audit["transitionCount"]
        == len(audit["transitionHistory"]),
        "Proposed audit transition count is invalid.",
    )
    require(
        discovery["knownGameIds"]
        == current_schedule_game_ids,
        "Proposed known-game IDs do not match the current schedule.",
    )
    require(
        set(discovery["newlyDiscoveredGameIds"]).issubset(
            set(discovery["knownGameIds"])
        ),
        "Newly discovered IDs are not a subset of known IDs.",
    )
    require(
        set(discovery["pendingCaptureGameIds"]).issubset(
            set(discovery["knownGameIds"])
        ),
        "Pending capture IDs are not a subset of known IDs.",
    )
    require(
        proposed["spoilerControl"]["state"] == "SEALED",
        "Proposed transition changed the spoiler state.",
    )

    return proposed


def find_forbidden_keys(value: Any) -> list[str]:
    matches: list[str] = []

    def visit(current: Any, path: str = "") -> None:
        if isinstance(current, dict):
            for key, child in current.items():
                child_path = f"{path}.{key}" if path else str(key)
                normalized = re.sub(r"[^a-z]", "", str(key).lower())

                if normalized in FORBIDDEN_OUTPUT_KEYS:
                    matches.append(child_path)

                visit(child, child_path)

        elif isinstance(current, list):
            for index, child in enumerate(current):
                visit(child, f"{path}[{index}]")

    visit(value)
    return matches


def discover_schedule_changes(
    *,
    repo_root: Path,
    team_key: str,
    fixture_path: Path,
    metadata_path: Path,
    run_id: str,
    apply: bool,
) -> dict[str, Any]:
    registry_path = (
        repo_root
        / "data/baseball/config/strat365/"
        / "strat365-active-team-registry-v0.json"
    )

    registry = load_json(registry_path)
    registry_team = find_registry_team(
        registry,
        team_key,
    )

    league_id = str(registry_team.get("leagueId"))
    team_id = str(registry_team.get("teamId"))
    schedule_url = str(registry_team.get("scheduleUrl"))

    require(
        team_key == f"{league_id}:{team_id}",
        "Registry teamKey is inconsistent with leagueId and teamId.",
    )

    state_path = (
        repo_root
        / "data/baseball/state/strat365/nightly"
        / league_id
        / team_id
        / "nightly-team-state-v0.json"
    )

    require(
        state_path.is_file(),
        "Nightly team state file is missing.",
    )
    require(
        fixture_path.is_file(),
        "Schedule fixture is missing.",
    )
    require(
        metadata_path.is_file(),
        "Schedule metadata is missing.",
    )

    state = load_json(state_path)
    metadata = load_json(metadata_path)
    html_text = fixture_path.read_text(
        encoding="utf-8",
        errors="strict",
    )

    current_schedule_game_ids, cross_league_links = (
        discover_game_ids(
            html_text,
            league_id,
        )
    )

    require(
        len(current_schedule_game_ids) > 0,
        "Current schedule contains no game IDs.",
    )
    require(
        len(cross_league_links) == 0,
        "Current schedule contains cross-league game links.",
    )

    validate_metadata(
        repo_root=repo_root,
        fixture_path=fixture_path,
        metadata_path=metadata_path,
        metadata=metadata,
        registry_team=registry_team,
        team_key=team_key,
        league_id=league_id,
        team_id=team_id,
        discovered_game_ids=current_schedule_game_ids,
    )

    validate_state_identity(
        state,
        team_key=team_key,
        league_id=league_id,
        team_id=team_id,
        schedule_url=schedule_url,
    )

    discovery = state["discovery"]

    known_game_ids = normalize_game_ids(
        discovery.get("knownGameIds"),
        "discovery.knownGameIds",
    )
    pending_capture_game_ids = normalize_game_ids(
        discovery.get("pendingCaptureGameIds"),
        "discovery.pendingCaptureGameIds",
    )

    baseline_game_ids = normalize_game_ids(
        state["scheduleBaseline"].get("historicalGameIds"),
        "scheduleBaseline.historicalGameIds",
    )

    require(
        set(baseline_game_ids).issubset(set(known_game_ids)),
        "Historical baseline IDs are not a subset of known IDs.",
    )
    require(
        set(pending_capture_game_ids).issubset(
            set(known_game_ids)
        ),
        "Pending capture IDs are not a subset of known IDs.",
    )

    missing_known_game_ids = numeric_game_sort(
        list(set(known_game_ids) - set(current_schedule_game_ids))
    )

    require(
        len(missing_known_game_ids) == 0,
        "Current schedule is missing previously known game IDs.",
    )

    new_game_ids = numeric_game_sort(
        list(set(current_schedule_game_ids) - set(known_game_ids))
    )

    schedule_unchanged = len(new_game_ids) == 0
    state_hash_before = sha256_file(state_path)
    checked_at_utc = utc_now_text()

    fixture_relative = repository_relative(
        repo_root,
        fixture_path,
    )
    metadata_relative = repository_relative(
        repo_root,
        metadata_path,
    )
    schedule_sha256 = sha256_file(fixture_path)

    proposed_state = state

    if new_game_ids:
        proposed_state = build_proposed_state(
            current_state=state,
            current_schedule_game_ids=current_schedule_game_ids,
            new_game_ids=new_game_ids,
            run_id=run_id,
            checked_at_utc=checked_at_utc,
            fixture_relative=fixture_relative,
            metadata_relative=metadata_relative,
            schedule_sha256=schedule_sha256,
        )

    state_write_count = 0

    if apply and new_game_ids:
        atomic_write_json(
            state_path,
            proposed_state,
        )
        state_write_count = 1

    state_hash_after = sha256_file(state_path)

    if not new_game_ids:
        require(
            state_hash_after == state_hash_before,
            "No-change discovery altered the state file.",
        )

    result = {
        "status": "PASS",
        "mode": "APPLY" if apply else "DRY_RUN",
        "teamKey": team_key,
        "leagueId": league_id,
        "teamId": team_id,
        "runId": run_id,
        "fixturePath": fixture_relative,
        "metadataPath": metadata_relative,
        "statePath": repository_relative(
            repo_root,
            state_path,
        ),
        "scheduleSha256": schedule_sha256,
        "currentScheduleGameCount": len(
            current_schedule_game_ids
        ),
        "knownGameCountBefore": len(known_game_ids),
        "knownGameCountProposed": len(
            proposed_state["discovery"]["knownGameIds"]
        ),
        "newlyDiscoveredGameCount": len(new_game_ids),
        "pendingCaptureGameCountBefore": len(
            pending_capture_game_ids
        ),
        "pendingCaptureGameCountProposed": len(
            proposed_state["discovery"]["pendingCaptureGameIds"]
        ),
        "currentStateRevision": int(state["stateRevision"]),
        "proposedStateRevision": int(
            proposed_state["stateRevision"]
        ),
        "scheduleUnchanged": schedule_unchanged,
        "stateWriteCount": state_write_count,
        "stateHashBefore": state_hash_before,
        "stateHashAfter": state_hash_after,
        "stateHashUnchanged": (
            state_hash_before == state_hash_after
        ),
        "crossLeagueGameLinkCount": len(
            cross_league_links
        ),
        "spoilerStatus": str(
            proposed_state["spoilerControl"]["state"]
        ),
        "outcomeFieldsPrinted": 0,
    }

    forbidden_output_keys = find_forbidden_keys(result)

    require(
        len(forbidden_output_keys) == 0,
        "Discovery result contains forbidden result-bearing keys.",
    )

    return result


def main() -> int:
    parser = argparse.ArgumentParser()

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
        "--metadata-path",
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
        repo_root = Path(args.repo_root).resolve()
        fixture_path = repository_path(
            repo_root,
            args.fixture_path,
        )
        metadata_path = repository_path(
            repo_root,
            args.metadata_path,
        )

        result = discover_schedule_changes(
            repo_root=repo_root,
            team_key=args.team_key,
            fixture_path=fixture_path,
            metadata_path=metadata_path,
            run_id=args.run_id,
            apply=args.apply,
        )

        print(
            json.dumps(
                result,
                ensure_ascii=True,
                separators=(",", ":"),
            )
        )

        return 0

    except DiscoveryFailure as exc:
        print(
            json.dumps(
                {
                    "status": "FAIL",
                    "failureDetail": str(exc),
                    "outcomeFieldsPrinted": 0,
                },
                ensure_ascii=True,
                separators=(",", ":"),
            )
        )

        return 1


if __name__ == "__main__":
    raise SystemExit(main())
