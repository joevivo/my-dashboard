# Observed Results Ingestion Design v0

## Purpose

Observed results ingestion lets BIE compare expected model signals against actual played Strat Baseball 365 outcomes.

This is the calibration bridge.

BIE models what the cards imply. Observed results show what happened in managed leagues.

## Core Rule

Observed results must remain separate from deterministic card evidence.

Card evidence says what is printed on the card.

Observed results say what happened in played seasons.

Calibration compares the two. It does not rewrite card truth.

## Strategic Sequence

1. Prove the 1980 card model.
2. Add salary, defense, ballpark, and roster-construction context.
3. Ingest 20+ played 1980 seasons.
4. Compare expected BIE signals against actual outcomes.
5. Identify overperforming and underperforming patterns.
6. Calibrate draft and roster strategy.
7. Pivot to 1968 with a proven architecture.

## Initial Scope

Observed Results v0 should ingest season-level and roster-level evidence first.

Do not start with pitch-by-pitch or play-by-play detail.

The first useful layer should answer:

- Which rosters won?
- Which ballparks won?
- Which roster structures worked?
- Which player types overperformed?
- Which draft signals correlated with success?
- Which warning flags were meaningful?

## Proposed Directory Layout

Raw observed evidence:

`data/baseball/raw/strat365/1980/observed-results/`

Parsed observed evidence:

`data/baseball/parsed/strat365/1980/observed-results/`

Calibration outputs:

`data/baseball/parsed/strat365/1980/calibration/`

Raw observed evidence should stay local-only until privacy and redistribution rules are clear.

## Proposed v0 Input Types

### Season Summary

One row per played season or league.

Potential fields:

- observedSeasonId
- stratSeason
- leagueName
- leagueUrl
- startDate
- endDate
- teams
- gamesPerTeam
- playoffTeams
- championTeamId
- sourceType
- capturedAt

### Team Summary

One row per team in a played league.

Potential fields:

- observedSeasonId
- teamId
- teamName
- managerName
- ballparkName
- wins
- losses
- winPct
- runsScored
- runsAllowed
- runDifferential
- playoffSeed
- playoffResult
- salaryTotalMillions

### Roster Snapshot

One row per player on a team roster.

Potential fields:

- observedSeasonId
- teamId
- playerId
- playerName
- role
- salaryMillions
- primaryPosition
- bats
- throws
- rosterSlot
- acquiredVia
- dropped
- sourceRosterDate

## Proposed Joins

Observed results should join to existing BIE layers by:

- season
- playerId
- ballparkName
- team or roster fixture where available

Useful joins:

- observed player result to defense-aware draft signal
- observed player result to ballpark-aware draft signal
- observed team result to roster-construction report
- observed team result to ballpark bucket
- observed team result to salary allocation

## First Calibration Questions

BIE should initially test:

- Did higher defense-aware roster strength correlate with wins?
- Did selected ballpark fit correlate with run differential?
- Did teams with missing structural coverage underperform?
- Did salary traps underperform their ranking?
- Did cheap defense-first players help more than raw offense suggests?
- Did power-amplifier parks reward HR-check hitters?
- Did power-suppressor parks protect HR-prone pitchers?

## Validation Rules

Observed Results v0 should verify:

- season IDs are unique
- team IDs are unique within observed season
- player IDs resolve where possible
- ballpark names resolve where possible
- wins plus losses are plausible
- salary totals are plausible
- roster sizes are plausible
- no observed result overwrites card evidence
- all parsed outputs preserve source provenance

## Non-Goals

Do not attempt yet:

- play-by-play modeling
- injury modeling
- dice-roll reconstruction
- daily transaction modeling
- automated strategy recommendations
- UI display
- final 1968 calibration

## Design Rule

Observed results are calibration evidence.

They should explain where BIE was right, where BIE was wrong, and which future signals need adjustment.
