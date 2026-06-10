# Listening Context Architecture

## Status

Research spike completed.

No production implementation has begun.

The purpose of this document is to define how behavioral listening data should integrate with the Music Time Machine experience without creating technical debt.

---

# Existing Architecture

## Biography Layer

Source:

Apple Music Library Tracks JSON

Current consumer:

library_range_summary.py

Provides:

* Artist Journeys
* Top Albums
* Top Tracks
* Historical Timelines
* Selected Range Snapshot
* Lifetime Journey

Answers:

"What was I listening to?"

This layer powers the current Artist Dossier.

---

# Behavioral Layer

Source:

DuckDB

Table:

apple_music_play_activity

Provides:

* album_name
* song_name
* container_type
* source_type
* shuffle_play
* repeat_play
* event_start_timestamp

Answers:

"How was I listening?"

Examples:

* Album vs Playlist vs Radio
* Sonos vs Originating Device
* Shuffle behavior
* Repeat behavior
* Listening intensity

---

# Important Discovery

DuckDB does not contain artist information.

Artist Dossier artists cannot be directly queried against DuckDB.

A mapping layer is required.

---

# Proposed Integration

Artist Dossier remains anchored to Library Tracks JSON.

Flow:

Artist Dossier
→ Top Albums
→ Top Tracks
→ Selected Date Range
→ DuckDB Behavioral Query

DuckDB is queried using:

* album_name
* song_name
* date range

Behavioral results are attached as a secondary context layer.

This avoids replacing the existing Time Machine engine.

---

# Example Future Dossier Section

Listening Context

Album Listening: 18%

Playlist Listening: 62%

Radio Listening: 20%

Primary Source:

Sonos

Behavior Read:

This artist was most commonly encountered through playlists and passive listening sessions rather than deliberate album playback.

---

# Companion Album Concept

A Companion Album is not necessarily a favorite album.

It is an album that repeatedly appears across long periods of life.

Example:

Ambient 1: Music for Airports

First Activity:
2015-07-06

Last Activity:
2026-02-15

Play Events:
889

Behavior:

Predominantly playlist-based listening.
Predominantly Sonos listening.

Interpretation:

Long-term companion album.

---

# Non-Goals

Do not:

* Replace Library Tracks JSON.
* Rebuild Time Machine on DuckDB.
* Add direct DuckDB queries inside React components.

All behavioral aggregation should occur before data reaches the UI.

---

# Development Rule

When modifying JSX:

Preferred:

1. Script patch
2. Full-file replacement
3. Single targeted edit

Avoid:

* multi-location manual JSX edits
* copy/paste surgery across several component sections

This project has repeatedly shown lower defect rates when modifications are applied programmatically and validated with npm run build.
