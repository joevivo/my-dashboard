# BIE Roster Template Evaluator v0

## Purpose

The roster template evaluator reviews a proposed Strat-O-Matic 365 roster against a BIE roster archetype.

It does not optimize a roster.

It answers:

1. Did the proposed roster resolve against the BIE player universe?
2. Does the roster fit the selected archetype?
3. Is salary allocated in the expected shape?
4. Are required hitter positions covered?
5. Is the pitching staff too starter-heavy or relief-heavy?
6. Which players carry model-risk flags?

## Script

baseball/parser/evaluate_roster_template_v0.py

## Input CSV Format

Minimum supported format:

playerName,slot
Foli, Tim,SS
Gantner, Jim,2B
Martin, John,starter
Kinney, Dennis,relief

The evaluator tolerates unquoted Last, First names in this format.

It also supports these name fields:

- playerName
- player
- name

It supports these optional id fields:

- playerId
- player_id

It supports these slot fields:

- slot
- rosterSlot

## Example Command

python .\baseball\parser\evaluate_roster_template_v0.py `
  .\data\baseball\parsed\strat365\1980\draft-reports\1980.comiskey-sample-roster-template-v0.csv `
  --archetype value-spine `
  --cap 80

## Archetype Comparison Command

Use this when the proposed roster should be scored against every supported archetype:

python .\baseball\parser\evaluate_roster_template_v0.py `
  .\data\baseball\parsed\strat365\1980\draft-reports\1980.comiskey-sample-roster-template-v0.csv `
  --compare-archetypes `
  --cap 80

Comparison mode prints:

- archetype key
- score
- error count
- warning count
- notes explaining the score

## Supported Archetypes

### value-spine

Full name: Value Spine + Selective Premium Anchor

Principle: Cheap defensive/value spine plus one selective premium hitter.

Budget shape:

| Area | Target |
|---|---:|
| Hitters | $38-44M |
| Starters | $18-24M |
| Relief | $10-16M |
| Bench/Flex | $4-8M |

### pitching-supported

Full name: Pitching-Supported Run Suppression

Principle: Lean into run suppression with stronger pitching allocation.

Budget shape:

| Area | Target |
|---|---:|
| Hitters | $34-40M |
| Starters | $22-28M |
| Relief | $12-18M |
| Bench/Flex | $3-7M |

### premium-anchor

Full name: Premium Anchor

Principle: Pay for one elite bat while preserving a balanced support structure.

Budget shape:

| Area | Target |
|---|---:|
| Hitters | $42-50M |
| Starters | $16-23M |
| Relief | $8-14M |
| Bench/Flex | $3-6M |

## Output Sections

The evaluator prints:

1. archetype match score
2. salary allocation
3. structural tensions
4. position coverage
5. player signal snapshot
6. model-risk players
7. unresolved rows

## Model-Risk Flags

Current risk flags include:

- high salary commitment
- card-strength risk
- defensive risk
- relief/workload dependency
- large negative park movement
- positive movement / thin card caution


## Structural Tensions

The evaluator now emits structural tensions when a roster differs from the selected archetype.

Current structural tensions can include:

- salary needed to approach the selected cap
- hitter salary needed to reach the archetype floor
- starter salary needed to reach the archetype floor
- relief salary needed to reach the archetype floor
- missing position coverage
- thin starter count
- thin relief count
- expensive negative park movers that should be reviewed

These tensions are not player recommendations. They identify where a roster differs from the selected archetype.

## Current Limitations

The evaluator does not yet model:

- innings requirements
- bullpen fatigue
- plate appearance allocation
- platoon deployment
- injury risk
- bench depth
- card-side handedness
- draft order
- opponent roster context

## Product Role

This script is the first bridge from BIE analytical reports to roster-level decision support.

Current product chain:

card evidence
  -> player signals
  -> candidate explanations
  -> draft strategy
  -> roster construction synthesis
  -> roster template evaluation

## Recommended Next Step

Use this evaluator against one or more candidate 1980 rosters.

Then port the same workflow to 1968 after the 1968 signal stack exists.
