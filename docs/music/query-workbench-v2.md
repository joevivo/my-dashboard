# Query Workbench v2

## Purpose

Query Workbench v2 should reveal the system's reasoning path:

Identity → Evidence → Facts → Insights → Next Investigations

The Workbench should not simply return results. It should help decide what to investigate next.

## Core Principle

A query result should answer:

1. What did the system resolve?
2. What evidence supports it?
3. What facts can be derived?
4. What insights are suggested?
5. What should the user explore next?

## Primary Sections

### 1. Query Header

Shows resolution and identity context.

Fields:
- Original query
- Resolved artist
- Canonical key
- Match rank
- Relationship/family name
- Relationship type

### 2. Evidence Panel

Shows source-backed measurements.

Fields:
- Actual plays
- Actual skips
- Hours listened
- Library evidence records
- Years active
- First played
- Latest played
- Top songs
- Top albums
- Timeline

### 3. Relationship Panel

Shown when the artist belongs to a family or career relationship.

Fields:
- Family name
- Primary artist
- Relationship type
- Family actual plays
- Family amplification factor
- Family years active
- Members matched
- Member distribution

### 4. Facts Panel

Shows deterministic facts from the Fact Engine.

Examples:
- Has play history
- Has library evidence
- Has family
- Reviewed standalone
- Unclassified
- Long-running
- High-volume
- High-evidence
- Needs review

Facts should be terse and reproducible.

### 5. Insights Panel

Shows inferred observations from the Insight Engine.

Examples:
- Permanent companion candidate
- Persistent catalog presence
- Known relationship
- Needs artist review
- Collection-only artist

Each insight should include:
- Type
- Severity
- Summary
- Reason

### 5A. Reasoning Trace

Every insight should expose the chain of reasoning that produced it.

Example:

Evidence

- 1,927 actual plays
- 14 active years
- 198 library evidence records

?

Facts

- High volume
- Long-running
- High evidence

?

Insight

Permanent Companion Candidate

?

Confidence

High

?

Rules Applied

PERMANENT_COMPANION_V1

Reasoning Trace extends provenance beyond source data to the logic that produced an insight.

### 6. Compare Panel

Suggests useful comparisons.

Examples:
- Compare with family members
- Compare with similar high-volume artists
- Compare with similar long-running artists
- Compare with unresolved artists

Initial version can use hardcoded suggestions.

### 7. Suggested Questions

The Workbench should offer next investigative paths.

Examples:
- How does this artist compare to its family members?
- Which artists have similar persistence?
- Which unresolved artists look most important?
- Show this artist's timeline.
- Show similar catalog-presence artists.
- Is this artist part of a missing family?

### 8. Open Questions

The system should expose uncertainty.

Open Questions are questions raised by the system, not the user.

Examples:

- Should Camper Van Beethoven belong to the Cracker Family?
- This artist has unusually high amplification.
- Timeline contains a large listening gap.
- Identity confidence is only medium.
- Similar artists disagree with current classification.

The Workbench should be able to say:

> Here is what I know, here is why I believe it, and here is what I am still unsure about.

## Product Direction

Query Workbench v2 should become an investigation cockpit.

Current model:

Search → Result

Target model:

Question → Evidence → Facts → Insights → Suggested next paths

## Implementation Phases

### Phase 1: Identity and Relationship Surface

Expose existing backend fields:
- canonical identity
- family
- relationship type
- family metrics
- amplification factor

### Phase 2: Facts and Insights

Consume generated Artist Universe, Fact Engine, and Insight Engine outputs.

### Phase 3: Suggested Questions

Add hardcoded next-question prompts based on available facts and insights.

### Phase 4: Comparative Intelligence

Build comparison endpoints and UI sections.

### Phase 5: Hypothesis Layer

Allow the system to propose unresolved relationships, anomalies, and investigations.

## Broader Intelligence Pipeline

The Query Workbench v2 model suggests a reusable intelligence pipeline:

Data Sources
?
Normalization
?
Identity Resolution
?
Universe
?
Facts
?
Insights
?
Reasoning Trace
?
Open Questions
?
Suggested Investigations

This pipeline is not limited to music. The same pattern can apply to books, playlists, albums, calendar events, notes, sports data, finance data, or other Defending Sisyphus domains.

## Design Rule

Every displayed insight must be traceable back to evidence.

No opaque conclusions.
No unexplained recommendations.
No narrative without provenance.
