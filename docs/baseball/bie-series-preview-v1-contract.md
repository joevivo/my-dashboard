# BIE Series Preview v1 — Product and Evidence Contract

## Purpose

BIE Series Preview v1 is the persisted, automatically regenerated intelligence
product for an active team's next Strat-O-Matic series.

It must synthesize all available BIE evidence into a concise managerial preview.
It must not infer unsupported facts. Missing or unavailable evidence remains
explicitly gated.

The Active Teams homepage consumes a compact synopsis from this persisted product.
The homepage must not independently calculate a competing series assessment.

## Product Questions

A Series Preview should answer:

1. Who are we playing, where, and when?
2. What is the competitive context of this series?
3. How are both teams currently performing?
4. Which players are driving each club?
5. Who is hot, cold, or on a meaningful streak?
6. Which starting pitchers are likely to appear?
7. What is the current bullpen state?
8. Which lineup, platoon, or card matchups matter?
9. Are injuries or roster constraints material?
10. How does the ballpark change the matchup?
11. What opponent tendencies matter tactically?
12. What are our strongest edge, biggest risk, and primary watch item?

## Governing Principles

- Evidence before inference.
- Season-to-date and recent-sample evidence remain distinct.
- Player-level claims require player-level evidence.
- Probable starters are projections unless explicitly confirmed.
- Likely lineups are projections unless explicitly confirmed.
- Missing evidence must remain visible.
- Source provenance must survive into the persisted artifact.
- A preview can still be generated when some sections are gated.
- The Active Teams synopsis is derived from the full preview.

## Logical Output Contract

### identity

- schema
- generatedAtUtc
- leagueId
- teamId
- teamName
- opponentTeamId
- opponentTeamName

### series

- status
- scheduledDate
- gameCount
- homeAway
- ballpark
- scheduleGameNumbers

### executiveOutlook

- status
- classification
- headline
- summary
- strongestEdge
- biggestRisk
- primaryWatchItem

The summary should normally be two or three sentences and should synthesize
multiple evidence families rather than repeat raw statistics.

### teamContext

- record
- standing
- gamesBehind
- runDifferential
- recentForm
- offense
- pitching
- defense
- recentSignals

### opponentContext

Same evidence family as teamContext.

### playerIntelligence

#### team

- topHitters
- topPitchers
- hotHitters
- hittingStreaks
- slumpingHitters
- recentKeyPerformers

#### opponent

Same evidence family.

Each player signal should retain:

- playerId when available
- playerName
- signalType
- statistic or evidence
- sample
- source
- evidenceStatus

### pitchingMatchup

- probableStarters
- starterMatchups
- rotationAssessment
- teamBullpen
- opponentBullpen

Probable starters should include:

- player identity
- handedness
- projection status
- confidence
- supporting evidence

Bullpen evidence should distinguish:

- season quality
- recent usage
- availability
- fatigue or workload signal
- role

### lineupMatchups

- teamLikelyLineup
- opponentLikelyLineup
- platoonEdges
- cardSplitEdges
- vulnerableMatchups
- benchImplications

Projected lineups must be labeled as projected.

### availability

- teamInjuries
- opponentInjuries
- unavailablePlayers
- rosterConstraints

### environment

- ballpark
- parkEffects
- teamVenueRecord
- opponentVenueRecord
- relevantHomeRoadContext

### tacticalContext

- teamManagerTendencies
- opponentManagerTendencies
- runningGame
- sacrificeBehavior
- hitAndRunBehavior
- intentionalWalkBehavior
- bullpenUsagePatterns
- otherMaterialTendencies

### managerNotebook

- advantagesToExploit
- risksToProtectAgainst
- playersToWatch
- tacticalQuestions
- watchlist

Managerial guidance must be traceable to evidence.

### evidence

#### gates

Each evidence family uses one of:

- AVAILABLE
- PARTIAL
- EVIDENCE_GATED
- NOT_CAPTURED
- NOT_APPLICABLE
- STALE

#### missingEvidence

Explicit list of evidence that would materially improve the preview.

#### sources

Source provenance for every consumed evidence family.

## Required Evidence Families

Series Preview v1 should be capable of consuming these logical inputs:

1. Upcoming-series schedule identity
2. Team season-to-date league intelligence
3. Opponent season-to-date league intelligence
4. Team recent-game intelligence
5. Opponent recent-game intelligence
6. Team player performance
7. Opponent player performance
8. Team roster and card evidence
9. Opponent roster and card evidence
10. Team probable-starter / rotation evidence
11. Opponent probable-starter / rotation evidence
12. Team bullpen usage and availability
13. Opponent bullpen usage and availability
14. Team injury / availability evidence
15. Opponent injury / availability evidence
16. Ballpark / park-factor evidence
17. Manager tendency evidence
18. Lineup projection evidence

## Existing Series Engine v0 Inputs

Current Series Engine v0 already supports:

- team readiness
- opponent readiness
- team schedule
- league intelligence

Current persisted output already contains useful foundations including:

- upcomingSeries
- previousSeries
- recentTeamSignals
- recentOpponentSignals
- leagueContext
- matchupAssessment
- managerialWatchlist
- managerRecommendations
- sourceEvidence
- sampleGovernance

These are retained and expanded rather than replaced.

## Evidence Expansion Strategy

### Reuse / adapt first

Existing repository work strongly suggests reusable evidence around:

- roster and player identity
- hitter and pitcher cards
- platoon profiles
- matchup profiles
- rotation modeling
- bullpen construction and usage
- injuries
- park context
- stolen-base / running-game evidence

These sources require contract mapping before being consumed by Series Preview v1.

### Explicit gaps to build

The initial repository inventory did not identify clear production-ready evidence
products named for:

- top players
- hitting streaks
- likely lineups
- recent form
- manager tendencies

These require deeper source mapping and potentially new normalized evidence
builders. File-name and literal-term inventory alone is not sufficient to declare
that the underlying data does not exist.

## Active Teams Synopsis Contract

The Active Teams card should eventually consume only:

- classification
- headline
- summary
- hotSignal
- edgeSignal
- watchSignal
- previewStatus
- generatedAtUtc

Example:

SERIES OUTLOOK — Aquarium advantage

Aquarium enters with the stronger rotation profile while two core hitters are
producing well recently. The opponent's defense materially reduces the margin
for giving away outs.

Hot: Fregosi — 8-game hitting streak
Edge: Aquarium starting pitching
Watch: opponent defense

Open Series Preview →

## Full Preview Surface

The dedicated Series Preview surface may expose:

- all player spotlights
- full probable-starter comparison
- bullpen state
- likely lineups
- card/platoon matchup tables
- injuries
- park analysis
- tactical tendencies
- detailed manager notebook
- evidence provenance and gates

The homepage remains an executive summary.

## Acceptance Criteria

Series Preview v1 is ready when:

1. One persisted preview is produced for every active team with an identified
   upcoming series.
2. Preview generation does not require interactive ChatGPT analysis.
3. The artifact distinguishes available, partial, gated, stale, and absent
   evidence.
4. At least season context, recent context, player intelligence, pitching,
   availability, environment, and tactical sections exist in the schema.
5. Player-level claims are source-backed.
6. Unsupported lineup, starter, bullpen, or tactical claims are not invented.
7. The Active Teams aggregate exposes a synopsis derived from the persisted
   preview.
8. The Active Teams UI renders that synopsis rather than independently deriving
   a matchup conclusion.
9. The full preview can be opened from the team card.
10. Preview regeneration can advance automatically when the next series changes.

## Series Preview v1 Information Architecture

The Series Preview is an evidence product, not a collection of equally weighted
widgets. Evidence-rich modules are surfaced prominently. Evidence-gated modules
remain compact and explicit rather than displaying empty or speculative content.

### Above the fold

1. **Series Identity**
   - opponent
   - series and venue context
   - team record and standing when available

2. **Executive Outlook**
   - classification
   - two- or three-sentence evidence synthesis
   - confidence and evidence posture

3. **Hot / Edge / Watch**
   - current player or streak signal when actually supported
   - strongest evidence-backed advantage
   - most material evidence-backed risk
   - omit empty signals rather than manufacture filler

4. **Team vs. Opponent Snapshot**
   - record
   - standing and games behind
   - run differential
   - offense
   - pitching
   - defense
   - recent form only when recent-form evidence exists

5. **Key Players**
   - top hitters
   - top pitchers
   - current hitting streaks
   - other performance signals only when captured

### Matchup detail

6. **Tactical Context**
   - running game
   - sacrifice behavior
   - hit-and-run behavior
   - intentional-walk behavior
   - other supported manager tendencies

7. **Pitching Matchup**
   - probable starters
   - starter matchups
   - rotation assessment
   - bullpen quality
   - bullpen recent usage
   - bullpen availability and workload

8. **Lineup Matchups**
   - projected team lineup
   - projected opponent lineup
   - platoon edges
   - card-split edges
   - vulnerable matchups
   - bench implications

9. **Availability & Environment**
   - injuries
   - unavailable players
   - roster constraints
   - ballpark
   - park effects
   - relevant home/road context

10. **Manager's Notebook**
    - advantages to exploit
    - risks to protect against
    - players to watch
    - tactical questions
    - watchlist
    - render only when guidance is traceable to evidence

11. **Evidence & Gaps**
    - evidence-family gate status
    - material missing evidence
    - source provenance

### Rendering rules

- Do not fabricate content to fill a module.
- Do not convert missing recent evidence into a statement about recent form.
- Do not interpret absence from a leader list as proof that no underlying
  signal exists.
- Projected lineups and starters must be labeled as projected.
- Managerial guidance must retain evidence traceability.
- Gated modules remain compact and do not visually compete with available
  intelligence.
- Detailed provenance belongs in Evidence & Gaps rather than being repeated
  throughout the page.

## Series Lifecycle and Spoiler-Free Replay

The Series Preview is the canonical internal destination for a series.

The Active Teams experience should link to this surface once the real internal
Series Preview route exists.

The surface is lifecycle-aware rather than being discarded once games begin.

### Before the series

The primary mode is **Series Preview**.

It presents only evidence knowable before the series and preserves all evidence
gates defined by this contract.

### During or after captured games

The same series surface may expose **Spoiler-Free Replay**.

Spoiler-Free Replay should:

- preserve the scheduled order of the three-game series
- begin with Game 1 and progress sequentially
- hide final scores, winners, updated records, series outcomes, and future-game
  results until deliberately revealed
- prevent Game 2 or Game 3 information from spoiling an earlier game
- support inning-level or event-level progression when play-by-play evidence
  exists
- explain material turning points without exposing unrevealed future events
- explain managerial decisions, substitutions, pitcher usage, tactical events,
  and run-production or run-prevention mechanisms when supported
- permit a spoiler-safe BIE postgame assessment after each completed game
- unlock the complete Series Wrap-Up only after Game 3 has been completed or
  deliberately revealed

### Series Wrap-Up

After spoiler-safe progression is complete, BIE may compare:

- the pre-series Executive Outlook
- expected advantages and risks
- what actually occurred
- which signals proved material
- which assumptions were unsupported
- which evidence was missing
- new tendencies or player signals learned from the series

### Navigation intent

The Active Teams homepage remains concise.

Its internal action should lead to **Open Series Preview** once the destination
route exists.

Replay and review navigation belong inside the series surface rather than
adding competing actions to the Active Teams card.

## BIE Feedback Loop

Series intelligence should form a closed evidence loop:

**Preview -> Spoiler-Free Replay -> Series Review -> Learning**

The purpose of the loop is not to grade BIE on whether a predicted outcome
occurred. BIE does not predict game winners.

The loop evaluates whether the evidence and managerial signals surfaced before
the series were useful.

After a series, BIE should be able to determine:

- which pre-series edges actually became material
- which identified risks actually affected games
- which player signals persisted, disappeared, or changed
- which tactical tendencies appeared in game play
- which expected matchup factors were irrelevant
- which uncaptured evidence would have materially improved preparation
- which new evidence should influence the next Series Preview

Learning produced by a completed series should remain traceable to the source
games and should be eligible to inform future BIE preparation only through an
explicit evidence-bearing artifact.

The feedback loop must not leak completed-game information backward into a
spoiler-safe replay or into the historical pre-series view.

## Series Route, API, and Durable Identity

A BIE series requires one durable identity that remains stable across:

**Preview -> Spoiler-Free Replay -> Series Review -> Learning**

Opponent identity or scheduled date alone is not sufficient because the same
clubs may meet again later in the season.

### Canonical seriesId

The canonical BIE `seriesId` is derived from:

- leagueId
- subject teamId
- the complete ordered `scheduleGameNumbers` sequence

Format:

`league-{leagueId}-team-{teamId}-games-{game1}-{game2}-{game3}`

Examples:

- `league-479336-team-1851052-games-64-65-66`
- `league-479431-team-1853975-games-37-38-39`
- `league-479610-team-1854215-games-1-2-3`

The implementation must use the complete ordered game-number sequence rather
than assuming every series is exactly three games.

The following are descriptive metadata, not primary identity fields:

- opponentTeamId
- opponentDisplayName
- scheduledDate
- homeAway
- gameCount

A later rematch against the same opponent therefore receives a different
`seriesId`.

### Frontend navigation contract

The existing custom `activeView` application-navigation model remains in use.

Do not introduce React Router solely for Series Preview.

The BIE destination view is:

`SeriesPreview`

Opening a Series Preview should establish a selected series identity containing
at minimum:

- leagueId
- teamId
- seriesId

The Active Teams action should eventually become:

**Open Series Preview**

The current external Strat-O-Matic schedule link may remain available from
inside the Series Preview as a secondary source/action. It is not the canonical
BIE destination.

The existing legacy `SeriesPlanner` remains a separate tool and must not be
silently repurposed as the BIE Series Preview.

### Backend API contract

The canonical series-specific endpoint is:

`GET /api/strat/league/:leagueId/team/:teamId/series/:seriesId`

The endpoint identifies one durable BIE series and is suitable for both current
and historical series.

The response should preserve the lifecycle sections needed by the same series
surface:

- seriesIdentity
- lifecycle
- preSeriesSnapshot
- replay
- review
- learning
- evidence

Sections that are not yet available must use evidence/lifecycle status rather
than fabricated content.

### seriesIdentity

`seriesIdentity` should include:

- seriesId
- leagueId
- teamId
- opponentTeamId
- opponentDisplayName
- scheduleGameNumbers
- scheduledDate
- homeAway
- gameCount

The API must validate that route parameters agree with the persisted
`seriesIdentity`.

### Lifecycle state

The lifecycle object should describe availability without exposing spoiler
content.

It may include:

- stage
- previewAvailable
- replayAvailable
- completedGameCount
- reviewAvailable
- learningAvailable

Lifecycle metadata must not contain scores, winners, updated records, series
outcomes, or future-game results when the user is still in spoiler-safe replay.

### Immutable preSeriesSnapshot

The evidence BIE possessed before the series must be preserved as an immutable
`preSeriesSnapshot`.

Once the first game of the series begins or is captured as completed, the
pre-series snapshot must not be rewritten from later season state.

This is required for two reasons:

1. **Spoiler safety** — completed-game information must not leak backward into
   the historical preview.
2. **Feedback-loop integrity** — Series Review must compare what actually
   happened against what BIE genuinely knew and surfaced beforehand.

The snapshot should retain:

- Executive Outlook
- team context
- opponent context
- player intelligence
- matchup evidence
- evidence gates
- missing evidence
- source provenance
- generation timestamp

Subsequent game captures may add replay, review, and learning evidence, but they
must not mutate the historical pre-series evidence basis.

### Replay identity

Replay games remain children of the same `seriesId`.

Each replay game should retain:

- scheduleGameNumber
- captured gameId when available
- ordinal within the series
- spoiler-safe reveal state in the UI

### Durable capture, reveal, and review state

Spoiler safety requires three independent per-game state families.

`captureState` is system-owned and describes what BIE has ingested and
normalized. Its v1 progression is:

`NOT_CAPTURED -> CAPTURED -> PARSED -> REVIEW_READY`

Background capture may advance through this progression without changing what
the user is allowed to see.

`revealState` is user-controlled and describes what has been deliberately
revealed. Its v1 progression is:

`LOCKED -> UNVIEWED -> IN_PROGRESS -> REVEALED`

A later game remains `LOCKED` until the prior game has been deliberately
revealed. Capture completion must never implicitly advance `revealState`.

`reviewState` describes how much BIE analysis may safely be exposed. Its v1
progression is:

`LOCKED -> REPLAY_READY -> IN_PROGRESS -> POSTGAME_READY -> COMPLETE`

`reviewState` may never expose evidence beyond the user's current
`revealState` boundary.

Each replay game therefore carries:

- `captureState.status`
- `captureState.capturedAtUtc`
- `captureState.parsedAtUtc`
- `captureState.reviewReadyAtUtc`
- `captureState.sourceEvidence`
- `revealState.status`
- `revealState.revealedThroughEventSequence`
- `revealState.revealedThroughInning`
- `revealState.startedAtUtc`
- `revealState.completedAtUtc`
- `reviewState.status`
- `reviewState.spoilerSafeThroughEventSequence`
- `reviewState.postgameAvailable`
- `reviewState.completedAtUtc`

The replay object also carries `sequencePolicy` with:

- `mode = STRICT_SERIES_ORDER`
- `captureIndependentOfReveal = true`
- `futureGameIsolation = true`
- `serverSideRedactionRequired = true`

Result-bearing data for unrevealed events or games must be omitted from the
API response. Hiding already-delivered spoiler data only in the browser is not
sufficient.

The first game may transition from `LOCKED` to `UNVIEWED` only after its
capture reaches `REVIEW_READY`. Game 2 and later additionally require the
preceding game's `revealState` to be `REVEALED`.

When a replay begins, `revealState` and `reviewState` advance only to the
event or inning boundary explicitly reached by the user. The final score,
winner, updated record, and postgame assessment become eligible only after the
final event has been deliberately revealed.

### Replay state transition API

The local BIE service exposes state-transition operations beneath the durable
series route:

- `POST /api/strat/league/:leagueId/team/:teamId/series/:seriesId/games/:ordinal/capture-state`
- `POST /api/strat/league/:leagueId/team/:teamId/series/:seriesId/games/:ordinal/reveal-state`
- `POST /api/strat/league/:leagueId/team/:teamId/series/:seriesId/games/:ordinal/review-state`

Capture-state transitions are system-owned and may advance independently of
user reveal state. Reveal-state transitions enforce strict series order.
Review-state transitions cannot complete before the corresponding game has
been deliberately revealed.

Every transition response passes through the same server-side spoiler
redaction used by the canonical series GET endpoint. Persistence of a
transition must not mutate `preSeriesSnapshot`.

Game identity must not require changing the parent series route.

### Review and learning identity

Series Review and Learning artifacts remain attached to the same `seriesId`.

This makes it possible to trace:

- a pre-series signal
- the games in which it did or did not matter
- the post-series assessment
- any evidence-bearing learning promoted into future preparation

No learned signal may be promoted solely because an outcome occurred. It must
remain traceable to supporting game evidence.
