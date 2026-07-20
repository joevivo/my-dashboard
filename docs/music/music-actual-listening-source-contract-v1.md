# Music Actual Listening Source Contract v1

## Status

- Contract version: v1
- Product area: Music Period Intelligence
- Sprint: Actual Listening Sprint 3
- Status: implementation-ready
- Scope: historical Actual Listening, behavioral outcomes, identity attribution, coverage, and provenance

## Purpose

This contract defines which Apple Music datasets may support Actual Listening claims, how plays and playback outcomes are interpreted, and which identity matches may be exposed to users.

It prevents the application from:

- treating Library Last Played Date as complete play history;
- treating Recent Apple Objects as Actual Plays;
- treating every short playback as a skip;
- using overlapping Play Count and Skip Count values as a behavioral denominator;
- attributing raw activity to artists through uncontrolled title-only matching;
- making preference or dislike claims from playback outcomes.

## Source hierarchy

### Apple Music Play Activity

Source:

`Apple Music Play Activity.csv`

Role:

- canonical event-level source for playback outcome semantics;
- canonical source for recorded forward skips;
- canonical source for manual track changes;
- canonical source for natural completions;
- canonical source for backward navigation and other event outcomes;
- supporting source for event timestamps, duration, song name, album name, and source type.

Observed source characteristics:

- rows: 199,396;
- date range: 2015-06-30 through 2026-05-26;
- Song Name coverage: 96.4%;
- album-field coverage: 86.1%;
- artist-field coverage: 0%;
- End Reason Type values: 15.

This source must not be assumed to contain complete artist identity.

### Apple Music Play History Daily Tracks

Original source:

`Apple Music - Play History Daily Tracks.csv`

Local projection:

`C:\Users\joevi\apple-music-sanitized\apple-music-daily-track-summary.csv`

Role:

- efficient date-range aggregation;
- Apple Play Count;
- total Play Duration Milliseconds;
- track description;
- daily source and outcome grouping;
- reconciliation against raw activity.

Observed source characteristics:

- rows: 100,791;
- date range: 2016-01-01 through 2026-05-19;
- Play Count: 86,615;
- Apple-reported Skip Count: 44,155;
- listening duration: 10,168.18 hours.

The sanitized projection reconciles exactly with the original source for:

- row count;
- Play Count;
- Skip Count;
- Play Duration Milliseconds.

The sanitized projection is an implementation optimization. Provenance must identify the original Apple export as the evidence source.

### Apple Music Library Tracks

Source:

`Apple Music Library Tracks.json.zip`

Role:

- artist identity;
- album identity;
- track identity;
- high-confidence attribution bridge for raw activity.

Library Last Played Date remains Library Evidence and is not Actual Listening.

### Recent Apple snapshot history

Source family:

`data/music/live/history/<capture-id>/`

Role:

- optional Recent Apple Observations;
- current or recently surfaced Apple objects;
- possible future contextual evidence.

Snapshot capture automation is not part of Sprint 3 and is not a required Sprint 4 prerequisite.

Existing irregular snapshots may be used only when a feature explicitly searches them and reports their coverage.

## Playback context governance

Playback context is evidence about the listening container or initiation surface associated with an Actual Listening event.

Governed context categories include:

- library;
- album;
- playlist;
- radio station;
- recommendation;
- queue;
- another explicitly identified source.

Rules:

- Playback context is separate from proof of play, listening duration, completion, or skip outcome.
- Report context only when the source explicitly supplies it or a documented deterministic rule derives it.
- Do not infer context from track identity, album membership, nearby events, or Recent Apple Observations alone.
- Results must distinguish known context, unavailable or not captured context, ambiguous context, and context sources that were not searched.
- The current v1 Apple Music Play Activity projection does not claim playback context.
- Adding playback context requires source-column support, parser preservation, manifest coverage reporting, and regression tests.

## Actual Listening metrics

The following period metrics may be calculated from valid Apple activity sources:

- actualPlays;
- listeningDurationMilliseconds;
- listeningHours;
- uniqueTrackCount;
- firstActivityAt;
- latestActivityAt;
- dailyActivity;
- sourceTypes;
- naturalCompletions;
- recordedForwardSkips;
- manualTrackChanges;
- backwardNavigations;
- shortPlays;
- interruptedEvents;
- technicalFailureEvents;
- excludedSourceEvents.

Every response must identify which source supplied each metric.

## Playback outcome classification

### Natural completion

Raw End Reason Type:

`NATURAL_END_OF_TRACK`

Canonical metric:

`naturalCompletions`

### Recorded forward skip

Raw End Reason Type:

`TRACK_SKIPPED_FORWARDS`

Canonical metric:

`recordedForwardSkips`

This is the only default playback outcome labeled as a skip.

### Manual track change

Raw End Reason Type:

`MANUALLY_SELECTED_PLAYBACK_OF_A_DIFF_ITEM`

Canonical metric:

`manualTrackChanges`

A manual track change is reported separately from a recorded forward skip.

### Backward navigation

Raw End Reason Type:

`TRACK_SKIPPED_BACKWARDS`

Canonical metric:

`backwardNavigations`

Backward navigation must not be treated as a negative preference signal.

### Short play

A duration threshold may classify an event as a short play.

A short play must not be relabeled as a skip unless the event also has an explicit skip outcome.

### Other event outcomes

The following remain separate from skip behavior:

- PLAYBACK_MANUALLY_PAUSED;
- PLAYBACK_SUSPENDED;
- SCRUB_BEGIN;
- SCRUB_END;
- EXITED_APPLICATION;
- OTHER.

Technical or source-quality outcomes include:

- FAILED_TO_LOAD;
- NOT_SUPPORTED_BY_CLIENT;
- blank End Reason Type;
- unsupported or malformed records.

## Eligible behavioral denominator

The initial eligible outcome denominator is:

`naturalCompletions + recordedForwardSkips + manualTrackChanges`

Excluded from that denominator:

- backward navigation;
- pause;
- suspension;
- scrub events;
- application exit;
- timeout;
- failed load;
- unsupported client;
- blank or unknown outcome.

The denominator may be revised only through a new contract version supported by source evidence.

## Prohibited skip calculation

The following calculation is prohibited:

`Skip Count / (Play Count + Skip Count)`

Reason:

Daily Play Count and Skip Count are not mutually exclusive. At least 18,718 daily rows contain both values.

Apple-reported daily Skip Count may be preserved for source reconciliation but is not the canonical numerator for behavioral skip rates.

## Skip reporting policy

Period-level factual reporting may state:

- recorded forward skip count;
- manual track-change count;
- natural completion count;
- eligible outcome count.

Example:

`8 recorded forward skips and 3 manual track changes occurred across 24 eligible outcomes.`

The product must not infer:

- dislike;
- dissatisfaction;
- rejection;
- negative taste;
- intent.

Entity-level skip rates and elevated-skip claims are deferred until identity attribution and comparison coverage are sufficient.

## Identity attribution tiers

### Tier A: exact identity

Requirements:

- normalized Song Name matches;
- normalized Album Name matches;
- the song-and-album pair resolves to exactly one artist.

Use:

- user-facing artist, album, and track counts;
- attributed behavioral counts;
- attributed coverage reporting.

Observed eligible-outcome coverage before normalization:

42.7%.

### Tier B: governed normalized album identity

Requirements:

- normalized Song Name matches;
- album mismatch is limited to controlled edition syntax such as:
  - deluxe edition;
  - expanded edition;
  - remaster;
  - anniversary edition;
  - bonus-track edition;
  - comparable governed edition labels;
- the normalized pair resolves to exactly one artist.

Use:

- user-facing attributed counts;
- explicit provenance describing the normalization.

Projected eligible-outcome coverage after conservative normalization:

46.5%.

### Tier C: title-only candidate

Requirements:

- title resolves to one artist in the current reference set;
- album identity is absent or does not match.

Use:

- internal investigation;
- unresolved-candidate reporting;
- future identity-governance work.

Tier C matches must not be promoted automatically to user-facing attribution.

### Tier D: ambiguous or unmatched

Includes:

- multiple artist candidates;
- no identity candidate;
- unsupported identity fields.

Use:

- period totals only;
- unresolved or ambiguous coverage counts.

## Attribution coverage

Any entity-level output must report:

- attributedEligibleOutcomeCount;
- totalEligibleOutcomeCount;
- attributedOutcomeCoverage;
- ambiguousOutcomeCount;
- unresolvedOutcomeCount;
- identityMethod counts.

Period-level totals must not be reduced to the attributed subset.

Entity-level counts must not imply full-history coverage when attribution is partial.

## Source coverage

Every queried source must report:

- source identifier;
- source type;
- requested start and end;
- available coverage start and end;
- matched record count;
- searched status;
- limitations;
- extraction or capture date when available.

A source whose coverage ends before the requested period must be reported as unavailable or unsupported for that portion of the period, not as zero listening.

## Static export limitation

The audited Apple exports are historical snapshots.

Observed latest dates:

- Play Activity: 2026-05-26;
- Daily Tracks: 2026-05-19.

The application must not imply that these sources cover later dates unless a newer export is installed and audited.

## Recent Apple Observations boundary

Recent Apple snapshots:

- are not Actual Plays;
- are not evidence of complete listening history;
- may contain repeated observations of the same Apple object;
- must expose snapshot and capture coverage when searched.

No scheduled capture infrastructure is required by this contract.

## Sprint 3 implementation boundary

In scope:

- date-range Actual Listening aggregation;
- plays and listening duration;
- behavioral outcome counts;
- eligible-outcome denominator;
- source coverage and provenance;
- high-confidence identity attribution;
- conservative album-edition normalization;
- unresolved and ambiguous attribution reporting;
- regression fixtures and API validation;
- structured Query Workbench rendering.

Out of scope:

- scheduled Apple snapshot capture;
- snapshot health monitoring;
- Recent Apple Observation integration;
- entity-level skip rates;
- elevated-skip baselines;
- dislike or preference inference;
- fuzzy title matching;
- broad album-family resolution;
- period-over-period interpretation;
- playback-context inference.

## Acceptance criteria

Sprint 3 is complete when:

1. Period Intelligence searches the relevant Actual Listening sources.
2. Actual plays and duration are returned for covered periods.
3. Natural completions, recorded forward skips, and manual track changes remain distinct.
4. The prohibited daily play-plus-skip denominator is not used.
5. Source coverage and export limitations are explicit.
6. Entity attribution uses only Tier A and Tier B matches.
7. Attribution coverage and unresolved counts are visible.
8. Zero activity, unavailable source, partial coverage, and unsearched source remain distinct.
9. Regression tests cover evidence, zero activity, partial coverage, invalid dates, outcome classification, and identity coverage.
10. Recent Apple snapshots and scheduling remain outside Sprint 3.
