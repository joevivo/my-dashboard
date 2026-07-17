# Music Eight-Epic Roadmap v1

## Purpose

The backlog audit found 63 textual references to future, deferred, or
unfinished work. Those references do not represent 63 independent projects.

The actionable Music backlog consolidates into eight implementation epics.
Detailed requirements remain in the consolidated backlog, Period Intelligence
requirements, and surface responsibility matrix.

## Roadmap Summary

| Epic | Priority | Outcome |
|---|---:|---|
| 1. Period Intelligence Contract and Coverage | P0 | Stable evidence and API semantics |
| 2. Period Intelligence Backend and UI | P1 | Complete period investigation |
| 3. Regression, Health, and Trust | P0/P1 | Diagnosable sources and outcomes |
| 4. Shared Canonical Artist Profile | P1 | One reusable artist summary |
| 5. Dashboard and Workbench Navigation | P1 | Signals launch investigations |
| 6. Playlist Intelligence Integration | P1/P2 | Playlist evidence joins investigations |
| 7. Music Library Reduction | P2 | Administration and curation only |
| 8. Album and Relationship Intelligence | P2/P3 | Deeper governed intelligence |

## Epic 1 - Period Intelligence Contract and Coverage

### Objective

Freeze the Period Intelligence contract and evidence rules before major UI work.

### Work packages

- Define the field-level response contract.
- Model searched, empty, unsearched, unavailable, stale, and unsupported sources.
- Define playlist, radio, album, library, autoplay, search, and unknown contexts.
- Correct ambiguous fields such as yearsActive.
- Move intelligence derivation out of React.

## Epic 2 - Period Intelligence Backend and UI

### Objective

Deliver the first complete investigation vertical slice.

### Work packages

- Join Actual Plays, Actual Skips, and listening duration where available.
- Preserve Library Tracks reconstruction as a separate evidence family.
- Search relevant Apple snapshot history.
- Surface artists, albums, tracks, playlists, stations, and known contexts.
- Build the Workbench Period Intelligence UI.
- Replace generic zero results with diagnostic coverage messages.

## Epic 3 - Regression, Health, and Trust

### Objective

Make source limitations, failures, and valid empty results visible and testable.

### Work packages

- Add representative regression fixtures.
- Distinguish operational failure from valid empty evidence.
- Display source freshness and archive availability.
- Report backend, snapshot, actual-play, and identity health.

## Epic 4 - Shared Canonical Artist Profile

### Objective

Use one durable artist and artist-family summary across Music surfaces.

### Work packages

- Consolidate identity, aliases, family membership, plays, skips, and duration.
- Include historical span, library depth, recent signals, coverage, and confidence.
- Remove duplicate profile derivation from frontend surfaces.
- Keep full evidence and reasoning in Query Workbench.

## Epic 5 - Dashboard and Workbench Navigation

### Objective

Connect present-state signals to deeper investigation.

### Work packages

- Launch artist, album, song, playlist, station, and period investigations.
- Preserve the originating signal and observation timestamp.
- Support Workbench to Artist Intelligence navigation.
- Support Artist Intelligence back to targeted investigations.
- Replace filter-first controls with investigation types.

## Epic 6 - Playlist Intelligence Integration

### Objective

Connect playlist evidence without treating playlist placement as play truth.

### Work packages

- Link playlist artists and tracks to Workbench investigations.
- Surface material playlist evidence in Artist Intelligence.
- Preserve explicit denominators and provenance.
- Defer broad playlist comparison until primary workflows are stable.

## Epic 7 - Music Library Reduction

### Objective

Reduce Music Library to administration, curation, and data hygiene.

### Work packages

- Inventory valid behavior in MusicLibrary.jsx and MusicTimeMachine.
- Move Period Intelligence fully into Query Workbench.
- Remove the embedded Dashboard and duplicate analytical behavior.
- Hide Music Library from primary navigation only after migration.

## Epic 8 - Album and Relationship Intelligence

### Objective

Advance deeper intelligence after foundational contracts are stable.

### Work packages

- Join album evidence through canonical Album Entities.
- Distinguish album depth from ecosystem concentration.
- Normalize live Apple album observations.
- Govern relationship concepts with formulas, confidence gates, and fixtures.

### Blocked classifications

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
- Relationship Shape

These classifications must not appear as production truth until governance is accepted.

## Deferred Product Research

- Desert Island 25
- Albums I Lived With
- Dedicated Permanent Companions UI
- Album Family above Canonical Album
- Broad playlist comparison
- Fixture candidate queue
- Compact Recently Active Albums treatment
- Additional entity types without identity contracts
- Unsupported emotional or autobiographical conclusions

## Execution Order

1. Freeze the Period Intelligence response contract.
2. Implement evidence coverage and diagnostic zero states.
3. Add available activity and snapshot evidence.
4. Build Period Intelligence regression fixtures.
5. Implement the Workbench Period Intelligence UI.
6. Connect Dashboard and Workbench navigation.
7. Consolidate the shared artist profile.
8. Integrate Playlist Intelligence.
9. Add source-health reporting.
10. Reduce Music Library.
11. Continue album and governed relationship intelligence.

## Current Focus

The next implementation vertical slice is Period Intelligence.
