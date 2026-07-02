# Music Facts, Insights, and Reasoning Trace Contract v1

## Status

Draft contract for Sprint 4.

No UI implementation should depend on this contract until it is reviewed and accepted.

---

## Purpose

This contract defines how Defending Sisyphus Music turns source-backed evidence into deterministic facts, supported hypotheses, user-facing insights, reasoning traces, open questions, and suggested investigations.

Core chain:

Evidence -> Facts -> Hypotheses -> Insights -> Confidence -> Rules Applied

Core rule:

No insight without traceable evidence.

---

## Relationship to Prior Contracts

This contract depends on:

- Music phase requirements checklist v1
- Music investigation packet contract v1
- Music source and provenance registry v1
- Music identity contract v1

Required ordering:

Identity -> Evidence -> Facts -> Hypotheses -> Insights -> Reasoning Trace -> Open Questions -> Suggested Investigations -> Confidence

Facts and insights must not bypass identity, source boundaries, or provenance.

---

## Investigation Output Layers

Canonical investigation output layers:

- evidence
- facts
- hypotheses
- insights
- reasoningTrace
- openQuestions
- suggestedInvestigations
- confidence

Each layer must be machine-checkable and inspectable.

---

## Evidence

Evidence is source-backed measurement or source-backed context.

Evidence is governed by the source/provenance registry.

Required evidence fields are defined in the investigation packet contract.

Evidence can support facts.

Evidence cannot directly produce insights without intermediate facts or documented reasoning.

Evidence must expose:

- source
- sourceType
- metricType
- value
- confidence
- provenance

Evidence rules:

- Evidence must come from an allowed source family.
- Evidence must use an allowed metric type.
- Evidence must not be treated as proving claims outside its source boundary.
- Evidence IDs must be stable within a packet.

---

## Facts

Facts are deterministic statements derived from evidence.

Facts are reproducible.

Facts are not speculative.

Required fact fields:

- id
- factType
- statement
- sourceEvidenceIds
- confidence

Recommended fact fields:

- value
- unit
- derivation
- entityRef
- dateRange
- sourceMetricTypes

Allowed initial fact types:

- count
- duration
- timeline
- identity
- sourceAvailability
- sourceLimitation
- relationship
- comparison
- distribution
- freshness
- placement
- context

Fact rules:

- Every fact must cite at least one sourceEvidenceId.
- A fact must not introduce unsupported claims.
- A fact should be terse.
- A fact should be suitable for display, audit, or downstream reasoning.
- Facts may aggregate evidence only when aggregation rules are documented.

Invalid fact examples:

- This artist is important.
- This album is a favorite.
- This is an Emerging Core Artist.

Valid fact examples:

- The artist has 1,056 actual plays in the selected scope.
- The family has activity across 14 years.
- The playlist contains 453 songs.
- The live snapshot was generated at a known timestamp.

---

## Hypotheses

Hypotheses are tentative interpretations supported by facts.

Hypotheses may be uncertain, but uncertainty must be explicit.

Required hypothesis fields:

- id
- claim
- confidence
- rationale
- supportingFactIds
- opposingFactIds

Recommended hypothesis fields:

- status
- ruleIds
- counterEvidence
- nextValidationStep
- limitations
- entityRef

Allowed hypothesis statuses:

- proposed
- supported
- weakened
- rejected
- needsReview

Hypothesis rules:

- No hypothesis without supporting facts.
- opposingFactIds must exist, even when empty.
- Medium or low confidence hypotheses must expose nextValidationStep.
- Hypotheses must not be rendered as settled conclusions.
- Hypotheses may be promoted only when formula and confidence rules exist.

Invalid hypothesis examples:

- The user loves this artist.
- This is a core artist because it feels right.

Valid hypothesis examples:

- This artist may represent a durable relationship because actual plays span more than ten years and recent evidence exists.
- This album may be a catalog anchor because canonical album events are high and distributed across multiple years.

---

## Insights

Insights are user-facing conclusions derived from facts and hypotheses.

Insights must be explainable.

Insights must be reproducible from packet data.

Required insight fields:

- id
- type
- summary
- confidence
- sourceHypothesisIds
- sourceFactIds

Recommended insight fields:

- severity
- reason
- displayPriority
- nextAction
- limitations
- entityRef
- ruleIds

Allowed initial insight types:

- relationshipSummary
- sourceLimitation
- identityWarning
- freshnessSignal
- playlistPlacementSignal
- contextSignal
- comparisonSignal
- investigationPrompt
- dataQualityIssue

Insight rules:

- No insight without provenance.
- No insight should be purely narrative.
- Every insight must cite sourceFactIds.
- Every interpretive insight should cite sourceHypothesisIds unless it is a direct source limitation or data-quality issue.
- Insights must not hide low or medium confidence.
- Insights must not claim formula-backed classifications until formula contracts exist.

Blocked insight types until formula contracts exist:

- Emerging Core Artist
- Dormant Relationship
- Return Signal
- Friction Score
- Momentum Score
- Catalog Ecosystem classification
- Playlist World Score classification

---

## Reasoning Trace

Reasoning trace exposes the chain that produced a hypothesis or insight.

Required reasoning trace fields:

- id
- targetId
- steps
- confidence
- rulesApplied

Recommended reasoning trace fields:

- evidenceIds
- factIds
- hypothesisIds
- insightIds
- limitations
- identityWarnings
- sourceWarnings

Each reasoning trace step should expose:

- stepNumber
- operation
- inputIds
- outputId
- explanation
- confidenceImpact

Allowed operations:

- resolveIdentity
- collectEvidence
- deriveFact
- compareFact
- evaluateHypothesis
- deriveInsight
- assignConfidence
- identifyLimitation
- suggestInvestigation

Reasoning trace rules:

- Every user-facing insight must have a target reasoning trace.
- Reasoning traces must identify rulesApplied.
- Reasoning traces must identify confidence reductions.
- Reasoning traces must identify source or identity limitations.
- Reasoning traces should be concise but auditable.

---

## Rules Applied

Rules applied are named logic units used by the reasoning trace.

Required rule fields:

- id
- name
- description
- inputTypes
- outputTypes
- confidenceEffect

Initial rule families:

- identityResolutionRule
- sourceBoundaryRule
- evidenceToFactRule
- factComparisonRule
- hypothesisSupportRule
- insightDerivationRule
- confidenceAdjustmentRule
- nextInvestigationRule

Rule requirements:

- Every rule must describe what it can and cannot conclude.
- Every derived metric rule must identify required source evidence.
- Every confidence adjustment rule must identify what lowers confidence.
- Formula-backed rules require separate formula documentation before production use.

---

## Open Questions

Open questions identify meaningful uncertainty discovered by the system.

Open questions are system-generated.

They are not merely copied from the user query.

Required open question fields:

- id
- question
- reason
- relatedEntityIds
- priority

Recommended open question fields:

- sourceEvidenceIds
- sourceFactIds
- sourceHypothesisIds
- suggestedInvestigationIds
- blockingStatus

Allowed priority values:

- high
- medium
- low

Open question rules:

- High-priority questions should block strong insights.
- Medium-priority questions may lower confidence.
- Low-priority questions may become suggested follow-ups.
- Open questions should be specific enough to drive the next investigation.

---

## Suggested Investigations

Suggested investigations are concrete next paths for the user or system.

Required suggested investigation fields:

- id
- label
- targetSurface
- reason

Recommended suggested investigation fields:

- query
- entityType
- canonicalKey
- priority
- requiredData
- blockedBy

Allowed target surfaces:

- Query Workbench
- Artist Intelligence
- Playlist Intelligence
- Music Dashboard
- Music Library Admin

Suggested investigation rules:

- Suggestions must explain why they are recommended.
- Suggestions should connect to facts, hypotheses, insights, or open questions.
- Suggestions must not imply a conclusion before the next investigation runs.
- Suggestions should prefer the surface best suited to the question.

---

## Confidence

Confidence summarizes trust in identity, evidence, and interpretation.

Required confidence dimensions:

- overall
- identity
- evidence
- interpretation

Recommended confidence dimensions:

- freshness
- sourceCoverage
- formulaReadiness
- limitations
- confidenceReasons

Allowed confidence values:

- high
- medium
- low
- notFound

Confidence rules:

- Packet-level confidence must not hide section-level uncertainty.
- Identity confidence can lower fact, hypothesis, and insight confidence.
- Source limitations can lower interpretation confidence.
- Missing formula documentation blocks formula-backed classifications.
- Live-only evidence cannot produce durable relationship confidence by itself.
- Library-only evidence cannot produce actual listening confidence by itself.
- Playlist-only evidence cannot produce listening truth by itself.

---

## Derived Metrics and Classifications

Derived metrics and classifications require formula contracts before production use.

A derived metric must define:

- name
- purpose
- required inputs
- allowed source families
- calculation
- confidence model
- limitations
- examples
- regression fixtures

Blocked until documented:

- Friction Score
- Momentum Score
- Emerging Core Artist
- Dormant Relationship
- Return Signal
- Catalog Ecosystem
- Playlist World Score

Derived classification rules:

- A blocked classification may appear as a hypothesis only if clearly labeled.
- A blocked classification must not appear as a settled insight.
- A blocked classification must include nextValidationStep.

---

## Packet Mapping

The investigation packet contract already defines top-level sections for:

- facts
- hypotheses
- insights
- reasoningTrace
- openQuestions
- suggestedInvestigations
- confidence

This contract defines the behavioral rules for those sections.

A valid packet must allow a reviewer to move backward from insight to hypothesis to fact to evidence.

---

## Non-Goals

This contract does not implement a Fact Engine.

This contract does not implement an Insight Engine.

This contract does not implement formula-backed classifications.

This contract does not alter source datasets.

This contract does not alter curated identity seeds.

This contract does not start UI work.

---

## Acceptance Criteria

This contract is accepted when:

- Facts are defined as deterministic and evidence-backed.
- Hypotheses are defined as supported but uncertain interpretations.
- Insights are defined as user-facing conclusions with provenance.
- Reasoning trace requirements are explicit.
- Open questions and suggested investigations are differentiated.
- Confidence rules are explicit.
- Derived formula-backed classifications remain blocked until formula contracts exist.
- The contract aligns with the investigation packet contract.
- Source and identity boundaries are preserved.
- No UI implementation is started.
