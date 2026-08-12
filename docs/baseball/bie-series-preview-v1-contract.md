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
