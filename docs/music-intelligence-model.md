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
