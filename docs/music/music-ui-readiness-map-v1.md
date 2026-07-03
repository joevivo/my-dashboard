# Music UI Readiness Map v1

## Status

Draft planning document for Sprint 7.

This document maps contracts and wireframes to future UI implementation work.

No UI implementation is started by this document.

---

## Purpose

This document defines what is ready, blocked, renamed, hidden, or deferred before Music UI implementation begins.

It answers:

- Which current UI surfaces can remain?
- Which current labels need to change?
- Which concepts are UI-safe now?
- Which concepts must remain blocked or hypothesis-only?
- Which panels should be built first?
- What is the first implementation slice?

Core rule:

UI implementation may begin only after every planned surface has an allowed claim type, source boundary, confidence treatment, and blocked-state treatment.

---

## Relationship to Prior Documents

This readiness map depends on:

- Music phase requirements checklist v1
- Music investigation packet contract v1
- Music source and provenance registry v1
- Music identity contract v1
- Music facts, insights, and reasoning trace contract v1
- Music derived formula and classification contract v1
- Music UI surface model v1
- Music UI wireframes v1
- Music regression fixture contract v1

---

## Readiness Status Values

| Status | Meaning |
|---|---|
| ready | safe for UI implementation |
| rename | existing UI concept can remain but needs safer language |
| hypothesisOnly | may appear only as a hypothesis with confidence and caveat |
| blocked | must not appear as settled UI output |
| adminOnly | belongs in Music Library Admin, not analytical surfaces |
| deferred | useful but not part of first UI slice |

---

## Page Readiness Inventory

| Surface | Readiness Goal | Sprint 7 Decision Needed |
|---|---|---|
| Music Intelligence | dashboard triage | first implementation slice and label cleanup |
| Artist Intelligence | durable profile | allowed relationship labels and blocked signal treatment |
| Query Workbench | investigation cockpit | packet-to-panel mapping |
| Playlist Intelligence | playlist/cohort analysis | playlist claims vs listening claims |
| Music Library Admin | source/data management | admin-only source and identity queues |

---

## Acceptance Criteria

This document is accepted when:

- current UI labels are audited.
- first implementation slice is defined.
- blocked concepts are mapped.
- hypothesis-only concepts are mapped.
- safe current concepts are mapped.
- page-by-page panel readiness is mapped.
- no unsupported formula-backed UI claims are allowed.
- no UI implementation is started.

---

## Current UI Concept Readiness Audit

This section maps known or planned UI-facing concepts to readiness decisions before implementation begins.

| Current or Planned Concept | Readiness | Required Treatment | Notes |
|---|---|---|---|
| Emerging Artists | rename | Rename to Recent Discoveries | Current logic means recently first-seen artists with enough plays, not Emerging Core Artist |
| Emerging Relationship | hypothesisOnly | Show only with confidence and caveat | May appear in Artist Intelligence or Query Workbench as a forming-relationship hypothesis |
| Emerging Core Artist | blocked | Do not show as badge or settled claim | Requires Momentum, Friction, evidence threshold, confidence model, and fixtures |
| Recent Discoveries | ready | Dashboard signal card | Safe if defined as first active recently plus minimum listening threshold |
| Dormant Relationship | blocked | Show only blocked notice or hypothesis | Requires dormancy window and historical baseline |
| Return Signal | blocked | Show only blocked notice or hypothesis | Requires dormant baseline and recent-return threshold |
| Catalog Ecosystem | hypothesisOnly | Show as hypothesis unless formula accepted | Relationship idea exists, but accepted formula gate is not complete |
| Playlist World Score | blocked | Do not show as score or classification | Requires playlist formula and fixtures |
| Friction Score | blocked | Do not show as score | Requires skip-rate/completion model and confidence rules |
| Momentum Score | blocked | Do not show as score | Requires recent window, baseline, decay/weighting model, and confidence rules |
| Source Freshness | ready | Show in header or Data Health | Must include source/snapshot context when available |
| Identity Warning | ready | Show near entity identity or Data Health | Must route to Query Workbench or Music Library Admin |
| Mojibake Candidate | adminOnly | Show in Music Library Admin or source-warning queue | Should not be treated as analytical relationship insight |
| Album Variant Review | adminOnly | Show in Music Library Admin and Query Workbench warning | Required before trusted album relationship claims |
| Same-title Song Collision | adminOnly | Show in Query Workbench identity/evidence warning | Must require artist-aware matching |

Rules:

- A rename decision preserves the concept but changes the visible label.
- A blocked decision prevents settled UI output.
- A hypothesisOnly decision allows investigation but not durable profile truth.
- An adminOnly decision keeps source cleanup out of the main analytical dashboard.
- A ready decision still requires source boundary and confidence treatment.

---

## Page-by-Page Panel Readiness

### Music Intelligence

| Panel | Readiness | Required Treatment |
|---|---|---|
| Header and source freshness | ready | show freshness and route warnings to Music Library Admin |
| Current Listening summary | ready | source-backed summary only |
| Long-Term Memory summary | ready | durable relationships only when supported |
| Data Health | ready | identity, mojibake, source, and freshness warnings |
| Recent Discoveries | ready | renamed from Emerging Artists |
| Return Candidates | hypothesisOnly | show as candidate until Return Signal formula is accepted |
| Dormant Candidates | hypothesisOnly | show as candidate until Dormant Relationship formula is accepted |
| Relationship Summary | hypothesisOnly | avoid unsupported durable classifications |
| Investigation Queue | ready | route unresolved claims to Query Workbench |

### Artist Intelligence

| Panel | Readiness | Required Treatment |
|---|---|---|
| Artist profile header | ready | show resolved identity, confidence, and warnings |
| Metric cards | ready | actual listening metrics must be source-backed |
| Relationship summary | hypothesisOnly | durable claim only when evidence and confidence support it |
| Albums panel | hypothesisOnly | canonical album identity required for relationship claims |
| Songs panel | hypothesisOnly | artist-aware matching required for same-title songs |
| Playlists panel | ready | playlist placement only, not actual listening truth |
| Signals panel | hypothesisOnly | blocked concepts must show blocked status |
| Reasoning trace summary | ready | link to Query Workbench for full packet |

### Query Workbench

| Panel | Readiness | Required Treatment |
|---|---|---|
| Query header | ready | show original query, resolved entity, type, and confidence |
| Identity panel | ready | show aliases, matched names, warnings, and family scope |
| Evidence panel | ready | show source family, metric type, provenance, and confidence |
| Facts panel | ready | facts must cite source evidence |
| Hypotheses panel | ready | hypotheses must cite facts and weakening factors |
| Insights panel | ready | safe conclusions only |
| Reasoning trace panel | ready | show evidence-to-confidence path |
| Next investigations | ready | route to correct surface |

### Playlist Intelligence

| Panel | Readiness | Required Treatment |
|---|---|---|
| Playlist header | ready | show playlist identity and source confidence |
| Summary metrics | ready | distinguish playlist membership from listening behavior |
| Bridge artists | hypothesisOnly | playlist relationship only unless listening evidence supports more |
| Shared core artists | hypothesisOnly | avoid durable relationship claims without evidence |
| Playlist World Score | blocked | do not show until formula accepted |
| Playlist comparison | deferred | not required for first implementation slice |

### Music Library Admin

| Panel | Readiness | Required Treatment |
|---|---|---|
| Source freshness | ready | show source/snapshot state |
| Mojibake queue | ready | admin/data-quality only |
| Identity mapping queue | ready | admin/data-quality only |
| Album variant queue | ready | admin/data-quality only |
| Same-title song collision queue | ready | admin/data-quality only |
| Fixture candidate queue | deferred | useful after regression fixture examples exist |

---

## First UI Implementation Slice

The first implementation slice should be narrow, safe, and contract-backed.

Recommended first slice:

- Music Intelligence dashboard cleanup.

Why this slice comes first:

- Music Intelligence is the entry point.
- Current emerging terminology needs correction.
- Dashboard signals should route to deeper surfaces instead of overexplaining.
- Source freshness and data health can be added without formula work.
- Blocked and hypothesis-only treatment can be established before advanced classifications.

Included changes:

| Change | Readiness | Notes |
|---|---|---|
| Rename Emerging Artists to Recent Discoveries | ready | current logic supports recent-first-seen plus minimum plays, not Emerging Core Artist |
| Add Recent Discoveries signal card | ready | dashboard-safe if label is precise |
| Add blocked status treatment | ready | prevents unsupported classification badges |
| Add hypothesis status treatment | ready | allows investigation without overclaiming |
| Add source freshness placement | ready | header or Data Health card |
| Add Data Health card | ready | source, identity, mojibake, and freshness warnings |
| Add Investigation Queue section | ready | routes unresolved claims to Query Workbench |
| Link Recent Discoveries to Query Workbench | ready | dashboard signal becomes investigation path |
| Hide Emerging Core Artist badge | ready | blocked until formulas and fixtures are accepted |
| Keep Friction and Momentum hidden | ready | blocked until formula gates are accepted |

Excluded from first slice:

| Excluded Item | Reason |
|---|---|
| Emerging Core Artist classification | blocked formula-backed concept |
| Friction Score | formula not accepted |
| Momentum Score | formula not accepted |
| Dormant Relationship badge | formula not accepted |
| Return Signal badge | formula not accepted |
| Playlist World Score | formula not accepted |
| Full Artist Intelligence redesign | separate UI implementation slice |
| Full Query Workbench packet renderer | separate UI implementation slice |
| Music Library Admin buildout | separate UI implementation slice |

First slice success criteria:

- Emerging Artists no longer appears as a visible UI label.
- Recent Discoveries appears with precise explanatory copy.
- No blocked concept appears as a settled badge.
- Dashboard includes source freshness or Data Health placement.
- Dashboard routes investigation actions to Query Workbench.
- No formula-backed classification is introduced.

---

## Current Source Touchpoint Audit

This section records the current UI/source touchpoints observed before implementation begins.

| Source File | Current Reference | Readiness Decision | Required Action |
|---|---|---|---|
| src/App.jsx | Query Workbench navigation | ready | keep navigation label |
| src/App.jsx | Music Intelligence navigation | ready | keep navigation label |
| src/App.jsx | Playlist Intelligence navigation | ready | keep navigation label |
| src/ArtistIntelligence.jsx | Emerging Relationship | hypothesisOnly | keep only if displayed as hypothesis with confidence/caveat |
| src/MusicDashboard.jsx | Music Intelligence page shell | ready | candidate first implementation surface |
| src/PlaylistIntelligence.jsx | Playlist World language | rename | avoid implying accepted Playlist World Score |
| src/music/components/MusicTimeMachine.jsx | Dormant | hypothesisOnly | avoid durable Dormant Relationship classification until formula accepted |
| src/utils/musicIntelligence.js | getDormantArtists() | hypothesisOnly | may feed candidates, not settled relationship badge |

Not observed in current source audit:

- Emerging Core Artist
- Friction Score
- Momentum Score
- Return Signal
- Data Health
- Source Freshness

Implementation implications:

- Do not introduce Emerging Core Artist, Friction Score, Momentum Score, or Return Signal in the first UI slice.
- Treat existing Dormant logic as candidate-generation only.
- Treat existing Emerging Relationship label as hypothesis-only.
- Treat Playlist World language as descriptive playlist grouping unless and until Playlist World Score is accepted.
- Add Data Health and Source Freshness as safe explanatory UI, not as new classifications.

---

## First Slice Implementation Checklist

This checklist defines the expected implementation order after Sprint 7 is accepted.

### 1. Music Dashboard Label Cleanup

| Task | Source Area | Expected Result |
|---|---|---|
| Replace visible Emerging Artists label | MusicDashboard / related data rendering | UI says Recent Discoveries |
| Preserve current logic initially | musicIntelligence utility layer | behavior does not change during label cleanup |
| Add explanatory copy | Music Intelligence dashboard | Recent Discoveries means recently first active with enough listening evidence |
| Prevent Emerging Core Artist label | Music Intelligence dashboard | blocked concept does not appear |

### 2. Source Freshness and Data Health

| Task | Source Area | Expected Result |
| Add source freshness placement | Music Intelligence header or Data Health card | user can see data recency context |
| Add Data Health card | Music Intelligence dashboard | identity/source/mojibake/freshness warnings have a home |
| Keep warnings non-analytical | Music Intelligence dashboard | warnings do not become relationship claims |
| Route unresolved source issues | Music Library Admin or Query Workbench | cleanup and investigation paths are explicit |

### 3. Hypothesis and Blocked-State Treatment

| Task | Source Area | Expected Result |
| Add hypothesis visual treatment | Music Intelligence / Artist Intelligence | candidates are visibly not settled claims |
| Add blocked visual treatment | Music Intelligence / Query Workbench | blocked concepts show missing gate reason |
| Keep Dormant as candidate only | MusicTimeMachine / musicIntelligence utility layer | no Dormant Relationship badge |
| Keep Emerging Relationship as hypothesis only | ArtistIntelligence | label must include confidence/caveat |

### 4. Investigation Routing

| Task | Source Area | Expected Result |
| Add Investigation Queue section | Music Intelligence dashboard | unresolved claims have an action path |
| Route Recent Discoveries to Query Workbench | Music Intelligence dashboard | signal opens investigation context |
| Route identity warnings to Query Workbench or Admin | dashboard/profile surfaces | source cleanup is separated from analysis |

### 5. Explicitly Excluded From First Slice

The first implementation slice must not include:

- Emerging Core Artist badge.
- Friction Score.
- Momentum Score.
- Return Signal badge.
- Dormant Relationship badge.
- Playlist World Score.
- full Artist Intelligence redesign.
- full Query Workbench packet renderer.
- full Music Library Admin buildout.

Implementation rule:

First slice changes should improve language, routing, and safety without introducing new formula-backed classifications.
