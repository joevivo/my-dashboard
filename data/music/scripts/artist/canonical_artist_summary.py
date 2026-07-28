from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys
from typing import Any, Mapping


SCRIPT_DIR = Path(__file__).resolve().parent
IDENTITY_DIR = SCRIPT_DIR.parent / "identity"

if str(IDENTITY_DIR) not in sys.path:
    sys.path.insert(0, str(IDENTITY_DIR))

from music_identity import resolve_artist


SCHEMA_VERSION = "music.canonical-artist-summary.v1"

ALLOWED_STATUSES = frozenset({
    "available",
    "partial",
    "searched_no_evidence",
    "identity_unresolved",
    "unavailable",
    "unsupported",
})

REQUIRED_TOP_LEVEL_FIELDS = (
    "schemaVersion",
    "status",
    "query",
    "entity",
    "scope",
    "coverage",
    "summary",
    "comparativeStanding",
    "family",
    "confidence",
    "limitations",
    "provenance",
    "suggestedInvestigations",
    "investigation",
    "compatibility",
)


class CanonicalArtistSummaryValidationError(ValueError):
    pass


def new_canonical_artist_summary(query: Any) -> dict[str, Any]:
    original = str(query or "").strip()

    return {
        "schemaVersion": SCHEMA_VERSION,
        "status": "identity_unresolved",
        "query": {
            "original": original,
            "normalized": original.casefold(),
        },
        "entity": {
            "entityType": "artist",
            "displayName": None,
            "canonicalKey": None,
            "aliases": [],
            "identityStatus": "unresolved",
            "identityConfidence": "low",
            "identitySource": "music_identity",
        },
        "scope": {
            "scopeType": "artist",
            "familyId": None,
            "familyName": None,
            "familyMembers": [],
            "primaryArtistKey": None,
        },
        "coverage": [],
        "summary": {
            "actualListening": {"status": "not_searched"},
            "libraryEvidence": {"status": "not_searched"},
            "recentApple": {
                "current": {"status": "not_searched"},
                "historicalSnapshots": {"status": "not_searched"},
            },
            "historicalSpan": {"status": "unavailable"},
            "catalog": {"status": "unavailable"},
        },
        "comparativeStanding": {"status": "unavailable"},
        "family": {
            "status": "not_applicable",
            "familyId": None,
            "familyName": None,
            "members": [],
            "relationshipType": None,
            "metrics": None,
            "provenance": [],
        },
        "confidence": {"overall": "unavailable"},
        "limitations": [],
        "provenance": [],
        "suggestedInvestigations": [],
        "investigation": {},
        "compatibility": {},
    }


def validate_canonical_artist_summary(response: Mapping[str, Any]) -> None:
    if not isinstance(response, Mapping):
        raise CanonicalArtistSummaryValidationError(
            "Canonical Artist summary must be a mapping."
        )

    missing = [
        field
        for field in REQUIRED_TOP_LEVEL_FIELDS
        if field not in response
    ]

    if missing:
        raise CanonicalArtistSummaryValidationError(
            f"Missing required fields: {', '.join(missing)}"
        )

    if response["schemaVersion"] != SCHEMA_VERSION:
        raise CanonicalArtistSummaryValidationError(
            "Unexpected canonical Artist schema version."
        )

    if response["status"] not in ALLOWED_STATUSES:
        raise CanonicalArtistSummaryValidationError(
            "Unsupported canonical Artist status."
        )

    for field in ("query", "entity", "scope", "summary"):
        if not isinstance(response[field], Mapping):
            raise CanonicalArtistSummaryValidationError(
                f"{field} must be a mapping."
            )

    for field in (
        "coverage",
        "limitations",
        "provenance",
        "suggestedInvestigations",
    ):
        if not isinstance(response[field], list):
            raise CanonicalArtistSummaryValidationError(
                f"{field} must be a list."
            )

def build_base_canonical_artist_summary(
    base_result: Mapping[str, Any],
    query: Any = None,
) -> dict[str, Any]:
    if not isinstance(base_result, Mapping):
        raise CanonicalArtistSummaryValidationError(
            "Base Artist result must be a mapping."
        )

    original_query = (
        query
        if query is not None
        else base_result.get("query")
    )

    response = new_canonical_artist_summary(original_query)

    resolved_name = str(
        base_result.get("resolvedArtist")
        or base_result.get("artist")
        or original_query
        or ""
    ).strip()

    identity = resolve_artist(resolved_name) if resolved_name else {}

    canonical_key = str(
        identity.get("canonicalKey") or ""
    ).strip()

    if canonical_key:
        response["status"] = "partial"
        response["entity"] = {
            "entityType": str(identity.get("type") or "artist"),
            "displayName": str(
                identity.get("displayName") or resolved_name
            ).strip(),
            "canonicalKey": canonical_key,
            "aliases": list(identity.get("aliases") or []),
            "identityStatus": "resolved",
            "identityConfidence": str(
                identity.get("confidence") or "normalized"
            ),
            "identitySource": str(
                base_result.get("identitySource")
                or "music_identity"
            ),
        }

    library_count = base_result.get("libraryEvidenceRecords")

    if isinstance(library_count, (int, float)):
        library_status = (
            "searched_with_evidence"
            if library_count > 0
            else "searched_no_evidence"
        )
    else:
        library_status = "unavailable"

    activity_source = str(
        base_result.get("playActivitySource") or ""
    ).strip()

    actual_source_id = (
        activity_source
        if activity_source and activity_source != "missing"
        else "apple_daily_track_summary"
    )

    actual_values = (
        base_result.get("actualPlays"),
        base_result.get("actualSkips"),
        base_result.get("listeningDurationMs"),
    )

    if not activity_source or activity_source == "missing":
        actual_status = "unavailable"
    elif any(
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and value > 0
        for value in actual_values
    ):
        actual_status = "searched_with_evidence"
    else:
        actual_status = "searched_no_evidence"

    response["coverage"] = [
        {
            "sourceId": "apple_music_library_tracks",
            "sourceFamily": "library_evidence",
            "status": library_status,
            "coverageBasis": (
                "Apple Music Library Tracks Last Played Date"
            ),
            "limitations": [],
        },
        {
            "sourceId": actual_source_id,
            "sourceFamily": "actual_listening",
            "status": actual_status,
            "coverageBasis": "Apple Music daily track summary",
            "limitations": [],
        },
    ]

    response["summary"]["actualListening"] = {
        "status": actual_status,
        "actualPlays": base_result.get("actualPlays"),
        "actualSkips": base_result.get("actualSkips"),
        "listeningDurationMs": base_result.get(
            "listeningDurationMs"
        ),
        "hoursListened": base_result.get("hoursListened"),
        "topSongs": deepcopy(
            base_result.get("actualTopSongs") or []
        ),
        "sourceId": actual_source_id,
    }

    years_represented = (
        base_result.get("yearsRepresented")
        if base_result.get("yearsRepresented") is not None
        else base_result.get("yearsActive")
    )

    response["summary"]["libraryEvidence"] = {
        "status": library_status,
        "recordCount": library_count,
        "yearsRepresented": years_represented,
        "firstEvidenceDate": base_result.get("firstPlayedDate"),
        "latestEvidenceDate": base_result.get("latestPlayedDate"),
        "topTracks": deepcopy(base_result.get("topSongs") or []),
        "topAlbums": deepcopy(base_result.get("topAlbums") or []),
        "timeline": deepcopy(base_result.get("timeline") or []),
        "sourceId": "apple_music_library_tracks",
    }

    response["summary"]["historicalSpan"] = {
        "status": library_status,
        "firstEvidenceDate": base_result.get("firstPlayedDate"),
        "latestEvidenceDate": base_result.get("latestPlayedDate"),
        "yearsRepresented": years_represented,
    }

    response["investigation"] = {
        "suggestedInvestigations": deepcopy(
            base_result.get("suggestedInvestigations") or []
        )
    }

    response["compatibility"] = deepcopy(dict(base_result))

    validate_canonical_artist_summary(response)
    return response
ALLOWED_COVERAGE_STATUSES = frozenset({
    "searched_with_evidence",
    "searched_no_evidence",
    "not_searched",
    "outside_coverage",
    "unavailable",
    "stale",
    "unsupported",
})


def _recent_apple_status(
    explicit_status: Any,
    *values: Any,
) -> str:
    status = str(explicit_status or "").strip()

    if status in ALLOWED_COVERAGE_STATUSES:
        return status

    if any(
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and value > 0
        for value in values
    ):
        return "searched_with_evidence"

    return "not_searched"


def _coverage_metric(
    value: Any,
    status: str,
) -> Any:
    if status == "searched_no_evidence":
        return 0

    if status != "searched_with_evidence":
        return None

    return value


def _upsert_coverage_record(
    response: dict[str, Any],
    record: Mapping[str, Any],
) -> None:
    source_id = record["sourceId"]

    response["coverage"] = [
        item
        for item in response["coverage"]
        if item.get("sourceId") != source_id
    ]

    response["coverage"].append(dict(record))


def apply_recent_apple_projection(
    response: Mapping[str, Any],
    bridge: Mapping[str, Any],
) -> dict[str, Any]:
    if not isinstance(response, Mapping):
        raise CanonicalArtistSummaryValidationError(
            "Canonical response must be a mapping."
        )

    if not isinstance(bridge, Mapping):
        raise CanonicalArtistSummaryValidationError(
            "Artist bridge must be a mapping."
        )

    result = deepcopy(dict(response))

    live = bridge.get("live")

    if not isinstance(live, Mapping):
        live = {}

    recent_count = live.get("recentObjectCount")
    heavy_count = live.get("heavyRotationCount")

    current_status = _recent_apple_status(
        live.get("currentStatus"),
        recent_count,
        heavy_count,
    )

    snapshot = live.get("snapshotHistory")

    if not isinstance(snapshot, Mapping):
        snapshot = {}

    observation_count = snapshot.get("observationCount")
    snapshot_count = snapshot.get("snapshotCount")
    unique_count = snapshot.get("uniqueObjectCount")

    snapshot_status = _recent_apple_status(
        snapshot.get("status"),
        observation_count,
        snapshot_count,
        unique_count,
    )

    result["summary"]["recentApple"] = {
        "current": {
            "status": current_status,
            "recentObjectCount": _coverage_metric(
                recent_count,
                current_status,
            ),
            "heavyRotationCount": _coverage_metric(
                heavy_count,
                current_status,
            ),
            "objects": {
                "recent": deepcopy(
                    live.get("recentObjects") or []
                ),
                "heavyRotation": deepcopy(
                    live.get("heavyRotationObjects") or []
                ),
            },
        },
        "historicalSnapshots": {
            "status": snapshot_status,
            "observationCount": _coverage_metric(
                observation_count,
                snapshot_status,
            ),
            "snapshotCount": _coverage_metric(
                snapshot_count,
                snapshot_status,
            ),
            "uniqueObjectCount": _coverage_metric(
                unique_count,
                snapshot_status,
            ),
            "firstObservedAt": snapshot.get("firstObservedAt"),
            "latestObservedAt": snapshot.get("latestObservedAt"),
            "topObjects": deepcopy(
                snapshot.get("topObjects") or []
            ),
        },
    }

    _upsert_coverage_record(
        result,
        {
            "sourceId": "apple_recent_objects",
            "sourceFamily": "recent_apple",
            "status": current_status,
            "coverageBasis": (
                "Current Apple Recent and Heavy Rotation objects"
            ),
            "limitations": [],
        },
    )

    _upsert_coverage_record(
        result,
        {
            "sourceId": "apple_snapshot_warehouse",
            "sourceFamily": "recent_apple",
            "status": snapshot_status,
            "coverageBasis": (
                "Historical Apple snapshot observations"
            ),
            "limitations": [],
        },
    )

    result["compatibility"]["bridge"] = deepcopy(
        dict(bridge)
    )

    validate_canonical_artist_summary(result)
    return result
COMPARATIVE_STANDING_SCHEMA_VERSION = (
    "music.artist-comparative-standing.response.v0"
)


def _comparative_coverage_status(status: Any) -> str:
    mapping = {
        "available": "searched_with_evidence",
        "partial": "searched_with_evidence",
        "searched_no_evidence": "searched_no_evidence",
        "identity_unresolved": "not_searched",
        "unavailable": "unavailable",
        "unsupported": "unsupported",
    }

    return mapping.get(
        str(status or "").strip(),
        "unavailable",
    )


def apply_comparative_standing_projection(
    response: Mapping[str, Any],
    comparative_standing: Mapping[str, Any],
) -> dict[str, Any]:
    if not isinstance(response, Mapping):
        raise CanonicalArtistSummaryValidationError(
            "Canonical response must be a mapping."
        )

    if not isinstance(comparative_standing, Mapping):
        raise CanonicalArtistSummaryValidationError(
            "Comparative Standing response must be a mapping."
        )

    if (
        comparative_standing.get("schemaVersion")
        != COMPARATIVE_STANDING_SCHEMA_VERSION
    ):
        raise CanonicalArtistSummaryValidationError(
            "Unexpected Comparative Standing schema version."
        )

    if comparative_standing.get("entityType") != "artist":
        raise CanonicalArtistSummaryValidationError(
            "Comparative Standing response must use artist scope."
        )

    metrics = comparative_standing.get("metrics")

    if not isinstance(metrics, list):
        raise CanonicalArtistSummaryValidationError(
            "Comparative Standing metrics must be a list."
        )

    for metric in metrics:
        if not isinstance(metric, Mapping):
            raise CanonicalArtistSummaryValidationError(
                "Comparative Standing metric must be a mapping."
            )

        if metric.get("entityType") != "artist":
            raise CanonicalArtistSummaryValidationError(
                "Artist summary cannot contain family-population metrics."
            )

    result = deepcopy(dict(response))

    result["comparativeStanding"] = deepcopy(
        dict(comparative_standing)
    )

    coverage_status = _comparative_coverage_status(
        comparative_standing.get("status")
    )

    limitations = comparative_standing.get("limitations")

    if not isinstance(limitations, list):
        limitations = []

    _upsert_coverage_record(
        result,
        {
            "sourceId": "artist_comparative_standing",
            "sourceFamily": "comparative_standing",
            "status": coverage_status,
            "coverageBasis": (
                "Governed source-specific artist comparison populations"
            ),
            "limitations": deepcopy(limitations),
        },
    )

    validate_canonical_artist_summary(result)
    return result
def apply_family_projection(
    response: Mapping[str, Any],
    family: Mapping[str, Any] | None,
    family_metrics: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    if not isinstance(response, Mapping):
        raise CanonicalArtistSummaryValidationError(
            "Canonical response must be a mapping."
        )

    result = deepcopy(dict(response))

    if family is None:
        if family_metrics is not None:
            raise CanonicalArtistSummaryValidationError(
                "Family metrics require a reviewed family."
            )

        result["family"] = {
            "status": "not_applicable",
            "familyId": None,
            "familyName": None,
            "members": [],
            "relationshipType": None,
            "metrics": None,
            "provenance": [],
        }

        result["scope"].update({
            "scopeType": "artist",
            "familyId": None,
            "familyName": None,
            "familyMembers": [],
            "primaryArtistKey": None,
        })

        result["compatibility"]["family"] = None
        result["compatibility"]["familyMetrics"] = None

        validate_canonical_artist_summary(result)
        return result

    if not isinstance(family, Mapping):
        raise CanonicalArtistSummaryValidationError(
            "Artist family must be a mapping or None."
        )

    if (
        family_metrics is not None
        and not isinstance(family_metrics, Mapping)
    ):
        raise CanonicalArtistSummaryValidationError(
            "Family metrics must be a mapping or None."
        )

    family_id = str(
        family.get("familyId")
        or family.get("familyName")
        or ""
    ).strip()

    family_name = str(
        family.get("familyName")
        or family_id
    ).strip()

    raw_members = (
        family.get("members")
        or family.get("aliases")
        or []
    )

    if not isinstance(raw_members, (list, tuple)):
        raise CanonicalArtistSummaryValidationError(
            "Artist family members must be a list."
        )

    members: list[str] = []

    for raw_member in raw_members:
        member = str(raw_member or "").strip()

        if member and member not in members:
            members.append(member)

    if not family_id:
        raise CanonicalArtistSummaryValidationError(
            "Reviewed family requires familyId or familyName."
        )

    if not members:
        raise CanonicalArtistSummaryValidationError(
            "Reviewed family requires at least one member."
        )

    provenance = family.get("provenance")

    if not isinstance(provenance, list):
        provenance = [
            {
                "sourceId": "artist_families_curated",
                "label": "Reviewed curated artist families",
                "coverageStatus": "searched_with_evidence",
            }
        ]

    metrics = (
        deepcopy(dict(family_metrics))
        if family_metrics is not None
        else deepcopy(family.get("metrics"))
    )

    result["family"] = {
        "status": "available",
        "familyId": family_id,
        "familyName": family_name,
        "members": members,
        "relationshipType": family.get("relationshipType"),
        "metrics": metrics,
        "provenance": deepcopy(provenance),
    }

    result["scope"].update({
        "scopeType": "artist",
        "familyId": family_id,
        "familyName": family_name,
        "familyMembers": members,
        "primaryArtistKey": family.get("primaryArtistKey"),
    })

    result["compatibility"]["family"] = deepcopy(dict(family))
    result["compatibility"]["familyMetrics"] = (
        deepcopy(dict(family_metrics))
        if family_metrics is not None
        else deepcopy(metrics)
    )

    validate_canonical_artist_summary(result)
    return result
CONFIDENCE_BY_COVERAGE_STATUS = {
    "searched_with_evidence": "high",
    "searched_no_evidence": "high",
    "stale": "low",
    "not_searched": "low",
    "outside_coverage": "unavailable",
    "unavailable": "unavailable",
    "unsupported": "unavailable",
}


def _coverage_confidence(status: Any) -> str:
    return CONFIDENCE_BY_COVERAGE_STATUS.get(
        str(status or "").strip(),
        "unavailable",
    )


def _identity_confidence(value: Any) -> str:
    normalized = str(value or "").strip().casefold()

    if normalized in {
        "high",
        "exact",
        "normalized",
        "reviewed",
        "canonical",
    }:
        return "high"

    if normalized in {"low", "tentative", "ambiguous"}:
        return "low"

    return "unavailable"


def _combined_confidence(*values: str) -> str:
    normalized = [
        value
        for value in values
        if value in {"high", "low", "unavailable"}
    ]

    if not normalized:
        return "unavailable"

    if all(value == "high" for value in normalized):
        return "high"

    if any(value == "high" for value in normalized):
        return "partial"

    if any(value == "low" for value in normalized):
        return "low"

    return "unavailable"


def apply_contract_metadata_projection(
    response: Mapping[str, Any],
) -> dict[str, Any]:
    if not isinstance(response, Mapping):
        raise CanonicalArtistSummaryValidationError(
            "Canonical response must be a mapping."
        )

    result = deepcopy(dict(response))
    summary = result["summary"]
    entity = result["entity"]

    actual_status = summary["actualListening"].get("status")
    library_status = summary["libraryEvidence"].get("status")

    recent = summary["recentApple"]
    current_status = recent["current"].get("status")
    snapshot_status = recent["historicalSnapshots"].get(
        "status"
    )

    comparative_status = _comparative_coverage_status(
        result["comparativeStanding"].get("status")
    )

    identity_confidence = _identity_confidence(
        entity.get("identityConfidence")
    )

    recent_confidence = _combined_confidence(
        _coverage_confidence(current_status),
        _coverage_confidence(snapshot_status),
    )

    result["confidence"] = {
        "overall": _combined_confidence(
            identity_confidence,
            _coverage_confidence(actual_status),
            _coverage_confidence(library_status),
            recent_confidence,
            _coverage_confidence(comparative_status),
        ),
        "identity": identity_confidence,
        "actualListening": _coverage_confidence(
            actual_status
        ),
        "libraryEvidence": _coverage_confidence(
            library_status
        ),
        "recentApple": recent_confidence,
        "comparativeStanding": _coverage_confidence(
            comparative_status
        ),
    }

    limitations: list[dict[str, Any]] = []

    for existing in result.get("limitations") or []:
        if isinstance(existing, Mapping):
            limitations.append(deepcopy(dict(existing)))

    limiting_statuses = {
        "not_searched",
        "outside_coverage",
        "unavailable",
        "stale",
        "unsupported",
    }

    for coverage in result["coverage"]:
        if not isinstance(coverage, Mapping):
            continue

        source_id = str(
            coverage.get("sourceId") or ""
        ).strip()

        source_family = str(
            coverage.get("sourceFamily") or "source"
        ).strip()

        status = str(
            coverage.get("status") or ""
        ).strip()

        for limitation in coverage.get("limitations") or []:
            if isinstance(limitation, Mapping):
                limitations.append(
                    deepcopy(dict(limitation))
                )

        if status in limiting_statuses:
            limitations.append({
                "code": f"{source_family}_{status}",
                "message": (
                    f"{source_id} coverage status is "
                    f"{status.replace('_', ' ')}."
                ),
                "sourceId": source_id,
            })

    unique_limitations: list[dict[str, Any]] = []
    seen_limitations: set[tuple[Any, Any, Any]] = set()

    for limitation in limitations:
        key = (
            limitation.get("code"),
            limitation.get("message"),
            limitation.get("sourceId"),
        )

        if key not in seen_limitations:
            seen_limitations.add(key)
            unique_limitations.append(limitation)

    result["limitations"] = unique_limitations

    result["provenance"] = [
        {
            "sourceId": coverage.get("sourceId"),
            "label": coverage.get("coverageBasis"),
            "coverageStatus": coverage.get("status"),
        }
        for coverage in result["coverage"]
        if isinstance(coverage, Mapping)
    ]

    investigation = result.get("investigation")

    if not isinstance(investigation, Mapping):
        investigation = {}

    suggestions = investigation.get(
        "suggestedInvestigations"
    )

    result["suggestedInvestigations"] = (
        deepcopy(suggestions)
        if isinstance(suggestions, list)
        else []
    )

    evidence_statuses = {
        coverage.get("status")
        for coverage in result["coverage"]
        if isinstance(coverage, Mapping)
    }

    if entity.get("identityStatus") != "resolved":
        result["status"] = "identity_unresolved"
    elif "searched_with_evidence" in evidence_statuses:
        result["status"] = (
            "partial"
            if evidence_statuses.intersection(
                limiting_statuses
            )
            else "available"
        )
    elif "searched_no_evidence" in evidence_statuses:
        result["status"] = "searched_no_evidence"
    else:
        result["status"] = "unavailable"

    validate_canonical_artist_summary(result)
    return result

def _default_comparative_standing_response(
    response: Mapping[str, Any],
) -> dict[str, Any]:
    entity = response["entity"]

    return {
        "schemaVersion": COMPARATIVE_STANDING_SCHEMA_VERSION,
        "status": (
            "unavailable"
            if entity.get("identityStatus") == "resolved"
            else "identity_unresolved"
        ),
        "entityType": "artist",
        "canonicalKey": entity.get("canonicalKey"),
        "displayName": entity.get("displayName"),
        "metrics": [],
        "limitations": [],
    }

def assemble_canonical_artist_summary(
    base_result: Mapping[str, Any],
    *,
    query: Any = None,
    bridge: Mapping[str, Any] | None = None,
    comparative_standing: Mapping[str, Any] | None = None,
    family: Mapping[str, Any] | None = None,
    family_metrics: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    if family is None and family_metrics is not None:
        raise CanonicalArtistSummaryValidationError(
            "Family metrics require a reviewed family."
        )

    result = build_base_canonical_artist_summary(
        base_result,
        query=query,
    )

    result = apply_recent_apple_projection(
        result,
        bridge if bridge is not None else {},
    )

    standing = (
        comparative_standing
        if comparative_standing is not None
        else _default_comparative_standing_response(result)
    )

    result = apply_comparative_standing_projection(
        result,
        standing,
    )

    result = apply_family_projection(
        result,
        family,
        family_metrics,
    )

    result = apply_contract_metadata_projection(result)

    validate_canonical_artist_summary(result)
    return result
