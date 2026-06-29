# Roster Fixture Format v0

## Purpose

A roster fixture is a small, explicit input file used to evaluate roster construction.

Roster fixtures let BIE test roster structure before building optimizers, UI, or observed-results calibration.

## Current Scope

Roster Fixture v0 supports one narrow use case:

Evaluate a known list of player IDs against:

- season
- roster name
- selected ballpark
- salary cap
- player IDs

It does not generate a roster, optimize a roster, or choose lineups.

## File Location

Roster fixtures live under:

`baseball/fixtures/rosters/`

Current fixture:

`baseball/fixtures/rosters/1980.sample-roster-v0.json`

## Schema

Required fields:

- `schemaVersion`
- `season`
- `name`
- `ballparkName`
- `salaryCapMillions`
- `playerIds`

Current schema version:

`bie.roster-fixture.v0`

## Current Evaluator

Current script:

`baseball/parser/evaluate_roster_construction_v0.py`

Current report output:

`data/baseball/parsed/strat365/1980/roster-construction/1980.sample-roster-v0.roster-construction-v0.json`

## Current Evaluation Checks

Roster Construction v0 evaluates:

- player count
- hitter count
- pitcher count
- salary total
- salary remaining
- salary cap exceeded
- position coverage
- missing required positions
- thin pitching staff
- scarce-position weak-range warnings
- defense-aware rank
- selected-ballpark rank
- selected-ballpark rank delta

## Non-Goals

Roster Fixture v0 does not define:

- batting order
- platoon deployment
- rotation
- bullpen roles
- closer usage
- defensive substitutions
- pinch-hitting strategy
- automated draft optimization

## Design Rule

A roster fixture is test evidence.

It should be small, explicit, stable, and regression-safe.
