#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "bie.strat365.active-team-aggregate.v0"


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def walk_objects(value: Any):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from walk_objects(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk_objects(child)


def registry_team(
    registry: Any,
    *,
    team_id: str,
    league_id: str,
) -> dict[str, Any]:
    candidates: list[dict[str, Any]] = []

    for obj in walk_objects(registry):
        if str(obj.get("teamId", "")) != team_id:
            continue

        obj_league = str(obj.get("leagueId", ""))

        if obj_league and obj_league != league_id:
            continue

        candidates.append(obj)

    if not candidates:
        raise ValueError(
            f"Registry entry not found for league={league_id} team={team_id}"
        )

    exact = [
        item
        for item in candidates
        if str(item.get("leagueId", "")) == league_id
    ]

    return exact[0] if exact else candidates[0]


def parse_path_mapping(values: list[str]) -> dict[str, Path]:
    result: dict[str, Path] = {}

    for value in values:
        if "=" not in value:
            raise ValueError(
                f"Expected KEY=PATH mapping; received: {value}"
            )

        key, raw_path = value.split("=", 1)
        key = key.strip()
        raw_path = raw_path.strip()

        if not key or not raw_path:
            raise ValueError(
                f"Invalid KEY=PATH mapping: {value}"
            )

        result[key] = Path(raw_path).resolve()

    return result


def first_nonempty(*values: Any) -> Any:
    for value in values:
        if value not in (None, "", [], {}):
            return value
    return None


def iso_candidates(state: dict[str, Any]) -> list[str]:
    candidates = [
        state.get("scheduleBaseline", {}).get("capturedAtUtc"),
        state.get("discovery", {}).get("lastCheckedAtUtc"),
        state.get("capture", {}).get("completedAtUtc"),
        state.get("pregamePacket", {}).get("createdAtUtc"),
        state.get("leagueIntelligence", {}).get("capturedAtUtc"),
        state.get("leagueIntelligence", {}).get("releasedAtUtc"),
    ]

    return [
        str(value)
        for value in candidates
        if value
    ]


def find_team_payload(
    payload: Any,
    *,
    team_id: str,
) -> dict[str, Any] | None:
    for obj in walk_objects(payload):
        if str(obj.get("teamId", "")) == team_id:
            return obj

    return None


def recursive_first(
    payload: Any,
    names: list[str],
) -> Any:
    for obj in walk_objects(payload):
        for name in names:
            value = obj.get(name)
            if value not in (None, "", [], {}):
                return value

    return None


def build_position(
    *,
    state: dict[str, Any],
    team_id: str,
    league_intelligence_path: Path | None,
    preseason: bool,
) -> dict[str, Any]:
    lifecycle = state.get("leagueIntelligence", {})

    if preseason and league_intelligence_path is None:
        return {
            "status": "PRESEASON",
            "standing": None,
            "gamesBehind": None,
            "runDifferential": None,
            "sourceStatus": lifecycle.get("status"),
        }

    if league_intelligence_path is None:
        return {
            "status": "NOT_MATERIALIZED",
            "standing": None,
            "gamesBehind": None,
            "runDifferential": None,
            "sourceStatus": lifecycle.get("status"),
        }

    payload = read_json(league_intelligence_path)
    team = find_team_payload(payload, team_id=team_id)

    if team is None:
        raise ValueError(
            f"Team {team_id} not found in league intelligence "
            f"{league_intelligence_path}"
        )

    standings = team.get("standings", {})
    metrics = standings.get("metrics", standings)

    return {
        "status": "AVAILABLE",
        "standing": first_nonempty(
            standings.get("standing"),
            standings.get("position"),
            standings.get("rank"),
        ),
        "gamesBehind": first_nonempty(
            standings.get("gamesBehind"),
            metrics.get("gamesBehind"),
        ),
        "runDifferential": first_nonempty(
            standings.get("runDifferential"),
            metrics.get("runDifferential"),
        ),
        "wins": first_nonempty(
            standings.get("wins"),
            metrics.get("wins"),
        ),
        "losses": first_nonempty(
            standings.get("losses"),
            metrics.get("losses"),
        ),
        "sourceStatus": lifecycle.get("status"),
    }


def build_opposition(
    *,
    team_id: str,
    schedule_path: Path | None,
    league_intelligence_path: Path | None,
    preseason: bool,
) -> dict[str, Any]:
    if schedule_path is None:
        return {
            "status": (
                "PRESEASON_NOT_MATERIALIZED"
                if preseason
                else "NOT_MATERIALIZED"
            ),
            "opponentTeamId": None,
            "opponentTeamName": None,
            "opponentRecord": None,
            "opponentStanding": None,
            "opponentStandingStatus": "NOT_MATERIALIZED",
            "opponentGamesBehind": None,
            "opponentRunDifferential": None,
            "upcomingSeries": None,
        }

    schedule = read_json(schedule_path)

    subject_team_id = schedule.get("teamId")
    if (
        subject_team_id is not None
        and str(subject_team_id) != team_id
    ):
        raise ValueError(
            f"Schedule team mismatch: expected {team_id}, "
            f"found {subject_team_id}"
        )

    opponent_team_id = recursive_first(
        schedule,
        [
            "opponentTeamId",
            "nextOpponentTeamId",
        ],
    )

    if opponent_team_id is None:
        raise ValueError(
            f"Schedule contract lacks opponentTeamId: "
            f"{schedule_path}"
        )

    opponent_team_id = str(opponent_team_id)

    schedule_name = recursive_first(
        schedule,
        [
            "opponentTeamName",
            "opponentName",
            "nextOpponent",
        ],
    )

    if league_intelligence_path is None:
        return {
            "status": (
                "PRESEASON_IDENTITY_AVAILABLE"
                if preseason
                else "IDENTITY_AVAILABLE"
            ),
            "opponentTeamId": opponent_team_id,
            "opponentTeamName": schedule_name,
            "opponentRecord": None,
            "opponentStanding": None,
            "opponentStandingStatus": (
                "PRESEASON"
                if preseason
                else "NOT_MATERIALIZED"
            ),
            "opponentGamesBehind": None,
            "opponentRunDifferential": None,
            "upcomingSeries": schedule,
        }

    league_payload = read_json(
        league_intelligence_path
    )

    opponent = find_team_payload(
        league_payload,
        team_id=opponent_team_id,
    )

    if opponent is None:
        raise ValueError(
            f"Opponent {opponent_team_id} not found in "
            f"{league_intelligence_path}"
        )

    standings = opponent.get("standings", {})
    metrics = standings.get("metrics", standings)

    wins = first_nonempty(
        standings.get("wins"),
        metrics.get("wins"),
    )
    losses = first_nonempty(
        standings.get("losses"),
        metrics.get("losses"),
    )

    games_behind = first_nonempty(
        standings.get("gamesBehind"),
        metrics.get("gamesBehind"),
    )

    run_differential = first_nonempty(
        standings.get("runDifferential"),
        metrics.get("runDifferential"),
    )

    standing = first_nonempty(
        standings.get("standing"),
        standings.get("position"),
        standings.get("rank"),
    )

    if wins is None or losses is None:
        raise ValueError(
            f"Opponent {opponent_team_id} lacks record evidence"
        )

    if games_behind is None:
        raise ValueError(
            f"Opponent {opponent_team_id} lacks games-behind evidence"
        )

    if run_differential is None:
        raise ValueError(
            f"Opponent {opponent_team_id} lacks run-differential evidence"
        )

    return {
        "status": "AVAILABLE",
        "opponentTeamId": opponent_team_id,
        "opponentTeamName": first_nonempty(
            opponent.get("teamName"),
            schedule_name,
        ),
        "opponentRecord": f"{wins}-{losses}",
        "opponentStanding": standing,
        "opponentStandingStatus": (
            "AVAILABLE"
            if standing is not None
            else "NOT_EXPOSED_BY_NORMALIZER"
        ),
        "opponentGamesBehind": games_behind,
        "opponentRunDifferential": run_differential,
        "upcomingSeries": schedule,
    }


def build_series_intelligence(
    *,
    team_id: str,
    series_engine_path: Path | None,
    preseason: bool,
) -> dict[str, Any]:
    if series_engine_path is None:
        return {
            "status": (
                "PRESEASON_NOT_MATERIALIZED"
                if preseason
                else "NOT_MATERIALIZED"
            ),
            "upcomingSeries": None,
            "recentTeamSignals": None,
            "leagueContext": None,
            "matchupAssessment": None,
            "managerialWatchlist": None,
            "managerRecommendations": None,
            "evidenceGates": {
                "probableStarters": "EVIDENCE_GATED",
                "likelyLineup": "EVIDENCE_GATED",
                "rosterCards": "EVIDENCE_GATED",
                "bullpenAvailability": "EVIDENCE_GATED",
            },
        }

    payload = read_json(series_engine_path)

    payload_team_id = first_nonempty(
        payload.get("teamId"),
        payload.get("subjectTeamId"),
    )

    if payload_team_id and str(payload_team_id) != team_id:
        raise ValueError(
            f"Series Engine team mismatch: expected {team_id}, "
            f"found {payload_team_id}"
        )

    return {
        "status": payload.get("status", "AVAILABLE"),
        "upcomingSeries": payload.get("upcomingSeries"),
        "recentTeamSignals": payload.get("recentTeamSignals"),
        "leagueContext": payload.get("leagueContext"),
        "matchupAssessment": payload.get("matchupAssessment"),
        "managerialWatchlist": payload.get("managerialWatchlist"),
        "managerRecommendations": payload.get("managerRecommendations"),
        "evidenceGates": {
            "probableStarters": (
                "AVAILABLE"
                if payload.get("probableStarters")
                else "EVIDENCE_GATED"
            ),
            "likelyLineup": (
                "AVAILABLE"
                if payload.get("likelyLineup")
                else "EVIDENCE_GATED"
            ),
            "rosterCards": "SOURCE_DEPENDENT",
            "bullpenAvailability": "SOURCE_DEPENDENT",
        },
    }


def build_team(
    *,
    registry: Any,
    state_path: Path,
    league_intelligence_paths: dict[str, Path],
    series_engine_paths: dict[str, Path],
    schedule_paths: dict[str, Path],
) -> tuple[dict[str, Any], list[str]]:
    state = read_json(state_path)

    team_id = str(state.get("teamId", ""))
    league_id = str(state.get("leagueId", ""))

    if not team_id or not league_id:
        raise ValueError(
            f"State lacks teamId/leagueId: {state_path}"
        )

    registry_entry = registry_team(
        registry,
        team_id=team_id,
        league_id=league_id,
    )

    schedule = state.get("scheduleBaseline", {})
    discovery = state.get("discovery", {})
    capture = state.get("capture", {})
    pregame = state.get("pregamePacket", {})
    series = state.get("series", {})
    league_intel = state.get("leagueIntelligence", {})

    known_game_ids = discovery.get("knownGameIds") or []
    pending_game_ids = discovery.get("pendingCaptureGameIds") or []

    preseason = len(known_game_ids) == 0
    phase = "PRESEASON" if preseason else "ACTIVE_SEASON"

    league_path = league_intelligence_paths.get(league_id)
    series_path = series_engine_paths.get(team_id)
    schedule_path = schedule_paths.get(team_id)

    position = build_position(
        state=state,
        team_id=team_id,
        league_intelligence_path=league_path,
        preseason=preseason,
    )

    series_intelligence = build_series_intelligence(
        team_id=team_id,
        series_engine_path=series_path,
        preseason=preseason,
    )

    opposition = build_opposition(
        team_id=team_id,
        schedule_path=schedule_path,
        league_intelligence_path=league_path,
        preseason=preseason,
    )

    review_status = series.get("wrapupStatus") or "UNKNOWN"

    team = {
        "identity": {
            "teamId": team_id,
            "leagueId": league_id,
            "teamName": first_nonempty(
                registry_entry.get("teamName"),
                registry_entry.get("name"),
            ),
            "season": first_nonempty(
                registry_entry.get("season"),
                registry_entry.get("seasonYear"),
                registry_entry.get("playerSetYear"),
            ),
            "active": registry_entry.get("active"),
        },
        "phase": phase,
        "lifecycle": {
            "scheduleBaselineStatus": schedule.get("status"),
            "historicalGameCount": len(
                schedule.get("historicalGameIds") or []
            ),
            "knownGameCount": len(known_game_ids),
            "pendingCaptureGameCount": len(pending_game_ids),
            "lastDiscoveredGameId": discovery.get(
                "lastDiscoveredGameId"
            ),
            "discoveryStatus": discovery.get("status"),
            "captureStatus": capture.get("status"),
            "pregamePacketStatus": pregame.get("status"),
            "seriesStatus": series.get("status"),
            "wrapupStatus": review_status,
            "leagueIntelligenceStatus": league_intel.get("status"),
        },
        "position": position,
        "opposition": opposition,
        "keyPlayerSignals": {
            "status": (
                "AVAILABLE"
                if series_intelligence.get("recentTeamSignals")
                else (
                    "PRESEASON"
                    if preseason
                    else "NOT_MATERIALIZED"
                )
            ),
            "signals": series_intelligence.get(
                "recentTeamSignals"
            ),
        },
        "seriesPreparation": series_intelligence,
        "seriesReview": {
            "status": review_status,
            "artifactPath": series.get("wrapupArtifactPath"),
            "reviewedGameIds": series.get("reviewedGameIds") or [],
        },
        "sources": {
            "nightlyState": str(state_path),
            "leagueIntelligence": (
                str(league_path)
                if league_path
                else None
            ),
            "seriesEngine": (
                str(series_path)
                if series_path
                else None
            ),
            "scheduleContract": (
                str(schedule_path)
                if schedule_path
                else None
            ),
        },
    }

    return team, iso_candidates(state)


def main() -> int:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--registry",
        type=Path,
        required=True,
    )

    parser.add_argument(
        "--state",
        type=Path,
        action="append",
        required=True,
    )

    parser.add_argument(
        "--league-intelligence",
        action="append",
        default=[],
        metavar="LEAGUE_ID=PATH",
    )

    parser.add_argument(
        "--series-engine",
        action="append",
        default=[],
        metavar="TEAM_ID=PATH",
    )

    parser.add_argument(
        "--schedule",
        action="append",
        default=[],
        metavar="TEAM_ID=PATH",
    )

    parser.add_argument(
        "--output",
        type=Path,
        required=True,
    )

    args = parser.parse_args()

    registry_path = args.registry.resolve()
    registry = read_json(registry_path)

    league_paths = parse_path_mapping(
        args.league_intelligence
    )
    series_paths = parse_path_mapping(
        args.series_engine
    )
    schedule_paths = parse_path_mapping(
        args.schedule
    )

    teams: list[dict[str, Any]] = []
    freshness_values: list[str] = []

    seen: set[tuple[str, str]] = set()

    for raw_state_path in args.state:
        state_path = raw_state_path.resolve()

        team, freshness = build_team(
            registry=registry,
            state_path=state_path,
            league_intelligence_paths=league_paths,
            series_engine_paths=series_paths,
            schedule_paths=schedule_paths,
        )

        identity = team["identity"]
        key = (
            str(identity["leagueId"]),
            str(identity["teamId"]),
        )

        if key in seen:
            raise ValueError(
                f"Duplicate active team state: {key}"
            )

        seen.add(key)
        teams.append(team)
        freshness_values.extend(freshness)

    teams.sort(
        key=lambda item: (
            str(item["identity"]["leagueId"]),
            str(item["identity"]["teamId"]),
        )
    )

    generated_at = (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )

    output = {
        "schemaVersion": SCHEMA_VERSION,
        "generatedAtUtc": generated_at,
        "freshness": {
            "scope": "PAGE_LEVEL",
            "latestSourceTimestampUtc": (
                max(freshness_values)
                if freshness_values
                else None
            ),
            "perCardSnapshotRequired": False,
        },
        "teamCount": len(teams),
        "teams": teams,
    }

    write_json(
        args.output.resolve(),
        output,
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())