# Music Artist Comparative Standing Fixture Contract v0

- Parent contract: `music-artist-comparative-standing-contract-v0.md`
- Source amendment: `music-artist-comparative-standing-source-availability-amendment-v0.md`
- State: approved by Ginto on 2026-07-27
- Drafted: 2026-07-27
- Implementation state: approved for deterministic fixture implementation and Python population-and-ranking module planning; production integration remains subject to fixture validation

## 1. Purpose

This contract defines the mandatory fixtures and expected results for Artist Comparative Standing.

The fixtures must validate ranking mathematics, metric-specific populations, source availability, artist identity behavior, artist-family separation, and source-semantic disclosures before production integration.

## 2. Locked source semantics

### 2.1 Library Evidence

- Source: full `Apple Music Library Tracks.json` export.
- Artist field: `Artist`.
- Metric value: number of library-track records assigned to the canonical artist.
- Population eligibility: canonical artist value greater than zero.
- Blank artist values are excluded.
- Missing evidence is not converted to zero.

### 2.2 Years Represented

- Source: full `Apple Music Library Tracks.json` export.
- Canonical year field: `Last Played Date`.
- Metric value: count of distinct calendar years represented by nonblank, parseable `Last Played Date` values for the canonical artist.
- Multiple records in the same calendar year count once.
- Track release year, `Track Year`, `Release Date`, library-add date, modification date, and purchase date are not substitutes.
- Population eligibility: at least one governed represented year.

This definition preserves the existing Artist query-engine semantics, which matched `Last Played Date` for all six audited artists.

### 2.3 Recent Apple Observations

- Source: `data/music/live/apple_snapshot_warehouse.csv`.
- Metric value: number of artist-bearing snapshot rows assigned to the canonical artist.
- Repeated appearances across snapshots remain separate observations.
- Population eligibility: observation count greater than zero.

### 2.4 Historical Unique Object Count

- Source: `data/music/live/apple_snapshot_warehouse.csv`.
- Canonical logical-object key: `entity_type + entity_id`.
- Repeated occurrences of the same typed key count once per canonical artist.
- Changes in `source` do not create a new logical object.
- Blank entity IDs are invalid for this metric.
- A typed key resolving to multiple canonical artists must fail validation rather than being counted silently.

The audited source contained 11,567 artist-bearing rows, no missing entity IDs, no typed-key artist conflicts, and no typed-key name changes.

### 2.5 Unavailable metrics

The following metrics remain unavailable and outside ranking populations:

- `actual_plays`;
- `listening_duration_ms`.

Their fixture results must contain null value, rank, percentile, and population size together with status `unavailable` and the approved source limitation.

## 3. Planned fixture artifact

The implementation fixture will be stored at:

`data/music/fixtures/artist-comparative-standing-v0.json`

The fixture must contain deterministic synthetic inputs. Source-baseline validation may be separate from ranking-unit fixtures.

## 4. Ranking mathematics fixtures

### 4.1 Competition ranking and ties

For descending values `100, 80, 80, 20`, expected results are:

| Value | Rank | Percentile |
|---:|---:|---:|
| 100 | 1 | 100.0 |
| 80 | 2 | 50.0 |
| 80 | 2 | 50.0 |
| 20 | 4 | 0.0 |

This verifies competition ranking `1, 2, 2, 4` and tie-aware midpoint percentile calculation.

### 4.2 Single-member population

For a population of one eligible entity:

- rank: `1`;
- percentile: null;
- status: `insufficient_population`;
- population size: `1`.

### 4.3 Excluded values

Zero, null, missing, unavailable, not searched, outside coverage, unresolved, ambiguous, unsupported, and invalid values must not enter an eligible positive-evidence population.

Exclusion must not change the values of eligible entities.

## 5. Library Evidence fixtures

Fixtures must verify:

1. multiple library records for one canonical artist are counted separately;
2. blank artists are excluded;
3. whitespace and case normalization do not split one identity;
4. governed aliases merge only through the canonical identity layer;
5. zero library records produce no ranked population member; and
6. artist-family records do not alter the standalone artist population.

## 6. Years Represented fixtures

Fixtures must verify:

1. two records in the same `Last Played Date` year count as one represented year;
2. records across three calendar years produce value `3`;
3. blank and unparseable dates are excluded;
4. `Track Year` and `Release Date` do not affect the metric;
5. an artist with no parseable `Last Played Date` is excluded from the ranked population; and
6. artist-family year sets are unioned and deduplicated separately from standalone artists.

## 7. Recent Apple Observation fixtures

Fixtures must verify:

1. every artist-bearing snapshot row counts as one observation;
2. the same object observed in three snapshots counts as three observations;
3. blank artists are excluded;
4. aliases resolve before aggregation; and
5. observation populations remain separate for artists and reviewed artist families.

## 8. Historical Unique Object fixtures

Fixtures must verify:

1. repeated `album + entity-1` rows count as one object;
2. `album + entity-1` and `song + entity-1` are distinct typed objects;
3. source changes do not split a typed object;
4. blank entity IDs fail metric validation;
5. one typed key assigned to two canonical artists fails validation; and
6. reviewed artist-family objects are unioned and deduplicated independently.

## 9. Unavailable-metric fixtures

For both `actual_plays` and `listening_duration_ms`, fixtures must verify:

- status `unavailable`;
- value null;
- rank null;
- percentile null;
- population size null;
- no population construction attempt; and
- approved limitation text explaining that governed Actual Listening lacks artist identity.

The legacy daily aggregate must not appear as a fallback source.

## 10. Artist and family population separation

Fixtures must contain at least one reviewed family with multiple members and must prove that:

- standalone members remain in the artist population;
- the family appears only in the family population;
- family metrics aggregate governed member evidence;
- family ranks compare only with other eligible reviewed families; and
- no family value is inserted into the standalone artist population.

## 11. Required response fields

Each metric result fixture must validate:

- `metricKey`;
- `status`;
- `value`;
- `unit`;
- `rank`;
- `percentile`;
- `populationSize`;
- `entityType`;
- `source`;
- `sourceLimitation`; and
- `calculationVersion`.

## 12. Source-baseline evidence

The implementation must retain separate source-health assertions for the audited inputs:

- Library Tracks archive SHA-256: `50087BC1B14475D37865914F4BDB4BE53A52126A750F99D89661F953BBFC0510`;
- Snapshot warehouse SHA-256: `F2DFD2E893BDAB78FA63B1452C1A96FC4BE0E043DD28CFA3FDA61802499F687D`;
- library rows: 34,643;
- normalized library artists: 5,186;
- artist-bearing snapshot rows: 11,567;
- snapshot artists: 2,653; and
- combined supported-source artist identities before canonical alias governance: 5,305.

These values describe the audited source baseline. They are not immutable product constants.

## 13. Acceptance gate

The fixture implementation is acceptable only when:

- every mandatory fixture passes;
- ranking and percentile calculations match the approved contract;
- unavailable metrics never enter populations;
- `Last Played Date` is the only Years Represented field;
- `entity_type + entity_id` is the Historical Unique Object key;
- artists and artist families remain separate populations;
- aliases are handled by the canonical identity layer;
- zero and missing evidence remain distinct;
- source limitations are preserved; and
- no ranking calculations are implemented in React.

## 14. Recommended decision

Approve this fixture contract, then create the deterministic JSON fixture and the Python population-and-ranking module plan.
