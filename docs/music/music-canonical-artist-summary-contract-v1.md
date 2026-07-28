# Music Canonical Artist Summary Contract v1

## 1. Document control

- Product: Defending Sisyphus Music
- Capability: Canonical Artist Summary
- Contract version: v1
- Repository baseline: `f80c12c`
- Status: Draft awaiting Ginto approval

## 2. Purpose

This contract defines one backend-owned canonical summary for an artist or reviewed artist family.

Artist Intelligence and Artist Dossier consume the concise summary. Query Workbench remains responsible for full evidence, provenance, reasoning, and unresolved questions.

React surfaces must render this contract without independently deriving identity, coverage, confidence, relationship classification, or missing-data semantics.

## 3. Architectural ownership

- Python owns canonical Artist summary assembly and Music-domain semantics.
- artist_query_summary.py only invokes the producer and serializes its response.
- Express validates HTTP input, invokes Python, handles operational failures, and returns the response unchanged.
- Express must not independently add family, bridge, Comparative Standing, investigation, confidence, or coverage semantics.
- Frontend consumers must not convert missing or unavailable evidence to zero.
## 4. Canonical response envelope

The backend response must contain these top-level fields:

- schemaVersion
- status
- query
- entity
- scope
- coverage
- summary
- comparativeStanding
- family
- confidence
- limitations
- provenance
- suggestedInvestigations
- investigation
- compatibility

The schema version is music.canonical-artist-summary.v1.

## 5. Status vocabulary

Top-level status must use one of:

- available
- partial
- searched_no_evidence
- identity_unresolved
- unavailable
- unsupported

Backend operational failure is not an evidence status. It remains a process or HTTP failure.
## 6. Identity and scope

The entity object must contain:

- entityType
- displayName
- canonicalKey
- aliases
- identityStatus
- identityConfidence
- identitySource

Canonical identity must come from the shared Music identity layer.

The implementation must not derive canonical keys by lowercasing a display name or replacing spaces with punctuation.

Unresolved identity must remain unresolved. The raw query must not be reported as a resolved artist.

The scope object must contain:

- scopeType
- familyId
- familyName
- familyMembers
- primaryArtistKey

scopeType must be either artist or artist_family.

Artist-only and artist-family evidence must remain separately identified.

Artist-family scope may use only reviewed curated families. Family aggregation must preserve member-level provenance and must not overwrite the artist-only summary.
## 7. Evidence coverage

Each governed evidence source must publish an explicit coverage record.

Every coverage record must contain:

- sourceId
- sourceFamily
- status
- coverageBasis
- limitations

Coverage status must use one of:

- searched_with_evidence
- searched_no_evidence
- not_searched
- outside_coverage
- unavailable
- stale
- unsupported

Missing, unavailable, unsupported, stale, outside-coverage, or unsearched evidence must not be converted to zero.

Zero is valid only when the governed source was searched successfully and returned no matching evidence.

Current Recent Apple objects and historical snapshot observations must have separate coverage records.

Backend operational failure must remain distinct from source unavailability.
## 8. Summary evidence families

The summary object contains separate source-owned evidence families.

### 8.1 Actual Listening

Actual Listening must contain:

- status
- actualPlays
- actualSkips
- listeningDurationMs
- hoursListened
- topSongs
- sourceId

Actual plays, skips, and duration remain nullable when coverage is unavailable or incomplete.

Missing coverage must produce null, not zero.

Raw listeningDurationMs is authoritative. Display hours may be derived from it.

Skip counts must not be inferred from Library Evidence or Recent Apple observations.

### 8.2 Library Evidence

Library Evidence must contain:

- status
- recordCount
- yearsRepresented
- firstEvidenceDate
- latestEvidenceDate
- topTracks
- topAlbums
- timeline
- sourceId

Library Evidence records are not confirmed plays.

Record count and years represented remain nullable when the source is unavailable or not searched.

Top-track and top-album counts derived from Library Evidence must be labeled as evidence counts, not plays.
### 8.3 Recent Apple

Recent Apple must contain separate current and historical-snapshot objects.

The current object must contain:

- status
- recentObjectCount
- heavyRotationCount
- objects

The historicalSnapshots object must contain:

- status
- observationCount
- snapshotCount
- uniqueObjectCount
- firstObservedAt
- latestObservedAt
- topObjects

Recent Apple observations are not confirmed plays.

An unavailable source must use nullable metrics. A successfully searched source with no matching evidence may use zero counts with searched_no_evidence status.

### 8.4 Historical span

Historical span must contain:

- status
- firstEvidenceDate
- latestEvidenceDate
- yearsRepresented

Historical span summarizes supported evidence boundaries. It must not independently create a relationship classification.

### 8.5 Catalog

Catalog must contain:

- status
- albumCount
- trackCount
- topAlbums
- topTracks

Catalog depth must remain separate from Actual Listening and Library Evidence record counts.

## 9. Comparative Standing

The canonical summary must embed the governed Artist Comparative Standing response unchanged or expose an explicit unavailable state.

Each result must preserve:

- metric
- source
- unit
- identity scope
- coverage status
- eligible population
- rank
- percentile
- provenance
- limitations

Artist and artist-family comparison populations must remain separate.

Missing or unavailable metrics must not enter a comparison population as zero.

This contract does not authorize a composite Artist score.

## 10. Family evidence

The family object must contain:

- status
- familyId
- familyName
- members
- relationshipType
- metrics
- provenance

Family evidence may use only reviewed curated families.

Artist-only metrics must remain available separately from family metrics.

Family membership alone must not create a relationship classification.

Family amplification may be exposed only as a derived fact with its inputs and calculation disclosed.
## 11. Confidence, limitations, and provenance

Confidence must be produced by the backend and traceable to evidence coverage.

The confidence object must contain:

- overall
- identity
- actualListening
- libraryEvidence
- recentApple
- comparativeStanding

React must not calculate an overall evidence-quality label from local thresholds.

Limitations must be structured records containing:

- code
- message
- sourceId

Provenance must be structured source records containing:

- sourceId
- label
- coverageStatus

Every material summary fact must be traceable to a source or governed derived calculation.

## 12. Investigation boundary

The investigation object may contain full evidence, facts, hypotheses, insights, reasoning traces, open questions, and suggested investigations.

The investigation object is not the concise canonical Artist summary.

Artist Intelligence and Artist Dossier consume the concise summary. Query Workbench remains the primary surface for full evidence and reasoning.

Suggested investigations must be backend-provided. React may render or navigate from them but must not invent analytical conclusions.
## 13. Compatibility projection

The first backend implementation may preserve existing top-level fields while frontend consumers migrate to the canonical contract.

Compatibility fields include:

- artist
- query
- libraryEvidenceRecords
- actualPlays
- actualSkips
- hoursListened
- listeningDurationMs
- playActivitySource
- actualTopSongs
- yearsActive
- firstSeen
- latestSeen
- firstPlayedDate
- latestPlayedDate
- classification
- notes
- topSongs
- topAlbums
- timeline
- source
- matchRank
- identity
- evidence
- activity
- derived
- family
- familyMetrics
- bridge
- investigation

Compatibility fields must be projections from the authoritative Python producer.

Express must not add or recalculate compatibility fields.

Compatibility values must not conflict with canonical values.

Removing compatibility fields requires a separate governed migration checkpoint.

## 14. Prohibited behavior

The implementation must not:

- convert missing, unavailable, unsupported, stale, outside-coverage, or unsearched evidence to zero;
- calculate evidence quality, relationship state, identity, or Comparative Standing in React;
- derive canonical identity from display-name punctuation or spacing;
- relabel Library Evidence or Recent Apple observations as confirmed plays;
- combine artist and artist-family evidence without disclosure;
- create an unexplained composite Artist score;
- preserve Express as a second Music-domain assembly layer;
- create separate canonical profile models for Dashboard, Workbench, Artist Intelligence, or Artist Dossier.
## 15. Required validation fixtures

The first implementation must include deterministic validation for:

1. Resolved artist with Library Evidence and Actual Listening.
2. Resolved artist with Library Evidence but unavailable Actual Listening.
3. Resolved artist with Recent Apple observations only.
4. Resolved artist searched successfully with zero evidence.
5. Blank or unresolved artist identity.
6. Artist with reviewed artist-family membership.
7. Artist without reviewed family membership.
8. Artist and artist-family Comparative Standing kept separate.
9. Source unavailable versus searched-no-evidence behavior.
10. Current Recent Apple objects versus historical snapshots.
11. Compatibility projection equality with canonical values.
12. Express response equality with the Python producer.
13. Frontend consumers do not convert missing evidence to zero.

Representative identities must include:

- R.E.M.
- U2
- The Beatles
- Sugar and Bob Mould
- Steve Miller and Steve Miller Band
- one intentionally missing fixture artist
## 16. First implementation checkpoint

The first code checkpoint must:

1. Add one Python canonical Artist summary assembler.
2. Produce schemaVersion music.canonical-artist-summary.v1.
3. Assemble identity, scope, coverage, Actual Listening, Library Evidence, Recent Apple, historical span, catalog, family evidence, Comparative Standing, confidence, limitations, provenance, and suggested investigations in Python.
4. Preserve existing top-level response fields as compatibility projections.
5. Add deterministic fixture-backed schema validation.
6. Prove artist_query_summary.py returns the fully assembled response.
7. Leave Express behavior unchanged except for response-equality validation.
8. Include no frontend migration in the same checkpoint.

A later checkpoint will make Express transport-only and migrate frontend consumers.

## 17. Acceptance criteria

This contract is ready for implementation when:

- Ginto approves the contract and migration sequence.
- Every required field has explicit missing-data semantics.
- Artist and artist-family scopes remain distinct.
- Comparative Standing remains source-specific and governed.
- Query Workbench and concise Artist-profile responsibilities remain distinct.
- The compatibility strategy is accepted.
- The first implementation checkpoint remains limited to backend contract assembly and validation.
