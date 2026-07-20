from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sqlite3
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

SCHEMA_VERSION = "music.actual-listening-event-projection.v1"

DEFAULT_SOURCE = (
    Path.home()
    / "Downloads"
    / "apple-music-working"
    / "Apple_Media_Services_python"
    / "Apple_Media_Services"
    / "Apple Music Activity"
    / "Apple Music Play Activity.csv"
)

REPO_ROOT = Path(__file__).resolve().parents[4]

DEFAULT_OUTPUT_DIR = (
    REPO_ROOT
    / "data"
    / "music"
    / "generated"
    / "actual-listening"
)

DATABASE_NAME = "actual-listening-events.sqlite3"
MANIFEST_NAME = "actual-listening-event-projection-manifest.json"

OUTCOME_BY_END_REASON = {
    "NATURAL_END_OF_TRACK": "natural_completion",
    "TRACK_SKIPPED_FORWARDS": "recorded_forward_skip",
    "MANUALLY_SELECTED_PLAYBACK_OF_A_DIFF_ITEM": "manual_track_change",
    "TRACK_SKIPPED_BACKWARDS": "backward_navigation",
    "PLAYBACK_MANUALLY_PAUSED": "playback_paused",
    "PLAYBACK_SUSPENDED": "playback_suspended",
    "SCRUB_BEGIN": "scrub_begin",
    "SCRUB_END": "scrub_end",
    "EXITED_APPLICATION": "exited_application",
    "PLAYBACK_STOPPED_DUE_TO_SESSION_TIMEOUT": "session_timeout",
    "FAILED_TO_LOAD": "technical_failure",
    "NOT_SUPPORTED_BY_CLIENT": "unsupported_client",
    "NOT_APPLICABLE": "not_applicable",
    "OTHER": "other",
}

ELIGIBLE_OUTCOMES = {
    "natural_completion",
    "recorded_forward_skip",
    "manual_track_change",
}

REQUIRED_COLUMNS = {
    "Event Start Timestamp",
    "Song Name",
    "Album Name",
    "Media Type",
    "Source Type",
    "End Reason Type",
    "Play Duration Milliseconds",
}


def text(value: object) -> str:
    return str(value or "").strip()


def integer(value: object) -> int:
    try:
        return int(float(text(value) or "0"))
    except (TypeError, ValueError):
        return 0


def event_date(timestamp: str) -> str | None:
    candidate = timestamp[:10]

    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", candidate):
        return candidate

    return None


def outcome_for(end_reason: str) -> str:
    if not end_reason:
        return "unknown"

    return OUTCOME_BY_END_REASON.get(end_reason, "unclassified")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)

    return digest.hexdigest()


def build_projection(source_path: Path, output_dir: Path) -> dict:
    if not source_path.exists():
        raise FileNotFoundError(
            f"Apple Music Play Activity source not found: {source_path}"
        )

    output_dir.mkdir(parents=True, exist_ok=True)

    database_path = output_dir / DATABASE_NAME
    manifest_path = output_dir / MANIFEST_NAME
    temporary_database = output_dir / f"{DATABASE_NAME}.tmp"
    temporary_manifest = output_dir / f"{MANIFEST_NAME}.tmp"

    if temporary_database.exists():
        temporary_database.unlink()

    if temporary_manifest.exists():
        temporary_manifest.unlink()

    source_stat = source_path.stat()
    build_started = time.perf_counter()

    row_count = 0
    dated_row_count = 0
    missing_date_count = 0
    first_date = None
    latest_date = None
    eligible_count = 0
    short_play_count = 0
    outcome_counts = Counter()
    end_reason_counts = Counter()

    connection = sqlite3.connect(temporary_database)

    try:
        connection.execute("PRAGMA journal_mode=OFF")
        connection.execute("PRAGMA synchronous=OFF")
        connection.execute("PRAGMA temp_store=MEMORY")

        connection.execute(
            """
            CREATE TABLE events (
                source_row_number INTEGER PRIMARY KEY,
                event_date TEXT,
                event_start_timestamp TEXT,
                song_name TEXT,
                album_name TEXT,
                media_type TEXT,
                source_type TEXT,
                end_reason_type TEXT,
                outcome TEXT NOT NULL,
                eligible_outcome INTEGER NOT NULL,
                short_play_under_30_seconds INTEGER NOT NULL,
                play_duration_ms_raw INTEGER NOT NULL
            )
            """
        )

        insert_sql = """
            INSERT INTO events (
                source_row_number,
                event_date,
                event_start_timestamp,
                song_name,
                album_name,
                media_type,
                source_type,
                end_reason_type,
                outcome,
                eligible_outcome,
                short_play_under_30_seconds,
                play_duration_ms_raw
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        batch = []

        with source_path.open(
            "r",
            encoding="utf-8-sig",
            errors="replace",
            newline="",
        ) as handle:
            reader = csv.DictReader(handle)
            fields = set(reader.fieldnames or [])
            missing_columns = sorted(REQUIRED_COLUMNS - fields)

            if missing_columns:
                raise RuntimeError(
                    "Required Play Activity columns are missing: "
                    + ", ".join(missing_columns)
                )

            for source_row_number, row in enumerate(reader, start=1):
                row_count += 1

                timestamp = text(row.get("Event Start Timestamp"))
                date_value = event_date(timestamp)
                end_reason = text(row.get("End Reason Type"))
                outcome = outcome_for(end_reason)
                duration_ms = integer(
                    row.get("Play Duration Milliseconds")
                )

                eligible = int(outcome in ELIGIBLE_OUTCOMES)
                short_play = int(0 <= duration_ms < 30_000)

                if date_value:
                    dated_row_count += 1
                    first_date = (
                        date_value
                        if first_date is None
                        else min(first_date, date_value)
                    )
                    latest_date = (
                        date_value
                        if latest_date is None
                        else max(latest_date, date_value)
                    )
                else:
                    missing_date_count += 1

                eligible_count += eligible
                short_play_count += short_play
                outcome_counts[outcome] += 1
                end_reason_counts[end_reason or "(blank)"] += 1

                batch.append(
                    (
                        source_row_number,
                        date_value,
                        timestamp,
                        text(row.get("Song Name")),
                        text(row.get("Album Name")),
                        text(row.get("Media Type")),
                        text(row.get("Source Type")),
                        end_reason,
                        outcome,
                        eligible,
                        short_play,
                        duration_ms,
                    )
                )

                if len(batch) >= 5_000:
                    connection.executemany(insert_sql, batch)
                    batch.clear()

            if batch:
                connection.executemany(insert_sql, batch)

        connection.execute(
            "CREATE INDEX idx_events_date ON events(event_date)"
        )
        connection.execute(
            "CREATE INDEX idx_events_date_outcome "
            "ON events(event_date, outcome)"
        )
        connection.execute(
            "CREATE INDEX idx_events_outcome ON events(outcome)"
        )

        connection.execute(
            """
            CREATE TABLE projection_metadata (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
            """
        )

        metadata = {
            "schemaVersion": SCHEMA_VERSION,
            "sourcePath": str(source_path),
            "sourceSizeBytes": str(source_stat.st_size),
            "sourceModifiedAt": datetime.fromtimestamp(
                source_stat.st_mtime,
                tz=timezone.utc,
            ).isoformat(),
            "rowCount": str(row_count),
            "coverageStart": str(first_date or ""),
            "coverageEnd": str(latest_date or ""),
        }

        connection.executemany(
            "INSERT INTO projection_metadata(key, value) VALUES (?, ?)",
            sorted(metadata.items()),
        )

        connection.commit()

        stored_row_count = connection.execute(
            "SELECT COUNT(*) FROM events"
        ).fetchone()[0]

        if stored_row_count != row_count:
            raise RuntimeError(
                "Projection row-count reconciliation failed: "
                f"source={row_count}; stored={stored_row_count}"
            )
    finally:
        connection.close()

    source_hash = sha256_file(source_path)

    if database_path.exists():
        database_path.unlink()

    temporary_database.replace(database_path)

    generated_at = datetime.now(timezone.utc).isoformat()
    build_seconds = time.perf_counter() - build_started

    manifest = {
        "schemaVersion": SCHEMA_VERSION,
        "generatedAt": generated_at,
        "source": {
            "path": str(source_path),
            "sizeBytes": source_stat.st_size,
            "modifiedAt": datetime.fromtimestamp(
                source_stat.st_mtime,
                tz=timezone.utc,
            ).isoformat(),
            "sha256": source_hash,
        },
        "projection": {
            "databasePath": str(database_path),
            "rowCount": row_count,
            "datedRowCount": dated_row_count,
            "missingDateCount": missing_date_count,
            "coverageStart": first_date,
            "coverageEnd": latest_date,
            "eligibleOutcomeCount": eligible_count,
            "shortPlayUnder30SecondsCount": short_play_count,
            "outcomeCounts": dict(sorted(outcome_counts.items())),
            "endReasonCounts": dict(sorted(end_reason_counts.items())),
            "fileSizeBytes": database_path.stat().st_size,
            "buildSeconds": round(build_seconds, 3),
        },
        "semantics": {
            "eligibleOutcomes": sorted(ELIGIBLE_OUTCOMES),
            "durationThresholdOnlyCreatesSkip": False,
            "dailyPlayPlusSkipDenominatorAllowed": False,
        },
    }

    temporary_manifest.write_text(
        json.dumps(
            manifest,
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    if manifest_path.exists():
        manifest_path.unlink()

    temporary_manifest.replace(manifest_path)

    benchmark_started = time.perf_counter()

    with sqlite3.connect(database_path) as benchmark_connection:
        benchmark_row = benchmark_connection.execute(
            """
            SELECT
                COUNT(*) AS row_count,
                COALESCE(SUM(eligible_outcome), 0),
                COALESCE(SUM(outcome = 'natural_completion'), 0),
                COALESCE(SUM(outcome = 'recorded_forward_skip'), 0),
                COALESCE(SUM(outcome = 'manual_track_change'), 0),
                COALESCE(SUM(outcome = 'backward_navigation'), 0)
            FROM events
            WHERE event_date BETWEEN ? AND ?
            """,
            ("2026-04-19", "2026-04-19"),
        ).fetchone()

    benchmark_seconds = time.perf_counter() - benchmark_started

    result = {
        "schemaVersion": SCHEMA_VERSION,
        "databasePath": str(database_path),
        "manifestPath": str(manifest_path),
        "sourceRowCount": row_count,
        "projectionRowCount": stored_row_count,
        "coverageStart": first_date,
        "coverageEnd": latest_date,
        "databaseSizeBytes": database_path.stat().st_size,
        "buildSeconds": round(build_seconds, 3),
        "benchmark": {
            "startDate": "2026-04-19",
            "endDate": "2026-04-19",
            "querySeconds": round(benchmark_seconds, 6),
            "rowCount": benchmark_row[0],
            "eligibleOutcomes": benchmark_row[1],
            "naturalCompletions": benchmark_row[2],
            "recordedForwardSkips": benchmark_row[3],
            "manualTrackChanges": benchmark_row[4],
            "backwardNavigations": benchmark_row[5],
        },
    }

    return result


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Build the governed Actual Listening raw-event projection."
        )
    )

    parser.add_argument(
        "--source",
        type=Path,
        default=DEFAULT_SOURCE,
    )

    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
    )

    arguments = parser.parse_args()
    result = build_projection(
        arguments.source,
        arguments.output_dir,
    )

    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()