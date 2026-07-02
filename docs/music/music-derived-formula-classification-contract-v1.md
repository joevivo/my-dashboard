# Music Derived Formula and Classification Contract v1

## Status

Draft contract for Sprint 5.

No UI implementation should depend on this contract until it is reviewed and accepted.

---

## Purpose

This contract defines the minimum gate a derived metric or derived classification must pass before it can be used as a trusted Music intelligence claim.

Core rule:

No derived classification becomes UI truth until its formula, confidence model, weakening factors, and regression fixtures are documented.

---

## Relationship to Prior Contracts

This contract depends on:

- Music phase requirements checklist v1
- Music investigation packet contract v1
- Music source and provenance registry v1
- Music identity contract v1
- Music facts, insights, and reasoning trace contract v1

Required ordering:

Identity -> Evidence -> Facts -> Formula -> Hypothesis -> Insight -> Confidence -> Regression Fixtures

Derived formulas must not bypass source boundaries, identity confidence, or reasoning trace requirements.

---

## Definitions

### Derived Metric

A numeric or categorical value calculated from source-backed evidence and deterministic facts.

Examples:

- Friction Score
- Momentum Score
- Playlist World Score
- Album concentration score
- Family amplification factor

### Derived Classification

A named relationship, status, or interpretation assigned using one or more derived metrics and explicit thresholds.

Examples:

- Emerging Core Artist
- Dormant Relationship
- Return Signal
- Catalog Ecosystem
- Dense Catalog Ecosystem
- Album-Centered Relationship

### Formula Gate

A checklist that determines whether a derived metric or classification is allowed to appear as trusted output.

---

## Formula Readiness Status

Allowed formula readiness values:

- blocked
- draft
- reviewed
- accepted
- productionEligible

Status meanings:

### blocked

The concept exists but is not allowed as a trusted insight or UI classification.

Allowed use:

- Mention in docs.
- Mention as a clearly labeled hypothesis.
- Appear in open questions or suggested investigations.

Not allowed:

- UI badge.
- Settled insight.
- Ranking sort.
- Dashboard KPI.

### draft

A proposed formula exists but has not been validated.

Allowed use:

- Internal analysis.
- Investigation packets as low-confidence hypothesis only.

Not allowed:

- Durable classification.
- UI default display.

### reviewed

The formula has been reviewed against known examples but lacks complete fixture coverage.

Allowed use:

- Medium-confidence hypothesis in Query Workbench.
- Regression fixture development.

Not allowed:

- Polished Artist Intelligence claim.
- Music Dashboard KPI.

### accepted

The formula has documented inputs, thresholds, confidence model, weakening factors, limitations, and fixtures.

Allowed use:

- Trusted investigation-packet insight.
- Artist Intelligence supporting claim.

Not allowed:

- Broad dashboard aggregation unless production eligibility is met.

### productionEligible

The formula is accepted, covered by regression fixtures, and stable enough for recurring UI surfaces.

Allowed use:

- Query Workbench.
- Artist Intelligence.
- Playlist Intelligence where applicable.
- Music Dashboard summary where applicable.

---

## Required Formula Fields

Every derived metric or classification must document:

- id
- name
- kind
- readinessStatus
- purpose
- entityTypes
- requiredInputs
- allowedSourceFamilies
- requiredIdentityConfidence
- requiredEvidenceConfidence
- calculation
- thresholds
- timeWindows
- confidenceModel
- weakeningFactors
- limitations
- outputShape
- reasoningTraceRequirements
- regressionFixtures
- examples
- nonGoals

Allowed kind values:

- metric
- classification
- hybrid

---

## Required Input Rules

Every formula must define required inputs.

Each input must include:

- inputName
- inputType
- sourceFamily
- sourceMetricType
- required
- acceptedConfidence
- missingDataBehavior

Missing data behavior must be one of:

- blockFormula
- lowerConfidence
- useDefault
- omitComponent
- returnNotFound

Rules:

- Required inputs cannot be silently defaulted.
- Missing source coverage must lower confidence or block the formula.
- Inputs must be traceable to evidence IDs or fact IDs.
- Derived metrics cannot source themselves.

---

## Allowed Source Families

Formula inputs may use these source families only when allowed by the source registry:

- Apple Music daily track summary
- Apple Music Library Tracks
- Apple Music Library Playlists
- DuckDB listening context
- Apple Music live endpoints
- Curated identity and album seeds
- Derived model output

Rules:

- Actual listening formulas require actual listening evidence.
- Library evidence formulas cannot claim actual listening behavior.
- Playlist formulas cannot claim actual listening truth.
- Live formulas cannot claim durable history by themselves.
- Curated identity formulas can resolve identity but cannot prove behavior.

---

## Confidence Model Requirements

Every formula must define how confidence is assigned.

Required confidence dimensions:

- identity
- evidence
- sourceCoverage
- timeWindow
- interpretation
- formulaReadiness

Allowed confidence outputs:

- high
- medium
- low
- notFound

Confidence rules:

- Formula confidence cannot exceed identity confidence unless explicitly justified.
- Formula confidence cannot exceed evidence confidence unless explicitly justified.
- Source-limited results must lower interpretation confidence.
- Live-only evidence cannot produce high durable relationship confidence.
- Playlist-only evidence cannot produce high listening relationship confidence.
- Library-only evidence cannot produce high actual listening confidence.
- Draft formulas cannot produce high-confidence insights.

---

## Weakening Factors

Every formula-backed classification must define what weakens it.

Standard weakening factors:

- lowIdentityConfidence
- weakSourceCoverage
- missingRecentWindow
- missingHistoricalBaseline
- highSkipRate
- lowPlayCount
- lowYearCoverage
- concentratedSingleSong
- concentratedSingleAlbum
- playlistOnlyEvidence
- libraryOnlyEvidence
- liveOnlyEvidence
- unresolvedFamilyMember
- unresolvedAlbumVariant
- contradictoryEvidence
- insufficientRegressionCoverage

Rules:

- Weakening factors must be visible in reasoning trace.
- A classification with major weakening factors should remain a hypothesis.
- A classification with unresolved blockers must not become a settled insight.

---

## Regression Fixture Requirements

Every accepted formula must include regression fixtures.

Each fixture must define:

- fixtureId
- entityType
- query
- canonicalKey
- expectedInputs
- expectedOutput
- expectedConfidence
- expectedWeakeningFactors
- sourceEvidenceRequired
- notes

Fixture categories:

- positiveControl
- negativeControl
- edgeCase
- sourceLimitedCase
- identityAmbiguousCase
- recentOnlyCase
- historicalOnlyCase

Rules:

- At least one positive and one negative control are required before accepted status.
- Source-limited cases are required for formulas that use incomplete data.
- Identity-ambiguous cases are required for artist, family, album, and song classifications.
- Fixtures must preserve expected confidence, not only expected label.

---

## Reasoning Trace Requirements

Every formula-backed output must produce reasoning trace.

Required trace chain:

Evidence -> Facts -> Formula Inputs -> Formula Output -> Weakening Factors -> Confidence -> Insight or Hypothesis

Required trace fields:

- evidenceIds
- factIds
- formulaId
- formulaVersion
- inputValues
- thresholdsApplied
- weakeningFactors
- confidenceImpact
- outputId

Rules:

- A user must be able to trace a classification back to source evidence.
- Formula thresholds must be visible.
- Confidence reductions must be visible.
- Blocked formulas must explain why they are blocked.

---

## Blocked Concepts

The following concepts remain blocked until individual formula specs exist:

- Friction Score
- Momentum Score
- Emerging Core Artist
- Dormant Relationship
- Return Signal
- Catalog Ecosystem
- Playlist World Score

Blocked concepts may appear only as:

- documentation concepts
- low-confidence hypotheses
- open questions
- suggested investigations

Blocked concepts must not appear as:

- UI badges
- settled insights
- default filters
- ranking controls
- dashboard KPIs

---

## Friction Score Gate

Readiness status:

- blocked

Required before promotion:

- Define skip-rate inputs.
- Define play-rate or completion proxy inputs.
- Define treatment of skips by source.
- Define confidence model for sparse play counts.
- Define how friction differs from dislike.
- Define weakening factors.
- Define regression fixtures.

Current allowed use:

- Hypothesis only.
- No UI classification.

---

## Momentum Score Gate

Readiness status:

- blocked

Required before promotion:

- Define recent time windows.
- Define historical baseline.
- Define live endpoint contribution.
- Define decay or weighting model.
- Define minimum activity threshold.
- Define confidence model for sparse recent data.
- Define regression fixtures.

Current allowed use:

- Hypothesis only.
- No UI classification.

---

## Emerging Core Artist Gate

Readiness status:

- blocked

Dependency:

- Momentum Score
- Friction Score

Required before promotion:

- Define minimum evidence threshold.
- Define rising momentum threshold.
- Define acceptable or falling friction threshold.
- Define historical baseline rule.
- Define confidence model.
- Define positive and negative controls.

Current allowed use:

- Hypothesis only.
- No UI classification.

---

## Dormant Relationship Gate

Readiness status:

- blocked

Required before promotion:

- Define historical significance threshold.
- Define dormancy window.
- Define recent inactivity rule.
- Define library-only and playlist-only behavior.
- Define confidence model.
- Define regression fixtures.

Current allowed use:

- Hypothesis only.
- No UI classification.

---

## Return Signal Gate

Readiness status:

- blocked

Dependency:

- Dormant Relationship

Required before promotion:

- Define dormant baseline.
- Define recent-return threshold.
- Define live endpoint contribution.
- Define minimum actual listening evidence.
- Define confidence model.
- Define regression fixtures.

Current allowed use:

- Hypothesis only.
- No UI classification.

---

## Catalog Ecosystem Gate

Readiness status:

- blocked

Required before promotion:

- Define catalog breadth inputs.
- Define album distribution score.
- Define minimum canonical album count.
- Define minimum actual listening threshold.
- Define how single-anchor relationships are excluded.
- Define confidence model.
- Define regression fixtures.

Current allowed use:

- Hypothesis only.
- No UI classification.

---

## Playlist World Score Gate

Readiness status:

- blocked

Required before promotion:

- Define playlist classification dependency.
- Define concentration calculation.
- Define artist count and track count inputs.
- Define generated playlist treatment.
- Define confidence model.
- Define regression fixtures.

Current allowed use:

- Hypothesis only.
- No UI classification.

---

## Promotion Rules

A formula can move from blocked to draft when:

- Required inputs are named.
- Source families are named.
- Initial calculation is documented.
- Known limitations are documented.

A formula can move from draft to reviewed when:

- Thresholds are documented.
- Confidence model is documented.
- Weakening factors are documented.
- At least two examples are documented.

A formula can move from reviewed to accepted when:

- Regression fixtures exist.
- Positive and negative controls exist.
- Source-limited behavior is documented.
- Identity ambiguity behavior is documented where relevant.

A formula can move from accepted to productionEligible when:

- It is stable across regression fixtures.
- It has no unresolved source-boundary violations.
- It has no unresolved identity-boundary violations.
- It can produce reasoning trace.
- It can expose confidence reductions.

---

## Non-Goals

This contract does not define final Friction, Momentum, Emerging Core Artist, Dormant Relationship, Return Signal, Catalog Ecosystem, or Playlist World Score formulas.

This contract does not implement formulas.

This contract does not alter source data.

This contract does not alter UI.

This contract does not promote any currently blocked concept to accepted.

---

## Acceptance Criteria

This contract is accepted when:

- Formula readiness statuses are documented.
- Required formula fields are documented.
- Input, confidence, weakening-factor, reasoning-trace, and fixture rules are documented.
- Blocked concepts remain blocked.
- Each blocked concept has a gate defining what is missing.
- Promotion rules are explicit.
- Source and identity boundaries are preserved.
- No UI implementation is started.
