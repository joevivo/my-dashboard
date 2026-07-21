# Music Query Workbench Date Range Answer-First UI v1

## Status

Accepted product direction.

This specification governs the first answer-first redesign of the Query
Workbench Date Range result.

The redesign must use currently connected evidence. It must not add a new
evidence source.

## Product Promise

Select a period and understand:

- what listening occurred;
- what stood out;
- what the available evidence supports;
- how complete the answer is;
- what remains unknown.

The result must answer the listening question before exposing evidence-system
architecture.

## Golden Workflow

The initial golden workflow is:

> What happened in my listening during this period?

The answer should address, when supported:

1. How much confirmed listening occurred?
2. Which tracks or albums stood out?
3. Was listening broad or concentrated?
4. What playback behavior was visible?
5. Which evidence sources were searched?
6. What material evidence remains unavailable?

Artist identity must not be inferred from Actual Listening projection v1.

## Core Product Principle

> Answer first, findings second, confidence third, evidence on demand.

The primary result is an analytical answer, not a source-audit console.

## Primary Result Hierarchy

### 1. What Happened

Display one direct answer containing no more than three short sentences.

The answer should combine the most material supported facts:

- confirmed Actual Plays;
- listening duration;
- breadth across tracks and albums;
- meaningful concentration or lack of concentration;
- a material coverage limitation.

Example:

> You had 99 confirmed plays on April 19, totaling 4.6 hours. Listening
> covered 95 tracks across 90 albums, and no leading track exceeded two
> plays. Artist identity was unavailable for confirmed play events.

The answer must not claim more certainty than the evidence supports.

### 2. What Stood Out

Display no more than three concise findings.

Preferred finding families:

- listening volume and breadth;
- playback behavior;
- concentration, leaders, or ties.

Examples:

> 99 confirmed plays covered 95 tracks and 90 albums.

> 68 plays ended naturally; 22 were recorded forward skips.

> Four tracks tied for the lead with two confirmed plays each.

Qualitative terms such as `broad`, `focused`, or `concentrated` require an
explicit deterministic rule.

Findings must not merely repeat the primary answer.

### 3. Confidence and Coverage

Display one compact disclosure.

Example:

> **Confidence: Medium.** Actual Listening and Library Evidence were
> searched. Artist identity was unavailable for Actual Listening. Recent
> Apple Objects and Playback Context were not searched.

Do not display all source-coverage entries and warnings in the primary view.

### 4. Listening Detail

Place detailed listening metrics behind an expandable control:

> Show listening detail

The expanded section may contain:

- Actual Plays;
- recorded forward skips;
- listening duration;
- unique tracks and albums;
- playback outcomes;
- top tracks by Actual Plays;
- top albums by Actual Plays;
- the Actual Listening source note.

Empty rankings should not consume large visible areas.

### 5. Evidence and Sources

Place evidence-system detail behind a separate expandable control:

> Show evidence and sources

The expanded section may contain:

- Library Evidence;
- source-coverage entries;
- warnings;
- provenance;
- capture dates;
- schema version;
- implementation limitations;
- suggested investigations.

Raw diagnostic and response-contract terminology belongs here.

## Default-View Exclusions

Do not display these by default:

- repeated `Period Intelligence` headings;
- response schema version;
- four source-status cards;
- raw states such as `not_searched`;
- repeated versions of the same source limitation;
- zero-value investigation facts;
- empty ranking sections;
- provenance identifiers;
- implementation terminology unless necessary to explain a limitation.

## Required State Behavior

### Covered period with matching Actual Listening

The primary result must:

- lead with confirmed listening;
- show no more than three findings;
- disclose unavailable artist identity;
- disclose unsearched sources compactly;
- keep detailed metrics and coverage expandable.

### Covered period with zero matching evidence

The primary result must:

- state that supported sources were searched;
- state that no matching evidence was found;
- distinguish zero evidence from an unsearched source;
- avoid a large default panel of zero metrics;
- retain detailed zero metrics inside expandable detail.

### Period outside Actual Listening coverage

The primary result must:

- state that Actual Listening does not cover the selected period;
- never display unsupported Actual Listening metrics as zero;
- preserve independently available Library Evidence;
- show the supported Actual Listening date range once;
- avoid repeating the same coverage limitation.

### Actual Listening unavailable

The primary result must:

- distinguish an unavailable projection from a period outside coverage;
- present the operational limitation compactly;
- preserve independently available evidence.

## Status Presentation

Translate machine states for display:

- `searched_with_evidence` -> `Searched — evidence found`
- `searched_no_evidence` -> `Searched — no evidence found`
- `not_searched` -> `Not searched`
- `unavailable` -> `Unavailable`
- `stale` -> `Stale`
- `unsupported_for_period` -> `Outside coverage`

Raw values may remain inside diagnostic detail.

## Source Separation Rules

The redesign must preserve these distinctions:

- Actual Listening is confirmed play-event evidence.
- Library Evidence is Last Played Date reconstruction.
- Recent Apple Objects are observations, not confirmed play history.
- Playback Context identifies how playback was initiated when known.
- Zero evidence is not equivalent to an unsearched source.
- Outside coverage is not equivalent to zero evidence.
- An unavailable source is not equivalent to outside coverage.

## Recent Apple Integration Boundary

Recent Apple integration is deferred until the answer-first Date Range
experience is accepted.

When added, Recent Apple observations must improve the synthesized answer.
They must not appear merely as another independent source card.

A future mixed-source answer may say:

> Confirmed play history ends May 26. More recent Apple observations suggest
> renewed activity around Billie Holiday, but those objects are observations,
> not confirmed plays.

Snapshot automation remains optional and non-blocking.

## Scope of the First UI Sprint

Included:

- Date Range result hierarchy;
- direct answer presentation;
- up to three findings;
- compact confidence and coverage;
- expandable listening detail;
- expandable evidence and sources;
- human-readable status labels;
- covered-evidence, covered-zero, outside-coverage, and unavailable states.

Excluded:

- new evidence-source integration;
- Recent Apple integration;
- playback-context ingestion;
- snapshot automation;
- Artist-mode redesign;
- Song-mode redesign;
- broad navigation redesign;
- response-contract version changes unless proven necessary.

## Acceptance Criteria

The redesign is accepted when:

1. The first visible result answers what happened during the selected period.
2. The primary result contains no more than three findings.
3. Confidence and material limitations are understandable without source
   cards.
4. Detailed listening metrics remain available on demand.
5. Coverage, warnings, provenance, and schema remain available on demand.
6. Covered zero, outside coverage, unavailable, and not searched remain
   distinct.
7. Actual Listening and Library Evidence remain semantically separate.
8. Unsupported artist identity is not inferred.
9. The three accepted visual scenarios continue to pass.
10. The frontend build and live-response regression gates pass.
