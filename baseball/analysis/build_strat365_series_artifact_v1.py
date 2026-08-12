#!/usr/bin/env python3

from __future__ import annotations

import argparse
import copy
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "bie.strat365.series-artifact.v1"


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8-sig") as handle:
        payload = json.load(handle)

    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object: {path}")

    return payload


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(
            payload,
            handle,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        handle.write("\n")


def build_series_id(
    *,
    league_id: str,
    team_id: str,
    game_numbers: list[Any],
) -> str:
    if not game_numbers:
        raise ValueError("scheduleGameNumbers is required")

    normalized = [str(value) for value in game_numbers]

    return (
        f"league-{league_id}-"
        f"team-{team_id}-games-"
        + "-".join(normalized)
    )


def source_paths(engine: dict[str, Any]) -> dict[str, str | None]:
    evidence = engine.get("sourceEvidence")

    if not isinstance(evidence, dict):
        evidence = {}

    return {
        key: (
            str(value)
            if value not in (None, "")
            else None
        )
        for key, value in evidence.items()
    }


def resolve_team_identity(
    *,
    engine: dict[str, Any],
) -> tuple[str, str]:
    team = engine.get("team")

    if not isinstance(team, dict):
        raise ValueError("Series Engine team object is missing")

    league_id = str(team.get("leagueId") or "").strip()

    if not league_id:
        raise ValueError("leagueId is missing")

    direct_candidates = [
        team.get("teamId"),
        engine.get("teamId"),
        engine.get("subjectTeamId"),
    ]

    player_intelligence = engine.get("playerIntelligence")

    if isinstance(player_intelligence, dict):
        player_team = player_intelligence.get("team")

        if isinstance(player_team, dict):
            direct_candidates.append(player_team.get("teamId"))

    for candidate in direct_candidates:
        value = str(candidate or "").strip()

        if value:
            return league_id, value

    source_evidence = engine.get("sourceEvidence")

    if not isinstance(source_evidence, dict):
        source_evidence = {}

    readiness_source = source_evidence.get("teamReadiness")

    if not readiness_source:
        raise ValueError(
            "teamId is missing and no teamReadiness source is available"
        )

    readiness_path = Path(str(readiness_source))

    if not readiness_path.exists():
        raise ValueError(
            f"teamReadiness source does not exist: {readiness_path}"
        )

    readiness = read_json(readiness_path)

    readiness_league_id = str(
        readiness.get("leagueId") or ""
    ).strip()

    if (
        readiness_league_id
        and readiness_league_id != league_id
    ):
        raise ValueError(
            "teamReadiness leagueId does not match Series Engine leagueId"
        )

    team_id = str(readiness.get("teamId") or "").strip()

    if not team_id:
        raise ValueError(
            "teamReadiness source does not contain teamId"
        )

    return league_id, team_id


def build_artifact(
    *,
    engine: dict[str, Any],
    engine_path: Path,
    snapshot_mode: str,
    generated_at_utc: str,
) -> dict[str, Any]:
    team = engine.get("team")

    if not isinstance(team, dict):
        raise ValueError("Series Engine team object is missing")

    upcoming = engine.get("upcomingSeries")

    if not isinstance(upcoming, dict):
        raise ValueError(
            "Series Engine upcomingSeries object is missing"
        )

    league_id, team_id = resolve_team_identity(
        engine=engine,
    )

    game_numbers = upcoming.get("scheduleGameNumbers")

    if not isinstance(game_numbers, list) or not game_numbers:
        raise ValueError(
            "upcomingSeries.scheduleGameNumbers is missing"
        )

    series_id = build_series_id(
        league_id=league_id,
        team_id=team_id,
        game_numbers=game_numbers,
    )

    identity = {
        "seriesId": series_id,
        "leagueId": league_id,
        "teamId": team_id,
        "opponentTeamId": upcoming.get("opponentTeamId"),
        "opponentDisplayName": (
            engine.get("playerIntelligence", {})
            .get("opponent", {})
            .get("teamName")
            if isinstance(
                engine.get("playerIntelligence"),
                dict,
            )
            else None
        ) or upcoming.get("opponentDisplayName"),
        "scheduleGameNumbers": copy.deepcopy(game_numbers),
        "scheduledDate": upcoming.get("scheduledDate"),
        "homeAway": upcoming.get("homeAway"),
        "gameCount": upcoming.get("gameCount"),
    }

    provenance = {
        "seriesEngine": str(engine_path),
        "seriesEngineSchema": engine.get("schema"),
        "sourceEvidence": source_paths(engine),
    }

    if snapshot_mode == "certified-pre-series":
        pre_series_snapshot = {
            "status": "AVAILABLE",
            "snapshotClassification": (
                "IMMUTABLE_PRE_SERIES"
            ),
            "certifiedPreSeries": True,
            "frozenAtUtc": generated_at_utc,
            "payload": copy.deepcopy(engine),
            "missingEvidence": [],
            "provenance": copy.deepcopy(provenance),
        }

        lifecycle = {
            "stage": "PRE_SERIES",
            "previewAvailable": True,
            "replayAvailable": False,
            "completedGameCount": 0,
            "reviewAvailable": False,
            "learningAvailable": False,
        }

    elif snapshot_mode == "historical-reconstructed":
        pre_series_snapshot = {
            "status": "PARTIAL",
            "snapshotClassification": (
                "HISTORICAL_RECONSTRUCTION_NOT_CERTIFIED"
            ),
            "certifiedPreSeries": False,
            "frozenAtUtc": None,
            "payload": None,
            "missingEvidence": [
                (
                    "complete immutable pre-series Series Preview "
                    "snapshot"
                ),
                (
                    "preserved pre-series provenance for "
                    "hitting-streak/player-intelligence evidence"
                ),
            ],
            "reconstructionEvidence": {
                "leagueContext": copy.deepcopy(
                    engine.get("leagueContext")
                ),
                "matchupAssessment": copy.deepcopy(
                    engine.get("matchupAssessment")
                ),
                "sampleGovernance": copy.deepcopy(
                    engine.get("sampleGovernance")
                ),
            },
            "provenance": copy.deepcopy(provenance),
            "warning": (
                "Core evidence predates the scheduled series, "
                "but the complete current Series Engine payload "
                "cannot be certified as the view BIE possessed "
                "before Game 1. It must not be used as an "
                "immutable historical preview."
            ),
        }

        lifecycle = {
            "stage": "POST_SCHEDULED_DATE_CAPTURE_STATE_UNKNOWN",
            "previewAvailable": False,
            "replayAvailable": False,
            "completedGameCount": None,
            "reviewAvailable": False,
            "learningAvailable": False,
        }

    else:
        raise ValueError(
            f"Unsupported snapshot mode: {snapshot_mode}"
        )

    replay = {
        "status": "NOT_CAPTURED",
        "games": [
            {
                "ordinal": index + 1,
                "scheduleGameNumber": game_number,
                "gameId": None,
                "evidenceStatus": "NOT_CAPTURED",
            }
            for index, game_number in enumerate(game_numbers)
        ],
    }

    return {
        "schemaVersion": SCHEMA_VERSION,
        "generatedAtUtc": generated_at_utc,
        "seriesIdentity": identity,
        "lifecycle": lifecycle,
        "preSeriesSnapshot": pre_series_snapshot,
        "replay": replay,
        "review": {
            "status": "NOT_CAPTURED",
            "artifact": None,
        },
        "learning": {
            "status": "NOT_CAPTURED",
            "artifact": None,
        },
        "evidence": {
            "status": (
                "AVAILABLE"
                if snapshot_mode == "certified-pre-series"
                else "PARTIAL"
            ),
            "sources": provenance,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--series-engine",
        type=Path,
        required=True,
    )

    parser.add_argument(
        "--output",
        type=Path,
        required=True,
    )

    parser.add_argument(
        "--snapshot-mode",
        required=True,
        choices=(
            "certified-pre-series",
            "historical-reconstructed",
        ),
    )

    args = parser.parse_args()

    engine = read_json(args.series_engine)

    generated_at_utc = (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )

    artifact = build_artifact(
        engine=engine,
        engine_path=args.series_engine,
        snapshot_mode=args.snapshot_mode,
        generated_at_utc=generated_at_utc,
    )

    write_json(args.output, artifact)

    print(
        json.dumps(
            {
                "status": "PASS",
                "seriesId": (
                    artifact["seriesIdentity"]["seriesId"]
                ),
                "snapshotClassification": (
                    artifact["preSeriesSnapshot"][
                        "snapshotClassification"
                    ]
                ),
                "output": str(args.output),
            },
            sort_keys=True,
        )
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
