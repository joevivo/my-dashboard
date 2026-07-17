# Music Period Intelligence Requirements v1

## Status

Draft requirements lock for Music Sprint 1.

This document records the confirmed gap between the current Period Intelligence
implementation and the intended Query Workbench evidence and investigation model.

## Purpose

Period Intelligence must explain what happened during a selected period, which
evidence supports that answer, which sources were searched, and what remains
unknown.

It must not collapse library evidence, actual plays, live Apple observations,
playback context, or missing source coverage into one undifferentiated result.

## Current State

The current `/api/music/time-machine` implementation:

- accepts a start date and end date;
- searches Apple Music Library Tracks `Last Played Date`;
- returns matched library-track records;
- returns top artists and albums;
- returns artist journeys and a memory read;
- labels the source as a Last Played Date reconstruction.

The current implementation does not search or report:

- Apple Music daily track-summary actual plays;
- actual skips;
- listening duration;
- recent Apple objects;
- heavy rotation signals;
- playlist or station identity;
- album, radio, autoplay, search, or recommendation context;
- evidence-source coverage;
- unavailable or unsearched sources;
- confidence;
- provenance records;
- investigation facts, insights, open questions, or suggested investigations.

## Canonical Evidence Types

### Actual Plays

Confirmed play activity from Apple Music daily track-summary evidence.

Actual plays must not be inferred from library records or live Apple objects.

### Actual Skips

Skip activity from Apple Music daily track-summary evidence.

Skip definitions and source limitations must remain visible.

### Library Evidence

Records from Apple Music Library Tracks.

Library evidence may indicate library presence or a reconstructed last-played
observation. It is not total play count.

### Recent Apple Objects

Timestamped objects captured from current Apple Music endpoints, including
recently played, heavy rotation, playlists, stations, albums, or other available
object classes.

Recent objects indicate current observation, not complete play history.

### Playback Context

The source or surface associated with a play or observation, where available.

Supported contexts should include:

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

A context must be labeled unknown when the source does not establish it.

## Required Period Identity

Every period response must include:

- requested start date;
- requested end date;
- timezone;
- generated timestamp;
- earliest evidence timestamp found;
- latest evidence timestamp found;
- source freshness;
- whether the period is complete, partial, or unsupported by each source.

## Required Evidence Coverage

The response must report each relevant source with one of these statuses:

- searched_with_evidence;
- searched_no_evidence;
- not_searched;
- unavailable;
- stale;
- unsupported_for_period.

Each source entry must include:

- source identifier;
- evidence type;
- status;
- record count;
- earliest timestamp;
- latest timestamp;
- freshness timestamp;
- limitation note.

The system must distinguish:

1. no evidence exists;
2. a source was searched and returned no evidence;
3. a potentially relevant source was not searched;
4. a source was unavailable;
5. a source cannot support the requested historical period.

## Required Listening Content

Where supported by evidence, a period response must include:

- actual play count;
- actual skip count;
- listening duration;
- unique tracks;
- unique artists;
- unique albums;
- library evidence records;
- recent Apple objects;
- top tracks;
- top artists;
- top albums;
- repeated tracks;
- repeated artists;
- repeated albums.

Every count must identify its evidence type.

## Required Period Tags

A period should be tagged with available descriptive context, including:

- artists present;
- albums present;
- tracks present;
- dominant artist;
- dominant album;
- dominant track;
- playlist names;
- radio station names;
- album-listening context;
- discovery or recommendation context;
- concentration versus exploration;
- returning versus newly observed artists;
- catalog-depth versus isolated-track behavior;
- unknown or incomplete context.

Tags must be evidence-backed and carry provenance.

## Required Playback Context Output

Where available, the response must identify:

- context type;
- context name;
- context identifier;
- associated artist, album, or track;
- observation or play count;
- evidence source;
- timestamp range;
- confidence.

Aggregate shares may be displayed only when their denominator and source are
explicit.

For example, `radioShare` must state what records were classified and whether
they represent actual plays, reconstructed events, or context rows.

## Required Investigation Model

Period Intelligence should follow the same conceptual sequence as other Query
Workbench investigations:

Identity -> Evidence -> Facts -> Insights -> Next Investigations

The period investigation should contain:

- question;
- entity;
- identity;
- evidence;
- facts;
- hypotheses;
- insights;
- confidence;
- reasoning trace;
- open questions;
- suggested investigations.

The period itself is the investigated entity.

## Required Zero-State Behavior

A zero result must explain evidence coverage rather than imply that no listening
occurred.

Acceptable example:

> No reconstructed library-track play evidence was found for this period.
> Recent Apple observations and daily play activity were not searched.

When sources were searched:

> No actual-play or reconstructed library-track evidence was found for this
> period. Recent Apple observations are unavailable for dates before their
> capture history begins.

The response must not use a generic message such as:

> No library-track evidence found.

without explaining other source coverage.

## Required UI Structure

The Period Intelligence result should present:

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

The UI must label evidence according to its actual meaning.

`Tracks Matched` should not be shown without an evidence qualifier such as
`Library Evidence Records Matched`.

`Time Machine` should not be the only visible source description.

## Required Cross-Surface Behavior

Dashboard signals should be able to open a preconfigured period or artist
investigation in the Query Workbench.

Period results should link to:

- artist investigations;
- album investigations when supported;
- song investigations;
- playlist investigations;
- related time periods.

The Artist Profile may summarize period findings but must not replace the
Workbench evidence and reasoning surface.

## API Contract Direction

A future period response should separate evidence families rather than flatten
them.

Illustrative top-level structure:

```json
{
  "period": {},
  "coverage": {},
  "actualActivity": {},
  "libraryEvidence": {},
  "recentAppleObservations": {},
  "playbackContexts": [],
  "artists": [],
  "albums": [],
  "tracks": [],
  "tags": [],
  "investigation": {},
  "warnings": []
}
```

This is an architectural direction, not yet a frozen field-level schema.

## Semantic Corrections

The Music domain should distinguish:

- active year count;
- relationship span in years;
- evidence-source classification;
- relationship classification;
- investigation conclusion.

Fields such as `yearsActive` and `classification` must not carry multiple
meanings.

## Non-Goals

This requirements version does not require:

- treating recent Apple objects as confirmed plays;
- fabricating playback context when Apple does not provide it;
- reconstructing a complete historical event stream from Library Tracks;
- producing unsupported emotional or relationship conclusions;
- redesigning all Music surfaces in the same implementation sprint.

## Acceptance Criteria

Period Intelligence v1 is acceptable when:

- evidence families remain distinct;
- all searched and unsearched sources are disclosed;
- actual plays and library records cannot be confused;
- playback contexts are shown when available;
- the period is tagged with evidence-backed artists, albums, tracks, and sources;
- zero states explain coverage;
- provenance and confidence are visible;
- the response follows the investigation model;
- Dashboard signals can lead into a relevant Workbench investigation;
- regression fixtures cover evidence, zero-result, partial-coverage, and
  unavailable-source scenarios.

## Dependencies

- Apple daily track-summary historical data;
- Apple snapshot warehouse history;
- source registry and provenance model;
- canonical artist, album, song, playlist, and station identity;
- investigation packet support for period entities;
- agreed playback-context classification rules.

## Risks

- overstating live observations as plays;
- presenting reconstructed records as complete history;
- misclassifying playlist or radio context;
- allowing UI labels to obscure evidence semantics;
- duplicating investigation logic in React rather than backend contracts;
- redesigning the UI before the period response contract is stable.
