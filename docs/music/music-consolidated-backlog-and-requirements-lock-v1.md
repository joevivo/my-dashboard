# Music Consolidated Backlog and Requirements Lock v1

## Document control

- Product: Defending Sisyphus Music
- Repository branch: `main`
- Repository baseline: `752550c`
- Reconciliation date: 2026-07-27
- Review state: proposed reconciled revision awaiting Ginto approval
- Governing rule: no new Music feature implementation begins until this revision
  and its priority order are reviewed and approved.

This document is the governing Music backlog, requirements lock, and
implementation sequence. It replaces historical sprint assumptions and stale
descriptions with the functionality now present in the repository and the work
that remains.

## 1. Status model

Every backlog item must use one of these states.

### Completed for v1

The capability is implemented and accepted for the current product contract.
Follow-up refinement may remain, but the core capability is no longer active
feature work.

### Active

The capability is part of the current approved implementation sequence.

### Near-term

The capability should follow the active work after its dependencies are met.

### Later

The capability remains valid but does not belong in the immediate sequence.

### Blocked pending governance

Implementation or production presentation is prohibited until formulas,
semantics, missing-data rules, confidence gates, or other governing decisions
are reviewed and approved.

### Explicitly deferred

The capability is intentionally outside the current plan. It must not re-enter
the implementation sequence without an explicit product decision.

## 2. Product analytical path

The Music product supports one continuous analytical path:

1. Music Dashboard observes and triages the present.
2. Query Workbench investigates evidence and explains what the evidence means.
3. Artist Intelligence presents a concise canonical artist or artist-family
   profile.
4. Playlist Intelligence analyzes playlists, cohorts, and curation evidence.
5. Music Library supports administration, curation, discovery, and data
   hygiene.

Transitions among these surfaces must preserve the originating signal, source,
timestamp, entity identity, investigation state, and a usable return path.

## 3. Surface responsibilities

### 3.1 Music Dashboard

The Dashboard observes current state.

It may present:

- current and recent Apple objects;
- heavy rotation;
- playlists;
- stations;
- current changes;
- concise canonical summaries;
- source-health and freshness indicators.

It must not present itself as complete listening history or expose full
reasoning traces.

### 3.2 Query Workbench

Query Workbench is the evidence and investigation cockpit.

It owns:

- identity resolution;
- evidence retrieval;
- evidence coverage;
- facts;
- interpretations;
- confidence;
- limitations;
- provenance;
- suggested investigations.

Supported investigation types should include:

- artist;
- song;
- period;
- album;
- playlist;
- current-versus-historical comparison;
- evidence inspection.

### 3.3 Artist Intelligence

Artist Intelligence is the concise canonical artist or artist-family profile.

It must use the shared canonical Artist summary contract rather than
independently rederive source semantics. Full evidence and derivation remain in
Query Workbench.

### 3.4 Playlist Intelligence

Playlists are first-class musical artifacts.

Playlist placement is evidence of curation, organization, or listening
context. Playlist placement is not confirmed Actual Play evidence.

### 3.5 Music Library

Music Library supports:

- search;
- curation;
- administration;
- import and export;
- data hygiene;
- access to curated artists, albums, playlists, shows, and related records.

It should not remain a primary analytical destination after valid analytical
behavior has been inventoried and migrated to its intended surface.

Music Library must not be removed from primary navigation until administration,
curation, search, and data-hygiene workflows remain clearly accessible.

## 4. Locked evidence semantics

### 4.1 Actual Plays

Actual Plays come from Apple Music daily track-summary evidence.

Library records, recent Apple objects, snapshot observations, and reconstructed
Last Played Date evidence must never be labeled as Actual Plays.

### 4.2 Actual Skips

Actual Skips come from Apple Music daily track-summary evidence.

Skip definitions, source limitations, and coverage boundaries must remain
visible. Skip counts must not be inferred from unrelated evidence families.

### 4.3 Library Evidence

Library Evidence comes from Apple Music Library Tracks and related canonical
library records.

Library presence and Last Played Date reconstruction are evidence of library
relationship and historical observation. They are not total play counts or a
complete listening history.

### 4.4 Recent Apple Objects

Recent Apple Objects are timestamped observations from current Apple Music
surfaces and stored Apple snapshots.

They indicate current or recently observed state. Historical snapshot
observations are not confirmed plays.

Current Recent Apple evidence and historical snapshot evidence must remain
separate.

### 4.5 Evidence coverage states

Every investigation must distinguish:

- searched with evidence;
- searched with zero evidence;
- outside source coverage;
- unavailable;
- not searched;
- stale;
- unsupported for the requested period.

Unavailable, unsearched, stale, unsupported, and genuinely empty evidence must
not be collapsed into one zero state.

Backend unavailability is an operational error. Source unavailability is an
evidence-coverage condition.

### 4.6 Context

Supported context values may include:

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

## 5. Completed for v1

### 5.1 Period Intelligence

The following are complete for v1:

- Period Intelligence response contract.
- The period is treated as the investigated entity.
- Period output aligns with the investigation packet contract.
- Every relevant evidence source reports an explicit coverage state.
- Diagnostic zero states distinguish searched-zero, unavailable, not searched,
  outside coverage, stale, and unsupported periods.
- Actual Listening v1 is integrated.
- Library Evidence remains separate from Actual Listening.
- Historical Recent Apple snapshot evidence is connected to Date Range
  investigation.
- Snapshot observations are explicitly identified as observations rather than
  confirmed plays.
- Date Range uses an answer-first interface.
- Representative Date Range API and visual acceptance scenarios have passed.

The following Period Intelligence scenarios are part of the maintained v1
contract:

- covered period with Actual Listening evidence;
- covered period with zero matching Actual Listening evidence;
- Library Evidence only;
- Recent Apple observations only;
- mixed evidence;
- searched source with zero evidence;
- unsearched source;
- unavailable source;
- unsupported historical period;
- ambiguous artist identity;
- artist-family identity.

The maintained Period Intelligence response structure includes:

1. period summary;
2. evidence coverage;
3. what played or appeared;
4. artists, albums, and tracks;
5. context and evidence-backed tags;
6. facts and interpretation;
7. confidence and limitations;
8. provenance;
9. suggested investigations.

### 5.2 Artist Investigation

The following are complete for v1:

- Actual Listening evidence.
- Library Evidence.
- Current Recent Apple objects.
- Historical Recent Apple snapshot observations.
- Snapshot-observation count.
- Unique logical-object count.
- Separation of current and historical Recent Apple evidence.
- Sugar and Bob Mould artist-family mapping.
- Steve Miller and Steve Miller Band artist-family mapping.
- Removal of Canonical Key from the visible Artist Investigation interface.

Recent accepted repository work includes:

- `195c455 Add historical Recent Apple artist evidence`
- `07d9062 Refine artist family identity presentation`

### 5.3 Verified implementation checkpoints

The following implementation checkpoints are verified in repository history:

- Artist Comparative Standing v1 is implemented end to end:
  - `f43606a Implement Comparative Standing runtime adapters`
  - `a3f247b Expose Comparative Standing artist responses`
  - `8ce6cf9 Regenerate Comparative Standing during Music refresh`
  - `7a9c912 Present Comparative Standing in Query Workbench`
  - `3e89912 Add indexed Comparative Standing cache`
- Music Time Machine structured v1 is mounted at `e661fb8`.
- Artist Dossier contract alignment is complete at `b0c82c6`.
- Music navigation ownership isolation is complete at `9562b3e`:
  - primary Music navigation metadata was extracted from `src/App.jsx` to
    `src/music/musicNavigation.js`;
  - existing Music labels, ordering, and routing behavior were preserved;
  - frontend build and staged diff validation passed;
  - the `music-intelligence` branch checkpoint was pushed to
    `origin/music-intelligence`.
- Period Intelligence remains complete for v1 as recorded in section 5.1.
- Artist Investigation remains complete for its current v1 behavior as recorded
  in section 5.2.

These checkpoints supersede backlog or roadmap language that describes Period
Intelligence or Artist Comparative Standing as the next unimplemented vertical
slice.

## 6. Authoritative implementation priority order
Direction A / Period Cockpit was approved by Ginto on August 24, 2026 as the
Music Intelligence Home design target. The design uses first-class
1 / 7 / 30 / 90 / Custom controls, a headline period read, compact KPIs,
artwork-led rankings where supported, period movement, composition-oriented
Listening Shape visuals, historical context, investigation paths, and explicit
evidence-source separation. Availability after May 26 is source-specific and
must not be represented by a blanket unavailable statement.

### Completed checkpoint - Backlog reconciliation

Status: Completed and pushed at `92a413d`.

### Active 1 - Reconcile the Music branches

`main` contains the transport-only Canonical Artist backend at `b8a615d`.
`music-intelligence` contains the Music roadmap and frontend work through
`1087220`. Both branches diverge from `41539d7`, with no overlapping changed
paths at the verified checkpoint.

Acceptance requires integration of `main` into `music-intelligence`,
preservation of unrelated work, and validation of the combined frontend and
backend.

### Implemented contract lock - Artist Comparative Standing

Status: Implemented for the current v1 scope. The following requirements remain
the governing regression and extension contract.

Each source-specific comparative statement must disclose:

- the measured dimension;
- the artist's value;
- percentile;
- numeric rank;
- eligible comparison-population size;
- comparison-population eligibility rule;
- evidence source;
- coverage basis;
- concise interpretation.

Example:

`97 confirmed plays - 84th percentile, rank 296 of 1,846 artists with Actual Listening evidence.`

Implemented candidate dimensions include:

- confirmed Actual Plays;
- confirmed listening duration;
- Library Evidence record count;
- historical relationship span;
- Recent Apple observation volume;
- snapshot persistence;
- unique observed objects.

Requirements:

- Missing source coverage must not be treated as zero activity.
- Artist-only comparisons and artist-family comparisons must remain distinct.
- Comparison populations must be source-specific.
- The eligible population must always be disclosed.
- Rankings must use deterministic and documented tie handling.
- A source with insufficient coverage must return an explicit coverage state
  rather than a misleading rank.
- The interface must not present one unexplained overall percentage.
- Source-specific comparative facts may appear without a composite relationship
  model.

Remaining Comparative Standing work is limited to regression coverage,
representative artist and artist-family validation, and explicitly approved
extensions. It is not the next feature vertical slice.

### Completed contract lock - Canonical Artist summary

Python owns Artist semantics. Express is transport-only for artist family,
family metrics, bridge and continuity, comparative standing, and investigation.

The backend migration is complete on `main` at `b8a615d`. Artist Intelligence
canonical-summary alignment is complete on `music-intelligence` at `c7caa09`.

### Active 2 - Complete canonical Artist frontend consumption

`src/QueryWorkbench.jsx` does not yet consume `canonicalArtistSummary`
directly.

Requirements:

- consume the canonical summary directly for Artist mode;
- preserve fallback only for non-Artist modes where necessary;
- preserve current and historical Recent Apple separation;
- preserve artist-only and artist-family scope;
- do not create a second frontend semantic model;
- retain evidence and investigation ownership in Query Workbench.

### Next 1 - Governed live/current 1 / 7 / 30 / 90 intelligence

Approximately May 26, 2026 is the historical/live source boundary.

The searched live pipeline contains timestamped Apple surface observations—not
timestamped listening events. Live observations must not be labeled as plays,
duration, skips, repeat frequency, or time-of-day listening.

Supported intelligence, subject to cadence and coverage:

- unique Recent Apple objects observed within a window;
- persistence, entries, exits, and position movement;
- breadth and concentration;
- prior-equivalent-window comparison;
- separate Heavy Rotation evidence;
- explicit freshness and coverage.

Window treatment:

- 1 day is conditional;
- 7 days requires cadence disclosure;
- 30 days is the first implementation window;
- 90 days remains partial until sufficient live history exists.

Unavailable or unsearched metrics must never become zero.

### Next 2 - Trust and integration

- Period Intelligence regression fixtures;
- visible source health and freshness;
- canonical artist identity in Actual Listening;
- evidence-specific terminology;
- cross-surface routing;
- reusable evidence components.

### Later

- Canonical Album Intelligence, normalization, and Album Dossiers;
- Song Intelligence and shared Song Investigation evidence;
- Playlist Intelligence expansion;
- Artist Journey refinement;
- session reconstruction;
- additional Comparative Standing extensions;
- shared Music Intelligence shell refinement.

### Superseded

- Period Intelligence as the next unimplemented slice;
- Artist Comparative Standing as the next unimplemented slice;
- Canonical Artist as the next unimplemented slice;
- continuous historical Actual Listening beyond May 26;
- identical metrics for all windows regardless of evidence.

### Parking lot and research

- unresolved and `UNKNOWN` evidence;
- historical snapshot persistence;
- Recent Apple and Heavy Rotation interpretation;
- identity-normalization candidates;
- relationship-model and composite-score governance;
- DuckDB or equivalent exploration tooling;
- later visual refinements.

### Parked Time Machine cleanup

Do not implement automatically. Remove Spring 2020, Summer 2021, 2015, and 2016
preset ranges. Retain manual start/end inputs and Previous Period / Next Period.

## 7. Near-term work

### 7.1 Period Intelligence regression fixtures

Create reusable regression fixtures for:

- Actual Listening evidence;
- Library-only evidence;
- Recent Apple-only evidence;
- mixed evidence;
- searched-zero evidence;
- unsearched source;
- unavailable source;
- unsupported historical period;
- ambiguous artist identity;
- artist-family identity;
- timezone boundaries.

Fixtures must validate both API contracts and user-facing diagnostic behavior.

### 7.2 Evidence-backed period tags

Complete tags for:

- artists present;
- albums present;
- tracks present;
- dominant artist;
- dominant album;
- dominant track;
- playlists;
- radio stations;
- album-centered listening;
- concentration versus exploration;
- returning versus newly observed artists;
- catalog depth versus isolated tracks;
- unknown or incomplete context.

Every tag must carry provenance. A tag must not be produced when the source
evidence does not support it.

### 7.3 Actual Listening artist identity

Add canonical artist identity to the Actual Listening projection.

Requirements:

- preserve source artist text;
- add canonical artist identity where resolved;
- retain ambiguity explicitly;
- support artist-family rollup without erasing artist-only evidence;
- prevent duplicate counting across aliases or family members;
- retain season-independent, source-independent identity rules.

### 7.4 Period terminology and presentation cleanup

Remaining non-blocking cleanup includes:

- clarify or replace `yearsActive`;
- distinguish active-year count from relationship span;
- rename unclear Library Evidence labels;
- replace unqualified `Tracks Matched` language with evidence-specific labels;
- avoid using `Time Machine` as the only visible source description;
- normalize malformed date-range arrow presentation;
- use compact detail presentation when covered metrics are all zero;
- suppress or reword low-value repeated facts;
- avoid repeating the same source limitation in multiple sections;
- suppress empty ranking sections when no evidence supports them;
- preserve diagnostic distinctions among zero, unsearched, unavailable, stale,
  and unsupported states;
- harden the timezone contract.

### 7.5 Cross-surface integration

Implement:

- Dashboard to preconfigured Workbench investigations;
- Workbench to canonical Artist Intelligence profiles;
- Artist Intelligence back to the originating Workbench investigation;
- Playlist Intelligence to artist, track, album, and claim investigations;
- Artist Intelligence links to material playlist evidence.

Each transition must preserve:

- originating signal;
- source;
- timestamp;
- canonical entity identity;
- active filters;
- investigation parameters;
- return state.

Artist Intelligence must not reproduce the full Workbench reasoning trace.

### 7.6 Visible Music source health and freshness

Expose:

- backend availability;
- latest successful Apple refresh;
- latest snapshot identifier;
- latest snapshot timestamp;
- objects captured;
- snapshot archive availability;
- Actual Listening source availability and coverage;
- Library source availability;
- identity-mapping health;
- stale or partial-data warnings.

Create a standard source-provenance registry used by Music surfaces.

Operational errors and valid evidence states must remain visually and
semantically distinct.

### 7.7 Compact Music Library administration and curation

Keep Library search visible.

Collapse these controls into a compact `Manage Library` panel or menu:

- Export Music Library;
- Restore JSON;
- Add Albums CSV;
- Download Album Template.

Also:

- reduce the oversized hero and header;
- keep album, artist, and show counts compact and inline;
- remove or consolidate duplicate Music Administration explanations;
- reclaim vertical space for curated Library content;
- inventory all valid analytical behavior before removing duplication;
- identify the destination surface for every migrated behavior;
- remove embedded Dashboard or duplicate analysis only after migration;
- preserve accessible administration and curation before changing navigation.

#### Library search follow-up

Current Library search filters lower curated Artists, Albums, Playlists, Shows,
and Explore sections. Dashboard summaries, Tag Browser, Artist Spotlight, and
Recently Added remain independent of the query.

When matching sections are collapsed, filtering may provide insufficient
visible confirmation.

Add:

- immediate search feedback;
- a dedicated results panel or equivalent visible interaction;
- total match count;
- per-category match counts;
- matching records;
- clear-query action;
- explicit zero-result state.

Preserve Dashboard summary behavior unless a later product decision deliberately
makes summaries query-responsive.

### 7.8 Song Investigation shared evidence contract

Rebuild Song Investigation on the shared evidence contract.

It must distinguish:

- Actual Plays;
- Actual Skips;
- listening duration;
- Library Evidence;
- current Recent Apple observations;
- historical snapshot observations;
- playlist-placement evidence;
- source coverage;
- provenance;
- confidence and limitations.

Song Investigation must not infer total history from library presence or recent
observations.

### 7.9 Canonical Album Intelligence

Continue canonical Album Intelligence with:

- canonical Album Entities;
- album identity resolution;
- album-depth measures;
- concentrated versus shallow album relationships;
- studio, live, compilation, and other release distinctions where supported;
- normalized live Apple album objects before persistence;
- current Recent Apple album signals joined to historical album evidence;
- source coverage and provenance.

## 8. Later work

### 8.1 Playlist Intelligence expansion

Later Playlist Intelligence work includes:

- canonical playlist identity;
- playlist navigation;
- curation evidence;
- historical playlist observations;
- governed cohort comparisons;
- playlist-to-artist and playlist-to-track relationships;
- broad playlist comparisons after comparison rules are approved.

### 8.2 Additional Album Intelligence

Later Album work includes:

- deeper album-family and edition handling;
- release-history relationships;
- governed album comparative standing;
- additional depth and persistence measures.

### 8.3 Specialty concepts

The following remain later or deferred unless explicitly reprioritized:

- Desert Island 25;
- Albums I Lived With;
- Permanent Companions dedicated interface;
- broad specialty collection experiences;
- fixture-candidate queue;
- compact Recently Active Albums density refinements;
- additional identity entity types without documented identity rules.

### 8.4 Deferred artist-family identity candidates

Status: Later. Do not implement during the Artist Comparative Standing slice.

Add these curated artist-family candidates for later identity review:

- Yaz and Alison Moyet.
- Blind Faith, Traffic, and Steve Winwood.

Eventual review requirements:

- preserve every artist and band as a distinct member identity;
- define the canonical family label and aliases before enabling family rollup;
- aggregate family evidence without double-counting shared or aliased records;
- retain artist-only and artist-family comparative populations separately;
- preserve member-level provenance when family evidence is displayed;
- require explicit review and acceptance before changing
  data/music/curated/artistFamilies.json.

## 9. Blocked pending governance

### 9.1 Composite relationship scoring

A composite relationship percentage or score remains blocked.

Governance must define:

- source weighting;
- missing-data behavior;
- artist-family rollups;
- recency;
- skips;
- confidence gates;
- minimum source coverage;
- normalization populations;
- tie handling;
- contradictory evidence;
- explanation requirements.

No unexplained overall percentage may be presented.

### 9.2 Relationship classifications

These concepts remain blocked until formulas, evidence requirements, and
confidence gates are reviewed and approved:

- Permanent Companion;
- Hidden Pillar;
- Quiet Persistence;
- Established Companion;
- Catalog Relationship;
- Album-Centered Relationship;
- Song-Centered Relationship;
- Emerging Core Artist;
- Dormant Core;
- Resurgent Core;
- Friction;
- Relationship Shape.

The production interface must not present blocked concepts as accepted
classifications.

### 9.3 Unsupported interpretation

Emotional, autobiographical, psychological, or life-event conclusions remain
unsupported unless explicit user-authored evidence and a governed product
decision establish them.

## 10. Explicitly deferred

The following are explicitly deferred:

- playback-context ingestion as an immediate sprint requirement;
- unattended automated Apple snapshot capture;
- daily snapshot-health monitoring;
- Listening Eras;
- reintroduction of Listening Eras into navigation or requirements;
- broad playlist comparisons;
- specialty collection interfaces not selected for implementation.

Existing intermittent timestamped snapshots are sufficient for current
exploratory use. Snapshot automation is optional and non-blocking.

Listening Eras remain removed and must not return without an explicit product
decision.

## 11. Source inventory

Current and planned Music intelligence may use:

- Apple Music daily track-summary historical data;
- Apple Music Library Tracks;
- current Apple Music objects;
- Apple snapshot warehouse history;
- canonical artist identity;
- canonical artist-family identity;
- canonical album identity;
- canonical song identity;
- canonical playlist identity;
- canonical station identity;
- canonical period identity;
- investigation packet contracts.

Every exposed fact, interpretation, tag, comparison, and warning must identify
its supporting evidence family or explicitly state that the source was
unavailable, unsearched, stale, unsupported, or empty.

## 12. Implementation guardrails

Do not:

- overstate recent observations as confirmed plays;
- present Library Tracks reconstruction as complete history;
- treat missing source coverage as zero activity;
- combine artist-only and artist-family evidence without disclosure;
- style major interfaces before stabilizing backend contracts;
- duplicate analytical logic across React components;
- delete valid Music Library functionality before migration;
- treat unavailable and empty evidence as the same condition;
- fabricate playback context;
- expose blocked classifications as production truth;
- introduce a composite score without approved governance;
- reintroduce Listening Eras without an explicit decision.

## 13. Approval and next-slice gate

Ginto approved Direction A / Period Cockpit on August 24, 2026.

Execution sequence:

1. commit and push this documentation-only reconciliation;
2. reconcile `main` into `music-intelligence`;
3. validate the combined Canonical Artist backend and Music frontend;
4. complete direct canonical consumption in Query Workbench;
5. implement governed 30-day Recent Apple comparison;
6. extend to 7-day, conditional 1-day, and partial 90-day treatments;
7. continue the approved Period Cockpit sequence.

No step may convert missing evidence into zero, label Recent Apple observations
as confirmed plays, conflate evidence sources, or disturb unrelated work.

The next repository action is:

`Reconcile main into music-intelligence and validate the combined Music scope`
