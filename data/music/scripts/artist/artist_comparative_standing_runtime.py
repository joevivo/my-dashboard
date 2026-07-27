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