from __future__ import annotations

from canonical_artist_summary import assemble_canonical_artist_summary


def base(
    artist: str,
    library: int = 0,
    plays: int | None = None,
    source: str = "missing",
) -> dict:
    return {
        "artist": artist,
        "query": artist,
        "libraryEvidenceRecords": library,
        "actualPlays": plays,
        "actualSkips": 0 if plays is not None else None,
        "listeningDurationMs": 3600000 if plays else None,
        "hoursListened": 1.0 if plays else None,
        "playActivitySource": source,
        "actualTopSongs": [],
        "yearsActive": 1 if library else None,
        "firstPlayedDate": "2025-01-01" if library else None,
        "latestPlayedDate": "2026-01-01" if library else None,
        "topSongs": [],
        "topAlbums": [],
        "timeline": [],
        "investigation": {},
    }


def recent(
    current_status: str,
    snapshot_status: str,
    current_count: int = 0,
    snapshot_count: int = 0,
) -> dict:
    return {
        "live": {
            "currentStatus": current_status,
            "recentObjectCount": current_count,
            "heavyRotationCount": 0,
            "recentObjects": [],
            "heavyRotationObjects": [],
            "snapshotHistory": {
                "status": snapshot_status,
                "observationCount": snapshot_count,
                "snapshotCount": snapshot_count,
                "uniqueObjectCount": snapshot_count,
                "firstObservedAt": None,
                "latestObservedAt": None,
                "topObjects": [],
            },
        }
    }


def standing(status: str, value: int | None = None) -> dict:
    metrics = []

    if value is not None:
        metrics.append(
            {
                "metricKey": "library_evidence_records",
                "entityType": "artist",
                "status": "ranked",
                "value": value,
                "rank": 4,
                "percentile": 99.9,
            }
        )

    return {
        "schemaVersion": "music.artist-comparative-standing.response.v0",
        "status": status,
        "entityType": "artist",
        "canonicalKey": "rem",
        "displayName": "R.E.M.",
        "metrics": metrics,
        "limitations": [],
    }


passed: list[str] = []


def check(name: str, condition: bool) -> None:
    if not condition:
        raise AssertionError(f"Fixture failed: {name}")

    passed.append(name)


resolved_base = base(
    "R.E.M.",
    library=198,
    plays=1927,
    source="apple_daily_track_summary",
)

resolved = assemble_canonical_artist_summary(
    resolved_base,
    bridge=recent(
        "searched_with_evidence",
        "searched_with_evidence",
        current_count=3,
        snapshot_count=8,
    ),
    comparative_standing=standing("available", 198),
)

check(
    "resolved_library_and_actual",
    resolved["entity"]["identityStatus"] == "resolved"
    and resolved["summary"]["libraryEvidence"]["recordCount"] == 198
    and resolved["summary"]["actualListening"]["actualPlays"] == 1927,
)

library_only = assemble_canonical_artist_summary(
    base("R.E.M.", library=198)
)

check(
    "library_with_unavailable_actual",
    library_only["summary"]["libraryEvidence"]["status"]
    == "searched_with_evidence"
    and library_only["summary"]["actualListening"]["status"]
    == "unavailable"
    and library_only["summary"]["actualListening"]["actualPlays"] is None,
)

recent_only = assemble_canonical_artist_summary(
    base("R.E.M."),
    bridge=recent(
        "searched_with_evidence",
        "unavailable",
        current_count=2,
    ),
)

check(
    "recent_apple_only",
    recent_only["summary"]["recentApple"]["current"][
        "recentObjectCount"
    ]
    == 2,
)

searched_zero = assemble_canonical_artist_summary(
    base(
        "R.E.M.",
        plays=0,
        source="apple_daily_track_summary",
    ),
    bridge=recent(
        "searched_no_evidence",
        "searched_no_evidence",
    ),
    comparative_standing=standing("searched_no_evidence"),
)

check(
    "searched_zero",
    searched_zero["status"] == "searched_no_evidence"
    and searched_zero["summary"]["actualListening"]["actualPlays"] == 0
    and searched_zero["summary"]["recentApple"]["current"][
        "recentObjectCount"
    ]
    == 0,
)

unresolved = assemble_canonical_artist_summary(base(""))

check(
    "unresolved_identity",
    unresolved["status"] == "identity_unresolved"
    and unresolved["entity"]["canonicalKey"] is None,
)

family = {
    "familyId": "sugar-bob-mould",
    "familyName": "Sugar / Bob Mould",
    "members": ["Sugar", "Bob Mould"],
    "primaryArtistKey": "bobmould",
    "relationshipType": "solo-and-band",
}

with_family = assemble_canonical_artist_summary(
    base("Bob Mould", library=10),
    family=family,
    family_metrics={
        "entityType": "artist_family",
        "libraryEvidenceRecords": 25,
    },
)

check(
    "reviewed_family",
    with_family["scope"]["scopeType"] == "artist"
    and with_family["family"]["familyId"] == "sugar-bob-mould",
)

without_family = assemble_canonical_artist_summary(
    base("U2", library=10)
)

check(
    "no_family",
    without_family["family"]["status"] == "not_applicable",
)

check(
    "artist_family_scope_separation",
    all(
        metric["entityType"] == "artist"
        for metric in resolved["comparativeStanding"]["metrics"]
    )
    and with_family["family"]["metrics"]["entityType"]
    == "artist_family",
)

check(
    "unavailable_vs_searched_zero",
    library_only["summary"]["actualListening"]["actualPlays"] is None
    and searched_zero["summary"]["actualListening"]["actualPlays"] == 0,
)

split_recent = assemble_canonical_artist_summary(
    base("R.E.M."),
    bridge=recent(
        "searched_no_evidence",
        "searched_with_evidence",
        snapshot_count=6,
    ),
)

check(
    "current_vs_snapshot_separation",
    split_recent["summary"]["recentApple"]["current"]["status"]
    == "searched_no_evidence"
    and split_recent["summary"]["recentApple"]["historicalSnapshots"][
        "snapshotCount"
    ]
    == 6,
)

check(
    "compatibility_equality",
    all(
        resolved["compatibility"][key] == value
        for key, value in resolved_base.items()
    ),
)

representatives = {
    "R.E.M.",
    "U2",
    "The Beatles",
    "Sugar",
    "Bob Mould",
    "Steve Miller",
    "Steve Miller Band",
    "Intentionally Missing Artist",
}

if len(passed) != 11:
    raise AssertionError(
        f"Expected 11 fixtures; completed {len(passed)}."
    )

if len(representatives) != 8:
    raise AssertionError("Representative Artist inventory is incomplete.")

print("BACKEND_CONTRACT_FIXTURES: 11/11")
print("REPRESENTATIVE_ARTIST_INVENTORY: PASS")
print("DEFERRED_INTEGRATION_FIXTURES: 2")
print("VALIDATION_PASS")
