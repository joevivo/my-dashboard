# Music Consolidated Backlog and Requirements Lock v1

## Status

Music Sprint 1 requirements lock and prioritized implementation backlog.

This document consolidates the current Music architecture, product decisions,
period requirements, surface responsibilities, semantic corrections, and
deferred intelligence concepts into one execution sequence.

## Product North Star

The Music product should support one continuous analytical path:

`Observe -> Investigate -> Understand -> Navigate`

- Music Dashboard observes and triages the present.
- Query Workbench investigates evidence and explains why it matters.
- Artist Intelligence presents a concise canonical artist or family profile.
- Playlist Intelligence analyzes playlists and cohorts.
- Music Library supports administration, curation, and data hygiene.

## Locked Product Decisions

### Dashboard

- The Dashboard observes current state.
- It shows recent Apple objects, heavy rotation, playlists, stations, changes,
  freshness, and investigation candidates.
- It does not present complete play history or full reasoning traces.

### Query Workbench

- The Workbench is the evidence and investigation cockpit.
- It owns identity resolution, evidence, facts, insights, provenance,
  confidence, uncertainty, open questions, and next investigations.
- It supports artist, song, period, album, playlist, and comparison questions.

### Artist Intelligence

- Artist Intelligence is the concise canonical artist or family profile.
- The same canonical summary model should be reusable by Dashboard and
  Workbench.
- Full evidence and derivation remain in Query Workbench.

### Playlist Intelligence

- Playlists are first-class musical artifacts.
- Playlist placement is evidence of curation or context, not actual-play truth.

### Music Library

- Music Library becomes an administration and curation surface.
- It should not remain a primary analytical destination.
- Embedded Dashboard and Time Machine behavior must migrate before removal.
- Keep Library search visible.
- Reduce the hero and header height while keeping album, artist, and show counts compact and inline.
- Group Export Music Library, Restore JSON, Add Albums CSV, and Download Album Template inside a compact `Manage Library` menu or expandable administration panel.
- Remove or consolidate the duplicate Music Administration explanation strip.
- Reclaim vertical space for curated Library content.


### Listening Eras

- Listening Eras are removed from the product.
- They must not return to navigation, requirements, reports, or backlog unless
  explicitly reconsidered.

## Locked Evidence Rules

### Actual Plays

- Actual Plays come from Apple Music daily track-summary evidence.
- Library records and live Apple objects must never be labeled as Actual Plays.

### Actual Skips

- Actual Skips come from Apple Music daily track-summary evidence.
- Skip definitions and source limitations must remain visible.

### Library Evidence

- Library Evidence comes from Apple Music Library Tracks.
- Library presence or Last Played Date reconstruction is not total play count.

### Recent Apple Objects

- Recent Apple Objects are timestamped observations from current Apple
  endpoints.
- They indicate current or fresh state, not complete historical listening.

### Source Coverage

Every investigation must distinguish:

- searched with evidence;
- searched with no evidence;
- not searched;
- unavailable;
- stale;
- unsupported for the requested period.

Unavailable, unsearched, and genuinely empty evidence must not be collapsed
into one zero-result message.

## Priority 0 — Contract and Trust Foundation

These items block substantial Music UI implementation.

### P0.1 Freeze the Period Intelligence response contract

- Define field-level schemas for period identity, coverage, activity, library
  evidence, recent observations, playback context, tags, warnings, and
  investigation output.
- Treat the period itself as the investigated entity.
- Align period output with the investigation packet contract.

### P0.2 Implement explicit evidence coverage

- Report every relevant evidence source and its status.
- Include record counts, timestamp coverage, freshness, and limitations.
- Generate diagnostic zero states from the coverage model.

### P0.3 Define playback-context classification

Supported context types should include:

- playlist;
- radio station;
- album;
- library;
- autoplay;
- search;
- recommendation surface;
- recently played surface;
- heavy rotation surface;
- unknown.

Context must not be fabricated when source data does not establish it.

### P0.4 Correct ambiguous semantic fields

- Replace or clarify `yearsActive`.
- Distinguish active-year count from relationship span.
- Separate evidence-source classification from relationship classification.
- Separate relationship classification from investigation conclusion.

### P0.5 Move domain reasoning out of React

- React components should render backend contracts.
- Relationship classifications, evidence interpretation, and confidence rules
  should not be independently recreated in UI components.

### P0.6 Establish regression fixtures

Required scenarios:

- period with actual-play evidence;
- period with library evidence only;
- period with recent Apple observations only;
- period with mixed evidence;
- searched source with zero evidence;
- unsearched source;
- unavailable source;
- unsupported historical period;
- ambiguous artist identity;
- artist-family identity;
- playlist and radio playback context;
- unknown playback context.

## Priority 1 — Period Intelligence Vertical Slice

This is the first major end-to-end implementation target.

### P1.1 Expand the period backend

- Join actual-play activity where available.
- Preserve Library Tracks reconstruction as a separate evidence family.
- Search snapshot warehouse history for recent Apple observations.
- Include playlists, stations, albums, tracks, and source context where known.
- Generate facts, insights, confidence, warnings, and suggested investigations.

### P1.2 Add evidence-backed period tags

Period tags should include available context such as:

- artists present;
- albums present;
- tracks present;
- dominant artist, album, and track;
- playlists and radio stations;
- album-centered listening;
- concentration versus exploration;
- returning versus newly observed artists;
- catalog depth versus isolated tracks;
- unknown or incomplete context.

Every tag must carry provenance.

### P1.3 Redesign the Period Intelligence UI

Required sections:

1. Period summary
2. Evidence coverage
3. What played or appeared
4. Artists, albums, and tracks
5. Playback contexts
6. Period tags
7. Facts and interpretation
8. Confidence and limitations
9. Provenance
10. Suggested investigations

#### Deferred Period Intelligence presentation polish

The Actual Listening v1 integration passed live and visual acceptance for:

- a covered period with matching Actual Listening;
- a covered period with zero matching evidence;
- a period outside Actual Listening projection coverage.

The following non-blocking presentation items remain:

- Consolidate repeated `Period Intelligence` labels in the result header.
- Render machine-readable statuses such as `not_searched` as human-readable
  labels everywhere.
- Rename `Library Evidence Read` to clearer investigation language.
- Investigate source-title normalization for values such as
  `20200816 She Want The Sandwich` without silently changing authoritative
  source data.
- Use a more compact detail state when all covered-period metrics are zero.
- Suppress or reword low-value facts such as
  `0 confirmed plays and 0 recorded forward skips`.
- Avoid repeating the same source limitation in Evidence Coverage, Coverage
  Warnings, and a dedicated coverage notice.
- Do not display the missing-artist limitation when Actual Listening is
  outside coverage because the projection was not searched.
- Consider suppressing empty Library Evidence ranking sections when both
  artist and album rankings are empty.
- Preserve the distinction between zero evidence, an unsearched source,
  an unavailable source, and a period outside source coverage.

These items must not delay further multi-source Period Intelligence work.

### P1.4 Correct period terminology

- Replace unqualified `Tracks Matched` with an evidence-specific label.
- Do not use `Time Machine` as the only visible source description.
- Correct the malformed date-range arrow encoding.
- Replace generic zero states with diagnostic source-coverage messages.

## Priority 1 — Cross-Surface Integration

### P1.5 Dashboard to Workbench

- Launch preconfigured artist, album, song, playlist, station, or period
  investigations from Dashboard signals.
- Preserve the originating signal and capture timestamp.

### P1.6 Workbench to Artist Intelligence

- Open the canonical artist profile from an investigation.
- Preserve enough state to return to the active investigation.

### P1.7 Artist Intelligence to Workbench

- Link evidence, uncertainty, and questions to targeted investigations.
- Do not reproduce full reasoning traces in the profile.

### P1.8 Playlist Intelligence integration

- Link playlist artists, tracks, and claims to Workbench investigations.
- Link material playlist evidence from Artist Intelligence.

## Priority 1 — Shared Artist Profile

### P1.9 Consolidate the canonical profile model

The shared profile should summarize:

- canonical artist identity;
- artist family and aliases;
- Actual Plays;
- Actual Skips;
- listening duration;
- historical span;
- library representation;
- catalog depth;
- recent Apple signals;
- relationship shape when governed and supported;
- evidence coverage and confidence.

### P1.10 Remove duplicate profile logic

- Dashboard and Workbench should consume the same canonical summary.
- Artist Intelligence should not independently rederive source semantics.

## Priority 1 — System Health and Trust

### P1.11 Add visible Music source health

Expose:

- backend availability;
- last Apple refresh;
- snapshot identifier;
- objects captured;
- archive availability;
- actual-play source availability;
- identity mapping health;
- stale or partial data warnings.

### P1.12 Separate operational failure from empty evidence

- Backend unavailable is an error.
- Source unavailable is a coverage condition.
- Source searched with zero results is a valid analytical outcome.
- Source not searched must be disclosed.

## Priority 2 — Workbench UX Architecture

### P2.1 Replace filter-first navigation with investigation types

Supported investigation types should include:

- artist investigation;
- period investigation;
- song investigation;
- album investigation;
- playlist investigation;
- current versus historical comparison;
- evidence inspection.

### P2.2 Build shared evidence components

Reusable components should render:

- evidence coverage;
- source cards;
- facts;
- insights;
- confidence;
- limitations;
- provenance;
- next investigations.

## Priority 2 — Music Library Reduction

### P2.3 Compact Library administration and inventory embedded functionality

- Keep Library search visible while reducing the oversized administration area.
- Replace the exposed export, restore, CSV import, and template-download controls with a compact `Manage Library` menu or expandable administration panel.
- Reduce the hero and header height and keep album, artist, and show counts inline.
- Remove or consolidate the duplicate Music Administration explanation strip.
- Reclaim vertical space for curated Library content.

- Document all valid behavior currently provided by `MusicLibrary.jsx` and
  `MusicTimeMachine`.
- Identify the destination surface for each behavior.

### P2.3a Make Library search visible and actionable

- Current `Search Library` behavior filters the lower curated Artists, Albums, Playlists, Shows, and Explore sections.
- Music Dashboard, Tag Browser, Artist Spotlight, and Recently Added remain independent of the query.
- When matching curated sections are collapsed, the interface provides little or no visible confirmation that filtering occurred.
- Add immediate search feedback through a dedicated results panel or an equivalent clearly visible interaction.
- Include total and per-category match counts, matching records, a clear-query action, and an explicit zero-result state.
- Preserve Dashboard summary behavior unless a later product decision deliberately makes summaries query-responsive.
- This is a known non-blocking usability follow-up and must not delay higher-priority Period Intelligence work.


### P2.4 Remove analytical duplication

- Move Period Intelligence fully into Query Workbench.
- Remove the embedded Music Dashboard section.
- Remove duplicate artist and playlist analysis after migration.

### P2.5 Change navigation status

- Hide Music Library from primary navigation only after administration and
  curation workflows remain accessible.

## Priority 2 — Album Intelligence

### P2.6 Enforce canonical Album Entities

- Live Apple data, historical activity, playlists, and album intelligence should
  join through canonical Album Entities rather than raw titles.

### P2.7 Develop album-depth measures

- Distinguish concentrated album relationships from shallow relationships.
- Measure album depth independently of ecosystem concentration.
- Separate studio, live, compilation, and other album forms where supported.

### P2.8 Integrate live album observations

- Normalize live Apple album objects before persistence.
- Connect current album signals to historical album evidence.

## Priority 3 — Governed Relationship Intelligence

These concepts remain blocked until formulas and gates are reviewed and accepted.

- Permanent Companion
- Hidden Pillar
- Quiet Persistence
- Established Companion
- Catalog Relationship
- Album-Centered Relationship
- Song-Centered Relationship
- Emerging Core Artist
- Dormant Core
- Resurgent Core
- Friction
- Relationship shape

The UI must not present blocked concepts as production classifications.

## Deferred Research and Product Concepts

The following remain outside the first implementation sequence:

- Desert Island 25;
- Albums I Lived With;
- Permanent Companions dedicated UI;
- album family above canonical album;
- broad playlist comparison;
- fixture candidate queue;
- compact Recently Active Albums card density;
- additional identity entity types without documented identity rules;
- unsupported emotional or autobiographical conclusions.

## Protected Existing Work

The following uncommitted implementation files must remain protected until their
intent is classified and reviewed:

- `data/music/scripts/bridge/artist_bridge.py`
- `server/lib/investigationBuilder.js`
- `src/App.jsx`
- `src/ArtistIntelligence.jsx`
- `src/MusicLibrary.jsx`
- `src/QueryWorkbench.jsx`
- `src/music/components/ArtistDossierModal.jsx`

These changes appear to improve terminology and remove presentation-side
classification logic. They should not be overwritten by new sprint work.

## Recommended Implementation Sequence

1. Review and preserve the seven existing uncommitted changes.
2. Freeze the Period Intelligence field-level API contract.
3. Implement source coverage and diagnostic zero states.
4. Add actual activity and snapshot evidence to period investigations.
5. Build Period Intelligence regression fixtures.
6. Implement the Period Intelligence UI vertical slice.
7. Connect Dashboard signals to Workbench investigations.
8. Consolidate the shared artist profile.
9. Integrate Playlist Intelligence transitions.
10. Add source-health and freshness reporting.
11. Reduce Music Library to administration and curation.
12. Continue Album Intelligence and governed classification work.

## Music Sprint 1 Exit Criteria

Music Sprint 1 is complete when:

- the current architecture and API paths are documented;
- the Period Intelligence requirements are documented;
- the surface responsibility matrix is documented;
- the consolidated backlog is prioritized;
- obsolete Listening Eras remnants are absent;
- existing uncommitted implementation work is identified and protected;
- the next implementation vertical slice is selected;
- dependencies and risks are explicit;
- the scoped documentation diff passes validation;
- the requirements documents are committed before implementation begins.

## Dependencies

- Apple daily track-summary historical data;
- Apple snapshot warehouse history;
- source provenance registry;
- canonical artist, album, song, playlist, station, and period identity;
- investigation packet support for period entities;
- playback-context classification rules;
- regression fixtures and representative source scenarios.

## Primary Risks

- overstating recent observations as confirmed plays;
- presenting Library Tracks reconstruction as complete history;
- styling the UI before stabilizing backend contracts;
- duplicating analytical logic across React components;
- deleting valid Music Library functionality before migration;
- treating unavailable and empty evidence as the same condition;
- exposing blocked relationship classifications as production truth.
