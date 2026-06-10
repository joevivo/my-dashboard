# Music Query Workbench Sprint v0

Generated: 2026-06-10

## Sprint Goal

Create a safe, non-UI research workflow for targeted music queries across artists, songs, albums, time periods, and listening context.

The core question:

How do I find artists that matter across my listening life even when they do not dominate weekly or monthly top lists?

## Definition of Done

- Identify available music data sources.
- Confirm which fields are reliable.
- Create reusable artist lookup script.
- Test The Breeders, Billie Holiday, The Misfits, and Death Cab for Cutie.
- Preserve Michelle Shocked as a source-limited memory case.
- Do not touch JSX.
- Preserve sprint notes and next-session handoff.

## Completed Items

### Created scripts

- data/music/scripts/music_lookup.py
- data/music/scripts/music_scan.py
- data/music/scripts/music_artist_lookup.py

### Confirmed DuckDB limitation

DuckDB table:

- data/music/music.db
- apple_music_play_activity

Available DuckDB fields:

- album_name
- song_name
- event_timestamp
- event_start_timestamp
- play_duration_ms
- container_name
- container_type
- source_type
- shuffle_play
- repeat_play

Critical finding:

The DuckDB playback table does not include artist_name.

Therefore, DuckDB alone cannot power artist lookup.

### Confirmed artist source

Artist lookup should use:

C:/Users/joevi/apple-music-sanitized/apple-music-daily-track-summary.csv

Reliable fields:

- Date Played
- Track Description

Artist parsing pattern:

Artist - Track

## Calibration Results

### Death Cab for Cutie

- Matching events: 1219
- First seen: 2016-01-10
- Latest seen: 2026-05-18
- Years active: 11
- Shape: Peak plus steady return
- Read: Major companion

### The Breeders

- Matching events: 135
- First seen: 2017-10-01
- Latest seen: 2026-05-13
- Years active: 10
- Shape: Steady companion
- Read: Minor but meaningful

### Billie Holiday

- Matching events: 99
- First seen: 2016-02-24
- Latest seen: 2026-05-07
- Years active: 11
- Shape: Steady companion
- Read: Quiet long-term presence / recurring song-session companion

### The Misfits

- Matching events: 56
- First seen: 2016-03-24
- Latest seen: 2026-04-01
- Years active: 7
- Shape: Peak plus steady return
- Read: Early spike with durable residue

### Michelle Shocked

- Current data sources do not preserve the meaningful listening history.
- DuckDB did not find expected Michelle Shocked albums or songs.
- Artist CSV found only one clear Michelle Shocked event.
- Known user context: Short Sharp Shocked and Captain Swing were personal-library listens.
- Read: Personal-library-only / source-limited memory.

## Product Insight

Time Machine answers:

What was I listening to during this period?

Music Query Workbench answers:

Where does this artist, song, or album live across time?

Both are useful, but they answer different questions.

## Architecture Insight

Current best source split:

| Question | Best Current Source |
|---|---|
| Artist presence | apple-music-daily-track-summary.csv |
| Song presence by artist | apple-music-daily-track-summary.csv |
| Album/context lookup | DuckDB apple_music_play_activity |
| Playlist/album/radio context | DuckDB apple_music_play_activity |
| Durable artist + album + song identity | Future identity layer |

Future identity layer should eventually support:

- artist_name
- album_name
- song_name
- source
- confidence
- notes

## Working Vocabulary

- Major companion
- Minor but meaningful
- Quiet long-term presence
- Steady companion
- Peak plus steady return
- Spike-heavy companion
- Recurring song/session companion
- Source-limited memory
- Personal-library-only
- Needs Identity Resolution

## Parking Lot

Do not address yet:

- Music UI workbench
- JSX changes
- broad refactor
- permanent saved query UI
- charts
- crisis/job-transition mining
- personal-library reconstruction beyond explicit known cases

## Current Sprint Verdict

Successful research sprint.

The original assumption that DuckDB could power targeted artist search was corrected.

The better model is:

Artist lookup = sanitized daily track summary CSV
Album/context lookup = DuckDB
Identity resolution = future layer

The workbench concept is validated by The Breeders, Billie Holiday, and The Misfits.

## Next-Session Handoff

Suggested next sprint:

Music Query Workbench v1 - Alias Handling and Markdown Output

Recommended sprint goal:

Improve the artist lookup script so it can handle aliases, normalize names, and export a clean Markdown report for one or more artists.

Recommended Definition of Done:

- Add an alias file for known artist name variants.
- Normalize examples:
  - The Misfits / Misfits
  - Matt Pond PA / matt pond PA
  - Almamegretta / Almagretta
  - Anne-Sophie Mutter / Annie Sophie Mutter
- Add optional Markdown output.
- Run comparison report for:
  - The Breeders
  - Billie Holiday
  - The Misfits
  - Death Cab for Cutie
- Preserve Michelle Shocked as source-limited memory.
- Do not touch JSX.
