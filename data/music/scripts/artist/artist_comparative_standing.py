from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime
from typing import Any, Callable, Iterable, Mapping, Sequence


CALCULATION_VERSION = "music.artist-comparative-standing.v0"
RANKABLE_STATUS = "ranked"
UNAVAILABLE_SOURCE = "actual-listening-event-projection-v1"
UNAVAILABLE_SOURCE_LIMITATION = (
    "Artist-level governed Actual Listening is unavailable because "
    "the current event projection does not contain artist identity."
)


class ComparativeStandingValidationError(ValueError):
    """Validation failure carrying a stable machine-readable error code."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


def _positive_number(value: Any) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and value > 0
    )


def _canonical_artist(
    value: Any,
    canonicalize_artist: Callable[[Any], Any],
) -> str:
    resolved = canonicalize_artist(value)

    if resolved is None:
        return ""

    if isinstance(resolved, Mapping):
        for key in (
            "canonicalArtist",
            "canonical_artist",
            "artist",
            "name",
            "value",
        ):
            candidate = str(resolved.get(key) or "").strip()

            if candidate:
                return candidate

        return ""

    return str(resolved).strip()


def extract_calendar_year(value: Any) -> int | None:
    """Extract an ISO-compatible calendar year without using fallback fields."""

    text = str(value or "").strip()

    if not text:
        return None

    try:
        return datetime.fromisoformat(
            text.replace("Z", "+00:00")
        ).year
    except ValueError:
        return None


def rank_positive_population(
    entries: Iterable[Mapping[str, Any]],
) -> dict[str, dict[str, Any]]:
    """
    Rank positive supported evidence using competition rank and midpoint
    percentiles.

    Entries outside status ``ranked`` or without a positive numeric value
    never enter the population.
    """

    eligible: list[dict[str, Any]] = []

    for raw_entry in entries:
        entity_id = str(raw_entry.get("entityId") or "").strip()
        status = str(raw_entry.get("status") or "").strip()
        value = raw_entry.get("value")

        if (
            entity_id
            and status == RANKABLE_STATUS
            and _positive_number(value)
        ):
            eligible.append(
                {
                    "entityId": entity_id,
                    "value": value,
                }
            )

    values = [entry["value"] for entry in eligible]
    population_size = len(values)
    results: dict[str, dict[str, Any]] = {}

    for entry in eligible:
        value = entry["value"]
        greater_count = sum(
            1
            for candidate in values
            if candidate > value
        )
        lower_count = sum(
            1
            for candidate in values
            if candidate < value
        )
        tie_count = sum(
            1
            for candidate in values
            if candidate == value
        )

        rank = 1 + greater_count

        if population_size == 1:
            result_status = "insufficient_population"
            percentile = None
        else:
            result_status = RANKABLE_STATUS
            percentile = (
                100.0
                * (
                    lower_count
                    + 0.5 * (tie_count - 1)
                )
                / (population_size - 1)
            )
            percentile = round(percentile, 6)

        results[entry["entityId"]] = {
            "status": result_status,
            "value": value,
            "rank": rank,
            "percentile": percentile,
            "populationSize": population_size,
        }

    return results


def build_library_evidence_values(
    records: Iterable[Mapping[str, Any]],
    canonicalize_artist: Callable[[Any], Any],
    *,
    artist_field: str = "Artist",
) -> dict[str, int]:
    """Count full-library records by canonical artist."""

    values: Counter[str] = Counter()

    for record in records:
        artist = _canonical_artist(
            record.get(artist_field),
            canonicalize_artist,
        )

        if artist:
            values[artist] += 1

    return dict(values)


def build_years_represented_sets(
    records: Iterable[Mapping[str, Any]],
    canonicalize_artist: Callable[[Any], Any],
    *,
    artist_field: str = "Artist",
    date_field: str = "Last Played Date",
) -> dict[str, list[int]]:
    """Collect distinct Last Played Date calendar years by canonical artist."""

    values: defaultdict[str, set[int]] = defaultdict(set)

    for record in records:
        artist = _canonical_artist(
            record.get(artist_field),
            canonicalize_artist,
        )
        year = extract_calendar_year(record.get(date_field))

        if artist and year is not None:
            values[artist].add(year)

    return {
        artist: sorted(years)
        for artist, years in values.items()
        if years
    }


def build_years_represented_values(
    records: Iterable[Mapping[str, Any]],
    canonicalize_artist: Callable[[Any], Any],
    *,
    artist_field: str = "Artist",
    date_field: str = "Last Played Date",
) -> dict[str, int]:
    """Count distinct governed represented years by canonical artist."""

    year_sets = build_years_represented_sets(
        records,
        canonicalize_artist,
        artist_field=artist_field,
        date_field=date_field,
    )

    return {
        artist: len(years)
        for artist, years in year_sets.items()
    }


def build_recent_apple_observation_values(
    rows: Iterable[Mapping[str, Any]],
    canonicalize_artist: Callable[[Any], Any],
    *,
    artist_field: str = "artist",
) -> dict[str, int]:
    """Count every artist-bearing snapshot row as one observation."""

    values: Counter[str] = Counter()

    for row in rows:
        artist = _canonical_artist(
            row.get(artist_field),
            canonicalize_artist,
        )

        if artist:
            values[artist] += 1

    return dict(values)


def logical_object_key(
    entity_type: Any,
    entity_id: Any,
) -> str:
    """Create the governed entity_type + entity_id logical-object key."""

    normalized_type = str(entity_type or "").strip().casefold()
    normalized_id = str(entity_id or "").strip()

    if not normalized_id:
        raise ComparativeStandingValidationError(
            "missing_entity_id",
            "Historical Unique Object Count requires a nonblank entity_id.",
        )

    if not normalized_type:
        raise ComparativeStandingValidationError(
            "missing_entity_type",
            "Historical Unique Object Count requires a nonblank entity_type.",
        )

    return f"{normalized_type}::{normalized_id}"


def build_historical_unique_object_sets(
    rows: Iterable[Mapping[str, Any]],
    canonicalize_artist: Callable[[Any], Any],
    *,
    artist_field: str = "artist",
    entity_type_field: str = "entity_type",
    entity_id_field: str = "entity_id",
) -> dict[str, list[str]]:
    """
    Deduplicate snapshot objects by entity_type + entity_id.

    A governed typed key resolving to more than one canonical artist fails
    validation instead of being counted silently.
    """

    artist_objects: defaultdict[str, set[str]] = defaultdict(set)
    key_artists: defaultdict[str, set[str]] = defaultdict(set)

    for row in rows:
        artist = _canonical_artist(
            row.get(artist_field),
            canonicalize_artist,
        )

        if not artist:
            continue

        typed_key = logical_object_key(
            row.get(entity_type_field),
            row.get(entity_id_field),
        )

        key_artists[typed_key].add(artist)
        artist_objects[artist].add(typed_key)

    conflicting_keys = {
        typed_key: sorted(artists)
        for typed_key, artists in key_artists.items()
        if len(artists) > 1
    }

    if conflicting_keys:
        first_key = sorted(conflicting_keys)[0]

        raise ComparativeStandingValidationError(
            "typed_key_artist_conflict",
            (
                f"Logical object {first_key!r} resolved to multiple "
                f"canonical artists: {conflicting_keys[first_key]}"
            ),
        )

    return {
        artist: sorted(object_keys)
        for artist, object_keys in artist_objects.items()
        if object_keys
    }


def build_historical_unique_object_values(
    rows: Iterable[Mapping[str, Any]],
    canonicalize_artist: Callable[[Any], Any],
    *,
    artist_field: str = "artist",
    entity_type_field: str = "entity_type",
    entity_id_field: str = "entity_id",
) -> dict[str, int]:
    """Count governed logical objects by canonical artist."""

    object_sets = build_historical_unique_object_sets(
        rows,
        canonicalize_artist,
        artist_field=artist_field,
        entity_type_field=entity_type_field,
        entity_id_field=entity_id_field,
    )

    return {
        artist: len(object_keys)
        for artist, object_keys in object_sets.items()
    }


def build_additive_family_population(
    artist_values: Mapping[str, int | float],
    reviewed_families: Sequence[Mapping[str, Any]],
    canonicalize_artist: Callable[[Any], Any],
) -> dict[str, int | float]:
    """
    Build a separate reviewed-family population from additive artist values.

    Standalone artist values are never modified.
    """

    family_values: dict[str, int | float] = {}

    for family in reviewed_families:
        family_id = str(
            family.get("familyId")
            or family.get("familyName")
            or ""
        ).strip()

        if not family_id:
            continue

        total: int | float = 0

        for member in family.get("members") or []:
            canonical_member = _canonical_artist(
                member,
                canonicalize_artist,
            )

            if canonical_member:
                total += artist_values.get(canonical_member, 0)

        if _positive_number(total):
            family_values[family_id] = total

    return family_values


def unavailable_metric_result(
    metric_key: str,
    unit: str,
    *,
    entity_type: str = "artist",
    source: str = UNAVAILABLE_SOURCE,
    source_limitation: str = UNAVAILABLE_SOURCE_LIMITATION,
) -> dict[str, Any]:
    """Return the approved unavailable metric response shape."""

    return {
        "metricKey": metric_key,
        "status": "unavailable",
        "value": None,
        "unit": unit,
        "rank": None,
        "percentile": None,
        "populationSize": None,
        "entityType": entity_type,
        "source": source,
        "sourceLimitation": source_limitation,
        "calculationVersion": CALCULATION_VERSION,
    }