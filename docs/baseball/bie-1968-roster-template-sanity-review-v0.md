# BIE 1968 Roster Template Sanity Review v0

## Purpose

This document records the first sanity review of the generated 1968 roster-template outputs.

The purpose is to answer:

> Do the generated legal roster templates make enough baseball and Strat365 sense to use as draft-prep concepts?

The answer is:

> Yes, with caution.

There are no draft blockers, but there is meaningful strategic identity debt.

## Artifacts

Tracked scripts:

- `baseball/parser/report_1968_roster_template_sanity_review_v0.py`
- `baseball/parser/verify_1968_roster_template_sanity_review_v0.py`

Generated local outputs:

- `data/baseball/parsed/strat365/1968/reports/1968.roster-template-sanity-review-v0.json`
- `data/baseball/parsed/strat365/1968/reports/1968.roster-template-sanity-review-v0.md`

The generated report outputs are local/generated artifacts and are not expected to be committed unless repo policy changes.

## Summary

| Strategy | Classification | Hitting | Pitching | Exclusive Players | Highest Overlap |
|---|---|---:|---:|---:|---:|
| balanced | model_debt | 44.05 | 35.95 | 0 | 0.800 |
| premium_hitter_heavy | model_debt | 53.78 | 26.22 | 2 | 0.760 |
| ace_pitcher_heavy | suspicious | 24.71 | 55.28 | 9 | 0.480 |
| value_heavy | model_debt | 53.52 | 26.22 | 1 | 0.800 |

## Draft Blockers

None.

This is the most important result. The current templates are not final recommendations, but they are usable as draft-prep concepts.

## Strategy Findings

### Balanced

Classification: `model_debt`

Findings:

- Passes current legality and salary-band checks.
- Has high overlap with `value_heavy`.
- Has zero exclusive players.
- Still useful as a baseline roster-construction reference.

Interpretation:

Balanced is a legal and useful baseline, but it does not yet have a distinct roster identity. It is currently a blend of common anchors rather than a strategy with unique player-selection logic.

### Premium Hitter Heavy

Classification: `model_debt`

Findings:

- Passes current legality and salary-band checks.
- No longer has the earlier unusable 6M pitching problem.
- Has high overlap with `value_heavy`.
- Has only 13 card-backed players, creating browser-baseline dependency risk.

Interpretation:

Premium-hitter-heavy is now plausible, but it is not yet sufficiently distinct from value-heavy.

### Ace Pitcher Heavy

Classification: `suspicious`

Findings:

- Passes current legality and salary-band checks.
- Is meaningfully distinct by exclusive-player count and pitcher spend.
- Has thin hitter spend at 24.71M.

Interpretation:

Ace-pitcher-heavy is the clearest distinct strategy. The concern is whether the offense is too thin to survive. That is a baseball/Strat365 judgment question, not a legality issue.

### Value Heavy

Classification: `model_debt`

Findings:

- Passes current legality and salary-band checks.
- Has high overlap with `balanced`.
- Is value-scored but not budget-distinct from `premium_hitter_heavy`.

Interpretation:

Value-heavy needs further differentiation. It should eventually mean something more specific than “similar to hitter-heavy but value-scored.”

## Universal Anchor Review

These players appear in all four v0 templates:

| Player | Role | Salary | Review Category |
|---|---|---:|---|
| Luis Tiant | S9/R3 | 10.12 | premium anchor review |
| Dave McNally | S9 | 9.16 | premium anchor review |
| Bill Freehan | C | 8.21 | premium anchor review |
| Lindy McDaniel | R3/C3 | 2.70 | common anchor |
| Pat Corrales | C | 2.39 | common anchor |
| Dalton Jones | 1B | 0.50 | cheap role anchor review |
| Gary Wagner | R4 | 0.50 | cheap role anchor review |

Interpretation:

The universal anchors are useful signal, but they should not be accepted blindly.

The premium anchors need Strat365/baseball validation. The cheap anchors need review to determine whether they are useful roster glue or artifacts of salary/value scoring.

## Model Debt

Current model debt:

- `balanced` has high overlap with `value_heavy`.
- `balanced` has zero exclusive players.
- `premium_hitter_heavy` has high overlap with `value_heavy`.
- `value_heavy` has high overlap with `balanced`.
- `value_heavy` is not budget-distinct from `premium_hitter_heavy`.

## Decision

The sanity review should be committed.

It establishes:

1. There are no draft blockers.
2. The generated rosters are useful for draft prep with caution.
3. Strategic identity debt is explicit.
4. The next artifact should focus on actionable draft pivots rather than more abstract optimization.

## Recommended Next Artifact

The next useful artifact is:

> 1968 draft pivot board v0

That should answer practical live-draft questions:

- if a target starter is gone, what are the next viable starter options?
- if a target closer is gone, what are the next closer-qualified relievers?
- if a target catcher is gone, what are the next catcher options?
- can the replacement preserve legality?
- can the replacement preserve the salary band?
- is the replacement card-backed or only browser-baseline?
