# Apple Music Dashboard Contract

## Source

Primary dashboard-safe source:

- Local-only file: C:\Users\joevi\apple-music-sanitized\apple-music-dashboard-rollup.json
- Do not commit this file.
- Do not commit sanitized CSVs.
- Do not commit raw Apple exports.

## Dashboard-safe sections

The dashboard may use these aggregate-only sections:

- totals
- durationSanity
- activity
- peaks
- recent
- favoritesByType
- playsByYear
- playsByMonth

The rollup schema audit confirms these sections contain aggregate fields rather than track, artist, album, playlist, station, device, or source-detail fields.

## Allowed dashboard metrics

The dashboard may display:

- total plays
- total skips
- skip rate
- capped listening hours
- active listening days
- active day rate
- average plays per active day
- average skips per active day
- average capped hours per active day
- average capped minutes per play
- first played date
- last played date
- highest play year
- highest play month
- last 12 months plays
- last 12 months skips
- last 12 months capped hours
- year-over-year play delta
- year-over-year capped-hour delta
- favorite type counts
- plays by year
- plays by month
- duration quality warning

## Excluded content

The dashboard must not display:

- track names
- artist names
- album names
- playlist names
- station names
- favorite item descriptions
- recently played descriptions
- top content names
- source type summaries
- device/platform summaries
- IP/location/account identifiers
- raw Apple export rows

## Duration rule

Use capped duration metrics for dashboard display by default.

Raw duration may be retained only as a diagnostic value behind a data-quality warning. If durationSanity.quality is not "clean", the UI should clearly indicate that Apple-reported duration required sanity adjustment.

## React readiness

React wiring is allowed only after this contract is accepted.

The first React implementation should read from a manually imported/local rollup object or a static mock shaped like apple-music-dashboard-rollup.json.

Do not build any UI that requires committing the private rollup JSON.
