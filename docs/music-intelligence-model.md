# Music Intelligence Model

Date: 2026-06-05

## Purpose

The Music section of Defending Sisyphus is not intended to be a streaming analytics dashboard.

Its purpose is to help identify enduring patterns, changes, and relationships within a lifetime of listening.

The goal is not to answer:

* How many songs were played?
* How many minutes were streamed?

The goal is to answer:

* What never left?
* What changed?
* What belongs together?

Music data should reveal patterns first.

Meaning should emerge from those patterns.

The system should avoid imposing narratives before evidence exists.

---

# Core Principle

Bad model:

Life Event → Music

Examples:

* Surgery Era
* Marathon Era
* New Job Era

This approach forces a narrative onto listening behavior.

Preferred model:

Listening Data → Patterns → Interpretation

The music should define the story.

The story should not define the music.

---

# Music Domains

## Library

The curated collection.

Represents intentional choices made by the user.

Examples:

* Artists
* Albums
* Shows
* Playlists
* Notes

The Library is user-authored.

It represents what is important enough to preserve regardless of listening statistics.

---

## Listening History

The factual record of listening activity.

Examples:

* Artist
* Album
* Song
* Play count
* Listen date
* Listening period
* Added to playlist
* Songs favorited

Listening History is evidence.

It should contain minimal interpretation.

---
## Evidence Layers

Music Intelligence operates on multiple evidence layers.

### Play Activity

Event-level listening history.

Used for:
- Total Plays
- Listening Days
- Companion Analysis
- Persistence Analysis

### Library Evidence

Derived from Apple Music Library Tracks exports.

Used for:
- Artist Presence
- Album Presence
- Years Active
- Long-term relationship reconstruction

Library Evidence is not equivalent to Total Plays.

Different evidence layers may produce different measurements for the same artist.

## Constants

Question:

What never leaves?

Constants identify artists, albums, or works that repeatedly appear across years of listening.

Examples:

* Artists present in every year of available history
* Longest-running favorites
* Most persistent listening relationships

A Constant is not necessarily the most-played artist.

A Constant is something that survives across time.

---

## Changes

Question:

What changed?

Changes identify meaningful shifts in listening behavior.

Examples:

* New artist discoveries
* Genre expansions
* Artist abandonment
* Artist rediscovery
* Listening habit shifts

Changes are often more interesting than popularity rankings because they reveal movement rather than volume.

---

## Constellations

Question:

What belongs together?

Constellations are recurring clusters of artists, albums, songs, or ideas.

Examples:

* College Radio
* Power Pop
* Chicago Punk
* Country Roads
* Saturday Night Fever

Constellations are not eras.

Constellations are not playlists.

Constellations are thematic relationships that may appear repeatedly across many years.

A constellation may span decades.

A Constellation is a user-defined collection of related music objects and ideas. Constellations may include artists, albums, songs, playlists, shows, and notes. Constellations are primarily personal constructs rather than industry-defined genres.

---

# Explicit Non-Goals

The system is not intended to become:

* A streaming statistics dashboard
* A leaderboard of play counts
* A life-event tagging system
* A replacement for Apple Music

The project should focus on understanding listening behavior rather than measuring consumption.

---

# Apple Music Integration

Apple Music exports should be treated as the primary source of listening history.

Imported data should support:

* Persistence analysis
* Change analysis
* Constellation discovery
* Listening pattern analysis

The import pipeline should prioritize normalized and sanitized datasets.

---

# Privacy Requirements

The Music system must never expose or display the following fields:

* Apple ID Number
* Client IP Address
* Device Identifier
* IP City
* IP Latitude
* IP Longitude
* IP Network
* Device details
* Subscription identifiers

Only sanitized and aggregated listening information belongs within Defending Sisyphus. As new items are introduced, we need to take care to review their impact on the privacy requirements.

---

# Future Questions

The following questions should guide future development:

## Constants

* Which artists never leave?
* Which albums survive multiple decades?
* Which artists appear in every listening period?

## Changes

* What surprised me?
* What disappeared?
* What returned unexpectedly?

## Constellations

* Which artists frequently appear together?
* Which themes repeatedly emerge?
* Which collections define my listening identity?

Every future Music feature should make at least one of these questions easier to answer.
# Pattern Definitions

## Constant

A Constant is an artist, album, or work that persists across time.

Constants are measured primarily through recurrence and longevity rather than listening volume.

Persistence is more important than popularity.

A Constant may never be the most-played artist in a given year.

A Constant repeatedly returns over many years of listening.

A Constant does not require continuous presence.

Repeated return over long periods of time is a stronger signal than uninterrupted listening.

### Constant Scores

Constant Scores are intended to measure how closely an artist, album, or work resembles an ideal Constant.

The score should not be a ranking against other artists in the library.

Instead, the score should represent proximity to the characteristics of a true Constant.

Potential characteristics include:

- Persistence
- Recurrence
- Longevity
- Engagement
- Recency

The goal is to create a meaningful measurement rather than a relative ranking.

A higher Constant Score indicates a stronger long-term listening relationship.

Historical Constant Scores and Active Constant Scores may be calculated separately.

Historical scores measure the long-term strength of a listening relationship.

Active scores measure the current strength of a listening relationship and may decay when an artist stops returning.

Example:

Artist A appears in listening history every year for a decade.

This is a stronger Constant than an artist that dominates a single year and disappears.
Library Footprint

Definition:

A measure of surviving artist evidence reconstructed from Apple Music Library Tracks. Useful for relationship persistence and archive presence. Not equivalent to listening volume.

Years Represented

Definition:

Number of years in which surviving evidence exists for an artist within Library Tracks reconstruction.

Library Evidence

Definition:

Reconstructed archival evidence derived from Apple Music Library Tracks. Best used for persistence, artist discovery, album survival, and relationship archaeology.

Library Footprint

Definition:

Count of surviving Library Tracks evidence associated with an artist.

Library Footprint is useful for understanding archive presence and
relationship persistence.

Library Footprint is not equivalent to listening volume.
Years Represented

Definition:

Number of years in which Library Evidence exists for an artist.

Useful for identifying persistent relationships and long-running
companions.

And I'd add one sentence that Brian Eno has now earned permanently:

Brian Eno serves as the canonical example demonstrating why
Play Activity and Library Evidence must remain separate systems.

---

## Importance Scale

The Music Intelligence model now separates evidence from importance.

### 1 ? Like

The artist is enjoyable or familiar but does not strongly define the listener's musical identity.

### 2 ? Fan

The artist is liked and recognizable as part of the listener's taste, but not central.

### 3 ? Important

The artist matters and helps explain part of the listener's musical world.

### 4 ? Essential

The artist is a major part of the listener's musical identity or worldview.

### 5 ? Constitutional

The artist helps explain how the listener understands music itself.

Constitutional artists are not necessarily the most played artists and may not have the largest Library Footprint. They are artists whose work shaped the listener's musical values.

Current strongest examples:

- R.E.M.
- The Beatles
- Peter Gabriel

Related examples under consideration:

- Billie Holiday
- Brian Eno
- King Crimson
- Sam Cooke

---

## Evidence Systems

Music Intelligence uses multiple evidence systems. These systems must not be collapsed into one another.

### Play Activity

Source: `apple_music_play_activity`

Best for answering:

- How much did I listen?
- What dominated my listening?
- What albums or artists had major listening volume?
- What persisted through actual play behavior?

Play Activity is the authoritative source for listening volume.

### Library Evidence

Source: `Apple Music Library Tracks`

Best for answering:

- What survived in the library?
- What artists and albums remain represented?
- Which relationships persisted across years?
- Which albums form the surviving archive footprint?

Library Evidence is useful for artist archaeology, persistence, and relationship reconstruction.

Library Evidence is not complete listening volume.

### Library Footprint

Library Footprint is the count of surviving Library Tracks evidence associated with an artist.

It should not be interpreted as Total Plays.

Brian Eno is the canonical example: Library Evidence may understate an artist with very high actual listening volume.

### Years Represented

Years Represented is the number of years in which Library Evidence exists for an artist.

This is useful for identifying persistence, but it is not the same as total listening activity.

## Foundational Texts (Experimental)

Some works function as teaching texts rather than favorite albums.

These works help explain how the listener believes music should be approached.

Current examples:

- Fugazi — 13 Songs
- George Winston — December
- Brian Eno — Music for Airports

Observed themes:

- Integrity
- Attention
- Expanded listening