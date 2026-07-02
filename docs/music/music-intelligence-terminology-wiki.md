# Music Intelligence Terminology Wiki

## Purpose

This document defines the canonical vocabulary used by Defending Sisyphus Music Intelligence.

Concepts are grouped into:

* Proven Concepts
* Emerging Concepts
* Future Concepts

Only Proven Concepts should drive classification logic without additional validation.

---

# Proven Concepts

## Permanent Companion

An artist with substantial evidence across many years and many listening contexts, indicating a durable long-term relationship rather than a temporary phase.

### Signals

* High years represented
* Broad catalog footprint
* Multi-album evidence
* Persistent recurrence

### Examples

* R.E.M.
* Wilco
* The Beatles
* Pearl Jam

---

## Hidden Pillar

An artist whose influence on the listening archive is larger than expected relative to perceived importance.

### Signals

* High persistence
* Meaningful listening volume
* Frequently omitted from conscious favorite-artist lists

---

## Quiet Persistence

An artist that appears consistently over many years without generating large listening peaks.

### Signals

* Long time span
* Low annual volume
* Frequent recurrence

### Examples

* Billie Holiday
* Sam Cooke

---

## Established Companion

A meaningful long-term artist relationship that has not yet reached Permanent Companion strength.

---

## Catalog Relationship

Evidence spans many albums and songs.

The relationship is with the artist's body of work rather than a single album or track.

---

## Album-Centered Relationship

A relationship concentrated around one album or a small number of albums.

---

## Song-Centered Relationship

A relationship largely carried by one or a few songs.

---

## Playlist Ritual Song

A song repeatedly appearing in intentional playlists and recurring listening contexts.

The song functions as a personal ritual object.

### Examples

* The Letter
* Hungry For You

---

## Playlist-Carried Song

A song whose listening identity is primarily driven by playlists.

---

## Album-Carried Song

A song whose listening identity is primarily driven by album listening.

---

## Identity Marker

A song strongly associated with a specific artist, album, or listening world.

### Examples

* R.E.M. — Radio Free Europe
* Sinéad O'Connor — Mandinka

---

## Context-Lost Marker

A song exists in the archive but lacks sufficient contextual evidence for strong interpretation.

---

## Context Share

Distribution of listening activity by source context.

### Current Context Types

| Context  | Meaning                 |
| -------- | ----------------------- |
| PLAYLIST | Playlist listening      |
| ALBUM    | Album listening         |
| RADIO    | Radio/station listening |
| UNKNOWN  | Context unavailable     |
| BLANK    | Context unavailable     |
| ARTIST   | Artist-based playback   |

---

## Missing Context Share

Percentage of events lacking meaningful listening context.

### Formula

(UNKNOWN + BLANK) / TOTAL

---

## Context Confidence

Confidence assigned to context-derived intelligence.

Context Confidence reflects completeness of listening-context evidence, not artist importance.

---

# Emerging Concepts

## Identity Artist

Artist whose relationship is disproportionately represented by a small number of defining works.

---

## Context Artist

Artist whose significance derives from repeated appearance across many playlist worlds and listening environments.

---

## Album Gateway

An album or song that acts as the primary entry point into a broader artist relationship.

---

## Source-Limited Memory

Artist or song with meaningful evidence that is constrained by archive limitations.

---

# Future Concepts

## Returning Artist

Artist that reappears after a significant absence period.

---

## Artist Momentum

Rate at which an artist's presence is increasing or decreasing.

---

## Relationship Drift

Long-term movement in artist importance over time.

---

## Active Listening Layer

Live listening intelligence derived from current listening behavior rather than historical exports.

# New Entries To Add

## Album Traversal

Definition:

An album listening session where tracks are consumed primarily in album order.

Characteristics:

* Consecutive tracks
* Strong album sequencing
* Few interruptions

Examples:

* The Beatles — The White Album
* R.E.M. — Green
* R.E.M. — Document

---

## Album Traversal With Interruption

Definition:

An album traversal session interrupted by pauses, skips, or real-world interruptions before resuming.

Characteristics:

* Album order preserved
* Session continuity maintained
* Temporary break in listening

Examples:

* R.E.M. — Green

---

## Album-Contained Session

Definition:

A listening session dominated by tracks from a single album without requiring album-order playback.

Characteristics:

* Strong album identity
* Non-linear listening
* Limited outside material

Examples:

* Wilco — A Ghost Is Born

---

## Companion Album Session

Definition:

A session where a listener repeatedly returns to an album, navigates within it, and spends extended time with it.

Characteristics:

* Multiple returns
* Restart behavior
* Deep engagement

Examples:

* Lana Del Rey — Norman Fucking Rockwell!

---

## Album Scan Session

Definition:

A session characterized by rapid skipping, previewing, or sampling of an album rather than sustained listening.

Characteristics:

* Many tracks
* Short durations
* Exploratory behavior

Examples:

* Whiskeytown — Pneumonia

---

## Practice Session

Definition:

Repeated playback of the same song or section of a song for focused attention, learning, or performance practice.

Characteristics:

* Frequent restarts
* Partial plays
* Repetition

Examples:

* Wilco — How to Fight Loneliness

---

## Source-Limited Album

Definition:

An album believed to be meaningful but weakly represented or absent in available listening data.

Characteristics:

* Strong remembered importance
* Minimal supporting evidence
* Potential archive limitations

Examples:

* The Feelies — Only Life

---

## Album Title Normalization

Definition:

The process of consolidating alternate releases and metadata variants into a canonical album identity.

Examples:

* Crazy Rhythms
* Crazy Rhythms (Bonus Track Version)

Future Goal:

Canonical album keys and album family rollups.

---

## UNKNOWN Container Type

Definition:

An Apple activity-data container classification whose listening intent is not fully understood.

Current Findings:

* UNKNOWN can appear inside album listening sessions.
* ALBUM → UNKNOWN → ALBUM transitions have been observed for the same song in the same session.
* UNKNOWN is currently believed to reflect Apple metadata behavior rather than a distinct listening mode.
