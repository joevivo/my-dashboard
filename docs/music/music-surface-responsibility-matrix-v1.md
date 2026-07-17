# Music Surface Responsibility Matrix v1

## Status

Requirements lock for Music Sprint 1.

This document defines the target responsibilities, boundaries, navigation
status, and cross-surface transitions for the Defending Sisyphus Music product.

## Product Model

The Music product uses four intelligence responsibilities and one supporting
administration responsibility:

- Music Dashboard observes and triages the present.
- Query Workbench investigates evidence and explains why it matters.
- Artist Intelligence presents the durable canonical artist or family profile.
- Playlist Intelligence analyzes playlists and cohorts as musical artifacts.
- Music Library supports administration, curation, normalization, and data hygiene.

These surfaces may share canonical data and components, but they must not
duplicate each other as independent analytical systems.

## Responsibility Matrix

| Surface | Primary purpose | Primary navigation | Owns | Must not own |
|---|---|---:|---|---|
| Music Dashboard | Current-state triage | Yes | Live signals, changes, anomalies, investigation leads, freshness | Full dossiers, raw reasoning traces, manual library administration |
| Query Workbench | Investigation cockpit | Yes | Entity resolution, evidence, facts, insights, provenance, uncertainty, next investigations | Polished canonical profiles, passive dashboard reporting |
| Artist Intelligence | Durable artist or family profile | Contextual | Canonical summary, relationship shape, actual-play history, catalog depth, family amplification | Raw debugging, source administration, playlist cohort mechanics |
| Playlist Intelligence | Playlist and cohort analysis | Yes | Playlist identity, overlap, shared artists, bridge songs, signatures, playlist DNA | Declaring listening truth from placement alone, replacing artist intelligence |
| Music Library | Administration and curation | No, after migration | Imported records, manual curation, normalization, aliases, metadata, data hygiene | Dashboard reporting, period intelligence, artist conclusions, playlist intelligence |

## Music Dashboard

### Purpose

The Dashboard answers:

- What is active now?
- What changed?
- What looks unusual?
- What deserves investigation?
- How fresh and complete is the current observation?

### Required Responsibilities

- Show current Apple Music observations.
- Show recent artists, albums, playlists, stations, and heavy rotation signals.
- Show freshness, capture time, and source limitations.
- Identify investigation candidates without overstating them as conclusions.
- Launch preconfigured artist, period, song, album, or playlist investigations.

### Boundary

The Dashboard summarizes signals. It does not provide full evidence packets,
complete artist profiles, or opaque relationship classifications.

## Query Workbench

### Purpose

The Workbench is the full evidence and investigation surface.

Its canonical reasoning path is:

`Identity -> Evidence -> Facts -> Insights -> Next Investigations`

### Required Responsibilities

- Resolve artist, family, album, song, playlist, station, and period entities.
- Keep Actual Plays, Library Evidence, and Recent Apple Objects distinct.
- Expose source coverage, provenance, confidence, and limitations.
- Distinguish searched, empty, unsearched, unavailable, stale, and unsupported sources.
- Support artist, song, period, album, playlist, and comparative investigations.
- Link investigation results to canonical profiles and related investigations.

### Boundary

The Workbench may be technically detailed. It must not become the polished
summary profile or conceal uncertainty behind narrative.

## Artist Intelligence

### Purpose

Artist Intelligence is the durable canonical summary for an artist or family.
This is the shared artist-profile model used by Dashboard and Workbench.

### Required Responsibilities

- Present canonical identity and artist-family relationships.
- Summarize actual plays, skips, listening duration, and historical span.
- Summarize library representation and catalog depth.
- Summarize current Apple signals without treating them as confirmed plays.
- Present relationship shape only when supported by governed evidence.
- Link to the Workbench for provenance, reasoning, and unresolved questions.
- Link to Playlist Intelligence when playlist evidence materially matters.

### Navigation Decision

Artist Intelligence is contextual rather than a permanent primary-navigation
destination. It is opened from Dashboard, Workbench, Playlist Intelligence,
or other artist references.

## Playlist Intelligence

### Purpose

Playlist Intelligence treats playlists as first-class musical artifacts.

### Required Responsibilities

- Resolve canonical playlist identity.
- Show playlist composition and overview.
- Show shared core artists and tracks.
- Identify bridge songs and overlap.
- Describe playlist signatures and playlist DNA.
- Distinguish intentional placement from observed listening.
- Link artists and tracks to their respective investigations.

### Boundary

Playlist presence is evidence of curation or placement. It is not actual-play
truth unless a separate play source establishes listening activity.

## Music Library

### Decision

Music Library becomes an administration and curation surface.

It should ultimately be removed from primary Music navigation once equivalent
administrative access is preserved.

### Retained Responsibilities

- Inspect imported library records.
- Import and export curated Music data.
- Maintain manual artists, albums, playlists, shows, and notes.
- Support canonicalization, aliases, and metadata correction.
- Surface data-quality and normalization issues.

### Responsibilities to Remove

- Embedded Music Dashboard reporting.
- Embedded Music Time Machine or Period Intelligence.
- Duplicate artist-profile behavior.
- Duplicate playlist analysis.
- Primary analytical summaries.

### Migration Rule

Existing functionality must not be deleted until its valid administrative or
analytical responsibility has a confirmed destination and regression coverage.

## MusicTimeMachine Component

The current `MusicTimeMachine` component is embedded in `MusicLibrary.jsx`.

Target decision:

- Period Intelligence belongs in Query Workbench.
- Reusable period presentation components may remain under `src/music/components`.
- Music Library must stop acting as a second period-analysis destination.
- Existing functionality should be inventoried before removal or extraction.

## Cross-Surface Transitions

### Dashboard to Workbench

A Dashboard signal should open a preconfigured investigation carrying the
relevant artist, album, playlist, station, or observed period.

### Workbench to Artist Intelligence

An artist or family investigation should open the canonical profile without
discarding the current investigation context.

### Artist Intelligence to Workbench

Profile evidence, uncertainty, and questions should link to targeted Workbench
investigations rather than duplicating the reasoning trace.

### Playlist Intelligence to Workbench

Playlist artists, tracks, and derived claims should link to their evidence and
identity investigations.

### Period Intelligence to Other Entities

Period results should link to artists, albums, tracks, playlists, stations, and
related time periods when those identities are supported.

## Shared Contracts

All surfaces must use shared contracts for:

- canonical identity;
- evidence-source terminology;
- source registry and provenance;
- actual activity;
- library evidence;
- recent Apple observations;
- investigation packets;
- facts, hypotheses, insights, and confidence;
- governed formulas and classifications.

React components should render these contracts rather than independently
recreating domain classifications and reasoning.

## Confirmed Current-State Conflicts

1. `MusicLibrary.jsx` embeds a Music Dashboard section.
2. `MusicLibrary.jsx` embeds `MusicTimeMachine`.
3. Period Intelligence uses a separate thin contract rather than the investigation model.
4. Artist and period investigations have asymmetric source coverage.
5. Some relationship classification logic has existed in frontend presentation code.
6. Music Library remains broader than its intended administration role.

## Implementation Order

1. Lock evidence and surface contracts.
2. Stabilize the Period Intelligence response contract.
3. Build shared investigation and profile presentation components.
4. Redesign Query Workbench around investigation types.
5. Connect Dashboard signals to investigations.
6. Consolidate Artist Intelligence around the canonical profile.
7. Integrate Playlist Intelligence transitions.
8. Reduce Music Library to administration and curation.
9. Remove duplicated analytical components after regression verification.

## Acceptance Criteria

This responsibility matrix is satisfied when:

- every major Music capability has one primary owning surface;
- shared data is reused through contracts rather than duplicated logic;
- Dashboard signals route into investigations;
- Workbench exposes evidence, reasoning, provenance, and uncertainty;
- Artist Intelligence provides a concise canonical profile;
- Playlist Intelligence remains distinct from actual-play truth;
- Music Library is limited to administration and curation;
- Period Intelligence exists only as a Workbench investigation experience;
- navigation reflects these responsibilities;
- regression coverage protects functionality during migration.

## Risks

- deleting valid Music Library functionality before migration;
- treating UI consolidation as only a visual redesign;
- duplicating investigation logic across React components;
- exposing recent observations as actual plays;
- hiding incomplete evidence coverage;
- creating parallel profile models for Dashboard and Workbench.

## Dependencies

- Period Intelligence requirements and response contract;
- canonical identity contract;
- investigation packet contract;
- source and provenance registry;
- playback-context classification;
- regression fixtures for each primary surface.
