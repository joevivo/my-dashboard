# BIE Draft Rule Failure Debrief v0

## Summary

The 1968 Strat365 draft plan failed because BIE generated draft guidance before proving roster legality.

The exposed hard failure was the 1968 roster requirement that a legal roster must include at least 5 pitchers who have starting pitcher Endurance ratings, such as S7.

This is not a strategy preference. It is a submission legality rule.

## Official 1968 Strat365 Roster Requirements

For the 1968 player set:

- You must have at least 25 players and no more than 28 players.
- You must have at least 13 and no more than 17 hitters.
- At least two hitters must have catcher as their primary position.
- You must have at least 11 and no more than 14 pitchers.
- You must have at least 5 pitchers who have starting pitcher Endurance ratings.
- You must have at least 4 pure relievers: a relief rating but no starter rating.
- You must have at least 1 pitcher who has a closer Endurance rating.

Source:
https://365.strat-o-matic.com/help/rules/baseball

## What Went Wrong

BIE treated Strat365 roster rules as background knowledge instead of executable constraints.

The draft workflow moved too quickly into:

1. player value
2. draft ordering
3. pitcher/hitter prioritization
4. roster construction
5. 1968 draft planning

But it skipped the required foundation:

1. rule ingestion
2. machine-readable rule spec
3. roster legality validation
4. regression fixtures
5. fail-closed draft generation

Because no legality validator existed, BIE could produce a plausible-looking draft plan that was structurally invalid.

## Product Failure

The failure was not that BIE chose the wrong player.

The failure was that BIE did not stop and say:

> This roster is illegal. It has only 4 starter-endurance pitchers. The 1968 Strat365 rules require at least 5.

Any future BIE draft workflow must fail closed before producing draft recommendations.

## Correction Added

The repo now includes a machine-readable 1968 roster rule spec:

- `data/baseball/canonical/rules/strat365_1968_roster_rules_v1.json`

The repo now includes a validator:

- `baseball/validation/validate_strat365_roster.py`

The repo now includes regression fixtures:

- `data/baseball/fixtures/rosters/1968_illegal_four_starters_v1.json`
- `data/baseball/fixtures/rosters/1968_legal_minimum_pitching_v1.json`

The repo now includes a regression runner:

- `baseball/validation/run_roster_validation_regressions.py`

## Current Regression Result

The illegal fixture fails as expected:

- 25 players
- 14 hitters
- 11 pitchers
- 2 primary catchers
- 4 starter-endurance pitchers
- 7 pure relievers
- 1 closer-endurance pitcher

Expected violation:

- `startingEndurancePitchers.belowMinimum`

The legal control fixture passes as expected.

## Required Policy Going Forward

BIE must not label any roster as draft-ready or submission-ready unless roster legality validation passes.

Any future draft optimizer must run in this order:

1. Load player-set rule spec.
2. Load candidate roster or draft plan.
3. Validate roster legality.
4. Report all legality violations.
5. Stop if illegal.
6. Continue to strategy/optimization only after legality passes.

## Next BIE Work

Before any further 1968 draft optimization:

1. Add validator support for actual parsed player/card data.
2. Map real pitcher endurance fields into the validator input shape.
3. Add validation for actual draft candidate outputs.
4. Add a command that validates the current planned draft roster.
5. Block draft recommendation output unless validation passes.

## Decision

The 1968 draft plan remains parked.

BIE is not ready for draft execution until roster legality validation is integrated into the draft pipeline.
