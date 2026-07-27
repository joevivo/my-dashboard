from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Mapping

from artist_comparative_standing_runtime import (
    RUNTIME_SCHEMA_VERSION,
    canonical_artist_key,
    load_and_build_runtime_snapshot,
    resolve_artist_identity,
)


library_path = Path(sys.argv[1])
snapshot_path = Path(sys.argv[2])
families_path = Path(sys.argv[3])
review_status_path = Path(sys.argv[4])

assertion_count = 0


def check(condition: bool, message: str) -> None:
    global assertion_count
    assertion_count += 1

    if not condition:
        raise AssertionError(message)


def positive_population_count(
    values: Mapping[str, Any],
) -> int:
    return sum(
        1
        for value in values.values()
        if isinstance(value, (int, float))
        and not isinstance(value, bool)
        and value > 0
    )


check(
    resolve_artist_identity("") is None,
    "Blank source artist must be rejected.",
)

check(
    canonical_artist_key("R.E.M.") == "rem",
    "R.E.M. canonicalKey changed.",
)

check(
    canonical_artist_key("U2") == "u2",
    "U2 canonicalKey changed.",
)

check(
    canonical_artist_key("The Beatles") == "thebeatles",
    "The Beatles canonicalKey changed.",
)

runtime = load_and_build_runtime_snapshot(
    library_tracks_path=library_path,
    snapshot_path=snapshot_path,
    families_path=families_path,
)

review_status = json.loads(
    review_status_path.read_text(
        encoding="utf-8-sig"
    )
)

check(
    runtime["schemaVersion"] == RUNTIME_SCHEMA_VERSION,
    "Unexpected runtime schema version.",
)

summary = runtime["sourceSummary"]

check(
    summary["libraryRowCount"] == 34643,
    "Library source row count changed.",
)

check(
    summary["snapshotRowCount"] == 13047,
    "Snapshot source row count changed.",
)

check(
    summary["rawArtistBearingSnapshotRowCount"] == 11567,
    "Raw artist-bearing snapshot count changed.",
)

check(
    summary["canonicalArtistBearingSnapshotRowCount"] == 11567,
    "Canonical artist-bearing snapshot count changed.",
)

check(
    summary["curatedFamilyCount"] == 16,
    "Curated family count changed.",
)

check(
    isinstance(review_status, dict)
    and len(review_status) == 11,
    "Standalone review-status source changed.",
)

check(
    runtime["artistDisplayNames"].get("rem") == "R.E.M.",
    "R.E.M. display-name mapping changed.",
)

check(
    runtime["artistDisplayNames"].get("u2") == "U2",
    "U2 display-name mapping changed.",
)

check(
    runtime["artistDisplayNames"].get("thebeatles")
    == "The Beatles",
    "The Beatles display-name mapping changed.",
)

expected_metrics = {
    "library_evidence_records",
    "historical_years_represented",
    "recent_apple_observations",
    "historical_unique_object_count",
}

check(
    set(runtime["artistPopulations"]) == expected_metrics,
    "Artist metric set is incorrect.",
)

check(
    set(runtime["familyPopulations"]) == expected_metrics,
    "Family metric set is incorrect.",
)

for metric_key in sorted(expected_metrics):
    artist_values = runtime["artistPopulations"][
        metric_key
    ]

    artist_rankings = runtime["artistRankings"][
        metric_key
    ]

    family_values = runtime["familyPopulations"][
        metric_key
    ]

    family_rankings = runtime["familyRankings"][
        metric_key
    ]

    check(
        bool(artist_values),
        f"Artist population is empty: {metric_key}",
    )

    check(
        len(artist_rankings)
        == positive_population_count(artist_values),
        f"Artist ranking population mismatch: {metric_key}",
    )

    check(
        len(family_rankings)
        == positive_population_count(family_values),
        f"Family ranking population mismatch: {metric_key}",
    )

    check(
        not set(artist_values).intersection(family_values),
        f"Family ID entered artist population: {metric_key}",
    )

    for result in artist_rankings.values():
        check(
            result["populationSize"] == len(artist_rankings),
            f"Artist population size mismatch: {metric_key}",
        )

    for result in family_rankings.values():
        check(
            result["populationSize"] == len(family_rankings),
            f"Family population size mismatch: {metric_key}",
        )

for metric in runtime["unavailableMetrics"].values():
    check(
        metric["status"] == "unavailable",
        "Unavailable status changed.",
    )

    check(
        metric["value"] is None,
        "Unavailable value must be null.",
    )

    check(
        metric["rank"] is None,
        "Unavailable rank must be null.",
    )

    check(
        metric["percentile"] is None,
        "Unavailable percentile must be null.",
    )

    check(
        metric["populationSize"] is None,
        "Unavailable population size must be null.",
    )

family_ids = set(
    runtime["familyPopulations"][
        "library_evidence_records"
    ]
)

check(
    "Tom Petty Family" in family_ids,
    "Tom Petty Family is missing.",
)

check(
    "Elvis Costello Family" in family_ids,
    "Elvis Costello Family is missing.",
)

probe_keys = {
    "REM": "rem",
    "U2": "u2",
    "BEATLES": "thebeatles",
}

print("COMPARATIVE_STANDING_RUNTIME_VALIDATION: PASS")
print(f"VALIDATION_ASSERTION_COUNT: {assertion_count}")
print(
    f"LIBRARY_ROW_COUNT: {summary['libraryRowCount']}"
)
print(
    f"SNAPSHOT_ROW_COUNT: {summary['snapshotRowCount']}"
)
print(
    "RAW_ARTIST_BEARING_SNAPSHOT_ROW_COUNT: "
    f"{summary['rawArtistBearingSnapshotRowCount']}"
)
print(
    "CANONICAL_ARTIST_BEARING_SNAPSHOT_ROW_COUNT: "
    f"{summary['canonicalArtistBearingSnapshotRowCount']}"
)
print(
    f"CURATED_FAMILY_COUNT: {summary['curatedFamilyCount']}"
)

for metric_key in sorted(expected_metrics):
    print(
        f"ARTIST_POPULATION_{metric_key}: "
        f"{len(runtime['artistPopulations'][metric_key])}"
    )

    print(
        f"FAMILY_POPULATION_{metric_key}: "
        f"{len(runtime['familyPopulations'][metric_key])}"
    )

for label, artist_key in probe_keys.items():
    print(f"PROBE_{label}_CANONICAL_KEY: {artist_key}")

    for metric_key in sorted(expected_metrics):
        value = runtime["artistPopulations"][
            metric_key
        ].get(artist_key)

        ranking = runtime["artistRankings"][
            metric_key
        ].get(artist_key) or {}

        print(
            f"PROBE_{label}_{metric_key}_VALUE: {value}"
        )

        print(
            f"PROBE_{label}_{metric_key}_RANK: "
            f"{ranking.get('rank')}"
        )

        print(
            f"PROBE_{label}_{metric_key}_PERCENTILE: "
            f"{ranking.get('percentile')}"
        )

print("CANONICAL_IDENTITY_FIELD: canonicalKey")
print("PRESENTATION_IDENTITY_FIELD: displayName")
print(
    "CANONICAL_IDENTITY_RESOLVER: "
    "music_identity.resolve_artist"
)
print("YEARS_REPRESENTED_FIELD: Last Played Date")
print("LOGICAL_OBJECT_KEY: entity_type + entity_id")
print("ARTIST_FAMILY_POPULATION_SEPARATION: PASS")
print("ACTUAL_PLAYS_STATUS: unavailable")
print("LISTENING_DURATION_STATUS: unavailable")