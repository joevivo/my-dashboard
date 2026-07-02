# Music Relationship Model v0

## What we learned

Music relationships are not just play counts. They have shape and context.

## Proven relationship types

| Type | Meaning | Examples |
|---|---|---|
| Core permanent artist companion | High-volume, multi-year, catalog-wide artist relationship | The Cure |
| Major artist-family companion | Related identities need rollup but should preserve sub-identities | Neil Young Family, Elvis Costello Family |
| Catalog companion | Many songs, low top-track share | The Feelies, Dire Straits |
| Single-song companion | One song carries most of the relationship | Haircut 100 / Love Plus One |
| Album-rooted companion | Multiple songs from one album-world recur across contexts | The Church / Starfish |
| Source-limited memory | Meaningful artist not visible in current data | Michelle Shocked |

## Data limitations

- Playlist names are not available in DuckDB.
- Playlist-carried listening is visible, but playlist identity is not.
- Album probes by title alone can be ambiguous.
- Artist and album context still live in different data surfaces.

## Normalization Lessons

Music identity is often fragmented by metadata.

Validated examples:

- Hüsker Dü vs Husker Du
- Björk vs Bjork
- Sinéad O'Connor vs Sinead O'Connor
- Love & Rockets vs Love and Rockets
- The Pixies vs Pixies

Future work:

- Artist normalization
- Album normalization
- Album family rollups
- Canonical identity keys

## UNKNOWN Container Findings

UNKNOWN is not necessarily a distinct listening behavior.

Evidence:

Document session (2026-01-21) showed:

ALBUM → UNKNOWN → ALBUM

for the same song (Lightnin' Hopkins) during the same listening session.

Current hypothesis:

UNKNOWN reflects Apple metadata limitations rather than a separate listening intent.

Status:

Research ongoing.
## Album Relationship Model v0
## Next Sprint Options

### Option A — Album Intelligence

- Build album-session reconstruction script
- Album Immersion Score
- Album relationship classification

### Option B — UNKNOWN Research

- Reconstruct additional UNKNOWN-heavy sessions
- Compare ALBUM vs UNKNOWN behavior
- Quantify metadata anomalies

### Option C — Normalization Layer

- Centralize normalize_text()
- Artist aliases
- Album title normalization
- Canonical album keys

### Option D — Live Data Foundation

- Begin Apple Developer API research
- Design historical + live listening architecture
- Define fresh-data ingestion strategy
