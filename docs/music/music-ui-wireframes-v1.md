# Music UI Wireframes v1

## Status

Draft visual planning document for Sprint 6B.

This is a low-fidelity wireframe and page-model document.

No UI implementation is started by this document.

---

## Purpose

This document translates the Music UI Surface Model into visual page layouts before UI readiness mapping begins.

It defines low-fidelity page models for:

- Music Intelligence
- Artist Intelligence
- Query Workbench
- Playlist Intelligence
- Music Library Admin
- Navigation flow

Core rule:

Wireframes must show where claims, signals, confidence, blocked concepts, and investigation actions appear before React implementation begins.

---

## Wireframe Principles

- Show page responsibility before component detail.
- Separate dashboard signals from profile claims.
- Separate facts from hypotheses.
- Show confidence and blocked status near the claim.
- Make every investigation path visible.
- Avoid implying unsupported formula-backed classifications.
- Keep visuals low-fidelity until UI readiness mapping is accepted.

---

## Page Inventory

| Page | Wireframe Purpose | Implementation Status |
|---|---|---|
| Music Intelligence | Dashboard triage and signal routing | planning only |
| Artist Intelligence | Durable artist or family profile | planning only |
| Query Workbench | Evidence-to-insight investigation cockpit | planning only |
| Playlist Intelligence | Playlist and cohort relationship analysis | planning only |
| Music Library Admin | Source, identity, normalization, and data-quality management | planning only |

---

## Wireframe 1: Music Intelligence Dashboard

Purpose:

- Show what changed.
- Show what matters.
- Route unresolved claims into investigation.
- Avoid presenting blocked classifications as settled truth.

Layout:

VISUAL:

Header:
- Page title: Music Intelligence
- Subtitle: What changed, what matters, what needs investigation?
- Source freshness indicator
- Link to Music Library Admin when source warnings exist

Top row summary cards:
- Current Listening
- Long-Term Memory
- Data Health
- Investigation Queue Count

Signal row:
- Recent Discoveries
- Return Candidates
- Dormant Candidates
- Heavy Rotation / Live Signals

Relationship row:
- Core Relationships
- Artist Families
- Catalog Worlds
- Album or Song Anchors

Investigation queue:
- Priority
- Entity
- Signal
- Why it matters
- Source boundary
- Confidence
- Action

Primary actions:
- Open in Query Workbench
- Open Artist Intelligence
- Open Playlist Intelligence
- Review source or identity warning

Blocked-status treatment:
- Emerging Core Artist: blocked until formula accepted
- Dormant Relationship: blocked until formula accepted
- Return Signal: blocked until formula accepted
- Playlist World Score: blocked until formula accepted

Notes:

- Recent Discoveries are UI-safe if they only mean first active recently plus enough listening evidence.
- Emerging Relationship is hypothesis-level.
- Emerging Core Artist must not appear as a dashboard badge yet.

---

## Wireframe 2: Artist Intelligence Profile

Purpose:

- Present a durable artist or artist-family relationship.
- Show identity, evidence, confidence, and uncertainty together.
- Avoid turning hypothesis-level signals into permanent labels.

Layout:

VISUAL:

Header:
- Artist or family display name
- Canonical key
- Resolved family, when applicable
- Primary relationship label
- Overall confidence
- Identity warnings

Metric row:
- Actual Plays
- Hours Listened
- Years Active
- Latest Activity
- Source Confidence

Relationship summary:
- Short narrative relationship claim
- Claim confidence
- Why this relationship matters
- What could weaken the claim

Evidence panels:
- Actual listening evidence
- Library evidence
- Playlist placement evidence
- Live or recent evidence

Catalog panels:
- Top albums
- Album relationship shape
- Top songs
- Song anchors or collisions

Signal panel:
- Recent Discovery status
- Emerging Relationship status
- Emerging Core Artist blocked status
- Dormant Relationship status
- Return Signal status
- Catalog Ecosystem status

Reasoning panel:
- Evidence
- Facts
- Hypotheses
- Insights
- Confidence
- Open questions

Primary actions:
- Open full packet in Query Workbench
- Compare similar artists
- Inspect albums
- Inspect playlists
- Review identity/source warning

Blocked-status treatment:
- Blocked concepts appear as blocked notices or hypotheses only.
- Blocked concepts do not appear in the primary relationship label.
- Confidence must sit near any relationship claim.

---

## Wireframe 3: Query Workbench Investigation Cockpit

Purpose:

- Render the investigation packet.
- Show the full reasoning path.
- Keep facts, hypotheses, insights, and blocked classifications separate.
- Provide the clearest path from question to next investigation.

Layout:

VISUAL:

Query header:
- Original query
- Resolved entity
- Entity type
- Investigation type
- Confidence
- Open related profile

Identity panel:
- Resolved artist, album, song, playlist, family, or date
- Canonical key
- Aliases
- Matched source names
- Identity warnings
- Family membership, when applicable

Evidence panel:
- Source family
- Metric type
- Value
- Date range
- Provenance
- Source confidence
- Source limitation

Facts panel:
- Deterministic facts derived from evidence
- Each fact cites source evidence IDs
- Facts do not contain interpretation

Hypotheses panel:
- Possible interpretations
- Supporting facts
- Opposing facts
- Weakening factors
- Confidence
- Next validation step

Insights panel:
- Safe conclusions only
- Insight confidence
- Source fact IDs
- Source hypothesis IDs
- Blocked or accepted status where relevant

Reasoning trace panel:
- Identity resolution
- Evidence collection
- Fact derivation
- Hypothesis evaluation
- Insight derivation
- Confidence assignment
- Rules applied

Next investigations panel:
- Open questions
- Suggested follow-up queries
- Target surface
- Why the investigation matters

Primary actions:
- Open Artist Intelligence
- Open Playlist Intelligence
- Inspect source evidence
- Create regression fixture candidate
- Flag identity or source issue

Blocked-status treatment:
- Blocked classifications may appear as hypotheses only.
- Workbench may show why a classification is blocked.
- Workbench must not promote blocked classifications into settled insights.

---

## Wireframe 4: Playlist Intelligence

Purpose:

- Explain playlist and cohort relationship patterns.
- Distinguish intentional placement from listening behavior.
- Surface bridge artists, exclusive artists, shared cores, and playlist-world candidates.
- Avoid treating playlist membership as actual listening truth.

Layout:

VISUAL:

Header:
- Playlist or cohort name
- Playlist classification
- Track count
- Artist count
- Source confidence
- Playlist freshness

Summary cards:
- Total songs
- Distinct artists
- Distinct albums
- Actual listening overlap, when available
- Exclusivity
- Shared core count

Relationship panels:
- Foundational artists
- Bridge artists
- Exclusive artists
- Shared core artists
- Playlist-world candidates

Evidence panels:
- Playlist membership evidence
- Actual listening overlap evidence
- Library evidence overlap
- Source limitations

Blocked-status treatment:
- Playlist World Score remains blocked until formula accepted.
- Playlist classification must not imply actual listening truth.
- Generated playlists require explicit treatment.

Primary actions:
- Open artist in Query Workbench
- Open Artist Intelligence
- Compare playlists
- Create regression fixture candidate

---

## Wireframe 5: Music Library Admin

Purpose:

- Manage source, identity, normalization, and data-quality concerns.
- Keep admin/data-cleanup tasks out of the main analytical dashboard.
- Provide a home for mojibake, aliases, album variants, source freshness, and unresolved mappings.

Layout:

VISUAL:

Header:
- Music Library Admin
- Source freshness status
- Last snapshot timestamp
- Active source warnings

Source panels:
- Apple Music daily summary
- Apple Music Library Tracks
- Apple Music Library Playlists
- DuckDB listening context
- Apple Music live endpoints
- Curated identity seeds
- Album normalization seeds

Data quality queues:
- Mojibake candidates
- Unresolved artist aliases
- Unresolved family members
- Album variant review
- Same-title song collisions
- Source-limited records

Admin actions:
- Review identity mapping
- Review album variant
- Inspect source provenance
- Mark fixture candidate
- Document source limitation

Not allowed:
- Relationship classification as primary output.
- Dashboard-style insight ranking.
- Formula-backed claims.
- UI badges for blocked classifications.

---

## Navigation Flow

Purpose:

- Show how users move from broad signal to explanation to cleanup.
- Keep the dashboard from becoming the explanation surface.
- Keep admin/source work out of profile pages unless explicitly needed.

VISUAL:

Music Intelligence
- starts with signal, summary, freshness, and investigation queue
- routes questions to Query Workbench

Query Workbench
- validates identity, evidence, facts, hypotheses, and insights
- routes durable entities to Artist Intelligence
- routes playlist questions to Playlist Intelligence
- routes data-quality issues to Music Library Admin

Artist Intelligence
- presents durable profile only after relationship context is understood
- links back to Query Workbench for full reasoning trace

Playlist Intelligence
- explains playlist/cohort relationship patterns
- links to Query Workbench for artist-specific investigations

Music Library Admin
- resolves source, identity, normalization, and quality issues
- returns cleaned context to Query Workbench or profile surfaces

---

## Badge and Status Treatment

Purpose:

- Make claim strength visible.
- Avoid overclaiming blocked formula-backed concepts.
- Keep UI language aligned with contracts.

Allowed status labels:

- fact-backed
- hypothesis
- blocked
- accepted
- productionEligible
- source-limited
- identity-warning
- needs-review

Status placement rules:

- Status must appear near the claim it qualifies.
- Blocked status must explain what is missing.
- Hypothesis status must show supporting facts or route to Query Workbench.
- Source-limited status must name the source boundary.
- Identity-warning status must route to identity or admin review.

Emerging treatment:

- Recent Discovery may appear as a dashboard signal.
- Emerging Relationship may appear as a hypothesis.
- Emerging Core Artist must appear only as blocked until formulas and fixtures are accepted.

---

## First Implementation Slice Candidate

This wireframe document does not start UI implementation, but it identifies a likely first UI slice.

Candidate:

- Music Intelligence dashboard cleanup.

Likely changes:

- Rename current Emerging Artists output to Recent Discoveries.
- Add blocked/hypothesis status treatment.
- Add source freshness and data-health placement.
- Route Recent Discoveries into Query Workbench.
- Avoid Emerging Core Artist badges.
- Keep formula-backed classifications hidden or blocked until accepted.

Implementation remains blocked until UI readiness mapping is accepted.

---

## Non-Goals

This document does not implement React components.

This document does not alter labels in current code.

This document does not define formulas.

This document does not create regression fixtures.

This document does not promote blocked classifications.

---

## Acceptance Criteria

This document is accepted when:

- Music Intelligence dashboard wireframe exists.
- Artist Intelligence profile wireframe exists.
- Query Workbench wireframe exists.
- Playlist Intelligence wireframe exists.
- Music Library Admin wireframe exists.
- Navigation flow is documented.
- Badge and status treatment is documented.
- Recent Discovery, Emerging Relationship, and Emerging Core Artist placement is visible.
- No UI implementation is started.
