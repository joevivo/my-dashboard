# BIE 1968 Roster Template Distinctness Audit v0

## Purpose

This document records the first distinctness audit for the 1968 roster-template comparison.

The audit answers:

> Are the generated legal roster templates actually different enough to be useful?

The answer is mixed:

- `ace_pitcher_heavy` is meaningfully distinct.
- `balanced`, `premium_hitter_heavy`, and `value_heavy` still share too much roster skeleton.
- Replacement candidate pools now exist and are useful for draft-pivot planning.

## Artifacts

Tracked scripts:

- `baseball/parser/report_1968_roster_template_distinctness_audit_v0.py`
- `baseball/parser/verify_1968_roster_template_distinctness_audit_v0.py`

Generated local outputs:

- `data/baseball/parsed/strat365/1968/reports/1968.roster-template-distinctness-audit-v0.json`
- `data/baseball/parsed/strat365/1968/reports/1968.roster-template-distinctness-audit-v0.md`

The generated report outputs are local/generated artifacts and are not expected to be committed unless repo policy changes.

## Summary

| Strategy | Total Salary | Hitting | Pitching | Card-backed | Exclusive Players |
|---|---:|---:|---:|---:|---:|
| balanced | 80.00 | 44.05 | 35.95 | 16 | 0 |
| premium_hitter_heavy | 80.00 | 53.78 | 26.22 | 13 | 2 |
| ace_pitcher_heavy | 79.99 | 24.71 | 55.28 | 15 | 9 |
| value_heavy | 79.74 | 53.52 | 26.22 | 16 | 1 |

## Pairwise Overlap

| Pair | Shared Players | Overlap |
|---|---:|---:|
| balanced vs premium_hitter_heavy | 17/25 | 0.680 |
| balanced vs ace_pitcher_heavy | 12/25 | 0.480 |
| balanced vs value_heavy | 20/25 | 0.800 |
| premium_hitter_heavy vs ace_pitcher_heavy | 11/25 | 0.440 |
| premium_hitter_heavy vs value_heavy | 19/25 | 0.760 |
| ace_pitcher_heavy vs value_heavy | 8/25 | 0.320 |

## Universal Shared Players

These players appear in all four v0 templates:

- Luis Tiant
- Dave McNally
- Bill Freehan
- Lindy McDaniel
- Pat Corrales
- Dalton Jones
- Gary Wagner

This is useful signal. These are currently functioning as common anchors across legal roster construction.

## Pitcher Function Salary

| Strategy | Pure Relief | Pure Relief Closer | Starter Only | Starter/Relief |
|---|---:|---:|---:|---:|
| balanced | 2.00 | 4.41 | 18.19 | 11.35 |
| premium_hitter_heavy | 2.50 | 2.70 | 9.16 | 11.86 |
| ace_pitcher_heavy | 3.23 | 10.38 | 31.55 | 10.12 |
| value_heavy | 2.50 | 2.70 | 9.16 | 11.86 |

## Interpretation

### Ace Pitcher Heavy

This template is meaningfully distinct.

It has:

- the highest pitcher spend
- the lowest hitter spend
- the most exclusive players
- the lowest overlap with value-heavy

This is a useful extreme construction reference.

### Balanced

The balanced template is legal and salary-banded, but it currently has zero exclusive players.

That does not make it useless. It means the v0 greedy model builds balanced by combining common anchors rather than discovering a distinct balanced identity.

### Premium Hitter Heavy

The premium-hitter-heavy template is now plausible because it no longer underfunds pitching.

However, it still overlaps heavily with value-heavy.

### Value Heavy

The value-heavy template is legal and value-scored, but it is not sufficiently distinct from premium-hitter-heavy.

This remains v0 model debt.

## Decision

The distinctness audit should be committed because it reveals important model behavior:

1. The system can generate legal salary-banded templates.
2. Only the ace-pitcher-heavy strategy is clearly distinct today.
3. Balanced/value/premium overlap needs future constraints.
4. Replacement pools are now available for draft-pivot work.

## Recommended Next Artifact

The next useful artifact is:

> 1968 draft pivot board v0

That should turn the replacement candidate pools into actionable draft support:

- if target starter is gone, show next viable starter options
- if target closer is gone, show next closer-qualified relievers
- if target catcher is gone, show next catcher options
- preserve salary band and legality while replacing one player
- identify which replacements are card-backed versus browser-baseline
