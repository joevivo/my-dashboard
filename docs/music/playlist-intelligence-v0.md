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
    "let's go streaking!"
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


---

# Playlist Scoring and Relationship Shapes

These concepts were harvested from the duplicate playlist model draft and are retained as draft requirements for future validation.

## Playlist Types

### Intentional Playlists

Playlists created or maintained by the user.

Examples:

* conversation fear
* deck & chill
* aquarium drinker
* songs of the apocalypse
* road trip
* Tom Petty

Intentional playlists are the primary evidence source for playlist intelligence.

### Generated Playlists

Algorithmically generated playlists.

Examples:

* Indie Rock Genius Mix
* Americana Genius Mix
* Classic R&B Genius Mix

Generated playlists may be retained as supporting evidence but should be excluded from primary playlist scoring unless explicitly marked otherwise.

---

## Draft Playlist Metrics

### Intentional Playlist Count

Number of non-generated playlists containing the artist.

### Generated Playlist Count

Number of generated playlists containing the artist.

### Track Links

Total artist-song appearances across intentional playlists.

### Density

Track Links divided by Intentional Playlist Count.

Density measures average playlist saturation.

### World Score

Largest Playlist Count divided by Track Links.

World Score measures concentration within a single playlist world.

Interpretation:

* High World Score = dominant artist world.
* Low World Score = distributed playlist presence.

---

## Draft Playlist Relationship Shapes

These classifications are provisional. They should not drive production UI classifications until formulas, thresholds, and confidence rules are documented.

### Sparse Curated Presence

Characteristics:

* Very few intentional playlist appearances.

Example:

* Billie Holiday

Observation:

Artist relationship is visible primarily through listening history rather than playlist construction.

### Dedicated World Artist

Characteristics:

* One dominant playlist world.
* High World Score.
* Large artist-specific playlist.

Example:

* Tom Petty

Observation:

The user maintains a dedicated artist universe.

### World + Context Artist

Characteristics:

* Dominant playlist world.
* Additional deployment across many contexts.

Example:

* Wilco

Observation:

Artist functions both as a dedicated world and as a recurring life companion.

### Distributed Identity Artist

Characteristics:

* Appears across many playlists.
* No dominant world.

Example:

* The Replacements

Observation:

Artist participates in self-expression and identity formation.

### Context Artist

Characteristics:

* Appears across many contextual playlists.
* No dominant world.

Example:

* Sam Cooke

Observation:

Artist helps define environments rather than identities.

Status:

Requires additional validation and refinement.

---

## Future Artist Intelligence Integration

Potential Artist Intelligence playlist section:

* Playlist classification.
* Intentional Playlist Count.
* Track Links.
* Density.
* World Score.
* Largest Playlist.
* Top Playlists.

Example:

Playlist Intelligence example:

Classification: World + Context Artist
Intentional Playlists: 18
Track Links: 70
Largest Playlist: aquarium drinker (41)
Top Playlists: aquarium drinker, 500 songs, road trip, Favorite Songs

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
