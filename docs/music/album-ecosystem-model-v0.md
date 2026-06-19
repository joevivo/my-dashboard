# Album Ecosystem Model v0

## Core Finding

Some album relationships derive a significant portion of their meaning from neighboring albums within the same artist catalog.

In these cases, the primary analytical entity is not the album alone but the album ecosystem.

This model emerged after Album Normalization Model v0 established that Canonical Album identity must precede Album Intelligence.

## Origin

This model emerged while investigating why R.E.M.'s *Document* felt more significant than its play count alone suggested.

Album normalization revealed that *Document* was part of a dense cluster of highly active R.E.M. albums including:

* Murmur
* Lifes Rich Pageant
* Fables of the Reconstruction
* Green
* Out of Time
* Automatic For The People

This led to the hypothesis that some album relationships are ecosystem relationships rather than isolated album relationships.

## Definition

An Album Ecosystem is a group of canonical albums that collectively carry a listener's relationship with an artist.

The ecosystem may be:

* Dense Catalog
* Primary-Anchor
* Concentrated Era
* Weak or Single-Anchor

Additional ecosystem types may emerge through future research.

## Why This Exists

Album play count alone does not explain relationship strength.

Example:

* *Norman Fucking Rockwell!* has high activity but may be more song-driven.
* *Document* feels stronger because it lives inside a dense R.E.M. album world.

The key question becomes:

> What role does an album play inside the listener's relationship with the artist?

## Observed Ecosystem Shapes

| Shape                           | Example       |
| ------------------------------- | ------------- |
| Dense Catalog Ecosystem         | R.E.M.        |
| Primary-Anchor Ecosystem        | Wilco         |
| Concentrated Era Ecosystem      | Peter Gabriel |
| Weak or Single-Anchor Ecosystem | Genesis       |

These categories are provisional and subject to revision as additional artists are analyzed. The Concentration Spectrum Model may eventually replace or simplify these type labels.

## Ecosystem Types

### Dense Catalog Ecosystem

A relationship distributed across many strong albums.

Example: R.E.M.

| Album                        | Canonical Events |
| ---------------------------- | ---------------: |
| Document                     |              433 |
| Out of Time                  |              306 |
| Green                        |              289 |
| Fables of the Reconstruction |              254 |
| Automatic For The People     |              248 |
| Lifes Rich Pageant           |              239 |
| Murmur                       |              234 |

#### Interpretation

R.E.M. is not carried by one album.

The relationship is distributed across a dense album world.

*Document* functions as a major node, but its meaning is reinforced by *Green*, *Lifes Rich Pageant*, *Murmur*, *Fables of the Reconstruction*, *Out of Time*, and *Automatic For The People*.


### Dense Catalog Ecosystem: matt pond PA

A second dense ecosystem candidate emerged from the archive-wide candidate report.

| Album | Library Track Play Count |
|---|---:|
| Emblems | 145 |
| Several Arrows Later | 83 |
| The Nature Of Maps | 79 |
| Green Fury | 78 |
| Last Light | 78 |
| Matt Pond's Youtube treasures | 62 |
| Skeletons and Friends | 55 |
| The Dark Leaves | 53 |
| Threeep | 48 |
| The Freeep | 43 |

#### Interpretation

matt pond PA appears to be a real dense album ecosystem.

The relationship is not carried by one album alone. *Emblems* is the leading album, but *Several Arrows Later*, *The Nature Of Maps*, *Green Fury*, *Last Light*, *Skeletons and Friends*, and *The Dark Leaves* all contribute meaningful weight.

This finding is important because matt pond PA was not one of the initial hand-selected ecosystem examples. The archive-wide candidate report surfaced it automatically.

This supports the value of ecosystem candidate discovery and suggests that dense catalog ecosystems can exist outside obvious classic-catalog artists like R.E.M.

Potential subtype:

Personal Catalog Ecosystem

A dense ecosystem formed through a listener's long-running relationship with a personally significant artist catalog rather than through broad canonical or critical reputation.


### Dense Catalog Ecosystem: The Replacements

The Replacements were surfaced by the archive-wide ecosystem candidate report rather than by manual selection.

After local canonical cleanup, their album distribution remained broad and balanced.

| Album | Library Track Play Count |
|---|---:|
| Stink | 48 |
| Let It Be | 45 |
| Pleased to Meet Me | 44 |
| All for Nothing | 29 |
| Sorry Ma, I Forgot to Take Out the Trash | 28 |
| Hootenanny | 20 |
| Tim | 18 |
| Don't Tell a Soul | 16 |
| All Shook Down | 9 |

#### Metrics

- Total: 277
- Anchor: 48
- Albums >= 50% anchor: 5
- Albums >= 25% anchor: 8
- Albums >= 10% anchor: 10

#### Interpretation

The Replacements appear to be a confirmed Dense Catalog Ecosystem.

The relationship is not explained by one dominant album. Activity is distributed across early, middle, and later catalog nodes including *Stink*, *Let It Be*, *Pleased to Meet Me*, *Sorry Ma*, *Hootenanny*, *Tim*, and *Don't Tell a Soul*.

This finding is important because the first candidate report suggested The Replacements might be an artifact of expanded editions and compilation noise. After local canonical cleanup, the dense shape remained.

This supports the idea that Dense Catalog Ecosystems can be discovered automatically and then validated through targeted canonical cleanup.

### Primary-Anchor Ecosystem

A relationship with one elevated album and several strong surrounding albums.

Example: Wilco.

| Album                | Canonical Events |
| -------------------- | ---------------: |
| Summerteeth          |              390 |
| Sky Blue Sky         |              273 |
| Yankee Hotel Foxtrot |              271 |
| Being There          |              207 |
| A Ghost Is Born      |              193 |
| A.M.                 |              152 |

#### Interpretation

Wilco has a clear primary anchor in *Summerteeth*.

However, the relationship is not isolated to that album.

*Sky Blue Sky*, *Yankee Hotel Foxtrot*, *Being There*, *A Ghost Is Born*, and *A.M.* form a surrounding ecosystem.

### Concentrated Era Ecosystem

A smaller ecosystem centered on a specific artistic period.

Example: Peter Gabriel.

| Album                                  | Canonical Events |
| -------------------------------------- | ---------------: |
| Peter Gabriel 3: Melt (Remastered)     |              143 |
| Plays Live                             |               70 |
| Peter Gabriel 4: Security (Remastered) |               59 |
| Peter Gabriel 1: Car (Remastered)      |               45 |
| Peter Gabriel 2: Scratch (Remastered)  |               28 |
| Plays Live (Highlights)                |               21 |

#### Interpretation

The Gabriel ecosystem appears concentrated around the Melt / Security / Plays Live era.

*Plays Live* should be treated as part of this artistic neighborhood rather than dismissed as merely a live album.

### Weak or Single-Anchor Ecosystem

A relationship dominated by one album with limited supporting structure.

Example: Genesis.

| Album                          | Canonical Events |
| ------------------------------ | ---------------: |
| The Lamb Lies Down On Broadway |              144 |
| Selling England By The Pound   |               59 |
| Duke                           |               31 |
| Abacab                         |               17 |
| A Trick Of The Tail            |               10 |
| Invisible Touch                |                4 |

#### Interpretation

Genesis currently appears closer to a single-anchor relationship than a dense ecosystem.

This suggests album ecosystems are not universal and may represent a specific type of artist relationship rather than a default property of all artists.

## Related Distinctions

### Album Footprint vs Album Relationship

Library track count measures album footprint, not relationship strength.

A Library Tracks report for Lana Del Rey showed album presence, but not necessarily album relationship depth.

Finding:

> Album footprint is not album relationship.

### Album Relationship vs Song Relationship

Some artists or albums may be carried primarily by individual songs rather than album-level attachment.

Examples under discussion:

* Lana Del Rey may currently appear more song-driven than album-driven.
* Dulcinea showed anchor-song behavior while also demonstrating meaningful album participation.
* The Queen Is Dead exposed limitations of the current event window and should not be overinterpreted from recent activity alone.

## Architectural Stack

Raw Apple Metadata
→ Album Normalization
→ Canonical Album
→ Album Entity
→ Album Ecosystem
→ Album Relationship
→ Album Intelligence


## Data Source Limitation

The current DuckDB music database contains only:

- apple_music_play_activity

This table is strong for behavioral analysis because it contains:

- album_name
- song_name
- event_timestamp
- play_duration_ms
- container_name
- source_type

However, it does not contain artist identity.

Consequence:

DuckDB play activity can support:

- album event counts
- album timelines
- album session reconstruction
- album traversal analysis
- canonical album normalization by album title

DuckDB play activity alone cannot support:

- archive-wide artist album ecosystem detection
- artist + canonical album entity construction
- top 25 album ecosystem candidate discovery
- reliable disambiguation of generic album titles

Automated Album Ecosystem detection requires an artist-album enrichment layer.

Likely enrichment source:

- Apple Music Library Tracks JSON

That source contains:

- Artist
- Album
- Album Artist
- Title
- Track Play Count
- Last Played Date

Future architecture should attach play-activity behavior to Album Entities using a joined or enriched identity layer.

Principle:

Identity first, behavior second.

Target model:

Apple Library Tracks
-> Artist + Album identity
-> Canonical Album Entity

Apple Play Activity
-> Album behavior
-> Session and traversal evidence

Joined Album Entity
-> Album Ecosystem detection
-> Album Relationship Modeling
-> Album Intelligence


## Candidate Discovery Report v0

A first archive-wide candidate report was generated from Apple Music Library Tracks JSON.

Important caveat:

This report uses Library Track Play Count grouped by Artist + Album. It is useful for candidate discovery, but it is not final play-activity truth.

### Major Discovery

The report successfully surfaced artists that had not been manually selected.

Strong candidates included:

- The Replacements
- R.E.M.
- matt pond PA
- Wilco
- Pearl Jam
- The Cure
- Hüsker Dü

### The Replacements Finding

The Replacements appeared as the strongest surprise candidate.

Metrics:

- Total: 235
- Top album: Pleased to Meet Me (Expanded Edition), 34
- Top album share: 14.5%
- Top two share: 28.1%
- Width >= 25% anchor: 10
- Evenness: 0.98

Interpretation:

The Replacements were later confirmed as a Dense Catalog Ecosystem after local canonical cleanup preserved the broad distribution.

### Report Limitation

The candidate report currently mixes:

- studio albums
- live albums
- expanded editions
- compilations
- greatest hits collections
- soundtrack albums
- disc-based artifacts

This means the report is useful for discovering candidates, but not yet sufficient for final ecosystem classification.

### Next Report Iteration

Candidate Report v2 should add a cleanup layer for compilation and edition artifacts.

Possible exclusion or review terms:

- greatest
- best of
- anthology
- chronicles
- hits
- disc 1
- disc 2
- soundtrack
- various artists
- collection
- singles

Live albums should not be automatically excluded because Peter Gabriel's Plays Live demonstrated that live albums can be legitimate ecosystem members.


## Ecosystem Shape Detection Rules v0

These rules are provisional. They are based on observed examples, not final thresholds.

### Core Metrics

#### Anchor Share

The percentage of ecosystem activity held by the top album.

Lower anchor share suggests a broader ecosystem.

#### Top Two Share

The percentage of ecosystem activity held by the top two albums.

High top-two share suggests a compact or anchor-heavy ecosystem.

#### Width >= 25% Anchor

The number of albums with activity at least 25% of the top album.

This is currently the most useful ecosystem-width signal.

#### Evenness

A normalized distribution score showing how evenly activity is distributed across albums.

Higher evenness suggests a denser ecosystem.

### Dense Catalog Ecosystem

Observed examples:

- R.E.M.
- matt pond PA
- The Replacements

Typical signals:

- Anchor share below 25%
- Width >= 25% anchor of 7 or more
- Evenness around 0.95 or higher
- Multiple albums contribute meaningful relationship weight

Interpretation:

The listener's relationship is distributed across a broad catalog rather than concentrated in one or two albums.

### Primary-Anchor Ecosystem

Observed example:

- Wilco

Typical signals:

- One clear leading album
- Several strong surrounding albums
- Width remains high
- Anchor share is elevated but not dominant

Interpretation:

One album has special gravity, but the relationship remains ecosystem-based.

### Compact Anchor Ecosystem

Observed example:

- Toad the Wet Sprocket

Typical signals:

- Anchor share around or above 50%
- Top two share high
- Smaller but meaningful supporting catalog
- One album may have strong internal depth

Interpretation:

The relationship is centered on one major album, but supporting albums still matter.

### Concentrated Era Ecosystem

Observed example:

- Peter Gabriel

Typical signals:

- Activity clusters around a specific artistic period
- Live albums may participate if they belong to that era
- Catalog breadth is limited but coherent

Interpretation:

The ecosystem is organized around an era rather than the artist's full catalog.

### Weak or Single-Anchor Ecosystem

Observed example:

- Genesis, based on current event-window evidence

Typical signals:

- One album dominates
- Low support from neighboring albums
- Low ecosystem width
- Lower evenness

Interpretation:

The artist relationship may be real, but album ecosystem evidence is weak or concentrated in one album.


## Concentration Spectrum Model v0

The first Relationship Concentration Report suggests that ecosystem shapes may not be discrete categories.

They may be positions along a concentration spectrum.

### Concentration Report Results

| Artist | Concentration | Anchor Share | Top Two Share | Width >= 25% Anchor | Evenness |
|---|---:|---:|---:|---:|---:|
| Genesis | 26.43 | 54.3% | 76.6% | 2 | 0.71 |
| Toad the Wet Sprocket | 24.71 | 55.4% | 77.2% | 2 | 0.83 |
| Peter Gabriel | 7.27 | 39.1% | 58.2% | 4 | 0.89 |
| Wilco | -7.60 | 26.2% | 44.6% | 6 | 0.97 |
| R.E.M. | -14.04 | 21.6% | 36.9% | 7 | 0.99 |
| matt pond PA | -15.53 | 22.9% | 36.0% | 8 | 0.97 |
| The Replacements | -16.26 | 19.4% | 37.5% | 8 | 0.96 |

### Interpretation

The ordering is meaningful.

Genesis and Toad appear highly concentrated: one album carries a large portion of the relationship.

Peter Gabriel sits in the middle: a clear anchor exists, but several albums participate meaningfully.

Wilco sits near the balanced side of the spectrum.

R.E.M., matt pond PA, and The Replacements appear low-concentration and broadly distributed.

### Model Implication

The current ecosystem types may eventually collapse into positions along a concentration spectrum rather than remaining fully separate categories.

Possible spectrum:

- High Concentration
  - Genesis
  - Toad the Wet Sprocket

- Medium Concentration
  - Peter Gabriel

- Balanced
  - Wilco

- Low Concentration / Dense Catalog
  - R.E.M.
  - matt pond PA
  - The Replacements

### Important Distinction

Concentration is not the same as depth.

Toad the Wet Sprocket is highly concentrated, but Dulcinea may still represent a deep album relationship.

This suggests at least two separate axes:

- Ecosystem Concentration
- Album Depth

Future Album Intelligence should avoid treating concentrated relationships as shallow relationships.

A concentrated artist ecosystem may still contain a deeply meaningful album.


## Album Depth Model Placeholder

The Concentration Spectrum findings suggest that ecosystem concentration and album depth are separate dimensions.

Examples:

- Toad the Wet Sprocket appears highly concentrated.
- Dulcinea may still represent a deep album relationship.
- R.E.M. appears low-concentration and broadly distributed.
- Document may represent both ecosystem participation and album depth.

Future work should determine how album depth can be measured independently of ecosystem concentration.

Possible depth signals:

- unique songs participating
- deep-cut participation
- album traversal behavior
- session reconstruction evidence
- returns after long gaps
- persistence across years

Status:

Research question for a future sprint.

## Open Questions

* How many ecosystem types exist?
* Can ecosystem shape be detected automatically?
* What thresholds separate Dense Catalog from Primary-Anchor ecosystems?
* What thresholds separate Primary-Anchor from Single-Anchor ecosystems?
* How should historic album relationships be represented when recent event data is incomplete?
* How should live albums participate in ecosystems?
* Can session reconstruction reveal album ecosystem behavior?
* Can ecosystem membership become a first-class analytical feature?
* How should future Apple Music live data enrich ecosystem detection?

## Current Status

Research model.

Do not integrate into GUI yet.

## Next Useful Work

* Test Toad the Wet Sprocket as a possible album-first ecosystem.
* Compare album ecosystem evidence with session reconstruction evidence.
* Develop ecosystem detection heuristics.
* Create ecosystem scoring metrics.
* Launch Apple Data Access Sprint v0.







