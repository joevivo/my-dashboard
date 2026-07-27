# Music Artist Comparative Standing Contract v0

## Document control

- Product: Defending Sisyphus Music
- Capability: Artist Comparative Standing
- Contract version: v0
- Repository baseline: `75eba8a`
- State: approved by Ginto on 2026-07-27
- Implementation state: approved for implementation planning; code not started

## 1. Purpose

This contract defines how the product may compare an artist or
artist family with other eligible entities.

It governs:

- supported metrics and units;
- eligible comparison populations;
- artist versus artist-family scope;
- rank, percentile, and tie handling;
- missing and unavailable evidence;
- backend response fields;
- UI disclosure and acceptance tests.

It does not authorize one composite relationship score.

## 2. Product question

> How large or persistent is this artist's supported evidence
> relative to other comparable artists?

Every result must remain tied to a source, metric, unit, identity
scope, coverage status, and eligible population.

## 3. Governing principles

1. Compare only evidence governed by the same metric.
2. Missing coverage is not zero evidence.
3. Artist and artist-family populations remain separate.
4. Every rank discloses population size.
5. Every percentile discloses metric, source, and scope.
6. Recent Apple observations are not confirmed plays.
7. Library Evidence is not complete listening history.
8. Ties use deterministic rules.
9. Backend contracts calculate standing.
10. React renders the contract without reinterpreting evidence.

## 4. Identity scopes

### 4.1 Artist scope

- Scope key: `artist`
- Measure one canonical artist identity.
- Apply aliases only when identity rules authorize them.
- Exclude other curated family members.
- Compare only with canonical artist identities.

### 4.2 Artist-family scope

- Scope key: `artist_family`
- Use only reviewed curated families.
- Preserve member-level provenance.
- Deduplicate aliases, members, and shared evidence.
- Compare only with other reviewed artist families.
- Never mix family totals into artist-only populations.

## 5. Initially supported dimensions

### 5.1 Confirmed Actual Plays

- Metric key: `actual_plays`
- Canonical unit: plays
- Existing fields: `actualPlays`, `actual_plays`
- Source: Actual Listening
- Interpretation: governed confirmed play outcomes

### 5.2 Confirmed listening duration

- Metric key: `listening_duration_ms`
- Canonical unit: milliseconds
- Display unit: hours
- Existing fields: `duration_ms`, `hoursListened`
- Rank using unrounded milliseconds.

### 5.3 Library Evidence records

- Metric key: `library_evidence_records`
- Canonical unit: records
- Source: Apple Music Library Tracks
- Interpretation: library representation, not confirmed plays

### 5.4 Historical years represented

- Metric key: `historical_years_represented`
- Canonical unit: distinct calendar years
- Existing fields: `yearsActive`, `yearsRepresented`
- UI label: Years Represented
- This is not an elapsed relationship span.

### 5.5 Recent Apple observation volume

- Metric key: `recent_apple_observations`
- Canonical unit: observations
- Existing field: `observationCount`
- Interpretation: captured observations, not confirmed listening

### 5.6 Unique historically observed objects

- Metric key: `historical_unique_object_count`
- Canonical unit: logical objects
- Existing presentation field: `historicalUniqueObjectCount`
- Must become a canonical backend field before ranking.

## 6. Deferred dimension

### 6.1 Snapshot Persistence

Snapshot Persistence is unsupported in v0.

The repository does not yet expose a canonical artist-level metric.
No percentile or rank may be displayed until the metric, coverage
denominator, and interpretation are separately approved.

## 7. Eligible comparison populations

Every metric uses its own eligible population.

An entity is eligible only when:

- identity scope matches the requested scope;
- the source was searched and returned supported evidence;
- the canonical metric is present;
- the metric value is greater than zero;
- the unit and contract version match;
- the entity is not duplicated through aliases or family rollup.

Exclude entities when the source is unavailable, not searched,
outside coverage, unresolved, ambiguous, null, or unsupported.

Excluded entities must not be inserted as zero-valued records.

## 8. Rank and percentile rules

### 8.1 Numeric rank

Use descending competition rank:

`rank = 1 + count(values greater than the entity value)`

Values `100, 80, 80, 50` produce ranks `1, 2, 2, 4`.

### 8.2 Percentile

Use a tie-aware midpoint percentile:

`percentile = 100 * (L + 0.5 * (T - 1)) / (N - 1)`

- `L`: eligible entities with a lower value
- `T`: entities tied at the same value
- `N`: eligible population size

Rules:

- highest unique value receives 100;
- lowest unique value receives 0;
- tied values receive the midpoint of tied positions;
- display may round, but ranking uses canonical values;
- when `N = 1`, rank may be 1 and percentile is null.

## 9. Allowed statuses

- `ranked`
- `searched_no_evidence`
- `unavailable`
- `not_searched`
- `outside_coverage`
- `identity_unresolved`
- `unsupported_metric`
- `insufficient_population`
- `invalid_metric`

Only `ranked` returns a non-null percentile.

## 10. Response contract

Each comparative dimension returns:

```json
{
  "metricKey": "actual_plays",
  "label": "Confirmed Actual Plays",
  "status": "ranked",
  "scope": "artist",
  "entityKey": "canonical-artist-key",
  "entityLabel": "Artist Name",
  "sourceFamily": "actual_listening",
  "coverageStatus": "searched_with_evidence",
  "value": 97,
  "unit": "plays",
  "displayValue": "97 confirmed plays",
  "rank": 296,
  "percentile": 84,
  "populationSize": 1846,
  "tieCount": 1,
  "populationDefinition": "Eligible canonical artists",
  "interpretation": "Higher than approximately 84% of eligible artists.",
  "provenance": [],
  "limitations": []
}
```

## 11. Presentation contract

Default presentation:

`97 confirmed plays — 84th percentile, rank 296 of 1,846 eligible artists.`

Do not display:

- one combined relationship percentage;
- rank without population size;
- percentile without metric and source;
- family standing as artist-only standing;
- zero when coverage is missing or unavailable.

## 12. Implementation boundaries

Recommended order:

1. Build eligible populations in the backend.
2. Add deterministic ranking helpers.
3. Add dimension-specific adapters.
4. Expose results through the shared Artist contract.
5. Add fixture-backed validation.
6. Render reusable Comparative Standing components.

Do not calculate ranking logic in `src/QueryWorkbench.jsx`.

## 13. Required fixtures

- unique top, middle, and bottom values;
- tied values;
- one-entity population;
- searched source with zero evidence;
- unavailable source;
- unresolved identity;
- artist-only and artist-family populations;
- alias and family-member deduplication;
- raw duration versus rounded display hours;
- unsupported Snapshot Persistence;
- deterministic repeated execution.

## 14. Acceptance gate

Implementation may begin only after Ginto approves:

- the six supported dimensions;
- Snapshot Persistence deferral;
- positive-evidence eligibility;
- separate artist and family populations;
- competition rank;
- midpoint percentile;
- one-entity behavior;
- response and presentation fields;
- implementation boundaries.
