from __future__ import annotations

import json
import sqlite3
from pathlib import Path


ACTUAL_LISTENING_SCHEMA_VERSION = (
    "music.actual-listening-event-projection.v1"
)

ACTUAL_LISTENING_DIRECTORY = (
    Path(__file__).resolve().parents[4]
    / "data"
    / "music"
    / "generated"
    / "actual-listening"
)

ACTUAL_LISTENING_DATABASE = (
    ACTUAL_LISTENING_DIRECTORY
    / "actual-listening-events.sqlite3"
)

ACTUAL_LISTENING_MANIFEST = (
    ACTUAL_LISTENING_DIRECTORY
    / "actual-listening-event-projection-manifest.json"
)


def empty_actual_listening_activity(status):
    return {
        "status": status,
        "actualPlays": None,
        "actualSkips": None,
        "listeningSeconds": None,
        "listeningHours": None,
        "uniqueArtistCount": None,
        "uniqueAlbumCount": None,
        "uniqueTrackCount": None,
        "topArtists": [],
        "topAlbums": [],
        "topTracks": [],
        "playbackOutcomes": {
            "naturalCompletions": None,
            "recordedForwardSkips": None,
            "manualTrackChanges": None,
        },
        "sourceNote": (
            "Apple Music Play Activity raw-event projection. "
            "Artist identity is not present in projection v1."
        ),
    }


def actual_listening_unavailable(message):
    return {
        "coverage": {
            "sourceId": "apple_daily_track_summary",
            "sourceType": "actual_listening",
            "status": "unavailable",
            "recordsExamined": None,
            "recordsMatched": None,
            "coverageStart": None,
            "coverageEnd": None,
            "capturedAt": None,
            "freshness": "unknown",
            "limitations": [message],
        },
        "activity": empty_actual_listening_activity(
            "unavailable"
        ),
        "warnings": [
            {
                "code": "ACTUAL_LISTENING_UNAVAILABLE",
                "message": message,
                "sourceId": "apple_daily_track_summary",
            }
        ],
        "provenance": None,
    }


def load_actual_listening(requested_start, requested_end):
    requested_start_text = str(requested_start)
    requested_end_text = str(requested_end)

    if not ACTUAL_LISTENING_DATABASE.exists():
        return actual_listening_unavailable(
            "The governed Actual Listening database was not found."
        )

    if not ACTUAL_LISTENING_MANIFEST.exists():
        return actual_listening_unavailable(
            "The governed Actual Listening manifest was not found."
        )

    try:
        manifest = json.loads(
            ACTUAL_LISTENING_MANIFEST.read_text(
                encoding="utf-8-sig"
            )
        )
    except (OSError, json.JSONDecodeError) as error:
        return actual_listening_unavailable(
            "The governed Actual Listening manifest could not "
            f"be read: {error}"
        )

    if (
        manifest.get("schemaVersion")
        != ACTUAL_LISTENING_SCHEMA_VERSION
    ):
        return actual_listening_unavailable(
            "The Actual Listening projection schema is not "
            "supported by Period Intelligence."
        )

    projection = manifest.get("projection") or {}
    coverage_start = str(
        projection.get("coverageStart") or ""
    )
    coverage_end = str(
        projection.get("coverageEnd") or ""
    )
    generated_at = manifest.get("generatedAt")

    if not coverage_start or not coverage_end:
        return actual_listening_unavailable(
            "The Actual Listening projection does not declare "
            "a usable coverage range."
        )

    no_overlap = (
        requested_end_text < coverage_start
        or requested_start_text > coverage_end
    )

    base_limitation = (
        "Projection v1 does not include artist identity; "
        "artist counts and top artists are unavailable."
    )

    if no_overlap:
        message = (
            "Actual Listening covers "
            f"{coverage_start} through {coverage_end} and does "
            "not cover the selected period."
        )

        activity = empty_actual_listening_activity(
            "unsupported_for_period"
        )

        return {
            "coverage": {
                "sourceId": "apple_daily_track_summary",
                "sourceType": "actual_listening",
                "status": "unsupported_for_period",
                "recordsExamined": None,
                "recordsMatched": None,
                "coverageStart": coverage_start,
                "coverageEnd": coverage_end,
                "capturedAt": generated_at,
                "freshness": "stale",
                "limitations": [
                    message,
                    base_limitation,
                ],
            },
            "activity": activity,
            "warnings": [
                {
                    "code": (
                        "ACTUAL_LISTENING_UNSUPPORTED_FOR_PERIOD"
                    ),
                    "message": message,
                    "sourceId": "apple_daily_track_summary",
                }
            ],
            "provenance": {
                "evidenceId": (
                    "actual-listening-event-projection"
                ),
                "sourceId": "apple_daily_track_summary",
                "sourceLabel": "Apple Music Play Activity",
                "sourceType": "actual_listening",
                "sourceNote": activity["sourceNote"],
            },
        }

    query_start = max(
        requested_start_text,
        coverage_start,
    )
    query_end = min(
        requested_end_text,
        coverage_end,
    )

    partial_coverage = (
        query_start != requested_start_text
        or query_end != requested_end_text
    )

    try:
        connection = sqlite3.connect(
            f"file:{ACTUAL_LISTENING_DATABASE.as_posix()}"
            "?mode=ro",
            uri=True,
        )

        try:
            aggregate = connection.execute(
                """
                SELECT
                    COUNT(*),
                    COALESCE(SUM(eligible_outcome), 0),
                    COALESCE(
                        SUM(
                            outcome = 'recorded_forward_skip'
                        ),
                        0
                    ),
                    COALESCE(
                        SUM(
                            outcome = 'natural_completion'
                        ),
                        0
                    ),
                    COALESCE(
                        SUM(
                            outcome = 'manual_track_change'
                        ),
                        0
                    ),
                    COALESCE(
                        SUM(
                            CASE
                                WHEN eligible_outcome = 1
                                THEN play_duration_ms_raw
                                ELSE 0
                            END
                        ),
                        0
                    ),
                    COUNT(
                        DISTINCT CASE
                            WHEN eligible_outcome = 1
                            THEN NULLIF(
                                TRIM(album_name),
                                ''
                            )
                        END
                    ),
                    COUNT(
                        DISTINCT CASE
                            WHEN eligible_outcome = 1
                            THEN NULLIF(
                                TRIM(song_name),
                                ''
                            )
                        END
                    )
                FROM events
                WHERE event_date BETWEEN ? AND ?
                """,
                (query_start, query_end),
            ).fetchone()

            top_tracks = connection.execute(
                """
                SELECT
                    song_name,
                    COUNT(*) AS plays
                FROM events
                WHERE event_date BETWEEN ? AND ?
                  AND eligible_outcome = 1
                  AND TRIM(
                      COALESCE(song_name, '')
                  ) != ''
                GROUP BY song_name
                ORDER BY plays DESC, song_name
                LIMIT 10
                """,
                (query_start, query_end),
            ).fetchall()

            top_albums = connection.execute(
                """
                SELECT
                    album_name,
                    COUNT(*) AS plays
                FROM events
                WHERE event_date BETWEEN ? AND ?
                  AND eligible_outcome = 1
                  AND TRIM(
                      COALESCE(album_name, '')
                  ) != ''
                GROUP BY album_name
                ORDER BY plays DESC, album_name
                LIMIT 10
                """,
                (query_start, query_end),
            ).fetchall()
        finally:
            connection.close()
    except sqlite3.Error as error:
        return actual_listening_unavailable(
            "The governed Actual Listening database could not "
            f"be queried: {error}"
        )

    records_examined = int(aggregate[0])
    actual_plays = int(aggregate[1])
    actual_skips = int(aggregate[2])
    natural_completions = int(aggregate[3])
    manual_track_changes = int(aggregate[4])
    listening_milliseconds = int(aggregate[5])
    unique_albums = int(aggregate[6])
    unique_tracks = int(aggregate[7])

    limitations = [base_limitation]

    if partial_coverage:
        limitations.insert(
            0,
            (
                "Only the overlapping source range "
                f"{query_start} through {query_end} was searched; "
                "the selected period extends beyond projection "
                "coverage."
            ),
        )

    coverage_status = (
        "searched_with_evidence"
        if actual_plays > 0
        else "searched_no_evidence"
    )

    activity = {
        "status": "available",
        "actualPlays": actual_plays,
        "actualSkips": actual_skips,
        "listeningSeconds": round(
            listening_milliseconds / 1000,
            3,
        ),
        "listeningHours": round(
            listening_milliseconds / 3_600_000,
            3,
        ),
        "uniqueArtistCount": None,
        "uniqueAlbumCount": unique_albums,
        "uniqueTrackCount": unique_tracks,
        "topArtists": [],
        "topAlbums": [
            {
                "album": str(album),
                "actualPlays": int(plays),
                "plays": int(plays),
            }
            for album, plays in top_albums
        ],
        "topTracks": [
            {
                "track": str(track),
                "song": str(track),
                "actualPlays": int(plays),
                "plays": int(plays),
            }
            for track, plays in top_tracks
        ],
        "playbackOutcomes": {
            "naturalCompletions": natural_completions,
            "recordedForwardSkips": actual_skips,
            "manualTrackChanges": manual_track_changes,
        },
        "sourceNote": (
            "Apple Music Play Activity raw-event projection. "
            "Actual Plays are governed eligible outcomes. "
            "Artist identity is not present in projection v1."
        ),
    }

    warnings = []

    if partial_coverage:
        warnings.append(
            {
                "code": (
                    "ACTUAL_LISTENING_PARTIAL_COVERAGE"
                ),
                "message": limitations[0],
                "sourceId": "apple_daily_track_summary",
            }
        )

    return {
        "coverage": {
            "sourceId": "apple_daily_track_summary",
            "sourceType": "actual_listening",
            "status": coverage_status,
            "recordsExamined": records_examined,
            "recordsMatched": actual_plays,
            "coverageStart": query_start,
            "coverageEnd": query_end,
            "capturedAt": generated_at,
            "freshness": (
                "stale"
                if requested_end_text > coverage_end
                else "current"
            ),
            "limitations": limitations,
        },
        "activity": activity,
        "warnings": warnings,
        "provenance": {
            "evidenceId": (
                "actual-listening-event-projection"
            ),
            "sourceId": "apple_daily_track_summary",
            "sourceLabel": "Apple Music Play Activity",
            "sourceType": "actual_listening",
            "sourceNote": activity["sourceNote"],
        },
    }


def apply_actual_listening_to_result(
    result,
    actual_listening,
):
    result["coverage"][0] = actual_listening["coverage"]
    result["activity"] = actual_listening["activity"]

    result["warnings"] = [
        warning
        for warning in result.get("warnings", [])
        if warning.get("code")
        != "ACTUAL_LISTENING_NOT_SEARCHED"
    ]

    result["warnings"].extend(
        actual_listening.get("warnings", [])
    )

    provenance = actual_listening.get("provenance")

    if provenance:
        result.setdefault("provenance", []).insert(
            0,
            provenance,
        )

    activity = result["activity"]
    activity_status = activity.get("status")
    actual_plays = activity.get("actualPlays")
    library_count = int(
        result.get("libraryEvidence", {}).get(
            "recordCount",
            0,
        )
        or 0
    )

    summary = result.setdefault("summary", {})

    if activity_status == "available":
        if actual_plays and actual_plays > 0:
            summary["headline"] = (
                f"{actual_plays} confirmed Actual "
                f"{'Play was' if actual_plays == 1 else 'Plays were'} "
                "found for this period."
            )

            summary["status"] = "partial_coverage"
            summary["narrative"] = (
                "Actual Listening and Library Evidence were "
                f"searched. {actual_plays} confirmed Actual "
                f"Plays and {library_count} Library Evidence "
                "records were found. Recent Apple Objects and "
                "playback context were not searched."
            )
        elif library_count > 0:
            summary["status"] = "partial_coverage"
            summary["narrative"] = (
                "Actual Listening was searched and returned no "
                "confirmed plays. Library Evidence was searched "
                f"and returned {library_count} records. Recent "
                "Apple Objects and playback context were not "
                "searched."
            )
        else:
            summary["status"] = "no_matching_evidence"
            summary["headline"] = (
                "No matching Actual Listening or Library "
                "Evidence was found for this period."
            )
            summary["narrative"] = (
                "Actual Listening and Library Evidence were "
                "searched and returned no matching evidence. "
                "Recent Apple Objects and playback context were "
                "not searched."
            )

        confidence = result.setdefault("confidence", {})
        confidence["level"] = "medium"

        limitations = [
            limitation
            for limitation in confidence.get(
                "limitations",
                [],
            )
            if "Actual listening" not in limitation
        ]

        limitations.append(
            "Recent Apple Objects and playback context were "
            "not searched."
        )

        confidence["limitations"] = list(
            dict.fromkeys(limitations)
        )

        statement = (
            f"Actual Listening contained {actual_plays} "
            "confirmed plays and "
            f"{activity.get('actualSkips', 0)} recorded "
            "forward skips."
        )

        result.setdefault("facts", []).insert(
            0,
            {
                "id": "actual-listening-period-summary",
                "statement": statement,
                "confidence": "high",
                "evidenceRefs": [
                    "actual-listening-event-projection"
                ],
            },
        )

    elif activity_status == "unsupported_for_period":
        coverage = actual_listening["coverage"]

        summary["narrative"] = (
            "Library Evidence was searched. Actual Listening "
            f"covers {coverage.get('coverageStart')} through "
            f"{coverage.get('coverageEnd')} and does not cover "
            "the selected period. Recent Apple Objects and "
            "playback context were not searched."
        )

    elif activity_status == "unavailable":
        summary["narrative"] = (
            "Library Evidence was searched. Actual Listening "
            "was unavailable. Recent Apple Objects and playback "
            "context were not searched."
        )
