# Music Artist Comparative Standing Source Availability Amendment v0

- Parent contract: `music-artist-comparative-standing-contract-v0.md`
- State: approved by Ginto on 2026-07-27
- Drafted: 2026-07-27
- Implementation state: approved for supported-metric implementation planning; artist-level Actual Plays and Listening Duration remain unauthorized

## 1. Purpose

This amendment governs metric availability when an approved Comparative Standing metric does not yet have an artist-bearing authoritative source.

It does not change the approved ranking formulas, population eligibility rules, artist-family separation, tie handling, or prohibition on composite relationship scores.

## 2. Evidence requiring this amendment

The source audits established the following:

- The governed Actual Listening projection contains 199,396 event rows.
- Projection v1 contains no artist column.
- The raw Apple Music Play Activity source contains `Container Artist Name`, but that field is blank in all 199,396 rows.
- No description field capable of supplying artist identity is present in the raw event source.
- The legacy `apple-music-daily-track-summary.csv` contains artist-bearing aggregate rows, but its play, skip, duration, and date-coverage totals do not reconcile to the governed Actual Listening projection.
- The surrounding Apple export contains populated container and playlist artist lists, but no defensible event-level join to the governed Play Activity rows was established.

Therefore, the current evidence does not support artist-level governed Actual Plays or governed Listening Duration.

## 3. Source-governance decision

Comparative Standing must not calculate artist-level Actual Plays or Listening Duration from the legacy daily aggregate.

The legacy aggregate may remain available for historical investigation and source reconciliation under its existing terminology, but it must not be presented as governed Actual Listening truth and must not be used to establish Comparative Standing ranks or percentiles.

Missing governed artist identity must not be converted to zero.

## 4. Metric availability

| Metric | Current availability | Comparative Standing behavior |
|---|---|---|
| `actual_plays` | Unavailable | Return `unavailable`; do not rank; do not insert zero. |
| `listening_duration_ms` | Unavailable | Return `unavailable`; do not rank; do not insert zero. |
| `library_evidence_records` | Supported | Build an eligible artist population from canonical full-library evidence. |
| `historical_years_represented` | Supported | Rank distinct represented calendar years from canonical historical evidence. |
| `recent_apple_observations` | Supported | Rank canonical artist observation counts from the snapshot warehouse. |
| `historical_unique_object_count` | Conditionally supported | Rank only after the logical-object count becomes a canonical backend field and passes fixture validation. |

## 5. Required response behavior

For unavailable metrics, the shared Artist response must provide:

- metric key;
- status `unavailable`;
- null value;
- null rank;
- null percentile;
- null population size;
- a source limitation explaining that governed Actual Listening does not currently include artist identity.

The response must not silently substitute:

- Apple-reported daily Play Count;
- Apple-reported daily Skip Count;
- library Track Play Count;
- snapshot observation counts;
- inferred artist values; or
- presentation-layer aggregates.

## 6. UI disclosure

The UI may display the unavailable metrics, but it must label them as unavailable rather than showing zero or omitting the limitation.

Approved disclosure:

> Artist-level governed Actual Listening is unavailable because the current event projection does not contain artist identity.

The UI must not imply that the artist has no plays or no listening duration.

## 7. Implementation scope authorized after amendment approval

After this amendment is approved, implementation planning may proceed for:

1. canonical artist population construction from full library and snapshot sources;
2. deterministic competition ranking and tie-aware midpoint percentile helpers;
3. Library Evidence comparative standing;
4. Years Represented comparative standing;
5. Recent Apple Observations comparative standing;
6. canonical Historical Unique Object Count and its comparative standing;
7. explicit unavailable responses for Actual Plays and Listening Duration;
8. separate reviewed artist-family populations; and
9. fixture-backed validation of all supported and unavailable states.

Implementation of artist-level Actual Plays and Listening Duration remains unauthorized.

## 8. Reactivation requirements

`actual_plays` and `listening_duration_ms` may become rankable only after all of the following are complete:

1. an authoritative artist-bearing event source or defensible governed join is identified;
2. artist identity coverage and unresolved rates are measured;
3. alias and canonicalization rules are documented;
4. artist parsing or joining exceptions are fixture-governed;
5. event totals reconcile to the approved Actual Listening semantics;
6. the Actual Listening source contract is amended or versioned;
7. the projection is rebuilt with artist identity; and
8. Ginto approves the resulting contract change.

## 9. Acceptance gate

This amendment is ready for approval when:

- the approved v0 ranking mathematics remain unchanged;
- unavailable metrics cannot enter a ranking population;
- missing governed artist identity cannot become zero;
- the legacy daily aggregate is explicitly prohibited as Comparative Standing truth;
- supported metrics may proceed independently;
- source limitations are visible in backend responses and the UI; and
- no implementation begins before explicit approval.

## 10. Recommended decision

Approve this amendment and continue Comparative Standing implementation for the currently supported metrics.

Defer artist-level Actual Plays and Listening Duration until a governed artist-bearing Actual Listening projection exists.
