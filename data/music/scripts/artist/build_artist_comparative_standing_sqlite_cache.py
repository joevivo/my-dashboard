from __future__ import annotations

import json
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import artist_comparative_standing_runtime as runtime
from artist_comparative_standing_runtime import (
    RESPONSE_SCHEMA_VERSION,
    RUNTIME_SCHEMA_VERSION,
    SQLITE_CACHE_MANIFEST_SCHEMA_VERSION,
    load_and_build_runtime_snapshot,
    select_artist_comparative_standing,
    sha256_file,
)


def json_text(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def input_record(path: Path) -> dict[str, Any]:
    stat = path.stat()

    return {
        "path": str(path.resolve()),
        "sha256": sha256_file(path),
        "sizeBytes": stat.st_size,
        "modifiedTimeNs": stat.st_mtime_ns,
    }


def atomic_write_bytes(
    path: Path,
    content: bytes,
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporary_path = path.with_name(
        f"{path.name}.tmp"
    )

    if temporary_path.exists():
        temporary_path.unlink()

    temporary_path.write_bytes(content)
    temporary_path.replace(path)


def response_for_canonical_key(
    snapshot: dict[str, Any],
    canonical_key: str,
) -> dict[str, Any]:
    display_name = (
        snapshot.get("artistDisplayNames", {}).get(
            canonical_key
        )
        or canonical_key
    )

    for candidate in (
        display_name,
        canonical_key,
    ):
        response = select_artist_comparative_standing(
            snapshot,
            candidate,
        )

        if response.get("canonicalKey") == canonical_key:
            return response

    raise ValueError(
        "Could not reproduce canonical artist response: "
        f"{canonical_key}"
    )


def main() -> int:
    if len(sys.argv) != 6:
        raise SystemExit(
            "Usage: build_artist_comparative_standing_sqlite_cache.py "
            "<library.zip> <snapshot.csv> <families.json> "
            "<cache.sqlite3> <manifest.json>"
        )

    library_path = Path(sys.argv[1])
    snapshot_path = Path(sys.argv[2])
    families_path = Path(sys.argv[3])
    cache_path = Path(sys.argv[4])
    manifest_path = Path(sys.argv[5])

    for path in (
        library_path,
        snapshot_path,
        families_path,
    ):
        if not path.exists():
            raise FileNotFoundError(path)

    snapshot = load_and_build_runtime_snapshot(
        library_tracks_path=library_path,
        snapshot_path=snapshot_path,
        families_path=families_path,
    )

    canonical_keys = set(
        snapshot.get(
            "artistDisplayNames",
            {},
        )
    )

    for rankings in snapshot.get(
        "artistRankings",
        {},
    ).values():
        canonical_keys.update(rankings)

    for family in snapshot.get(
        "familyDefinitions",
        [],
    ):
        canonical_keys.update(
            family.get("members") or []
        )

    responses = []

    for canonical_key in sorted(canonical_keys):
        response = response_for_canonical_key(
            snapshot,
            canonical_key,
        )

        responses.append(
            (
                canonical_key,
                response.get("displayName"),
                json_text(response),
            )
        )

    no_evidence_template = (
        select_artist_comparative_standing(
            snapshot,
            "Comparative Standing Missing Artist Fixture",
        )
    )

    if (
        no_evidence_template.get("status")
        != "searched_no_evidence"
    ):
        raise ValueError(
            "No-evidence response template was not produced."
        )

    temporary_cache = cache_path.with_name(
        f"{cache_path.name}.tmp"
    )

    if temporary_cache.exists():
        temporary_cache.unlink()

    cache_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with sqlite3.connect(
        temporary_cache
    ) as connection:
        connection.execute(
            "PRAGMA journal_mode = OFF"
        )
        connection.execute(
            "PRAGMA synchronous = OFF"
        )

        connection.execute(
            """
            CREATE TABLE cache_metadata (
                key TEXT PRIMARY KEY,
                value_json TEXT NOT NULL
            )
            """
        )

        connection.execute(
            """
            CREATE TABLE artist_responses (
                canonical_key TEXT PRIMARY KEY,
                display_name TEXT,
                response_json TEXT NOT NULL
            )
            """
        )

        connection.executemany(
            """
            INSERT INTO artist_responses (
                canonical_key,
                display_name,
                response_json
            )
            VALUES (?, ?, ?)
            """,
            responses,
        )

        connection.execute(
            """
            INSERT INTO cache_metadata (
                key,
                value_json
            )
            VALUES (?, ?)
            """,
            (
                "noEvidenceTemplate",
                json_text(no_evidence_template),
            ),
        )

        connection.execute(
            """
            INSERT INTO cache_metadata (
                key,
                value_json
            )
            VALUES (?, ?)
            """,
            (
                "runtimeSchemaVersion",
                json_text(RUNTIME_SCHEMA_VERSION),
            ),
        )

        connection.execute(
            """
            INSERT INTO cache_metadata (
                key,
                value_json
            )
            VALUES (?, ?)
            """,
            (
                "responseSchemaVersion",
                json_text(RESPONSE_SCHEMA_VERSION),
            ),
        )

        connection.commit()
        connection.execute("VACUUM")

    connection.close()

    temporary_cache.replace(cache_path)

    generated_at = datetime.now(
        timezone.utc
    ).isoformat()

    runtime_path = Path(
        runtime.__file__
    ).resolve()

    ranking_path = (
        runtime.SCRIPT_DIR
        / "artist_comparative_standing.py"
    )

    identity_path = (
        runtime.IDENTITY_DIR
        / "music_identity.py"
    )

    manifest = {
        "schemaVersion": (
            SQLITE_CACHE_MANIFEST_SCHEMA_VERSION
        ),
        "generatedAt": generated_at,
        "runtimeSchemaVersion": RUNTIME_SCHEMA_VERSION,
        "responseSchemaVersion": RESPONSE_SCHEMA_VERSION,
        "sources": {
            "libraryTracks": input_record(
                library_path
            ),
            "snapshotWarehouse": input_record(
                snapshot_path
            ),
            "artistFamilies": input_record(
                families_path
            ),
        },
        "code": {
            "runtime": input_record(
                runtime_path
            ),
            "ranking": input_record(
                ranking_path
            ),
            "identity": input_record(
                identity_path
            ),
        },
        "cache": {
            "path": str(cache_path.resolve()),
            "sha256": sha256_file(cache_path),
            "sizeBytes": cache_path.stat().st_size,
            "storage": "sqlite3",
            "artistResponseCount": len(responses),
        },
    }

    manifest_bytes = (
        json.dumps(
            manifest,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    ).encode("utf-8")

    atomic_write_bytes(
        manifest_path,
        manifest_bytes,
    )

    print("COMPARATIVE_STANDING_SQLITE_CACHE_GENERATION: PASS")
    print(f"GENERATED_AT: {generated_at}")
    print(f"ARTIST_RESPONSE_COUNT: {len(responses)}")
    print(f"CACHE_PATH: {cache_path}")
    print(f"CACHE_SHA256: {manifest['cache']['sha256']}")
    print(f"CACHE_SIZE_BYTES: {manifest['cache']['sizeBytes']}")
    print(f"MANIFEST_PATH: {manifest_path}")
    print(f"MANIFEST_SHA256: {sha256_file(manifest_path)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())