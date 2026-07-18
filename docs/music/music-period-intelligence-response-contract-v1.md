# Music Period Intelligence Response Contract v1

## Status

Frozen field-level contract for the first Period Intelligence implementation vertical slice.

This contract defines the response shape, evidence semantics, source coverage states,
compatibility requirements, and zero-state behavior for period investigations.

## API Direction

### Canonical route

`GET /api/music/query/period?start=YYYY-MM-DD&end=YYYY-MM-DD`

### Compatibility route

`GET /api/music/time-machine?start=YYYY-MM-DD&end=YYYY-MM-DD`

During migration, the compatibility route should return the same v1 response.

The compatibility route may be removed only after Query Workbench and
`MusicTimeMachine` no longer depend on the legacy response.

## Contract Principles

- The selected period is the investigated entity.
- Actual listening, Library Evidence, and Recent Apple Objects remain separate.
- Missing source coverage is explicit.
- Zero means searched with no matching evidence.
- Null means unavailable, unsupported, or not searched.
- Recent Apple Objects must never be presented as confirmed plays.
- Library Last Played Date reconstruction must never be presented as complete history.
- Every fact, tag, and insight must point to supporting evidence.
- Unsupported interpretation must remain absent rather than inferred.

## Top-Level Response

```json
{
  "schemaVersion": "music.period-intelligence.v1",
  "generatedAt": "2026-07-17T18:00:00Z",
  "request": {},
  "period": {},
  "summary": {},
  "coverage": [],
  "activity": {},
  "libraryEvidence": {},
  "recentAppleObservations": {},
  "playbackContexts": {},
  "periodTags": [],
  "facts": [],
  "insights": [],
  "confidence": {},
  "warnings": [],
  "provenance": [],
  "suggestedInvestigations": [],
  "legacy": {}
}
```

## Request

```json
{
  "startDate": "2026-07-01",
  "endDate": "2026-07-14",
  "timeZone": "America/Chicago"
}
```

| Field | Type | Required | Meaning |
|---|---|---:|---|
| startDate | ISO date | yes | Inclusive period start |
| endDate | ISO date | yes | Inclusive period end |
| timeZone | IANA timezone | yes | Timezone used for period boundaries |

The API must reject invalid dates and an end date earlier than the start date.

## Period Identity

```json
{
  "entityType": "period",
  "canonicalKey": "2026-07-01_2026-07-14_America-Chicago",
  "startDate": "2026-07-01",
  "endDate": "2026-07-14",
  "timeZone": "America/Chicago",
  "inclusiveDayCount": 14,
  "label": "Jul 1-14, 2026"
}
```

## Summary

```json
{
  "status": "evidence_found",
  "headline": "Billie Holiday led the available period evidence.",
  "narrative": "Actual listening and library evidence were available; recent Apple history was partial."
}
```

### Summary status values

- evidence_found
- no_matching_evidence
- partial_coverage
- unsupported_period
- operational_error

The narrative must identify material coverage limitations.

## Evidence Coverage

Coverage is an array with one entry for every relevant source family.

```json
{
  "sourceId": "apple_daily_track_summary",
  "sourceType": "actual_listening",
  "status": "searched_with_evidence",
  "recordsExamined": 1250,
  "recordsMatched": 97,
  "coverageStart": "2026-07-01",
  "coverageEnd": "2026-07-14",
  "capturedAt": null,
  "freshness": "current",
  "limitations": []
}
```

### Coverage status values

- searched_with_evidence
- searched_no_evidence
- not_searched
- unavailable
- stale
- unsupported_for_period

### Source type values

- actual_listening
- library_evidence
- recent_apple_observation
- playback_context

### Coverage rules

- `recordsMatched` is zero only when the source was searched successfully.
- `recordsMatched` is null when the source was not searched or unavailable.
- Coverage dates describe the source range examined, not inferred relationship dates.
- Limitations are plain-language statements suitable for UI display.

## Actual Listening Activity

```json
{
  "status": "available",
  "actualPlays": 97,
  "actualSkips": 33,
  "listeningSeconds": 19440,
  "listeningHours": 5.4,
  "uniqueArtistCount": 12,
  "uniqueAlbumCount": 19,
  "uniqueTrackCount": 46,
  "topArtists": [],
  "topAlbums": [],
  "topTracks": []
}
```

### Activity item shape

```json
{
  "canonicalKey": "billie holiday",
  "artist": "Billie Holiday",
  "album": "Lady in Satin",
  "track": "I Get Along Without You Very Well",
  "actualPlays": 5,
  "actualSkips": 1,
  "listeningSeconds": 1260,
  "evidenceRefs": ["play-activity-001"]
}
```

Unavailable metrics must be null rather than zero.

## Library Evidence

```json
{
  "status": "available",
  "recordCount": 14,
  "uniqueArtistCount": 1,
  "uniqueAlbumCount": 2,
  "uniqueTrackCount": 14,
  "topArtists": [],
  "topAlbums": [],
  "topTracks": [],
  "timeline": [],
  "sourceNote": "Reconstruction from Apple Music Library Tracks Last Played Date. This is not complete play-count history."
}
```

Library Evidence counts are evidence records, not Actual Plays.

## Recent Apple Observations

```json
{
  "status": "available",
  "objectCount": 3,
  "capturedSnapshotCount": 1,
  "firstCapturedAt": "2026-07-14T01:00:00Z",
  "latestCapturedAt": "2026-07-14T01:00:00Z",
  "artists": [],
  "albums": [],
  "tracks": [],
  "playlists": [],
  "stations": [],
  "sourceNote": "Timestamped Apple source observations. These objects are not confirmed plays."
}
```

## Playback Contexts

```json
{
  "status": "partial",
  "knownEventCount": 48,
  "unknownEventCount": 49,
  "denominator": 97,
  "items": []
}
```

### Context item shape

```json
{
  "contextType": "playlist",
  "contextName": "Late Night Jazz",
  "eventCount": 18,
  "share": 0.1856,
  "denominator": 97,
  "evidenceRefs": ["context-001"]
}
```

### Context type values

- playlist
- radio_station
- album
- library
- autoplay
- search
- recommendation
- recently_played_surface
- heavy_rotation_surface
- unknown

A share must always include its denominator.

## Period Tags

```json
{
  "tag": "album_centered",
  "label": "Album-centered listening",
  "confidence": "medium",
  "evidenceRefs": ["play-activity-003", "play-activity-008"],
  "rationale": "One album accounted for 58 percent of Actual Plays."
}
```

Tags must be evidence-backed and may not be generated from unavailable sources.

## Facts

```json
{
  "factType": "actual-play-count",
  "statement": "The period contains 97 Actual Plays.",
  "value": 97,
  "evidenceRefs": ["play-activity-source"]
}
```

Facts are direct evidence statements and must not contain relationship conclusions.

## Insights

```json
{
  "insightType": "concentration",
  "statement": "Listening was concentrated around one artist.",
  "confidence": "medium",
  "evidenceRefs": ["play-activity-artist-summary"],
  "limitations": ["Playback context was unavailable for 49 events."]
}
```

Insights are interpretations and must disclose confidence and limitations.

## Confidence

```json
{
  "level": "medium",
  "reasons": [
    "Actual listening activity was available.",
    "Recent Apple snapshot coverage was partial."
  ]
}
```

### Confidence values

- high
- medium
- low
- unknown

No numeric confidence score is frozen in v1.

## Warnings

```json
{
  "code": "RECENT_APPLE_PARTIAL",
  "message": "Recent Apple observations were available for only part of the selected period.",
  "sourceId": "apple_live_snapshot_warehouse"
}
```

Warnings must be stable enough for frontend handling and readable without code lookup.

## Provenance

```json
{
  "evidenceId": "play-activity-source",
  "sourceId": "apple_daily_track_summary",
  "sourceLabel": "Apple Music Daily Track Summary",
  "sourceType": "actual_listening",
  "recordCount": 97,
  "coverageStart": "2026-07-01",
  "coverageEnd": "2026-07-14",
  "capturedAt": null,
  "notes": []
}
```

## Suggested Investigations

```json
{
  "investigationType": "artist",
  "label": "Investigate Billie Holiday",
  "parameters": {
    "artist": "Billie Holiday"
  },
  "reason": "The artist led Actual Plays during the selected period."
}
```

## Diagnostic Zero States

### Searched with no evidence

`No matching Actual Plays were found in the searched activity source for this period.`

### Source not searched

`Actual listening history was not searched for this response.`

### Source unavailable

`Actual listening history is currently unavailable.`

### Unsupported period

`This source does not cover the selected period.`

### Operational error

`Period Intelligence could not complete because the backend operation failed.`

These states must not share the same UI message.

## Legacy Compatibility

The v1 migration may temporarily retain the current flat fields under `legacy`:

```json
{
  "tracksMatched": 14,
  "topAlbums": [],
  "topArtists": [],
  "artistJourneys": [],
  "memoryRead": [],
  "sourceNote": "Reconstruction from Apple Music Library Tracks Last Played Date."
}
```

Rules:

- New frontend work must use the structured v1 fields.
- Legacy fields are compatibility-only.
- Legacy fields must not be expanded.
- Deprecation warnings should be added before removal.
- Both current frontend consumers must migrate before removal.

## Error Response

```json
{
  "schemaVersion": "music.period-intelligence.error.v1",
  "error": {
    "code": "INVALID_PERIOD",
    "message": "The end date must be on or after the start date.",
    "details": {}
  }
}
```

Expected error codes:

- INVALID_START_DATE
- INVALID_END_DATE
- INVALID_PERIOD
- PERIOD_TOO_LARGE
- SOURCE_EXECUTION_FAILED
- PERIOD_INTELLIGENCE_FAILED

## Implementation Boundaries

- `period_intelligence.py` should become the canonical period builder.
- `library_range_summary.py` should not remain an independent competing contract.
- The server should not derive domain intelligence in route code.
- React should not infer coverage status from missing fields.
- React should not calculate relationship classifications.
- Source adapters should populate evidence families independently.
- The response assembler should generate summary, facts, insights, and warnings.

## Acceptance Criteria

- The canonical and compatibility routes return the same schema version.
- Every relevant source has one coverage entry.
- Actual listening metrics are null when the source is unavailable.
- Library counts are labeled as evidence records.
- Recent Apple Objects are never labeled as plays.
- Playback-context shares include denominators.
- Every fact, tag, and insight includes evidence references.
- Zero states distinguish empty, unsearched, unavailable, and unsupported.
- Query Workbench renders structured fields without consulting legacy fields.
- MusicTimeMachine is migrated or removed before legacy fields are deleted.
- Regression fixtures cover all coverage status values.

## Initial Implementation Sequence

1. Add the canonical route as an alias to the existing period operation.
2. Add request validation and period identity.
3. Add coverage entries for each evidence family.
4. Move the existing Library Tracks output under `libraryEvidence`.
5. Preserve current fields under `legacy`.
6. Add Actual Plays, skips, and duration when source coverage permits.
7. Add Recent Apple snapshot evidence.
8. Add playback-context output.
9. Add facts, insights, confidence, warnings, and provenance.
10. Migrate Query Workbench.
11. Migrate or retire MusicTimeMachine.
12. Remove the compatibility fields in a later contract version.
