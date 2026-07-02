# Music Investigation Packet Contract v1

## Status

Draft contract for Sprint 1.

No UI implementation should depend on this contract until it is reviewed and accepted.

---

## Purpose

A Music Investigation Packet is the canonical output shape for a music investigation.

It should allow Query Workbench to produce a complete, inspectable answer and allow Artist Intelligence to consume the same evidence model later.

The packet exists to preserve this chain:

Question -> Entity -> Identity -> Evidence -> Facts -> Hypotheses -> Insights -> Reasoning Trace -> Open Questions -> Suggested Investigations -> Confidence

---

## Primary Consumers

### Query Workbench

Query Workbench should render the packet as an investigation cockpit.

Responsibilities:

- Show the full reasoning path.
- Expose source-backed evidence.
- Show deterministic facts.
- Show hypotheses and insights.
- Surface uncertainty and next investigations.
- Make provenance inspectable.

### Artist Intelligence

Artist Intelligence may consume the same packet shape, but should render it as a polished profile.

Responsibilities:

- Emphasize stable relationship interpretation.
- Hide low-level debugging unless expanded.
- Preserve evidence, confidence, and provenance.
- Link back to Query Workbench for inspection.

---

## Top-Level Shape

Current observed packet fields:

- question
- entity
- identity
- evidence
- facts
- hypotheses
- insights
- reasoningTrace
- openQuestions
- suggestedInvestigations
- confidence

Required top-level fields:

- question
- entity
- identity
- evidence
- facts
- hypotheses
- insights
- reasoningTrace
- openQuestions
- suggestedInvestigations
- confidence

No top-level narrative field should be required.

Narrative should be derived from evidence, facts, hypotheses, insights, and reasoning trace.

---

## question

Purpose: capture what was asked and how the system interpreted the request.

Required fields:

- originalQuery
- normalizedQuery
- investigationType

Recommended fields:

- requestedEntityType
- requestedScope
- generatedAt

---

## entity

Purpose: declare the resolved entity being investigated.

Required fields:

- type
- displayName
- canonicalKey

Recommended fields:

- sourceEntityIds
- primaryDisplayName
- entityVersion

Allowed initial entity types:

- artist
- artistFamily
- song
- album
- playlist
- date
- cohort

---

## identity

Purpose: expose identity resolution and matching context.

Required fields:

- resolvedName
- canonicalKey
- matchConfidence
- notes

Recommended fields:

- aliases
- familyName
- familyMembers
- matchedSourceNames
- unresolvedNames
- identityWarnings

Identity must make uncertainty explicit.

---

## evidence

Purpose: hold source-backed measurements.

Each evidence item must be independently inspectable.

Required fields per evidence item:

- id
- label
- source
- sourceType
- value
- confidence
- provenance

Recommended fields per evidence item:

- metricType
- freshness
- dateRange
- unit
- calculation
- sourcePath
- sourceColumns
- limitations

Allowed metric types:

- actualListeningMetric
- libraryEvidenceMetric
- playlistPlacementMetric
- liveSignal
- curatedIdentityMetric
- derivedMetric

Evidence rules:

- Actual plays must remain separate from library evidence records.
- Playlist placement must not be treated as listening truth.
- Live objects must include freshness where available.
- Derived metrics must identify their source evidence.

---

## facts

Purpose: represent deterministic statements derived from evidence.

Facts are reproducible and should not be speculative.

Required fields per fact:

- id
- factType
- statement
- sourceEvidenceIds

Recommended fields:

- value
- unit
- confidence
- derivation

Allowed initial fact types:

- count
- duration
- timeline
- identity
- sourceAvailability
- sourceLimitation
- relationship
- comparison

Fact rules:

- Facts must cite evidence IDs.
- Facts should not introduce unsupported claims.
- Facts should be terse.

---

## hypotheses

Purpose: represent provisional interpretive claims.

Hypotheses are allowed to be uncertain, but must show support and opposition.

Required fields per hypothesis:

- id
- claim
- confidence
- rationale
- supportingFactIds
- opposingFactIds

Recommended fields:

- status
- ruleIds
- counterEvidence
- nextValidationStep

Allowed statuses:

- proposed
- supported
- weakened
- rejected
- needsReview

Hypothesis rules:

- No hypothesis without supporting facts.
- Medium or low confidence hypotheses should expose next validation steps.
- Opposing fact IDs may be empty, but the field should exist.

---

## insights

Purpose: represent user-facing conclusions derived from facts and hypotheses.

Required fields per insight:

- id
- type
- summary
- confidence
- sourceHypothesisIds
- sourceFactIds

Recommended fields:

- severity
- reason
- displayPriority
- nextAction

Insight rules:

- No insight without provenance.
- No insight should be purely narrative.
- Every insight should be reproducible from facts, hypotheses, and reasoning trace.

---

## reasoningTrace

Purpose: expose the chain that produced an insight or hypothesis.

Required fields per trace item:

- id
- targetId
- steps
- confidence
- rulesApplied

Recommended fields:

- evidenceIds
- factIds
- hypothesisIds
- limitations

Reasoning trace rule:

Evidence -> Facts -> Hypothesis -> Insight -> Confidence -> Rules Applied

---

## openQuestions

Purpose: expose uncertainty raised by the system.

Required fields per question:

- id
- question
- reason
- relatedEntityIds
- priority

Recommended fields:

- sourceEvidenceIds
- sourceFactIds
- suggestedInvestigationIds

Allowed priorities:

- high
- medium
- low

Open questions should be system-generated, not merely copied from the user.

---

## suggestedInvestigations

Purpose: route the user to the next useful investigation.

Required fields per suggestion:

- id
- label
- targetSurface
- reason

Recommended fields:

- query
- entityType
- canonicalKey
- priority
- requiredData

Allowed target surfaces:

- Query Workbench
- Artist Intelligence
- Playlist Intelligence
- Music Dashboard
- Music Library Admin

---

## confidence

Purpose: summarize packet-level confidence.

Required fields:

- overall
- identity
- evidence
- interpretation

Recommended fields:

- freshness
- limitations
- confidenceReasons

Allowed confidence values:

- high
- medium
- low
- notFound

Packet-level confidence must not hide section-level uncertainty.

---

## Provenance Requirements

Every packet must expose:

1. Entity identity
2. Metric type
3. Data source
4. Confidence/freshness
5. Next investigation path

Minimum source metadata where available:

- source
- sourceType
- generatedAt
- snapshotId
- latestPlayed
- latestSeen
- dateRange
- sourcePath
- sourceColumns

---

## Non-Goals

This contract does not define UI layout.

This contract does not define Friction, Momentum, Emerging Core Artist, Dormant Relationship, Return Signal, or Catalog Ecosystem formulas.

This contract does not require source dataset rewrites.

This contract does not require every packet consumer to display every field by default.

---

## Acceptance Criteria

This contract is accepted when:

- The example Elvis Costello Family packet can be mapped to this contract.
- Required fields are documented.
- Optional fields are clearly separated from required fields.
- Provenance requirements are explicit.
- Query Workbench and Artist Intelligence responsibilities are distinct.
- Derived intelligence remains blocked until formula docs exist.
