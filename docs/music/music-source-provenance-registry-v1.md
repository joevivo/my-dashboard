# Music Source and Provenance Registry v1

## Status

Draft contract for Sprint 2.

No UI implementation should depend on this registry until it is reviewed and accepted.

---

## Purpose

This registry defines what each Music source is allowed to prove, what it cannot prove, and what provenance every metric must expose.

Core rule:

No source may be allowed to prove more than it actually contains.

---

## Source Families

Canonical source families:

- Apple Music daily track summary
- Apple Music Library Tracks
- Apple Music Library Playlists
- DuckDB listening context
- Apple Music live endpoints
- Curated identity and album seeds
- Derived model output
- Reports and examples

---

## Apple Music daily track summary

Canonical source key:

- apple_music_daily_track_summary

Source type:

- apple_music_daily_summary

Allowed to prove:

- Actual plays
- Actual skips
- Listening duration
- Listening hours
- First played
- Latest played
- Active listening dates
- Artist/song daily play evidence when artist and song are present in the source

Not allowed to prove:

- Current library membership
- Playlist membership
- Playlist intent
- Album edition identity by itself
- Live/current listening state
- Artist family identity unless joined to curated identity data

Required provenance fields:

- source
- sourceType
- metricType
- dateRange
- latestPlayed
- sourcePath or sourceLabel
- confidence

Default confidence:

- High for direct actual play, skip, and duration metrics.
- Medium when joined to identity, family, or album normalization layers.
- Low when matching depends on ambiguous artist/song text.

Primary warning:

Actual listening data is historical listening truth, but it is not library ownership, playlist membership, or live freshness.

---

## Apple Music Library Tracks

Canonical source key:

- apple_music_library_tracks

Source type:

- apple_music_library

Allowed to prove:

- Library evidence records
- Library presence
- Track metadata
- Album metadata
- Artist metadata as represented in library export
- First seen
- Latest seen
- Source-limited memory cases
- Album normalization candidates

Not allowed to prove:

- Actual plays
- Actual skips
- Listening hours
- Playlist placement
- Live/current behavior
- Listening context

Required provenance fields:

- source
- sourceType
- metricType
- firstSeen
- latestSeen
- sourcePath or sourceLabel
- confidence

Default confidence:

- High for library evidence presence.
- Medium for album or artist interpretation.
- Low when metadata variants, aliases, or mojibake affect identity.

Primary warning:

Library evidence records must never be labeled as actual plays or total plays.

---

## Apple Music Library Playlists

Canonical source key:

- apple_music_library_playlists

Source type:

- apple_music_playlist_library

Allowed to prove:

- Playlist membership
- Playlist placement
- Playlist song count
- Playlist artist count
- Playlist album count
- Shared core artists
- Bridge songs
- Intentional playlist evidence when playlist classification is known
- Generated playlist evidence when playlist classification is known

Not allowed to prove:

- Actual listening
- Actual skips
- Listening hours
- Favorite artist status by itself
- Artist relationship shape by itself
- Current live behavior

Required provenance fields:

- source
- sourceType
- metricType
- playlistName
- playlistClassification when available
- sourcePath or sourceLabel
- confidence

Default confidence:

- High for direct playlist membership.
- Medium for playlist-derived metrics such as bridge songs or shared core artists.
- Low for playlist relationship-shape interpretation until formulas exist.

Primary warning:

Playlist placement is intentional placement evidence, not listening truth.

---

## DuckDB listening context

Canonical source key:

- duckdb_apple_music_play_activity

Source type:

- duckdb_listening_context

Known table:

- apple_music_play_activity

Allowed to prove:

- Listening context rows
- Container type
- Source type
- Album/radio/playlist/unknown context distribution where fields exist
- Event timestamp
- Session/context analysis when supported by available columns

Not allowed to prove:

- Reliable artist lookup by itself
- Canonical artist identity by itself
- Playlist names when unavailable
- Library ownership
- Live/current behavior

Required provenance fields:

- source
- sourceType
- metricType
- table
- sourceColumns
- dateRange
- confidence

Default confidence:

- High for direct context fields present in the table.
- Medium when joined to sanitized artist/song evidence.
- Low when context is inferred from partial or ambiguous matches.

Primary warning:

DuckDB context enriches listening interpretation but does not replace artist identity resolution.

---

## Apple Music live endpoints

Canonical source keys:

- apple_music_recent_played
- apple_music_heavy_rotation
- apple_music_library_albums_live
- apple_music_library_playlists_live
- apple_music_library_songs_live

Source type:

- apple_music_live_endpoint

Allowed to prove:

- Live/recent objects
- Heavy rotation signals
- Current endpoint-visible library objects
- Freshness snapshots
- Recent activity candidates

Not allowed to prove:

- Long-term historical listening truth by itself
- Full listening history
- Actual total plays
- Actual total skips
- Durable relationship classification by itself

Required provenance fields:

- source
- sourceType
- endpoint
- generatedAt
- snapshotId
- latestObjectTimestamp when available
- confidence

Default confidence:

- High for endpoint-returned object presence at snapshot time.
- Medium for recent activity interpretation.
- Low for durable relationship interpretation unless joined to historical sources.

Primary warning:

Live endpoints indicate current or fresh state. Historical truth remains the exported Apple Music daily summary.

---

## Curated identity and album seeds

Canonical source keys:

- curated_artist_families
- curated_album_identity_seed

Source type:

- curated_model_seed

Allowed to prove:

- Canonical names
- Aliases
- Artist family membership
- Album identity mappings
- Album variant grouping
- Known identity decisions

Not allowed to prove:

- Actual plays
- Actual skips
- Listening hours
- Playlist placement
- Live/current behavior

Required provenance fields:

- source
- sourceType
- canonicalKey
- matchedSourceNames
- confidence
- notes

Default confidence:

- High for explicit curated mappings.
- Medium when mappings are partial.
- Low when mappings are proposed but not reviewed.

Primary warning:

Curated seeds define identity, not listening behavior.

---

## Derived model output

Canonical source keys:

- derived_facts
- derived_hypotheses
- derived_insights
- derived_reasoning_trace

Source type:

- derived

Allowed to prove:

- Reproducible facts derived from source evidence
- Hypotheses supported by facts
- Insights supported by facts and hypotheses
- Reasoning traces
- Confidence summaries

Not allowed to prove:

- Primary source facts without evidence IDs
- Actual plays without actual listening evidence
- Library presence without library evidence
- Playlist placement without playlist evidence
- Live freshness without live snapshot metadata

Required provenance fields:

- source
- sourceType
- sourceEvidenceIds
- sourceFactIds when applicable
- ruleIds when applicable
- confidence
- limitations

Default confidence:

- Inherits confidence from source evidence.
- Must be reduced when identity, source coverage, or formulas are incomplete.

Primary warning:

Derived output is not a source of truth. It is an interpretation layer.

---

## Reports and examples

Canonical source keys:

- docs_music_reports
- docs_music_examples

Source type:

- documentation_fixture

Allowed to prove:

- Historical project reasoning
- Example packet shape
- Research context
- Regression ideas

Not allowed to prove:

- Current metrics by itself
- Current source truth by itself
- Production formula correctness by itself

Required provenance fields:

- source
- sourceType
- documentPath
- generatedAt or commit when available
- confidence

Default confidence:

- Medium for project context.
- Low for current facts unless validated against source data.

Primary warning:

Reports and examples are fixtures and context, not primary source truth.

---

## Metric Type Rules

Allowed metric types:

- actualListeningMetric
- libraryEvidenceMetric
- playlistPlacementMetric
- liveSignal
- curatedIdentityMetric
- derivedMetric
- documentationFixture

Rules:

- actualListeningMetric requires Apple Music daily track summary or a validated future equivalent.
- libraryEvidenceMetric requires Apple Music Library Tracks.
- playlistPlacementMetric requires Apple Music Library Playlists.
- liveSignal requires Apple Music live endpoint metadata.
- curatedIdentityMetric requires a curated seed.
- derivedMetric requires sourceEvidenceIds or sourceFactIds.
- documentationFixture cannot be used as primary evidence for current metrics.

---

## Confidence Rules

High confidence:

- Direct source evidence exists.
- Identity is resolved.
- Source is allowed to prove the claim.
- Freshness is available when needed.

Medium confidence:

- Source evidence exists but requires joins or interpretation.
- Identity is mostly resolved but has aliases, family rollups, or metadata variants.
- Context is incomplete but usable.

Low confidence:

- Weak evidence.
- Ambiguous identity.
- Source limitation affects interpretation.
- Required freshness is missing.

Not found:

- The relevant source does not contain the entity or metric.
- Not found must not be treated as proof that the relationship is unimportant.

---

## Acceptance Criteria

This registry is accepted when:

- Every known source family has allowed and disallowed claims.
- Required provenance fields are documented for every source family.
- Metric type rules are explicit.
- Confidence rules are explicit.
- The registry reinforces source separation from the requirements checklist.
- No UI implementation is started.
