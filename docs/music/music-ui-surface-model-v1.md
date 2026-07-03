# Music UI Surface Model v1

## Status

Draft contract for Sprint 6A.

This is a planning and terminology document only.

No UI implementation is started by this document.

---

## Purpose

This document defines the intended Music UI surface model before detailed UI readiness mapping begins.

Core rule:

The dashboard shows what to investigate. The artist page shows the relationship. The workbench explains the reasoning.

---

## Surface Model Summary

| Surface | Primary Role | Output Type |
|---|---|---|
| Music Intelligence | Triage dashboard | Signals, queues, summaries |
| Artist Intelligence | Durable profile | Relationship explanation |
| Query Workbench | Investigation cockpit | Evidence, facts, hypotheses, trace |
| Playlist Intelligence | Playlist/cohort analysis | Playlist placement and cohort relationships |
| Music Library Admin | Data management | Source, identity, normalization, quality controls |

---

## Visual 1: Overall Music Intelligence Model

VISUAL:

Music Intelligence
What changed? What matters? What needs investigation?

[Current Listening]     [Long-Term Memory]      [Data Health]
recent plays            core relationships      source freshness
heavy rotation          durable families        identity warnings
live snapshots          catalog worlds          mojibake / gaps

[Signals]
Recent Discoveries      Return Candidates       Dormant Candidates
newly visible artists   active again            meaningful but quiet

[Relationship Map]
Core Relationships      Catalog Worlds          Album/Song Anchors
durable artists         broad album depth       carried by key works

[Investigation Queue]
- Explain this recent discovery
- Validate this family relationship
- Check playlist-only evidence
- Resolve identity/source warnings

---

## Music Intelligence Page

Music Intelligence is a triage dashboard.

It should answer:

- What changed recently?
- What looks important?
- What looks stale or dormant?
- What looks suspicious?
- Where should I click next?

Allowed:

- Recent activity summaries.
- Recent Discoveries.
- source freshness.
- identity warnings.
- investigation queues.
- known relationship summaries.
- blocked concept notices.
- links into Query Workbench, Artist Intelligence, Playlist Intelligence, or Music Library Admin.

Not allowed:

- formula-backed classifications unless accepted or productionEligible.
- Emerging Core Artist badges while formula status is blocked.
- durable relationship claims from live-only evidence.
- actual listening claims from library-only or playlist-only evidence.
- confidence-free classifications.

---

## Visual 2: Music Intelligence Dashboard Layout

VISUAL:

Header:
- Music Intelligence
- What changed, what matters, what needs investigation?
- Freshness / source status

Top summary cards:
- Recent Plays
- Heavy Rotation
- Long Memory
- Data Health

Signal cards:
- Recent Discoveries
- Return Candidates
- Dormant Candidates

Relationship summary:
- Core Artists
- Artist Families
- Catalog Worlds

Investigation queue:
- Priority
- Entity
- Reason
- Source Boundary
- Open in Workbench

---

## Artist Intelligence Page

Artist Intelligence is a durable artist or artist-family profile.

It should answer:

- Who is this artist or family?
- What is the listener relationship?
- What evidence supports that relationship?
- What albums, songs, playlists, and time periods matter?
- What is uncertain?

Allowed:

- identity resolution.
- family membership.
- actual listening metrics.
- library evidence metrics.
- playlist placement evidence.
- relationship summary.
- source confidence.
- signal badges when supported.
- reasoning trace summary.
- open questions.

Not allowed:

- blocked derived classifications as settled profile labels.
- Emerging Core Artist unless formula readiness is accepted or productionEligible.
- Catalog Ecosystem as settled unless formula readiness is accepted or productionEligible.
- unqualified relationship labels without confidence.

---

## Visual 3: Artist Intelligence Profile Layout

VISUAL:

Artist profile header:
- Artist name
- Resolved family, when applicable
- Relationship label
- Confidence
- Identity warnings

Metric cards:
- Actual Plays
- Hours
- Years Active
- Source Confidence

Relationship summary:
- Narrative claim backed by evidence, facts, and confidence.

Detail panels:
- Albums
- Songs
- Playlists
- Timeline

Signals:
- Recent Discovery
- Emerging Relationship
- Emerging Core Artist blocked status
- Catalog Ecosystem status

Reasoning trace:
- Evidence
- Facts
- Hypotheses
- Insights
- Confidence

---

## Query Workbench

Query Workbench is the investigation cockpit.

It should answer:

- What did the system resolve?
- What evidence was found?
- What facts were derived?
- What hypotheses are proposed?
- What insights are safe?
- What should be investigated next?

Allowed:

- evidence.
- facts.
- hypotheses.
- blocked classifications.
- reasoning trace.
- open questions.
- suggested investigations.
- confidence reductions.

Not allowed:

- converting blocked hypotheses into settled insights.
- hiding source limitations.
- hiding identity warnings.

---

## Visual 4: Query Workbench Investigation Layout

VISUAL:

Query header:
- original query
- resolved entity
- investigation type

Identity:
- resolved artist, song, album, family, aliases, warnings

Evidence:
- source rows
- source families
- confidence
- provenance

Facts:
- deterministic claims derived from evidence

Hypotheses:
- possible relationship interpretations
- weakening factors

Insights:
- safe conclusions only

Reasoning trace:
- Evidence -> Facts -> Hypothesis -> Insight -> Confidence

Next investigations:
- suggested follow-up queries
- unresolved questions

---

## Emerging Terminology Map

Current code and UI use emerging language in at least two ways:

| Current Surface | Current Term |
|---|---|
| Artist Intelligence | Emerging Relationship |
| musicIntelligence utility | getEmergingArtists |

This creates a terminology gap because current docs define Emerging Core Artist as a blocked future classification.

Recommended terms:

| Term | Meaning | Surface | Status |
|---|---|---|---|
| Recent Discovery | Artist first appeared recently and crossed minimum listening threshold | Music Intelligence | UI-safe |
| Emerging Relationship | A relationship may be forming but is not proven durable | Query Workbench / Artist Intelligence | hypothesis |
| Emerging Core Artist | Formula-backed classification requiring momentum, friction, evidence, and confidence gates | Future UI | blocked |

Term ladder:

- Recent Discovery
- Emerging Relationship hypothesis
- Emerging Core Artist classification

---

## Recent Discovery

Recent Discovery means:

- artist first active year is within the recent window.
- artist total plays meet the minimum meaningful threshold.
- result is based on actual listening evidence where available.
- result does not imply durable relationship status.

Allowed:

- Music Intelligence signal card.
- Investigation queue.
- Artist Intelligence signal.

Not allowed:

- Core artist label.
- Durable relationship claim.
- Emerging Core Artist claim.

---

## Emerging Relationship

Emerging Relationship means:

- the system sees evidence that a relationship may be forming.
- the claim is interpretive.
- the claim needs supporting facts and weakening factors.
- the claim remains a hypothesis unless formula gates are accepted.

Allowed:

- Query Workbench hypothesis.
- Artist Intelligence signal with confidence and caveat.
- Investigation queue.

Not allowed:

- dashboard KPI.
- settled durable relationship label.
- core artist badge.

---

## Emerging Core Artist

Emerging Core Artist means:

- Momentum Score is accepted.
- Friction Score is accepted.
- minimum evidence threshold is accepted.
- confidence model is accepted.
- regression fixtures exist.

Current status:

- blocked.

Allowed:

- documentation.
- low-confidence hypothesis.
- open question.
- suggested investigation.

Not allowed:

- UI badge.
- settled insight.
- default filter.
- ranking control.
- dashboard KPI.

---

## Surface Permission Matrix

| Concept | Music Intelligence | Artist Intelligence | Query Workbench |
|---|---|---|---|
| Recent Discovery | Signal card | Signal only | Fact/explanation |
| Emerging Relationship | Investigation queue | Hypothesis signal | Hypothesis |
| Emerging Core Artist | Blocked notice only | Blocked notice only | Blocked hypothesis only |
| Dormant Relationship | Blocked until formula accepted | Blocked or accepted signal | Hypothesis or insight depending on formula |
| Return Signal | Blocked until formula accepted | Blocked or accepted signal | Hypothesis or insight depending on formula |
| Catalog Ecosystem | Summary only if accepted | Relationship explanation if accepted | Hypothesis or insight depending on formula |
| Playlist World Score | Blocked until formula accepted | Supporting context only | Hypothesis or insight depending on formula |
| Identity Warning | Data Health | Source Confidence | Identity section |
| Source Freshness | Header / Data Health | Source Confidence | Evidence section |

---

## Page-to-Contract Mapping

| Contract | Music Intelligence | Artist Intelligence | Query Workbench |
|---|---|---|---|
| Requirements checklist | governs page scope | governs profile scope | governs investigation scope |
| Investigation packet | summary cards link to packet | profile consumes packet | primary packet renderer |
| Source registry | source badges and warnings | provenance and confidence | full evidence source boundary |
| Identity contract | warnings only | identity/profile header | identity resolution section |
| Facts/insights/reasoning | summary and queue | explanation and trace | full trace |
| Formula/classification | gate badges and blocked notices | relationship signals | hypothesis/insight status |

---

## Visual 5: Navigation Flow

VISUAL:

- Music Intelligence
  - click Recent Discovery
- Query Workbench
  - validate evidence, facts, and hypothesis
- Artist Intelligence
  - durable profile once relationship is understood
- Playlist Intelligence or Music Library Admin
  - use when playlist placement or source cleanup is needed
- Query Workbench
  - return to investigation when new questions appear

---

## Visual 6: Claim Strength Ladder

VISUAL:

- Raw Evidence
- Fact
- Hypothesis
- Insight
- Accepted Classification
- Production UI Signal

Rules:

- Recent Discovery can be fact-backed now.
- Emerging Relationship is hypothesis-level until formulas improve.
- Emerging Core Artist is blocked until formula and regression gates are accepted.

---

## Non-Goals

This document does not implement UI.

This document does not change current code.

This document does not define final formulas.

This document does not promote Emerging Core Artist.

This document does not replace the regression fixture contract.

---

## Acceptance Criteria

This document is accepted when:

- The primary Music surfaces are defined.
- Dashboard, profile, and workbench roles are distinct.
- Low-fi visuals are included.
- Emerging terminology is separated into Recent Discovery, Emerging Relationship, and Emerging Core Artist.
- Surface permissions are documented.
- Contract mappings are documented.
- No UI implementation is started.
