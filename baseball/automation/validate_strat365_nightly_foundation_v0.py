#!/usr/bin/env python3
"""Validate the Strat365 spoiler-safe nightly automation foundation."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
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

STATE_ROOT_RELATIVE = Path(
    "data/baseball/state/strat365/nightly"
)

RESULT_BEARING_KEYS = {
    "score",
    "scores",
    "winner",
    "winnerTeam",
    "loser",
    "loserTeam",
    "homeRuns",
    "awayRuns",
    "lineScore",
    "result",
    "resultText",
    "seriesOutcome",
    "updatedRecord",
    "decisivePlay",
}


class ValidationFailure(Exception):
    """Raised when a nightly-foundation invariant fails."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)

    return digest.hexdigest().upper()


def has_utf8_bom(path: Path) -> bool:
    with path.open("rb") as handle:
        return handle.read(3) == b"\xef\xbb\xbf"


def load_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ValidationFailure(f"Required JSON file is missing: {path}")

    if has_utf8_bom(path):
        raise ValidationFailure(f"UTF-8 BOM is prohibited: {path}")

    try:
        with path.open("r", encoding="utf-8") as handle:
            value = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        raise ValidationFailure(
            f"Unable to parse JSON file {path}: {exc}"
        ) from exc

    if not isinstance(value, dict):
        raise ValidationFailure(
            f"Expected a JSON object at the root of {path}"
        )

    return value


def require(
    condition: bool,
    message: str,
) -> None:
    if not condition:
        raise ValidationFailure(message)


def require_string_list(
    value: Any,
    field_path: str,
) -> list[str]:
    require(
        isinstance(value, list),
        f"{field_path} must be an array.",
    )

    require(
        all(isinstance(item, str) for item in value),
        f"{field_path} must contain strings only.",
    )

    require(
        len(value) == len(set(value)),
        f"{field_path} contains duplicate values.",
    )

    return list(value)


def find_result_bearing_fields(
    node: Any,
    path: str = "$",
) -> list[str]:
    matches: list[str] = []

    if isinstance(node, dict):
        for key, value in node.items():
            child_path = f"{path}.{key}"

            if key in RESULT_BEARING_KEYS:
                matches.append(child_path)

            matches.extend(
                find_result_bearing_fields(
                    value,
                    child_path,
                )
            )

    elif isinstance(node, list):
        for index, value in enumerate(node):
            matches.extend(
                find_result_bearing_fields(
                    value,
                    f"{path}[{index}]",
                )
            )

    return matches


def allowed_values(
    contract: dict[str, Any],
    key: str,
) -> set[str]:
    allowed = contract.get("allowedValues", {}).get(key)

    require(
        isinstance(allowed, list) and allowed,
        f"Contract allowedValues.{key} is missing or invalid.",
    )

    require(
        all(isinstance(item, str) for item in allowed),
        f"Contract allowedValues.{key} must contain strings.",
    )

    return set(allowed)


def validate_state(
    *,
    repo_root: Path,
    registry_team: dict[str, Any],
    contract: dict[str, Any],
    required_properties: set[str],
) -> dict[str, Any]:
    league_id = str(registry_team.get("leagueId", ""))
    team_id = str(registry_team.get("teamId", ""))
    team_key = str(registry_team.get("teamKey", ""))

    state_relative = (
        STATE_ROOT_RELATIVE
        / league_id
        / team_id
        / "nightly-team-state-v0.json"
    )

    state_path = repo_root / state_relative
    state = load_json(state_path)

    actual_properties = set(state.keys())

    require(
        actual_properties == required_properties,
        (
            f"Top-level state properties do not match the contract "
            f"for {team_key}. Missing="
            f"{sorted(required_properties - actual_properties)}; "
            f"Additional="
            f"{sorted(actual_properties - required_properties)}"
        ),
    )

    require(
        state.get("schemaVersion")
        == contract.get("stateSchemaVersion"),
        f"State schema version mismatch for {team_key}.",
    )

    identity_fields = (
        "teamKey",
        "leagueId",
        "teamId",
        "teamName",
        "strategyProfile",
        "active",
    )

    for field_name in identity_fields:
        require(
            state.get(field_name)
            == registry_team.get(field_name),
            (
                f"Registry/state identity mismatch for "
                f"{team_key}: {field_name}"
            ),
        )

    state_revision = state.get("stateRevision")

    require(
        isinstance(state_revision, int)
        and not isinstance(state_revision, bool)
        and state_revision >= 0,
        f"Invalid stateRevision for {team_key}.",
    )

    baseline = state.get("scheduleBaseline")
    discovery = state.get("discovery")
    capture = state.get("capture")
    pregame = state.get("pregamePacket")
    series = state.get("series")
    intelligence = state.get("leagueIntelligence")
    spoiler = state.get("spoilerControl")
    audit = state.get("audit")
    validation = state.get("validation")
    cutover = state.get("cutover")

    for name, value in (
        ("cutover", cutover),
        ("scheduleBaseline", baseline),
        ("discovery", discovery),
        ("capture", capture),
        ("pregamePacket", pregame),
        ("series", series),
        ("leagueIntelligence", intelligence),
        ("spoilerControl", spoiler),
        ("audit", audit),
        ("validation", validation),
    ):
        require(
            isinstance(value, dict),
            f"{name} must be an object for {team_key}.",
        )

    require(
        baseline.get("status")
        in allowed_values(
            contract,
            "scheduleBaselineStatus",
        ),
        f"Invalid baseline status for {team_key}.",
    )

    require(
        discovery.get("status")
        in allowed_values(
            contract,
            "discoveryStatus",
        ),
        f"Invalid discovery status for {team_key}.",
    )

    require(
        capture.get("status")
        in allowed_values(
            contract,
            "captureStatus",
        ),
        f"Invalid capture status for {team_key}.",
    )

    require(
        pregame.get("status")
        in allowed_values(
            contract,
            "pregamePacketStatus",
        ),
        f"Invalid pregame-packet status for {team_key}.",
    )

    require(
        series.get("status")
        in allowed_values(
            contract,
            "seriesStatus",
        ),
        f"Invalid series status for {team_key}.",
    )

    require(
        series.get("wrapupStatus")
        in allowed_values(
            contract,
            "wrapupStatus",
        ),
        f"Invalid series-wrapup status for {team_key}.",
    )

    require(
        intelligence.get("status")
        in allowed_values(
            contract,
            "leagueIntelligenceStatus",
        ),
        f"Invalid league-intelligence status for {team_key}.",
    )

    require(
        spoiler.get("state")
        in allowed_values(
            contract,
            "spoilerState",
        ),
        f"Invalid spoiler state for {team_key}.",
    )

    historical_game_ids = require_string_list(
        baseline.get("historicalGameIds"),
        f"{team_key}.scheduleBaseline.historicalGameIds",
    )

    known_game_ids = require_string_list(
        discovery.get("knownGameIds"),
        f"{team_key}.discovery.knownGameIds",
    )

    newly_discovered_game_ids = require_string_list(
        discovery.get("newlyDiscoveredGameIds"),
        f"{team_key}.discovery.newlyDiscoveredGameIds",
    )

    pending_capture_game_ids = require_string_list(
        discovery.get("pendingCaptureGameIds"),
        f"{team_key}.discovery.pendingCaptureGameIds",
    )

    captured_game_ids = require_string_list(
        capture.get("capturedGameIds"),
        f"{team_key}.capture.capturedGameIds",
    )

    failed_game_ids = require_string_list(
        capture.get("failedGameIds"),
        f"{team_key}.capture.failedGameIds",
    )

    series_game_ids = require_string_list(
        series.get("gameIds"),
        f"{team_key}.series.gameIds",
    )

    unlocked_game_ids = require_string_list(
        series.get("unlockedGameIds"),
        f"{team_key}.series.unlockedGameIds",
    )

    reviewed_game_ids = require_string_list(
        series.get("reviewedGameIds"),
        f"{team_key}.series.reviewedGameIds",
    )

    require(
        baseline.get("historicalGameCount")
        == len(historical_game_ids),
        f"Historical game count mismatch for {team_key}.",
    )

    require(
        set(newly_discovered_game_ids)
        <= set(known_game_ids),
        f"Newly discovered games must be known for {team_key}.",
    )

    require(
        set(pending_capture_game_ids)
        <= set(newly_discovered_game_ids),
        f"Pending captures must be newly discovered for {team_key}.",
    )

    require(
        set(captured_game_ids)
        <= set(known_game_ids),
        f"Captured games must be known for {team_key}.",
    )

    require(
        set(failed_game_ids)
        <= set(known_game_ids),
        f"Failed games must be known for {team_key}.",
    )

    require(
        set(unlocked_game_ids)
        <= set(series_game_ids),
        f"Unlocked games must belong to the series for {team_key}.",
    )

    require(
        set(reviewed_game_ids)
        <= set(unlocked_game_ids),
        f"Reviewed games must already be unlocked for {team_key}.",
    )

    require(
        spoiler.get("automaticOutcomeDisclosure") is False,
        f"Automatic outcome disclosure must remain disabled for {team_key}.",
    )

    require(
        spoiler.get("explicitGameUnlockRequired") is True,
        f"Explicit game unlock must remain required for {team_key}.",
    )

    require(
        spoiler.get("unlockOneGameAtATime") is True,
        f"One-game-at-a-time unlock must remain enabled for {team_key}.",
    )

    require(
        spoiler.get("seriesWrapupRequiresAllGamesReviewed") is True,
        f"Series wrapup must require all games reviewed for {team_key}.",
    )

    require(
        spoiler.get("leagueIntelligenceRemainsSealedDuringReplay")
        is True,
        f"League intelligence must remain sealed during replay for {team_key}.",
    )

    result_fields = find_result_bearing_fields(state)

    require(
        not result_fields,
        (
            f"Result-bearing fields are prohibited in operational state "
            f"for {team_key}: {result_fields}"
        ),
    )

    if baseline.get("status") == "PENDING_INITIAL_SCHEDULE_BASELINE":
        require(
            state_revision == 0,
            f"Pending initial baseline must have revision 0 for {team_key}.",
        )

        require(
            cutover.get("mode")
            == "BASELINE_ALL_EXISTING_GAMES_AS_HISTORICAL",
            f"Invalid cutover mode for {team_key}.",
        )

        require(
            cutover.get("userReplayStatus")
            == "CAUGHT_UP_BEFORE_AUTOMATION",
            f"Invalid cutover replay status for {team_key}.",
        )

        require(
            discovery.get("status") == "NOT_RUN",
            f"Discovery must not run before baseline for {team_key}.",
        )

        require(
            capture.get("status") == "NOT_RUN",
            f"Capture must not run before baseline for {team_key}.",
        )

        require(
            series.get("status") == "NO_ACTIVE_SERIES",
            f"No series may be active before baseline for {team_key}.",
        )

        require(
            series.get("wrapupStatus") == "NOT_ELIGIBLE",
            f"Wrapup must be ineligible before baseline for {team_key}.",
        )

        require(
            spoiler.get("state") == "SEALED",
            f"Initial spoiler state must be SEALED for {team_key}.",
        )

        require(
            pregame.get("sealed") is True,
            f"Initial pregame state must remain sealed for {team_key}.",
        )

        require(
            intelligence.get("sealed") is True,
            f"Initial league intelligence must remain sealed for {team_key}.",
        )

        require(
            not any(
                (
                    historical_game_ids,
                    known_game_ids,
                    newly_discovered_game_ids,
                    pending_capture_game_ids,
                    captured_game_ids,
                    failed_game_ids,
                    series_game_ids,
                    unlocked_game_ids,
                    reviewed_game_ids,
                )
            ),
            f"All game arrays must be empty before baseline for {team_key}.",
        )

    require(
        validation.get("registryTeamIdentityMatch") is True,
        f"Registry identity validation is not PASS for {team_key}.",
    )

    require(
        validation.get("gameResultsStoredInState") is False,
        f"State must declare that game results are excluded for {team_key}.",
    )

    require(
        validation.get("status") == "PASS",
        f"State validation marker is not PASS for {team_key}.",
    )

    return {
        "teamKey": team_key,
        "statePath": state_relative.as_posix(),
        "strategyProfile": state["strategyProfile"],
        "baselineStatus": baseline["status"],
        "spoilerState": spoiler["state"],
        "stateRevision": state_revision,
        "knownGameCount": len(known_game_ids),
        "resultBearingFieldCount": len(result_fields),
        "sha256": sha256_file(state_path),
    }


def validate_foundation(repo_root: Path) -> dict[str, Any]:
    registry_path = repo_root / REGISTRY_RELATIVE
    contract_path = repo_root / CONTRACT_RELATIVE

    registry = load_json(registry_path)
    contract = load_json(contract_path)

    require(
        registry.get("schemaVersion")
        == "strat365-active-team-registry-v0",
        "Unexpected active-team registry schema version.",
    )

    require(
        contract.get("schemaVersion")
        == "strat365-nightly-team-state-contract-v0",
        "Unexpected nightly-state contract schema version.",
    )

    active_teams = [
        team
        for team in registry.get("teams", [])
        if isinstance(team, dict)
        and team.get("active") is True
    ]

    expected_active_count = (
        contract.get("validation", {})
        .get("activeTeamCountExpected")
    )

    require(
        len(active_teams) == expected_active_count,
        (
            "Active-team count does not match the contract: "
            f"expected {expected_active_count}; "
            f"found {len(active_teams)}."
        ),
    )

    team_keys = [
        str(team.get("teamKey", ""))
        for team in active_teams
    ]

    league_ids = [
        str(team.get("leagueId", ""))
        for team in active_teams
    ]

    team_ids = [
        str(team.get("teamId", ""))
        for team in active_teams
    ]

    strategy_profiles = [
        str(team.get("strategyProfile", ""))
        for team in active_teams
    ]

    require(
        len(team_keys) == len(set(team_keys)),
        "Active team keys are not unique.",
    )

    require(
        len(league_ids) == len(set(league_ids)),
        "Active league IDs are not unique.",
    )

    require(
        len(team_ids) == len(set(team_ids)),
        "Active team IDs are not unique.",
    )

    require(
        len(strategy_profiles)
        == len(set(strategy_profiles)),
        "Active strategy profiles are not unique.",
    )

    required_property_list = require_string_list(
        contract.get("requiredTopLevelProperties"),
        "contract.requiredTopLevelProperties",
    )

    required_properties = set(required_property_list)

    require(
        len(required_properties) == 19,
        "Contract must define exactly 19 required state properties.",
    )

    require(
        contract.get("storagePolicy", {})
        .get("gameResultsExcludedFromState")
        is True,
        "Contract must exclude game results from state.",
    )

    require(
        contract.get("thirdTeamPolicy", {})
        .get("pipelineCodeChangeRequired")
        is False,
        "Third-team policy must remain configuration-driven.",
    )

    state_results = [
        validate_state(
            repo_root=repo_root,
            registry_team=team,
            contract=contract,
            required_properties=required_properties,
        )
        for team in active_teams
    ]

    return {
        "status": "PASS",
        "registryPath": REGISTRY_RELATIVE.as_posix(),
        "contractPath": CONTRACT_RELATIVE.as_posix(),
        "registryTeamCount": len(registry.get("teams", [])),
        "activeTeamCount": len(active_teams),
        "validatedStateCount": len(state_results),
        "uniqueLeagueCount": len(set(league_ids)),
        "uniqueTeamCount": len(set(team_ids)),
        "uniqueStrategyProfileCount": len(
            set(strategy_profiles)
        ),
        "pendingBaselineCount": sum(
            item["baselineStatus"]
            == "PENDING_INITIAL_SCHEDULE_BASELINE"
            for item in state_results
        ),
        "sealedStateCount": sum(
            item["spoilerState"] == "SEALED"
            for item in state_results
        ),
        "resultBearingFieldCount": sum(
            item["resultBearingFieldCount"]
            for item in state_results
        ),
        "utf8WithoutBomFileCount": 2 + len(state_results),
        "registrySha256": sha256_file(registry_path),
        "contractSha256": sha256_file(contract_path),
        "states": state_results,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Validate the Strat365 nightly registry, "
            "contract, and team states."
        )
    )

    parser.add_argument(
        "--repo-root",
        required=True,
        help="Repository root directory.",
    )

    args = parser.parse_args()

    try:
        result = validate_foundation(
            Path(args.repo_root).resolve()
        )
    except ValidationFailure as exc:
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
