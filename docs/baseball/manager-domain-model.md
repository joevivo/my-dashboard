# Manager Domain Model

## Purpose

BIE exists to help a human manager make better Strat Baseball 365 decisions.

The engine is not built for parsing cards as an end in itself.

The engine is built to support managerial judgment.

## Core Managerial Unit

The fundamental planning unit is the series.

In this league context:

- 12 teams compete.
- Top 4 advance to the playoffs.
- Games are played as 3-game series.
- Strategy changes happen on a per-series cadence.

Therefore, BIE should optimize for series decisions, not isolated single-game decisions.

## Managerial Timeline

1. Draft
2. Ballpark selection
3. Roster construction
4. Lineup construction
5. Platoon planning
6. Bullpen construction
7. Series preparation
8. Series execution
9. Series review
10. Season adjustment
11. Playoff preparation

## Draft Questions

Before and during draft construction, BIE should help answer:

- Which players are strong neutral values?
- Which cheap players are salary traps?
- Which defenders are worth the offensive tradeoff?
- Which offensive profiles need a specific ballpark?
- Which pitchers are protected or exposed by a specific ballpark?
- Which player types create roster flexibility?
- Which player types require roster protection?

## Ballpark Questions

BIE should help answer:

- Which hitters rise or fall in this park?
- Which pitchers rise or fall in this park?
- Which parks amplify power?
- Which parks suppress power?
- Which parks create handedness asymmetry?
- Which parks make singles more valuable?
- Which parks make HR-prone pitchers unusable?

## Roster Construction Questions

Future BIE roster construction should help answer:

- Is every position covered?
- Are scarce defensive positions protected?
- Is the salary cap allocated rationally?
- Is the bench playable?
- Are platoons covered?
- Is the bullpen deep enough?
- Are there too many bat-first liabilities?
- Does the roster match the selected ballpark?

## Series Preparation Questions

Before each series, BIE should help answer:

- What lineup gives the best 3-game expectation?
- Which platoon advantages matter most?
- Which defenders should start despite weaker bats?
- Which pitchers are exposed by the opponent's park or lineup?
- Which bench bats matter most in the series?
- Which bullpen roles are fragile?

## Observed Results Questions

After ingesting actual 1980 seasons, BIE should help answer:

- Which draft signals correlated with winning?
- Which player types overperformed?
- Which player types underperformed?
- Which ballpark strategies worked?
- Which salary values were traps?
- Which defensive warnings mattered?
- Which bullpen constructions worked?

## Rule

Observed results calibrate BIE.

Observed results do not rewrite deterministic card evidence.
