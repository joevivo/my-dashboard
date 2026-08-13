from __future__ import annotations

import argparse
import copy
import hashlib
import json
import subprocess
import sys
import tempfile

from datetime import datetime, timezone
from pathlib import Path


SCHEMA = "bie.strat365.series-artifact.v1"
SOURCE_TYPES = (
    "play-by-play",
    "recap",
    "replay",
)


def load_json(path: Path):
    return json.loads(
        path.read_text(encoding="utf-8")
    )


def write_json(path: Path, value):
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    path.write_text(
        json.dumps(
            value,
            indent=2,
        ) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def sha256_bytes(value: bytes):
    return hashlib.sha256(
        value
    ).hexdigest().upper()


def sha256_file(path: Path):
    return sha256_bytes(
        path.read_bytes()
    )


def signature(value):
    payload = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")

    return sha256_bytes(payload)


def repo_relative(
    path: Path,
    repo_root: Path,
):
    try:
        return str(
            path.resolve().relative_to(
                repo_root.resolve()
            )
        ).replace("\\", "/")
    except ValueError:
        return str(path.resolve())


def resolve_repo_path(
    value,
    repo_root: Path,
):
    path = Path(str(value))

    if path.is_absolute():
        return path

    return repo_root / path


def captured_at():
    return (
        datetime.now(timezone.utc)
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z")
    )


def expected_game_id(game):
    for key in (
        "scheduleGameNumber",
        "gameId",
        "ordinal",
    ):
        value = game.get(key)

        if value is not None:
            return str(value)

    raise ValueError(
        "Target game has no usable game identity"
    )


def source_type_from_name(name):
    lower = name.lower()

    if "play-by-play" in lower:
        return "play-by-play"

    if "-recap." in lower:
        return "recap"

    if "-replay." in lower:
        return "replay"

    return None


def validate_capture_source(
    metadata_path: Path,
    metadata,
    repo_root: Path,
):
    if int(metadata.get("httpStatus", 0)) != 200:
        raise ValueError(
            "Capture metadata HTTP status is not 200"
        )

    raw_value = metadata.get(
        "rawResponsePath"
    )

    headers_value = metadata.get(
        "responseHeadersPath"
    )

    expected_hash = str(
        metadata.get(
            "sha256",
            "",
        )
    ).upper()

    if not (
        raw_value
        and headers_value
        and expected_hash
    ):
        raise ValueError(
            "Capture metadata is missing required provenance"
        )

    raw_path = resolve_repo_path(
        raw_value,
        repo_root,
    )

    headers_path = resolve_repo_path(
        headers_value,
        repo_root,
    )

    if not raw_path.exists():
        raise ValueError(
            "Captured raw response does not exist"
        )

    if not headers_path.exists():
        raise ValueError(
            "Captured response headers do not exist"
        )

    if sha256_file(raw_path) != expected_hash:
        raise ValueError(
            "Captured raw response hash mismatch"
        )

    validation = metadata.get(
        "validation",
        {},
    )

    for key in (
        "rawBodyPresent",
        "rawBodyHashMatch",
        "responseHeadersPresent",
    ):
        if validation.get(key) is False:
            raise ValueError(
                f"Capture validation failed: {key}"
            )

    return {
        "metadataPath":
            metadata_path,
        "metadata":
            metadata,
        "rawPath":
            raw_path,
        "headersPath":
            headers_path,
        "sha256":
            expected_hash,
    }


def discover_sources(
    run_directory: Path,
    repo_root: Path,
    league_id: str,
    team_id: str,
    game_id: str,
):
    discovered = {
        name: []
        for name in SOURCE_TYPES
    }

    for path in run_directory.rglob(
        f"game-{game_id}-*.json"
    ):
        source_type = source_type_from_name(
            path.name
        )

        if source_type is None:
            continue

        try:
            metadata = load_json(path)
        except Exception:
            continue

        if (
            str(metadata.get("leagueId"))
            != league_id
        ):
            continue

        if (
            str(metadata.get("gameId"))
            != game_id
        ):
            continue

        team_ids = [
            str(value)
            for value in metadata.get(
                "teamIds",
                [],
            )
        ]

        if team_id not in team_ids:
            continue

        discovered[source_type].append(
            validate_capture_source(
                path,
                metadata,
                repo_root,
            )
        )

    for source_type in SOURCE_TYPES:
        count = len(
            discovered[source_type]
        )

        if count != 1:
            raise ValueError(
                f"Expected exactly one "
                f"{source_type} source; found {count}"
            )

    return {
        key: values[0]
        for key, values
        in discovered.items()
    }


def find_target_game(
    series,
    series_game_number: int,
):
    games = (
        series.get("replay", {})
        .get("games", [])
    )

    matches = [
        game
        for game in games
        if int(game.get("ordinal", -1))
        == series_game_number
    ]

    if len(matches) != 1:
        raise ValueError(
            "Series game ordinal is not unique"
        )

    return matches[0]


def build_source_evidence(
    sources,
    repo_root: Path,
):
    result = []

    for source_type in SOURCE_TYPES:
        source = sources[source_type]
        metadata = source["metadata"]

        result.append(
            {
                "sourceType":
                    source_type.upper()
                    .replace("-", "_"),
                "metadataPath":
                    repo_relative(
                        source["metadataPath"],
                        repo_root,
                    ),
                "rawResponsePath":
                    repo_relative(
                        source["rawPath"],
                        repo_root,
                    ),
                "responseHeadersPath":
                    repo_relative(
                        source["headersPath"],
                        repo_root,
                    ),
                "sha256":
                    source["sha256"],
                "capturedAtUtc":
                    metadata.get(
                        "capturedAtUtc"
                    ),
                "provenance":
                    metadata.get(
                        "provenance",
                        {},
                    ),
            }
        )

    return result


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--repo-root",
        default=".",
    )

    parser.add_argument(
        "--series-artifact",
        required=True,
    )

    parser.add_argument(
        "--run-directory",
        required=True,
    )

    parser.add_argument(
        "--series-game-number",
        type=int,
        required=True,
    )

    parser.add_argument(
        "--replay-adapter",
        required=True,
    )

    parser.add_argument(
        "--output-path",
        required=True,
    )

    return parser.parse_args()


def main():
    args = parse_args()

    repo_root = Path(
        args.repo_root
    ).resolve()

    series_path = Path(
        args.series_artifact
    )

    run_directory = Path(
        args.run_directory
    )

    replay_adapter = Path(
        args.replay_adapter
    )

    output_path = Path(
        args.output_path
    )

    series = load_json(
        series_path
    )

    if (
        series.get("schemaVersion")
        != SCHEMA
    ):
        raise ValueError(
            "Unsupported series artifact schema"
        )

    identity = series.get(
        "seriesIdentity",
        {},
    )

    league_id = str(
        identity.get("leagueId")
    )

    team_id = str(
        identity.get("teamId")
    )

    snapshot = series.get(
        "preSeriesSnapshot",
        {},
    )

    if not (
        snapshot.get(
            "certifiedPreSeries"
        ) is True
        and snapshot.get(
            "snapshotClassification"
        )
        == "IMMUTABLE_PRE_SERIES"
    ):
        raise ValueError(
            "Pre-series snapshot is not certified immutable"
        )

    snapshot_before = signature(
        snapshot
    )

    target = find_target_game(
        series,
        args.series_game_number,
    )

    capture_before = copy.deepcopy(
        target.get(
            "captureState",
            {},
        )
    )

    reveal_before = copy.deepcopy(
        target.get(
            "revealState",
            {},
        )
    )

    review_before = copy.deepcopy(
        target.get(
            "reviewState",
            {},
        )
    )

    if (
        capture_before.get("status")
        != "NOT_CAPTURED"
    ):
        raise ValueError(
            "Binder only accepts NOT_CAPTURED games"
        )

    if (
        reveal_before.get("status")
        != "LOCKED"
    ):
        raise ValueError(
            "Binder requires reveal state LOCKED"
        )

    game_id = expected_game_id(
        target
    )

    sources = discover_sources(
        run_directory,
        repo_root,
        league_id,
        team_id,
        game_id,
    )

    with tempfile.TemporaryDirectory() as temp:
        candidate_path = (
            Path(temp)
            / "replay-candidate.json"
        )

        command = [
            sys.executable,
            str(replay_adapter),
            "--play-by-play",
            str(
                sources[
                    "play-by-play"
                ]["rawPath"]
            ),
            "--metadata",
            str(
                sources[
                    "play-by-play"
                ]["metadataPath"]
            ),
            "--result-source",
            str(
                sources[
                    "recap"
                ]["rawPath"]
            ),
            "--result-metadata",
            str(
                sources[
                    "recap"
                ]["metadataPath"]
            ),
            "--output",
            str(candidate_path),
            "--expected-league-id",
            league_id,
            "--expected-team-id",
            team_id,
            "--expected-game-id",
            game_id,
        ]

        process = subprocess.run(
            command,
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False,
        )

        if process.returncode != 0:
            raise ValueError(
                "Replay adapter failed"
            )

        candidate = load_json(
            candidate_path
        )

    if (
        candidate.get(
            "bindingEligibility"
        )
        != "READY_FOR_REAL_REPLAY_FIREWALL"
    ):
        raise ValueError(
            "Replay adapter candidate is not binding eligible"
        )

    events = candidate.get(
        "events",
        [],
    )

    hidden_result = candidate.get(
        "hiddenResult",
        {},
    )

    final_score = hidden_result.get(
        "finalScore"
    )

    winner = hidden_result.get(
        "winner"
    )

    if not events:
        raise ValueError(
            "Replay candidate contains no events"
        )

    if not (
        isinstance(final_score, dict)
        and len(final_score) == 2
        and winner in final_score
    ):
        raise ValueError(
            "Replay candidate hidden result is invalid"
        )

    bound = copy.deepcopy(
        series
    )

    bound_target = find_target_game(
        bound,
        args.series_game_number,
    )

    bound_target["gameId"] = game_id
    bound_target["events"] = events
    bound_target["winner"] = winner
    bound_target["finalScore"] = final_score

    now = captured_at()

    source_evidence = build_source_evidence(
        sources,
        repo_root,
    )

    captured_times = [
        value.get("capturedAtUtc")
        for value in source_evidence
        if value.get("capturedAtUtc")
    ]

    bound_target["captureState"] = {
        "status":
            "REVIEW_READY",
        "capturedAtUtc":
            (
                max(captured_times)
                if captured_times
                else now
            ),
        "parsedAtUtc":
            now,
        "reviewReadyAtUtc":
            now,
        "sourceEvidence":
            source_evidence,
    }

    if (
        signature(
            bound.get(
                "preSeriesSnapshot",
                {},
            )
        )
        != snapshot_before
    ):
        raise ValueError(
            "Pre-series snapshot mutation detected"
        )

    if (
        bound_target.get(
            "revealState",
            {}
        )
        != reveal_before
    ):
        raise ValueError(
            "Reveal state mutation detected"
        )

    if (
        bound_target.get(
            "reviewState",
            {}
        )
        != review_before
    ):
        raise ValueError(
            "Review state mutation detected"
        )

    write_json(
        output_path,
        bound,
    )


if __name__ == "__main__":
    main()