# Music Regression Fixture Contract v1

## Status

Draft contract for Sprint 6C.

This is a requirements and testing contract only.

No UI implementation is started by this document.

---

## Purpose

This contract defines how Defending Sisyphus Music proves that identity, evidence, facts, hypotheses, insights, formulas, terminology, and UI-surface claims behave correctly before UI implementation begins.

Core rule:

No claim should enter a UI surface unless at least one fixture proves how the system should handle it.

---

## Relationship to Prior Contracts

This contract depends on:

- Music phase requirements checklist v1
- Music investigation packet contract v1
- Music source and provenance registry v1
- Music identity contract v1
- Music facts, insights, and reasoning trace contract v1
- Music derived formula and classification contract v1
- Music UI surface model v1
- Music UI wireframes v1

Required validation chain:

Fixture -> Source Evidence -> Identity -> Facts -> Hypotheses -> Insights -> Confidence -> UI Surface Permission

---

## Fixture Goals

Regression fixtures must prove:

- known-good identity resolution.
- known-bad or ambiguous identity handling.
- source boundary enforcement.
- fact derivation from evidence.
- hypothesis and insight separation.
- blocked formula/classification behavior.
- emerging terminology behavior.
- UI surface permission behavior.
- confidence and weakening-factor behavior.

---

## Fixture Categories

| Category | Purpose |
|---|---|
| positiveControl | Proves expected supported behavior |
| negativeControl | Proves unsupported behavior is rejected or blocked |
| edgeCase | Proves unusual but important behavior |
| sourceLimitedCase | Proves source limitations reduce confidence or block claims |
| identityAmbiguousCase | Proves ambiguity does not become false certainty |
| blockedClassificationCase | Proves blocked concepts remain blocked |
| uiTerminologyCase | Proves UI labels do not overclaim |
| regressionBugCase | Proves a known bug does not return |

---

## Required Fixture Fields

Each fixture must define:

- fixtureId
- title
- category
- entityType
- query
- canonicalKey
- surface
- purpose
- sourceEvidenceRequired
- identityExpectation
- expectedFacts
- expectedHypotheses
- expectedInsights
- expectedConfidence
- expectedWeakeningFactors
- expectedBlockedClaims
- expectedSurfaceTreatment
- forbiddenOutputs
- notes

Allowed surface values:

- Music Intelligence
- Artist Intelligence
- Query Workbench
- Playlist Intelligence
- Music Library Admin

---

## Acceptance Criteria

This contract is accepted when:

- Fixture categories are documented.
- Required fixture fields are documented.
- Required seed fixture list is documented.
- Emerging terminology fixtures are included.
- Blocked classification fixtures are included.
- Source-limited and identity-ambiguous cases are included.
- UI surface permission expectations are included.
- No UI implementation is started.

---

## Required Seed Fixtures

The first fixture set must cover known high-value cases before UI work starts.

| Fixture | Entity Type | Primary Purpose | Required Surface Coverage |
|---|---|---|---|
| Elvis Costello Family | artistFamily | family rollup and member distribution | Artist Intelligence, Query Workbench |
| Neil Young Family | artistFamily | broad family identity and variant members | Artist Intelligence, Query Workbench |
| Grateful Dead Family | artistFamily | family amplification and side-project inclusion | Artist Intelligence, Query Workbench |
| Husker Du / Bob Mould / Sugar | artistFamily | family boundary and mojibake/alias handling | Artist Intelligence, Query Workbench, Music Library Admin |
| Diane song collision | song | same-title collision and artist-aware matching | Query Workbench |
| R.E.M. Green album variants | album | album variant normalization and canonical album identity | Artist Intelligence, Query Workbench, Music Library Admin |
| Recent Discovery vs Emerging Core Artist | artist | UI terminology separation | Music Intelligence, Query Workbench |
| Emerging Relationship hypothesis | artist | hypothesis-level signal treatment | Artist Intelligence, Query Workbench |
| Playlist World Score blocked case | playlist | blocked formula-backed playlist classification | Playlist Intelligence, Query Workbench |
| Dormant Relationship blocked case | artist | blocked dormancy classification | Music Intelligence, Artist Intelligence, Query Workbench |
| Return Signal blocked case | artist | blocked renewed-activity classification | Music Intelligence, Artist Intelligence, Query Workbench |
| Catalog Ecosystem hypothesis case | artist | catalog relationship hypothesis without accepted formula | Artist Intelligence, Query Workbench |

Rules:

- Each seed fixture must define expected confidence.
- Each seed fixture must define expected weakening factors.
- Each seed fixture must define forbidden outputs.
- Each seed fixture must define surface treatment.
- Blocked concepts must remain blocked unless the formula contract later promotes them.
- UI terminology fixtures must verify that labels do not overclaim.

---

## Emerging Terminology Fixtures

Emerging terminology requires explicit regression coverage because current UI/code uses emerging language differently from the formula contract.

Required checks:

- getEmergingArtists output must map to Recent Discovery unless stronger formula-backed evidence exists.
- Recent Discovery must not imply Emerging Core Artist.
- Emerging Relationship must remain hypothesis-level unless formula gates are accepted.
- Emerging Core Artist must remain blocked until Momentum Score, Friction Score, confidence model, and regression fixtures are accepted.

Forbidden outputs:

- Recent Discovery displayed as Core Artist.
- Recent Discovery displayed as Emerging Core Artist.
- Emerging Relationship displayed as settled durable relationship.
- Emerging Core Artist displayed as UI badge while blocked.


---

## Source Boundary Fixtures

Source boundary fixtures prove that no source is allowed to claim more than it actually contains.

Required source boundary cases:

| Case | Expected Behavior |
|---|---|
| library-only evidence | must not produce actual listening claim |
| playlist-only evidence | must not produce actual listening truth |
| live-only evidence | must not produce durable relationship claim |
| curated identity only | may resolve identity but must not prove behavior |
| derived output only | must trace back to evidence or facts |

Rules:

- Source-limited fixtures must reduce confidence or block the claim.
- Source-limited fixtures must name the limiting source boundary.
- Source-limited fixtures must define forbidden outputs.
- Source-limited fixtures must define expected UI surface treatment.

---

## Blocked Classification Fixtures

Blocked classification fixtures prove that future concepts remain blocked until formula gates are accepted.

Required blocked classifications:

- Emerging Core Artist
- Dormant Relationship
- Return Signal
- Catalog Ecosystem
- Playlist World Score
- Friction Score
- Momentum Score

Expected behavior:

- may appear as documentation concept.
- may appear as low-confidence hypothesis.
- may appear as open question.
- may appear as suggested investigation.
- must not appear as settled insight.
- must not appear as UI badge.
- must not appear as dashboard KPI.
- must not drive ranking or filtering.

Each blocked classification fixture must define:

- formula gate that blocks the claim.
- missing inputs.
- missing thresholds.
- missing confidence model.
- missing regression fixture coverage.
- expected blocked surface treatment.
- forbidden outputs.

---

## Identity Ambiguity Fixtures

Identity ambiguity fixtures prove that unresolved or ambiguous identity does not become false certainty.

Required identity ambiguity cases:

| Case | Expected Behavior |
|---|---|
| artist alias match | may resolve if alias is documented |
| mojibake variant | may resolve if normalized or explicitly mapped |
| same-title song collision | must require artist-aware matching |
| album variant collision | must require canonical album identity rules |
| family member ambiguity | must expose unresolved member or lower confidence |
| not found result | must not become relationship judgment |

Rules:

- Identity ambiguity must lower identity confidence or block the claim.
- Same-title songs must not be matched by title alone.
- Albums must not be canonicalized by title alone.
- Artist family rollups must expose included, excluded, and unresolved members.
- Not found must remain a source result, not proof that the relationship does not exist.

Required fixture outputs:

- expected identity status.
- expected identity confidence.
- expected identity warnings.
- expected forbidden matches.
- expected surface treatment.

---

## UI Surface Permission Fixtures

UI surface permission fixtures prove that each page shows only the claims it is allowed to show.

Required surface permission cases:

| Surface | Required Check |
|---|---|
| Music Intelligence | dashboard signals do not become settled relationship claims |
| Artist Intelligence | profile labels do not use blocked classifications |
| Query Workbench | hypotheses, insights, and blocked claims remain visually distinct |
| Playlist Intelligence | playlist placement does not become actual listening truth |
| Music Library Admin | admin/source issues do not become analytical claims |

Rules:

- Music Intelligence may show Recent Discoveries as signals.
- Music Intelligence must not show Emerging Core Artist as a badge while blocked.
- Artist Intelligence may show Emerging Relationship as hypothesis only.
- Artist Intelligence must keep blocked classifications out of the primary relationship label.
- Query Workbench may show blocked concepts only with blocked status and missing gate reasons.
- Playlist Intelligence must distinguish playlist membership from listening behavior.
- Music Library Admin must focus on source, identity, normalization, and data quality.

Required fixture outputs:

- expected surface.
- expected label.
- expected status.
- expected confidence.
- expected explanation.
- forbidden UI labels.
- required routing action.

---

## Fixture Record Template

Each concrete fixture should use this logical shape.

| Field | Purpose | Required |
|---|---|---|
| fixtureId | stable fixture identifier | yes |
| title | human-readable fixture name | yes |
| category | fixture category | yes |
| entityType | artist, artistFamily, song, album, playlist, date, or cohort | yes |
| query | query or entity input being tested | yes |
| canonicalKey | expected canonical identity key | yes when identity resolves |
| surface | UI surface being protected | yes |
| purpose | why this fixture exists | yes |
| sourceEvidenceRequired | evidence that must be present | yes |
| identityExpectation | expected identity result, warnings, and confidence | yes |
| expectedFacts | facts that should be derived | yes |
| expectedHypotheses | hypotheses that may be proposed | yes |
| expectedInsights | insights that may be shown | yes |
| expectedConfidence | expected confidence level and reason | yes |
| expectedWeakeningFactors | factors that lower confidence or block a claim | yes |
| expectedBlockedClaims | blocked claims and missing gates | yes when applicable |
| expectedSurfaceTreatment | how the surface should display the result | yes |
| forbiddenOutputs | labels, claims, or badges that must not appear | yes |
| notes | extra context | no |

Recommended fixture id format:

- music-fixture-artist-family-elvis-costello-v1
- music-fixture-song-diane-collision-v1
- music-fixture-ui-recent-discovery-vs-emerging-core-v1
- music-fixture-playlist-world-score-blocked-v1

---

## Fixture Completion Rules

A fixture is complete only when it answers:

- What input is being tested?
- What identity should resolve?
- What evidence must be present?
- What facts should be derived?
- What hypotheses are allowed?
- What insights are allowed?
- What confidence should be assigned?
- What weakening factors apply?
- What claims are blocked?
- What outputs are forbidden?
- What UI surface behavior is expected?

Rules:

- A fixture without forbidden outputs is incomplete.
- A fixture without expected confidence is incomplete.
- A fixture without source evidence expectations is incomplete.
- A blocked classification fixture must name the missing gate.
- A UI terminology fixture must name the safe display label.
- An identity ambiguity fixture must name the forbidden false match.

---

## Sprint 6C Exit Criteria

Sprint 6C is complete when:

- The regression fixture contract is documented.
- Seed fixtures are named.
- Fixture categories are defined.
- Fixture record shape is defined.
- Emerging terminology behavior is protected.
- Source boundary behavior is protected.
- Identity ambiguity behavior is protected.
- Blocked classification behavior is protected.
- UI surface permission behavior is protected.
- No UI implementation is started.
