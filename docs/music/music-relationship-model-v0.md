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

## Next sprint options

1. Clean artist group aliases.
2. Build album-centered detection.
3. Plan playlist allocation strategy.
4. Run more retrospective batches.