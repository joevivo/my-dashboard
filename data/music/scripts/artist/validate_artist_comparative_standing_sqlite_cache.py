from __future__ import annotations

import json
import sqlite3
import sys
import tempfile
from pathlib import Path
from typing import Any

from artist_comparative_standing_runtime import (
    ComparativeStandingCacheError,
    RESPONSE_SCHEMA_VERSION,
    SQLITE_CACHE_MANIFEST_SCHEMA_VERSION,
    load_cached_artist_comparative_standing,
    sha256_file,
)


assertion_count = 0


def check(condition: bool, message: str) -> None:
    global assertion_count
    assertion_count += 1

    if not condition:
        raise AssertionError(message)


def metric_map(
    response: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    return {
        metric["metricKey"]: metric
        for metric in response["metrics"]
    }


def main() -> int:
    if len(sys.argv) != 6:
        raise SystemExit(
            "Usage: validate_artist_comparative_standing_sqlite_cache.py "
            "<library.zip> <snapshot.csv> <families.json> "
            "<cache.sqlite3> <manifest.json>"
        )

    library_path = Path(sys.argv[1])
    snapshot_path = Path(sys.argv[2])
    families_path = Path(sys.argv[3])
    cache_path = Path(sys.argv[4])
    manifest_path = Path(sys.argv[5])

    manifest = json.loads(
        manifest_path.read_text(
            encoding="utf-8-sig"
        )
    )

    check(
        manifest["schemaVersion"]
        == SQLITE_CACHE_MANIFEST_SCHEMA_VERSION,
        "SQLite cache manifest schema changed.",
    )

    check(
        manifest["cache"]["sha256"]
        == sha256_file(cache_path),
        "SQLite cache fingerprint changed.",
    )

    check(
        manifest["cache"]["sizeBytes"]
        == cache_path.stat().st_size,
        "SQLite cache size changed.",
    )

    with sqlite3.connect(cache_path) as connection:
        row_count = connection.execute(
            """
            SELECT COUNT(*)
            FROM artist_responses
            """
        ).fetchone()[0]

    check(
        row_count >= 5125,
        "SQLite artist-response coverage is incomplete.",
    )

    def load(name: str) -> dict[str, Any]:
        return load_cached_artist_comparative_standing(
            name,
            cache_path=cache_path,
            manifest_path=manifest_path,
            library_tracks_path=library_path,
            snapshot_path=snapshot_path,
            families_path=families_path,
        )

    rem = load("R.E.M.")
    u2 = load("U2")
    beatles = load("The Beatles")
    missing = load(
        "Comparative Standing Missing Artist Fixture"
    )

    rem_metrics = metric_map(rem)
    u2_metrics = metric_map(u2)
    beatles_metrics = metric_map(beatles)
    missing_metrics = metric_map(missing)

    check(
        rem["schemaVersion"] == RESPONSE_SCHEMA_VERSION,
        "Cached response schema changed.",
    )

    check(
        rem["canonicalKey"] == "rem",
        "R.E.M. canonical key changed.",
    )

    check(
        rem_metrics["library_evidence_records"]["rank"] == 4,
        "R.E.M. Library rank changed.",
    )

    check(
        rem_metrics["historical_years_represented"]["rank"] == 1,
        "R.E.M. years rank changed.",
    )

    check(
        rem_metrics["recent_apple_observations"]["rank"] == 3,
        "R.E.M. observation rank changed.",
    )

    check(
        rem_metrics[
            "historical_unique_object_count"
        ]["rank"]
        == 3,
        "R.E.M. unique-object rank changed.",
    )

    check(
        u2_metrics["library_evidence_records"]["rank"] == 52,
        "U2 Library rank changed.",
    )

    check(
        beatles_metrics[
            "historical_unique_object_count"
        ]["rank"]
        == 5,
        "The Beatles unique-object rank changed.",
    )

    check(
        all(
            metric["entityType"] == "artist"
            for metric in rem["metrics"]
        ),
        "Family rankings entered an artist response.",
    )

    check(
        missing["status"] == "searched_no_evidence",
        "Missing artist response status changed.",
    )

    supported_missing = [
        metric
        for metric in missing["metrics"]
        if metric["metricKey"]
        not in {
            "actual_plays",
            "listening_duration_ms",
        }
    ]

    check(
        all(
            metric["status"] == "searched_no_evidence"
            and metric["value"] is None
            and metric["rank"] is None
            for metric in supported_missing
        ),
        "Missing artist produced false evidence or zero.",
    )

    unavailable_missing = [
        missing_metrics["actual_plays"],
        missing_metrics["listening_duration_ms"],
    ]

    check(
        all(
            metric["status"] == "unavailable"
            and metric["value"] is None
            for metric in unavailable_missing
        ),
        "Unavailable metrics changed for missing artist.",
    )

    check(
        missing["reviewedFamilyIds"] == [],
        "Missing artist entered a reviewed family.",
    )

    tampered_manifest = json.loads(
        json.dumps(manifest)
    )

    tampered_manifest[
        "sources"
    ][
        "libraryTracks"
    ][
        "sha256"
    ] = "0" * 64

    with tempfile.TemporaryDirectory() as temporary:
        temporary_path = (
            Path(temporary)
            / "tampered-manifest.json"
        )

        temporary_path.write_text(
            json.dumps(tampered_manifest),
            encoding="utf-8",
        )

        try:
            load_cached_artist_comparative_standing(
                "R.E.M.",
                cache_path=cache_path,
                manifest_path=temporary_path,
                library_tracks_path=library_path,
                snapshot_path=snapshot_path,
                families_path=families_path,
            )
        except ComparativeStandingCacheError:
            tampered_failed_closed = True
        else:
            tampered_failed_closed = False

    check(
        tampered_failed_closed,
        "Tampered source manifest did not fail closed.",
    )

    print("COMPARATIVE_STANDING_SQLITE_CACHE_VALIDATION: PASS")
    print(f"VALIDATION_ASSERTION_COUNT: {assertion_count}")
    print(f"ARTIST_RESPONSE_COUNT: {row_count}")
    print("SOURCE_AND_CODE_FINGERPRINT_VALIDATION: PASS")
    print("CACHE_CONTENT_FINGERPRINT_VALIDATION: PASS")
    print("TAMPERED_MANIFEST_FAIL_CLOSED: PASS")
    print("STALE_CACHE_FALLBACK: PROHIBITED")
    print("MISSING_ARTIST_FALSE_ZERO: PROHIBITED")
    print("ARTIST_FAMILY_SEPARATION: PASS")
    print("PROBE_REM_LIBRARY_RANK: 4")
    print("PROBE_REM_YEARS_RANK: 1")
    print("PROBE_U2_LIBRARY_RANK: 52")
    print("PROBE_BEATLES_UNIQUE_OBJECT_RANK: 5")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())