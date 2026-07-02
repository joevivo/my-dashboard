# Album Normalization Model v0

## Core Finding

Raw Apple album names are not stable analytical entities.

Album Intelligence must use Canonical Album identity before ranking, relationship scoring, companion album detection, or session reconstruction.

## Evidence

Album normalization audit found:

- Raw album titles: 17,392
- Canonical candidates: 16,687
- Reduction: 705
- Reduction percent: 4.05%
- Canonical groups with variants: 595
- Events affected: 26,203

The modest title reduction is misleading. The affected events include many major relationship albums.

## Key Examples

### Green

- Green: 11
- Green (Remastered): 32
- Green (Remastered 2013): 120
- Green (25th Anniversary Deluxe Edition): 126
- Canonical total: 289

### Document

- Document: 292
- Document (25th Anniversary Edition): 141
- Canonical total: 433

### Abbey Road

- Abbey Road: 78
- Abbey Road (Remastered): 61
- Abbey Road (2019 Mix): 110
- Abbey Road (Super Deluxe Edition): 73
- Canonical total: 322

## Companion Album Impact

Albums entering the Top 100 only after canonical normalization:

- Abbey Road
- Green
- Fables of the Reconstruction
- Lifes Rich Pageant
- Murmur
- Narrow Stairs
- Being There
- New Adventures In Hi-Fi
- Let It Be
- A Ghost Is Born
- Every Where Is Some Where
- Several Arrows Later
- The Joshua Tree

## Model

Raw Album Title
→ Marker Extraction
→ Marker Classification
→ Canonical Album
→ Album Intelligence
→ Session Reconstruction
→ Album Relationship Modeling

## Identity Rule

Canonical album identity should be:

Artist Identity + Canonical Album Title

Album title alone is insufficient because generic titles like Greatest Hits, Anthology, Legend, Faith, and War can collide across artists.

## Marker Taxonomy

### Edition markers

Safe candidates for canonical collapse:

- Deluxe Edition
- Deluxe Version
- Remastered
- Remaster
- Expanded Edition
- Bonus Track Version
- Anniversary Edition
- Super Deluxe Edition
- 2019 Mix
- 2024 Remaster
- Remastered 2013
- 2007 Stereo Mix

### Album-type markers

Classification metadata, not automatic collapse:

- Live
- Original Motion Picture Soundtrack
- Music from the Motion Picture
- Original Soundtrack
- Box Set
- Single
- Demo
- Instrumentals

### Review markers

Require caution or curation:

- Acoustic
- Remixes
- Re-Recorded Versions
- Radio Edit
- Video Version
- feat.
- White Album
- UK

## Architectural Conclusion

Album normalization is not metadata cleanup.

It is entity resolution.

Album Intelligence cannot be trusted on raw Apple album names because raw names fragment album relationships across editions.

Canonical Album identity is now a prerequisite layer for Album Intelligence.
Album normalization moved 13 albums into the Top 100 companion-album candidate list that would not have appeared using raw Apple metadata.
## Future Work

### Album Families

Potential future layer above Canonical Album.

Examples:

- The Beatles ↔ The White Album
- The Lamb Lies Down on Broadway ↔ 2007 Stereo Mix ↔ 50th Anniversary
- Curated aliases discovered during intelligence work

Album Families should remain curated and separate from automatic normalization.

### Live Albums

Future versions should classify live albums separately from studio albums.

Examples:

- Live
- Live at...
- Unplugged
- Concert recordings

Live albums may require distinct relationship models and session analysis.

### Apple Music Live Data

Future Apple Music API ingestion should pass through album normalization before persistence into Album Intelligence models.

Canonical Album identity should remain stable regardless of source system metadata.
