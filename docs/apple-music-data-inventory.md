# Apple Music Data Inventory

## Dashboard source decision

Use `apple-music-dashboard-rollup.json` as the primary Apple Music dashboard source.

Do not wire React directly to sanitized CSV files.

## File decisions

| File | Rows | Risk | Dashboard Decision |
|---|---:|---|---|
| apple-music-dashboard-rollup.json | n/a | Low | Primary dashboard source |
| apple-music-summary.json | 8 summary entries | Low | Audit/validation only |
| apple-music-daily-track-summary.csv | 100,791 | High | Local-only aggregate source |
| apple-music-track-history.csv | 86,683 | High | Local-only |
| apple-music-recently-played.csv | 200 | High | Local-only |
| apple-music-top-content.csv | 595 | High | Local-only |
| apple-music-favorites.csv | 526 | High | Aggregate favorite-type counts only |
| apple-music-play-statistics.csv | 279 | Medium | Aggregate-only |
| apple-music-liked-radio-tracks.csv | 128 | High | Local-only |
| apple-music-favorite-stations.csv | 53 | High | Local-only |

## Sensitive or excluded columns

Do not display or directly wire dashboard UI to fields such as:

- Track Description
- Track Name
- Content
- Item Description
- Container Description
- Station Description
- Source Type
- Feature Name

## Safe dashboard rule

The dashboard should consume aggregate fields only from the rollup:

- totals
- durationSanity
- activity
- peaks
- recent
- favoritesByType
- playsByYear
- playsByMonth

## Implementation note

If new Apple Music files are added later, inspect headers and produce aggregate rollups locally before considering dashboard use.
