# Playlist Intelligence v0

## Purpose

Playlist Intelligence exists to understand playlists as first-class musical artifacts rather than simple song containers.

The goal is not to identify favorite songs or favorite artists.

The goal is to understand why playlists exist, how they differ, and what role they play within a listening life.

---

# Core Concepts

## Playlist

A curated collection of songs intended to serve a particular purpose.

Examples:

* 500 Songs
* deck & chill
* let's go streaking!

### Data Model

```json
{
  "name": "500 Songs",
  "songCount": 453,
  "artistCount": 219,
  "albumCount": 397,
  "totalPlays": 3948
}
```

---

## Shared Core Artist

An artist appearing across multiple major playlists.

These artists may reveal foundational musical relationships that transcend playlist purpose.

Examples:

* Tom Petty & The Heartbreakers
* Sam Cooke
* Fleetwood Mac
* Talk Talk

### Data Model

```json
{
  "artist": "Tom Petty & The Heartbreakers",
  "playlists": [
    "500 Songs",
    "deck & chill",
    "let’s go streaking!"
  ]
}
```

---

## Bridge Song

A song appearing in multiple playlists.

Bridge songs connect playlist worlds and may reveal recurring themes, moods, or identities.

Examples:

* Breakdown
* Finally Moving
* Belong
* Gouge Away

### Data Model

```json
{
  "artist": "Pretty Lights",
  "song": "Finally Moving",
  "playlists": [
    "500 Songs",
    "deck & chill"
  ]
}
```

---

## Playlist Signature

A song that helps explain the character of a playlist.

A signature song is not necessarily:

* the most played
* the most popular
* the most famous

A signature song is representative.

### Data Model

```json
{
  "playlist": "deck & chill",
  "artist": "Lana Del Rey",
  "song": "High By the Beach",
  "reason": "Representative of playlist character"
}
```

Selection criteria remain an open research topic.

---

## Playlist DNA

Objective characteristics describing a playlist.

Playlist DNA should be evidence-based rather than interpretive.

Examples:

* artist diversity
* album diversity
* replay profile
* unique artist count
* shared artist count

### Data Model

```json
{
  "playlist": "deck & chill",
  "artistDiversity": 265,
  "albumDiversity": 286,
  "uniqueArtistCount": 216,
  "sharedArtistCount": 49
}
```

---

# Playlist Intelligence Page v0

## Section 1: Playlist Overview

Displays:

* Playlist Name
* Song Count
* Artist Count
* Album Count
* Total Plays

Purpose:

Provide a high-level view of the playlist ecosystem.

---

## Section 2: Shared Core Artists

Displays artists appearing across multiple major playlists.

Purpose:

Identify foundational artist relationships.

---

## Section 3: Bridge Songs

Displays songs appearing across multiple major playlists.

Purpose:

Identify recurring musical touchstones.

---

## Section 4: Playlist Signatures

Displays representative songs for each playlist.

Purpose:

Explain playlist character.

---

## Section 5: Playlist DNA

Displays objective playlist metrics.

Purpose:

Describe playlist behavior using evidence rather than interpretation.

---

# Future Research Areas

The following remain open questions:

* Playlist archetypes
* Playlist purpose classification
* Playlist evolution over time
* Admission committee analysis
* Near-miss recommendations
* Playlist overlap scoring
* Structural artists vs bridge artists

These concepts require additional evidence before inclusion in the primary intelligence model.

```
```
