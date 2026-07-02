# Music Phase Requirements Checklist v1

## Status

Draft for review before any UI work.

UI implementation is blocked until this checklist is reviewed and accepted.

---

## 1. Product Surface Responsibilities

### Music Dashboard

Purpose: triage.

The Music Dashboard should answer:

- What changed?
- What is active?
- What looks unusual?
- What deserves investigation next?

Responsibilities:

- Show high-level Music state.
- Surface recent/live signals.
- Surface investigation candidates.
- Route users into deeper surfaces.

Not responsible for:

- Full artist profiles.
- Full reasoning traces.
- Manual curation workflows.
- Detailed playlist/cohort analysis.

---

### Query Workbench

Purpose: investigation cockpit.

The Query Workbench should expose the reasoning path:

Identity -> Evidence -> Facts -> Insights -> Next Investigations

Responsibilities:

- Resolve the queried entity.
- Show identity and canonical keys.
- Show source-backed evidence.
- Derive deterministic facts.
- Suggest insights only when evidence supports them.
- Show open questions and next investigation paths.
- Expose reasoning trace and provenance.

Not responsible for:

- Being the polished artist profile.
- Being the dashboard.
- Hiding uncertainty.
- Producing opaque narrative.

---

### Artist Intelligence

Purpose: durable artist or artist-family profile.

Responsibilities:

- Present a polished artist/family view.
- Show long-term relationship shape.
- Show actual play history.
- Show catalog depth.
- Show family amplification where relevant.
- Link to Query Workbench for investigation/debug paths.
- Link to Playlist Intelligence where playlist/cohort evidence matters.

Not responsible for:

- Raw query debugging.
- Source-level admin workflows.
- Playlist cohort mechanics.

---

### Playlist Intelligence

Purpose: playlist and cohort analysis.

Playlist Intelligence treats playlists as first-class musical artifacts.

Responsibilities:

- Show playlist overview.
- Show shared core artists.
- Show bridge songs.
- Show playlist signatures.
- Show playlist DNA.
- Analyze intentional placement and playlist overlap.

Not responsible for:

- Declaring favorite artists by itself.
- Treating playlist placement as actual listening truth.
- Replacing artist relationship intelligence.

---

### Music Library

Current decision needed.

Possible target role:

Admin / curation surface only.

Allowed responsibilities if retained:

- Inspect imported library records.
- Support curation and normalization.
- Expose data hygiene issues.
- Help manage identities, aliases, and metadata.

Not responsible for:

- Being a primary analytical destination.
- Duplicating Dashboard, Query Workbench, Artist Intelligence, or Playlist Intelligence.

Open decision:

- Keep as admin/curation.
- Hide from primary navigation.
- Deprecate after equivalent admin workflows exist elsewhere.

---

## 2. Canonical Terminology

### Actual plays

Primary listening metric from Apple Music daily track summary.

Must not be confused with library records.

---

### Actual skips

Skip activity from Apple Music daily track summary.

---

### Listening hours

Derived listening duration from actual play data.

Must indicate whether duration is capped, cleaned, or raw.

---

### Library evidence records

Evidence from Apple Music Library Tracks.

This is evidence of library presence, not play count.

Must never be labeled "Total Plays."

---

### Live objects

Objects from live Apple Music endpoints such as recent played, library objects, and heavy rotation.

Live objects indicate current/fresh state, not long-term historical truth by themselves.

---

### Heavy rotation signals

Signals from Apple Music heavy rotation endpoint.

Must include generated timestamp or freshness marker.

---

### First seen / latest seen

Dates when an entity appears in evidence records.

Used for source visibility.

---

### First played / latest played

Dates from actual listening activity.

Used for listening history.

---

### Family amplification

Family actual plays divided by solo/canonical artist actual plays.

Must show numerator and denominator or make them inspectable.

---

### Relationship shape

A descriptive classification of the artist relationship pattern.

Must be evidence-backed.

---

### Friction

A future derived metric.

Likely related to skip rate, abandonment, shallow replay, or resistance.

Blocked until formula and confidence model are documented.

---

### Momentum

A future derived metric.

Likely related to recent increase/decrease versus baseline.

Blocked until time windows and formula are documented.

---

### Emerging Core Artist

A future classification.

Proposed rule family:

Momentum rising + friction falling or acceptable + enough evidence depth.

Blocked until Momentum and Friction are defined.

---

### Dormant Relationship

A future classification for a historically meaningful relationship with weak recent signal.

Blocked until dormancy window and baseline are defined.

---

### Return Signal

A future classification for renewed activity after dormancy.

Blocked until dormant baseline and recent-return threshold are defined.

---

### Catalog Ecosystem

A relationship pattern where listening spans a broad artist catalog.

Must not be based on play count alone.

Requires album/song breadth, years represented, and context where available.

---

## 3. Provenance Contract

Every Music result or UI panel must expose five things:

1. Entity identity
2. Metric type
3. Data source
4. Confidence/freshness
5. Next investigation path

### Entity identity

Examples:

- Artist
- Artist family
- Song
- Album
- Playlist
- Date
- Cohort

Required fields where available:

- Display name
- Canonical key
- Entity type
- Aliases or matched names
- Family membership, if applicable

---

### Metric type

Every displayed value must identify what kind of metric it is:

- Actual listening metric
- Library evidence metric
- Playlist placement metric
- Live signal
- Derived metric
- Classification
- Hypothesis

---

### Data source

Every metric or claim must identify its source.

Known source families:

- Apple Music daily track summary
- Apple Music Library Tracks
- Apple Music Library Playlists
- DuckDB listening context
- Apple Music live endpoints
- Curated identity/album seeds
- Derived model output

---

### Confidence/freshness

Every insight must expose confidence.

Every time-sensitive source must expose freshness.

Examples:

- High confidence: direct match in actual listening data.
- Medium confidence: source-backed but incomplete context.
- Low confidence: weak evidence, unresolved identity, or source limitation.
- Freshness: latest played, latest seen, generatedAt, snapshotId, or source export date.

---

### Next investigation path

Every panel should suggest at least one useful next path:

- Open in Query Workbench.
- Open Artist Intelligence.
- Open Playlist Intelligence.
- Compare with family members.
- Inspect timeline.
- Inspect top albums.
- Review identity mapping.
- Review source limitation.
- Review playlist overlap.

---

## 4. Analytical Intelligence Gates

The following must not be implemented as UI classifications until the requirements below are met:

- Friction
- Momentum
- Emerging Core Artist
- Dormant Relationship
- Return Signal
- Catalog Ecosystem

### Gate 1: Identity

Canonical identity must be resolved first.

Required:

- Canonical artist or family key.
- Matched source names.
- Alias/family mapping status.
- Identity confidence.

---

### Gate 2: Source separation

The system must keep these separate:

- Actual plays
- Library evidence
- Playlist placement
- Live objects
- Derived classifications

No panel should imply that one source type proves another.

---

### Gate 3: Time windows

Define before implementation:

- Recent window
- Baseline window
- Dormancy window
- Return window
- Export/live freshness rules

---

### Gate 4: Formula

Each derived metric must have a documented calculation.

Minimum formula requirements:

- Inputs
- Source columns/files
- Date windows
- Normalization rules
- Edge cases
- Confidence rules

---

### Gate 5: Counter-evidence

Each classification must show what could weaken it.

Examples:

- High skips may weaken a positive relationship claim.
- Low catalog breadth may weaken Catalog Ecosystem.
- Weak recent data may weaken Momentum.
- Missing identity mapping may weaken family conclusions.

---

### Gate 6: Reasoning trace

Every insight must be traceable:

Evidence -> Facts -> Insight -> Confidence -> Rules Applied

No opaque conclusions.

---

## 5. Deferred Artifact Decisions

### Duplicate playlist model doc

File:

- docs/music/# Music Playlist Intelligence Model v0.md

Decision:

- Do not commit as-is.
- Treat as duplicate/merge source.
- Extract any missing concepts into playlist-intelligence-v0.md later.
- Delete after confirmed merge.
- Also fix mojibake in canonical playlist docs.

---

### Artists Living Rent Free report

File:

- docs/music/artists-living-rent-free-v1.md

Decision:

- Keep.
- Move to docs/music/reports/artists-living-rent-free-v1.md.
- Treat as research report, not core model doc.

---

### Investigation packet example

File:

- docs/music/investigation-packet-v1.json

Decision:

- Keep.
- Move to docs/music/examples/investigation-packet-elvis-costello-family-v1.json.
- Treat as example packet / schema fixture.
- Use as a reference for future Query Workbench packet shape.

---

## 6. Open Decisions Before UI Work

- Should Music Library remain visible in primary navigation?
- Should Music Library become admin/curation only?
- Should Query Workbench produce reusable investigation packets as JSON?
- Should Artist Intelligence consume the same packet shape as Query Workbench?
- What exact formulas define Friction and Momentum?
- What recent/baseline windows define Emerging Core Artist?
- What source is authoritative for live freshness?
- Which mojibake cleanup belongs in this phase?
- Should reports/examples be committed now as docs fixtures?

---

## 7. UI Blocker Statement

Do not begin UI implementation until the following are approved:

- Product surface responsibilities
- Canonical terminology
- Provenance contract
- Analytical intelligence gates
- Music Library decision
- Deferred artifact classification
