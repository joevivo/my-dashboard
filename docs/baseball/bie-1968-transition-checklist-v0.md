# BIE 1968 Transition Checklist v0

## Purpose

This checklist defines what must be true before BIE can be trusted for a 1968 Strat-O-Matic 365 draft.

The 1980 model is the proofbed. The 1968 season is the next practical target.

## Product Principle

Do not assume the 1980 model transfers cleanly to 1968.

BIE should prove parser compatibility, signal-generation parity, and strategy relevance before producing draft recommendations for a new season.

## Current BIE Product State

BIE currently supports a report-driven product alpha for the 1980 season:

- model summary
- draft candidate explanations
- draft strategy brief
- roster construction synthesis
- roster template evaluation
- observed calibration reports

Current product chain:

card evidence
  -> player signals
  -> candidate explanations
  -> draft strategy
  -> roster construction synthesis
  -> roster template evaluation

## 1968 Transition Goals

The 1968 transition should answer:

1. Can BIE parse the 1968 card universe?
2. Can BIE ingest and model 1968 ballparks?
3. Can BIE regenerate the same signal stack for 1968?
4. Do 1980 scoring assumptions still make sense?
5. Can BIE produce a useful 1968 draft strategy brief?
6. Can BIE evaluate a proposed 1968 roster template?

## Phase 1: Data Readiness

Required:

- 1968 player universe captured
- 1968 card pages captured
- 1968 ballparks captured
- salary data captured
- roster metadata captured
- defense metadata captured

Acceptance criteria:

- every 1968 player has a player id
- every 1968 player has role metadata
- every 1968 player has salary metadata
- every 1968 card page has a parsed output file
- every 1968 ballpark has SI/HR left/right factors

Primary risks:

- card HTML may differ from 1980
- purchased-card access may block capture
- salary format may differ
- ballpark names may differ from expected paths
- defense metadata may require parser adjustment

## Phase 2: Parser Compatibility

Run 1968 equivalents of:

- parser sample verification
- parser full-corpus verification
- result cell verification
- normalized result label verification
- split range verification
- result modifier verification
- result atom verification
- result semantics verification
- result probability verification
- card probability summary verification

Acceptance criteria:

- zero missing parsed files
- zero parser failures
- zero unmatched normalized outcome rows
- unresolved split ranges documented and bounded
- result semantics mapped for all rows
- probability statuses explainable

## Phase 3: Signal Generation Parity

Generate 1968 equivalents of:

- neutral draft signals
- salary-adjusted draft signals
- defensive draft signals
- defense-aware draft signals
- ballpark-aware draft signals
- matchup player profiles
- card probability summaries

Acceptance criteria:

- rankable hitter count is explainable
- rankable pitcher count is explainable
- unresolved hitter/pitcher counts are documented
- top neutral, salary-adjusted, defense-aware, and ballpark-aware players are plausible
- per-ballpark rankings are contiguous
- ballpark fits exist for every rankable player

## Phase 4: Model Sanity Review

Inspect:

1. top neutral card-strength hitters and pitchers
2. top salary-adjusted values
3. biggest defense-aware risers
4. biggest defense-aware fallers
5. biggest ballpark movers
6. park-sensitive players
7. fake-value candidates
8. relief-heavy pitcher value traps
9. starter workload candidates
10. position scarcity

## Phase 5: 1968 Draft Reports

Generate 1968 versions of:

- draft candidate explanations
- draft strategy brief
- roster construction synthesis
- roster template evaluation

Minimum useful output:

- target ballpark thesis
- top hitter value candidates
- premium hitter anchors
- low-cost hitter role players
- playable defensive anchors
- park movement candidates
- park movement cautions
- large negative park movers
- low-cost pitcher values
- mid-salary pitcher values
- premium pitcher anchors
- starter workload targets
- relief targets
- model cautions

## Phase 6: Roster Template Evaluation

Before the final 1968 draft, BIE should evaluate proposed rosters against an archetype.

The evaluator should review:

- salary allocation
- position coverage
- starter workload shape
- relief dependency
- defensive spine
- premium anchor exposure
- park-fit alignment
- fake-value exposure
- model-risk flags
- archetype match score

## Non-Goals

Do not build UI yet.

Do not ingest more observed teams manually.

Do not optimize a final roster before 1968 signal parity is proven.

Do not treat ballpark-aware rank as final truth.

Do not assume 1980 model weights are correct for 1968.

## Product Readiness Gates

BIE is ready for 1968 draft preparation when:

- 1968 parser full-corpus verification passes
- 1968 ballpark-aware signal verification passes
- 1968 draft candidate explanation report runs
- 1968 draft strategy brief runs
- 1968 roster construction synthesis runs
- at least one proposed roster can be evaluated against an archetype

BIE is ready for 1968 draft execution when:

- target ballpark has been selected
- budget shape has been selected
- starter workload risk has been reviewed
- relief dependency has been reviewed
- premium-anchor strategy has been selected
- fake-value candidates have been identified

## Recommended Next Step

Prove the roster-template evaluator on one or more 1980 candidate rosters.

Then apply the same workflow to 1968 after the 1968 signal stack exists.
