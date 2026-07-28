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

The following implementation checkpoints are present at repository state
`b0c82c6`:

- Artist Comparative Standing v1 is implemented end to end:
  - `f43606a Implement Comparative Standing runtime adapters`
  - `a3f247b Expose Comparative Standing artist responses`
  - `8ce6cf9 Regenerate Comparative Standing during Music refresh`
  - `7a9c912 Present Comparative Standing in Query Workbench`
  - `3e89912 Add indexed Comparative Standing cache`
- Music Time Machine structured v1 is mounted at `e661fb8`.
- Artist Dossier contract alignment is complete at `b0c82c6`.
- Period Intelligence remains complete for v1 as recorded in section 5.1.
- Artist Investigation remains complete for its current v1 behavior as recorded
  in section 5.2.

These checkpoints supersede backlog or roadmap language that describes Period
Intelligence or Artist Comparative Standing as the next unimplemented vertical
slice.

## 6. Active implementation priority order

### Priority 1 - Complete backlog reconciliation and approval

Status: Active until this document is reviewed and approved.

Acceptance requires:

- completed work is accurately recorded;
- stale sprint, working-tree, and implementation-priority statements are
  identified;
- remaining work is assigned an explicit status;
- the roadmap statement naming Period Intelligence as the next vertical slice is
  recorded as stale and queued for a separate documentation correction;
- implementation dependencies are explicit;
- the revised priority order is approved by Ginto;
- only this backlog document is committed and pushed in the reconciliation
  checkpoint.

No feature implementation begins before this acceptance.

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

### Priority 2 - Define the canonical Artist summary contract

Status: Proposed next implementation vertical slice after backlog approval.

Why this is next:

- Artist Dossier already consumes backend-owned artist and journey semantics.
- Artist Investigation extraction depends on a stable shared Artist contract.
- Reusable evidence components must render shared contracts rather than recreate
  source semantics in React.
- Comparative Standing must enter the shared Artist summary without becoming an
  unexplained composite score.

The shared Artist summary must support:

- canonical artist identity;
- known aliases and artist-family identity;
- artist-only and artist-family scope;
- Actual Plays;
- Actual Skips;
- listening duration;
- historical relationship span;
- Library Evidence representation;
- catalog depth;
- current Recent Apple signals;
- historical snapshot observations;
- comparative standing when supported;
- evidence coverage;
- confidence;
- limitations;
- provenance;
- suggested investigations.

Relationship shape may appear only after its governing model is approved.

Dashboard, Query Workbench, Artist Intelligence, and Artist Dossier must consume
the shared contract rather than independently deriving artist semantics.

Exact slice scope:

1. document the canonical backend-owned Artist summary schema;
2. define identity, scope, evidence, coverage, comparative, confidence,
   limitation, provenance, and investigation fields;
3. preserve explicit distinctions among missing, unsearched, unavailable,
   unsupported, searched-zero, and observed evidence;
4. define the concise canonical profile boundary versus full Query Workbench
   evidence and derivation;
5. validate representative individual-artist and artist-family scenarios;
6. align existing consumers without adding frontend semantic reclassification.

Exclusions:

- Music Time Machine quick-range cleanup;
- new Music evidence sources or ingestion;
- Comparative Standing expansion;
- Playlist Intelligence work;
- broad visual redesign;
- relationship-model invention;
- React-only relabeling that changes backend meaning.

Dependencies:

- approval of this reconciled backlog;
- maintained Period Intelligence coverage semantics;
- existing backend `artist` and `journey` objects;
- existing Artist Comparative Standing responses;
- surface-responsibility boundaries.

Primary risks:

- creating another surface-specific wrapper instead of a shared contract;
- converting missing evidence into zero;
- moving backend classification into React;
- duplicating Query Workbench evidence in concise Artist surfaces;
- combining artist-only and artist-family evidence without disclosure.

Acceptance criteria:

- one documented canonical Artist summary schema exists;
- representative artist and artist-family fixtures pass;
- Artist Intelligence and Artist Dossier consume the same canonical summary;
- Query Workbench remains the owner of full evidence, provenance, and
  derivation;
- frontend relationship-classification logic remains absent;
- missing and unsearched evidence remain distinct from zero;
- Comparative Standing retains its disclosed population and coverage basis;
- structured validation and frontend build pass.

### Priority 3 - Extract Artist Investigation from QueryWorkbench

Status: Blocked until the canonical Artist summary contract is stable.

Requirements:

- extract the Artist Investigation result from oversized inline logic in
  `src/QueryWorkbench.jsx`;
- preserve current accepted behavior;
- preserve current and historical Recent Apple separation;
- preserve artist-family handling;
- render backend contracts rather than reimplement domain reasoning;
- avoid moving the same oversized logic into a differently named component;
- add focused acceptance coverage before removing the inline implementation.

### Priority 4 - Build reusable evidence components

Status: Blocked until the shared Artist contract is defined and its first
consumer boundary is validated.

Reusable components should render:

- evidence coverage;
- source cards;
- facts;
- insights;
- confidence;
- warnings;
- limitations;
- provenance;
- suggested investigations;
- comparative standing.

Components must render shared contracts. Source semantics and analytical
classification logic must not be independently recreated in React components.

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

This reconciled backlog becomes the requirements lock only after Ginto reviews
and approves:

- the completed-for-v1 record;
- the verified implementation checkpoints;
- the active implementation order;
- the retained Artist Comparative Standing contract;
- the canonical Artist summary contract slice;
- the near-term workstreams;
- blocked and deferred decisions.

After approval:

1. commit and push only this reconciled backlog document;
2. confirm the Music scope and staging area are clean and synchronized while
   preserving explicitly unrelated repository changes;
3. correct the stale roadmap Current Focus statement in a separate
   documentation-only checkpoint;
4. begin the canonical Artist summary contract v1 vertical slice;
5. do not broaden the slice without updating this backlog.

The recommended next implementation slice is:

`Artist Comparative Standing contract and comparison-population design`

Feature implementation remains prohibited until the backlog checkpoint is
approved, committed, and pushed.
