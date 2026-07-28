from __future__ import annotations

import csv
import json
import sys
import zipfile
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


SCRIPT_DIR = Path(__file__).resolve().parent
IDENTITY_DIR = SCRIPT_DIR.parent / "identity"

if str(IDENTITY_DIR) not in sys.path:
    sys.path.append(str(IDENTITY_DIR))

from music_identity import resolve_artist

from artist_comparative_standing import (
    build_historical_unique_object_sets,
    build_library_evidence_values,
    build_recent_apple_observation_values,
    build_years_represented_sets,
    rank_positive_population,
    unavailable_metric_result,
)


RUNTIME_SCHEMA_VERSION = (
    "music.artist-comparative-standing.runtime.v0"
)


def resolve_artist_identity(value: Any) -> dict[str, str] | None:
    """Resolve nonblank artist evidence through the shared identity layer."""

    raw_name = str(value or "").strip()

    if not raw_name:
        return None

    resolved = resolve_artist(raw_name)

    if not isinstance(resolved, Mapping):
        raise TypeError(
            "music_identity.resolve_artist must return a mapping."
        )

    canonical_key = str(
        resolved.get("canonicalKey") or ""
    ).strip()

    display_name = str(
        resolved.get("displayName")
        or resolved.get("rawName")
        or raw_name
    ).strip()

    if not canonical_key:
        return None

    return {
        "canonicalKey": canonical_key,
        "displayName": display_name,
        "confidence": str(
            resolved.get("confidence") or ""
        ).strip(),
    }


def canonical_artist_key(value: Any) -> str:
    """Return the stable canonicalKey used for population identity."""

    identity = resolve_artist_identity(value)

    if identity is None:
        return ""

    return identity["canonicalKey"]


def load_library_tracks(path: Path) -> list[dict[str, Any]]:
    """Load the full Apple Music Library Tracks JSON archive."""

    with zipfile.ZipFile(path, "r") as archive:
        json_entries = [
            name
            for name in archive.namelist()
            if name.casefold().endswith(".json")
        ]

        if not json_entries:
            raise ValueError(
                "Library Tracks archive contains no JSON entry."
            )

        preferred_entries = [
            name
            for name in json_entries
            if name.casefold().endswith(
                "apple music library tracks.json"
            )
        ]

        entry_name = (
            preferred_entries[0]
            if preferred_entries
            else json_entries[0]
        )

        with archive.open(entry_name) as handle:
            payload = json.load(handle)

    if not isinstance(payload, list):
        raise ValueError(
            "Library Tracks JSON must contain a top-level array."
        )

    return [
        row
        for row in payload
        if isinstance(row, dict)
    ]


def load_snapshot_rows(path: Path) -> list[dict[str, str]]:
    """Load the canonical Apple snapshot warehouse."""

    with path.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as handle:
        return list(csv.DictReader(handle))


def load_curated_families(
    path: Path,
) -> list[dict[str, Any]]:
    """Load reviewed family rollups without merging artist identities."""

    payload = json.loads(
        path.read_text(encoding="utf-8-sig")
    )

    if not isinstance(payload, list):
        raise ValueError(
            "artistFamilies.json must contain an array."
        )

    families: list[dict[str, Any]] = []

    for row in payload:
        if not isinstance(row, dict):
            continue

        family_id = str(
            row.get("familyName")
            or row.get("familyId")
            or ""
        ).strip()

        members: list[str] = []

        for raw_member in row.get("members") or []:
            member_key = canonical_artist_key(raw_member)

            if member_key and member_key not in members:
                members.append(member_key)

        if not family_id or not members:
            continue

        families.append(
            {
                "familyId": family_id,
                "familyName": family_id,
                "primaryArtistKey": canonical_artist_key(
                    row.get("primaryArtist")
                ),
                "relationshipType": str(
                    row.get("relationshipType") or ""
                ).strip(),
                "members": members,
            }
        )

    return families


def build_artist_display_names(
    library_tracks: Sequence[Mapping[str, Any]],
    snapshot_rows: Sequence[Mapping[str, Any]],
) -> dict[str, str]:
    """Create canonicalKey-to-displayName presentation metadata."""

    display_names: dict[str, str] = {}

    raw_names = [
        row.get("Artist")
        for row in library_tracks
    ] + [
        row.get("artist")
        for row in snapshot_rows
    ]

    for raw_name in raw_names:
        identity = resolve_artist_identity(raw_name)

        if identity is None:
            continue

        display_names.setdefault(
            identity["canonicalKey"],
            identity["displayName"],
        )

    return display_names


def build_family_sums(
    artist_values: Mapping[str, int | float],
    families: Sequence[Mapping[str, Any]],
) -> dict[str, int | float]:
    """Build a separate additive family population."""

    results: dict[str, int | float] = {}

    for family in families:
        family_id = str(
            family.get("familyId") or ""
        ).strip()

        total: int | float = sum(
            artist_values.get(str(member), 0)
            for member in family.get("members") or []
        )

        if family_id and total > 0:
            results[family_id] = total

    return results


def build_family_unions(
    artist_sets: Mapping[str, Sequence[Any]],
    families: Sequence[Mapping[str, Any]],
) -> dict[str, list[Any]]:
    """Build a separate deduplicated family evidence population."""

    results: dict[str, list[Any]] = {}

    for family in families:
        family_id = str(
            family.get("familyId") or ""
        ).strip()

        union_values: set[Any] = set()

        for member in family.get("members") or []:
            union_values.update(
                artist_sets.get(str(member), [])
            )

        if family_id and union_values:
            results[family_id] = sorted(union_values)

    return results


def rank_metric_values(
    values: Mapping[str, int | float],
) -> dict[str, dict[str, Any]]:
    """Rank one metric-specific positive-evidence population."""

    return rank_positive_population(
        [
            {
                "entityId": entity_id,
                "status": "ranked",
                "value": value,
            }
            for entity_id, value in values.items()
        ]
    )


def build_runtime_snapshot(
    *,
    library_tracks: Iterable[Mapping[str, Any]],
    snapshot_rows: Iterable[Mapping[str, Any]],
    curated_families: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Build separately ranked artist and family populations."""

    library_tracks = list(library_tracks)
    snapshot_rows = list(snapshot_rows)
    curated_families = list(curated_families)

    artist_display_names = build_artist_display_names(
        library_tracks,
        snapshot_rows,
    )

    artist_library_values = build_library_evidence_values(
        library_tracks,
        canonical_artist_key,
    )

    artist_year_sets = build_years_represented_sets(
        library_tracks,
        canonical_artist_key,
        date_field="Last Played Date",
    )

    artist_year_values = {
        artist: len(years)
        for artist, years in artist_year_sets.items()
        if years
    }

    artist_observation_values = (
        build_recent_apple_observation_values(
            snapshot_rows,
            canonical_artist_key,
        )
    )

    artist_object_sets = (
        build_historical_unique_object_sets(
            snapshot_rows,
            canonical_artist_key,
        )
    )

    artist_object_values = {
        artist: len(object_keys)
        for artist, object_keys in artist_object_sets.items()
        if object_keys
    }

    family_library_values = build_family_sums(
        artist_library_values,
        curated_families,
    )

    family_year_sets = build_family_unions(
        artist_year_sets,
        curated_families,
    )

    family_year_values = {
        family_id: len(years)
        for family_id, years in family_year_sets.items()
        if years
    }

    family_observation_values = build_family_sums(
        artist_observation_values,
        curated_families,
    )

    family_object_sets = build_family_unions(
        artist_object_sets,
        curated_families,
    )

    family_object_values = {
        family_id: len(object_keys)
        for family_id, object_keys in family_object_sets.items()
        if object_keys
    }

    artist_populations = {
        "library_evidence_records": artist_library_values,
        "historical_years_represented": artist_year_values,
        "recent_apple_observations": artist_observation_values,
        "historical_unique_object_count": artist_object_values,
    }

    family_populations = {
        "library_evidence_records": family_library_values,
        "historical_years_represented": family_year_values,
        "recent_apple_observations": family_observation_values,
        "historical_unique_object_count": family_object_values,
    }

    raw_artist_bearing_count = sum(
        1
        for row in snapshot_rows
        if str(row.get("artist") or "").strip()
    )

    canonical_artist_bearing_count = sum(
        1
        for row in snapshot_rows
        if canonical_artist_key(row.get("artist"))
    )

    return {
        "schemaVersion": RUNTIME_SCHEMA_VERSION,
        "sourceSummary": {
            "libraryRowCount": len(library_tracks),
            "snapshotRowCount": len(snapshot_rows),
            "rawArtistBearingSnapshotRowCount": (
                raw_artist_bearing_count
            ),
            "canonicalArtistBearingSnapshotRowCount": (
                canonical_artist_bearing_count
            ),
            "curatedFamilyCount": len(curated_families),
        },
        "artistDisplayNames": artist_display_names,
        "artistPopulations": artist_populations,
        "artistEvidenceSets": {
            "historical_years_represented": artist_year_sets,
            "historical_unique_object_count": artist_object_sets,
        },
        "artistRankings": {
            metric_key: rank_metric_values(values)
            for metric_key, values in artist_populations.items()
        },
        "familyDefinitions": curated_families,
        "familyPopulations": family_populations,
        "familyEvidenceSets": {
            "historical_years_represented": family_year_sets,
            "historical_unique_object_count": family_object_sets,
        },
        "familyRankings": {
            metric_key: rank_metric_values(values)
            for metric_key, values in family_populations.items()
        },
        "unavailableMetrics": {
            "actual_plays": unavailable_metric_result(
                "actual_plays",
                "plays",
            ),
            "listening_duration_ms": unavailable_metric_result(
                "listening_duration_ms",
                "milliseconds",
            ),
        },
    }


def load_and_build_runtime_snapshot(
    *,
    library_tracks_path: Path,
    snapshot_path: Path,
    families_path: Path,
) -> dict[str, Any]:
    """Load governed sources and build the complete snapshot."""

    return build_runtime_snapshot(
        library_tracks=load_library_tracks(
            library_tracks_path
        ),
        snapshot_rows=load_snapshot_rows(
            snapshot_path
        ),
        curated_families=load_curated_families(
            families_path
        ),
    )

from functools import lru_cache


RESPONSE_SCHEMA_VERSION = (
    "music.artist-comparative-standing.response.v0"
)

SUPPORTED_METRIC_DEFINITIONS = (
    {
        "metricKey": "library_evidence_records",
        "unit": "records",
        "source": "apple-music-library-tracks",
    },
    {
        "metricKey": "historical_years_represented",
        "unit": "years",
        "source": "apple-music-library-tracks",
    },
    {
        "metricKey": "recent_apple_observations",
        "unit": "observations",
        "source": "apple-snapshot-warehouse",
    },
    {
        "metricKey": "historical_unique_object_count",
        "unit": "objects",
        "source": "apple-snapshot-warehouse",
    },
)


def select_artist_comparative_standing(
    runtime_snapshot: Mapping[str, Any],
    artist_name: Any,
) -> dict[str, Any]:
    """
    Select one governed standalone-artist response.

    Ranking values are copied from runtime_snapshot. This function never
    recalculates ranks or combines artist and family populations.
    """

    identity = resolve_artist_identity(artist_name)

    if identity is None:
        return {
            "schemaVersion": RESPONSE_SCHEMA_VERSION,
            "status": "identity_unresolved",
            "entityType": "artist",
            "canonicalKey": None,
            "displayName": str(artist_name or "").strip() or None,
            "reviewedFamilyIds": [],
            "metrics": [],
        }

    canonical_key = identity["canonicalKey"]
    display_name = (
        runtime_snapshot.get("artistDisplayNames", {}).get(
            canonical_key
        )
        or identity["displayName"]
    )

    metrics: list[dict[str, Any]] = []

    for definition in SUPPORTED_METRIC_DEFINITIONS:
        metric_key = definition["metricKey"]

        rankings = runtime_snapshot.get(
            "artistRankings",
            {},
        ).get(
            metric_key,
            {},
        )

        ranking = rankings.get(canonical_key)

        if ranking is None:
            metrics.append(
                {
                    "metricKey": metric_key,
                    "status": "searched_no_evidence",
                    "value": None,
                    "unit": definition["unit"],
                    "rank": None,
                    "percentile": None,
                    "populationSize": len(rankings),
                    "entityType": "artist",
                    "source": definition["source"],
                    "sourceLimitation": None,
                    "calculationVersion": (
                        "music.artist-comparative-standing.v0"
                    ),
                }
            )

            continue

        metrics.append(
            {
                "metricKey": metric_key,
                "status": ranking["status"],
                "value": ranking["value"],
                "unit": definition["unit"],
                "rank": ranking["rank"],
                "percentile": ranking["percentile"],
                "populationSize": ranking["populationSize"],
                "entityType": "artist",
                "source": definition["source"],
                "sourceLimitation": None,
                "calculationVersion": (
                    "music.artist-comparative-standing.v0"
                ),
            }
        )

    unavailable_metrics = runtime_snapshot.get(
        "unavailableMetrics",
        {},
    )

    for metric_key in (
        "actual_plays",
        "listening_duration_ms",
    ):
        unavailable = unavailable_metrics.get(metric_key)

        if unavailable is None:
            raise ValueError(
                f"Unavailable metric is missing: {metric_key}"
            )

        metrics.append(dict(unavailable))

    reviewed_family_ids = sorted(
        str(family.get("familyId") or "").strip()
        for family in runtime_snapshot.get(
            "familyDefinitions",
            [],
        )
        if canonical_key in (
            family.get("members") or []
        )
        and str(family.get("familyId") or "").strip()
    )

    supported_statuses = {
        metric["status"]
        for metric in metrics
        if metric["metricKey"]
        not in {
            "actual_plays",
            "listening_duration_ms",
        }
    }

    response_status = (
        "searched_no_evidence"
        if supported_statuses == {"searched_no_evidence"}
        else "available"
    )

    return {
        "schemaVersion": RESPONSE_SCHEMA_VERSION,
        "status": response_status,
        "entityType": "artist",
        "canonicalKey": canonical_key,
        "displayName": display_name,
        "reviewedFamilyIds": reviewed_family_ids,
        "metrics": metrics,
    }

DEFAULT_REPO_ROOT = SCRIPT_DIR.parents[3]
DEFAULT_LIBRARY_TRACKS_PATH = (
    Path.home()
    / "Downloads"
    / "apple-music-working"
    / "Apple_Media_Services_python"
    / "Apple_Media_Services"
    / "Apple Music Activity"
    / "Apple Music Library Tracks.json.zip"
)
DEFAULT_SNAPSHOT_PATH = (
    DEFAULT_REPO_ROOT
    / "data"
    / "music"
    / "live"
    / "apple_snapshot_warehouse.csv"
)
DEFAULT_FAMILIES_PATH = (
    DEFAULT_REPO_ROOT
    / "data"
    / "music"
    / "curated"
    / "artistFamilies.json"
)
DEFAULT_RANKING_MODULE_PATH = (
    SCRIPT_DIR
    / "artist_comparative_standing.py"
)
DEFAULT_IDENTITY_MODULE_PATH = (
    IDENTITY_DIR
    / "music_identity.py"
)
DEFAULT_CACHE_DIRECTORY = (
    DEFAULT_REPO_ROOT
    / "data"
    / "music"
    / "generated"
    / "comparative-standing"
)
DEFAULT_CACHE_PATH = (
    DEFAULT_CACHE_DIRECTORY
    / "artist-comparative-standing-cache-v0.sqlite3"
)
DEFAULT_CACHE_MANIFEST_PATH = (
    DEFAULT_CACHE_DIRECTORY
    / "artist-comparative-standing-cache-manifest-v0.json"
)

SQLITE_CACHE_MANIFEST_SCHEMA_VERSION = (
    "music.artist-comparative-standing.sqlite-cache-manifest.v0"
)


class ComparativeStandingCacheError(RuntimeError):
    """Raised when the governed SQLite cache is unavailable or stale."""


def sha256_file(path: Path) -> str:
    """Return an uppercase SHA-256 fingerprint for one file."""

    import hashlib

    digest = hashlib.sha256()

    with path.open("rb") as handle:
        for chunk in iter(
            lambda: handle.read(1024 * 1024),
            b"",
        ):
            digest.update(chunk)

    return digest.hexdigest().upper()


def _validate_cache_input(
    record: Mapping[str, Any],
    *,
    path: Path,
    label: str,
) -> None:
    if not path.exists():
        raise ComparativeStandingCacheError(
            f"Governed cache input is missing: {label}"
        )

    stat = path.stat()

    if record.get("sizeBytes") != stat.st_size:
        raise ComparativeStandingCacheError(
            f"Governed cache input size changed: {label}"
        )

    if record.get("modifiedTimeNs") != stat.st_mtime_ns:
        raise ComparativeStandingCacheError(
            f"Governed cache input timestamp changed: {label}"
        )

    expected_hash = str(
        record.get("sha256") or ""
    ).upper()

    if expected_hash != sha256_file(path):
        raise ComparativeStandingCacheError(
            f"Governed cache input hash changed: {label}"
        )


def _load_validated_cache_manifest(
    *,
    cache_path: Path,
    manifest_path: Path,
    library_tracks_path: Path,
    snapshot_path: Path,
    families_path: Path,
    runtime_path: Path,
    ranking_path: Path,
    identity_path: Path,
) -> dict[str, Any]:
    if not manifest_path.exists():
        raise ComparativeStandingCacheError(
            "Comparative Standing SQLite cache manifest was not found."
        )

    if not cache_path.exists():
        raise ComparativeStandingCacheError(
            "Comparative Standing SQLite cache was not found."
        )

    manifest = json.loads(
        manifest_path.read_text(
            encoding="utf-8-sig"
        )
    )

    if not isinstance(manifest, Mapping):
        raise ComparativeStandingCacheError(
            "Comparative Standing cache manifest must be an object."
        )

    if (
        manifest.get("schemaVersion")
        != SQLITE_CACHE_MANIFEST_SCHEMA_VERSION
    ):
        raise ComparativeStandingCacheError(
            "Comparative Standing SQLite cache manifest schema changed."
        )

    if (
        manifest.get("runtimeSchemaVersion")
        != RUNTIME_SCHEMA_VERSION
    ):
        raise ComparativeStandingCacheError(
            "Comparative Standing runtime schema changed."
        )

    if (
        manifest.get("responseSchemaVersion")
        != RESPONSE_SCHEMA_VERSION
    ):
        raise ComparativeStandingCacheError(
            "Comparative Standing response schema changed."
        )

    sources = manifest.get("sources")

    if not isinstance(sources, Mapping):
        raise ComparativeStandingCacheError(
            "Comparative Standing cache source records are missing."
        )

    source_inputs = (
        (
            "libraryTracks",
            library_tracks_path,
        ),
        (
            "snapshotWarehouse",
            snapshot_path,
        ),
        (
            "artistFamilies",
            families_path,
        ),
    )

    for source_key, source_path in source_inputs:
        record = sources.get(source_key)

        if not isinstance(record, Mapping):
            raise ComparativeStandingCacheError(
                f"Cache source record is missing: {source_key}"
            )

        _validate_cache_input(
            record,
            path=source_path,
            label=source_key,
        )

    code = manifest.get("code")

    if not isinstance(code, Mapping):
        raise ComparativeStandingCacheError(
            "Comparative Standing cache code records are missing."
        )

    code_inputs = (
        (
            "runtime",
            runtime_path,
        ),
        (
            "ranking",
            ranking_path,
        ),
        (
            "identity",
            identity_path,
        ),
    )

    for code_key, code_path in code_inputs:
        record = code.get(code_key)

        if not isinstance(record, Mapping):
            raise ComparativeStandingCacheError(
                f"Cache code record is missing: {code_key}"
            )

        _validate_cache_input(
            record,
            path=code_path,
            label=code_key,
        )

    cache_record = manifest.get("cache")

    if not isinstance(cache_record, Mapping):
        raise ComparativeStandingCacheError(
            "Comparative Standing cache record is missing."
        )

    cache_stat = cache_path.stat()

    if cache_record.get("sizeBytes") != cache_stat.st_size:
        raise ComparativeStandingCacheError(
            "Comparative Standing SQLite cache size changed."
        )

    expected_cache_hash = str(
        cache_record.get("sha256") or ""
    ).upper()

    if expected_cache_hash != sha256_file(cache_path):
        raise ComparativeStandingCacheError(
            "Comparative Standing SQLite cache hash changed."
        )

    return dict(manifest)


def load_cached_artist_comparative_standing(
    artist_name: Any,
    *,
    cache_path: Path = DEFAULT_CACHE_PATH,
    manifest_path: Path = DEFAULT_CACHE_MANIFEST_PATH,
    library_tracks_path: Path = DEFAULT_LIBRARY_TRACKS_PATH,
    snapshot_path: Path = DEFAULT_SNAPSHOT_PATH,
    families_path: Path = DEFAULT_FAMILIES_PATH,
    runtime_path: Path = Path(__file__).resolve(),
    ranking_path: Path = DEFAULT_RANKING_MODULE_PATH,
    identity_path: Path = DEFAULT_IDENTITY_MODULE_PATH,
) -> dict[str, Any]:
    """Load one response from the fingerprint-validated SQLite cache."""

    identity = resolve_artist_identity(artist_name)

    if identity is None:
        return {
            "schemaVersion": RESPONSE_SCHEMA_VERSION,
            "status": "identity_unresolved",
            "entityType": "artist",
            "canonicalKey": None,
            "displayName": str(artist_name or "").strip() or None,
            "reviewedFamilyIds": [],
            "metrics": [],
        }

    _load_validated_cache_manifest(
        cache_path=cache_path,
        manifest_path=manifest_path,
        library_tracks_path=library_tracks_path,
        snapshot_path=snapshot_path,
        families_path=families_path,
        runtime_path=runtime_path,
        ranking_path=ranking_path,
        identity_path=identity_path,
    )

    import sqlite3

    cache_uri = (
        f"file:{cache_path.resolve().as_posix()}?mode=ro"
    )

    with sqlite3.connect(
        cache_uri,
        uri=True,
    ) as connection:
        response_row = connection.execute(
            """
            SELECT response_json
            FROM artist_responses
            WHERE canonical_key = ?
            """,
            (
                identity["canonicalKey"],
            ),
        ).fetchone()

        if response_row is not None:
            response = json.loads(
                response_row[0]
            )

            if (
                response.get("schemaVersion")
                != RESPONSE_SCHEMA_VERSION
            ):
                raise ComparativeStandingCacheError(
                    "Cached artist response schema changed."
                )

            return response

        template_row = connection.execute(
            """
            SELECT value_json
            FROM cache_metadata
            WHERE key = 'noEvidenceTemplate'
            """
        ).fetchone()

    if template_row is None:
        raise ComparativeStandingCacheError(
            "No-evidence response template is missing."
        )

    response = json.loads(
        template_row[0]
    )
    response["canonicalKey"] = identity["canonicalKey"]
    response["displayName"] = identity["displayName"]
    response["reviewedFamilyIds"] = []

    return response


@lru_cache(maxsize=1)
def load_default_runtime_snapshot() -> dict[str, Any]:
    """Build the full governed snapshot for validation and regeneration."""

    return load_and_build_runtime_snapshot(
        library_tracks_path=DEFAULT_LIBRARY_TRACKS_PATH,
        snapshot_path=DEFAULT_SNAPSHOT_PATH,
        families_path=DEFAULT_FAMILIES_PATH,
    )


def load_default_artist_comparative_standing(
    artist_name: Any,
) -> dict[str, Any]:
    """Select one artist response from the governed SQLite cache."""

    return load_cached_artist_comparative_standing(
        artist_name,
    )
