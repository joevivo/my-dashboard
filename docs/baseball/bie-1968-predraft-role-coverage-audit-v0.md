# BIE 1968 Pre-Draft Role Coverage Audit v0

## Purpose

This document records the 1968 role-coverage audit that unblocked draft-readiness work after the roster-rule failure.

The goal is not to produce a final draft card. The goal is to prove that BIE can identify legal roster-role coverage before draft guidance is trusted.

## Prior Failure

The earlier 1968 draft workflow failed because BIE produced plausible draft guidance before proving roster legality.

The critical exposed rule was that a legal 1968 Strat365 roster requires at least 5 starter-endurance pitchers. BIE also needs enough pitchers, pure relievers, primary catchers, and closer-endurance coverage.

## New Audit Artifacts

- Script: `baseball/parser/report_1968_predraft_role_coverage_audit_v0.py`
- Verifier: `baseball/parser/verify_1968_predraft_role_coverage_audit_v0.py`
- Local JSON report: `data/baseball/parsed/strat365/1968/reports/1968.predraft-role-coverage-audit.json`
- Local Markdown report: `data/baseball/parsed/strat365/1968/reports/1968.predraft-role-coverage-audit.md`

## Key Result

| Role Coverage | Count |
|---|---:|
| Players | 537 |
| Hitters | 325 |
| Pitchers | 212 |
| Starter-endurance pitchers | 152 |
| Pure relievers | 60 |
| Closer-endurance pitchers | 26 |
| Primary catchers | 50 |
| Card-backed players | 156 |

The verifier passed all legality checks.

## Closer-Endurance Resolution

The 1968 playerset/list metadata carries pitcher endurance such as `R4`, `S7/R3`, and `S9*`.

Authenticated card evidence contains richer relief text such as `relief(4)/4`, `relief(2)/5`, and `relief(3)/3`.

BIE now derives closer coverage from card evidence:

| Card Evidence | Derived Meaning |
|---|---|
| `relief(4)/4` | `R4/C4` |
| `relief(2)/5` | `R2/C5` |
| `relief(3)/0` | `R3` with no closer endurance |

The closer rule should remain enforced. The issue was that closer evidence existed only at the card-evidence layer.

## Top Derived Closer Candidates

| Player | Team | Derived Role | Salary | Score |
|---|---|---|---:|---:|
| McDaniel, Lindy | NYY '68 | R3/C3 | 2.70 | 75.23 |
| Romo, Vicente | CLE '68 | R4/C4 | 4.44 | 67.02 |
| Hoerner, Joe | STL '68 | R2/C5 | 1.71 | 65.28 |
| Messersmith, Andy | CAL '68 | R4/C2 | 6.18 | 62.02 |
| Hamilton, Steve | NYY '68 | R2/C4 | 1.53 | 60.19 |
| Wilhelm, Hoyt | CHW '68 | R2/C4 | 1.62 | 59.75 |

## Top-Slice Warning

The global hybrid-score board is not itself a draft card. Role coverage emerges by the top 60/top 100, but a draft card still needs role balancing.

| Slice | Hitters | Pitchers | SP | Pure RP | Closer | Primary C |
|---:|---:|---:|---:|---:|---:|---:|
| Top 25 | 25 | 0 | 0 | 0 | 0 | 1 |
| Top 40 | 36 | 4 | 3 | 1 | 1 | 1 |
| Top 60 | 48 | 12 | 8 | 4 | 3 | 3 |
| Top 100 | 58 | 42 | 30 | 12 | 6 | 4 |

## Metadata Debt

All 156 parsed 1968 card-evidence files currently report `source.season = 1980` even though the paths and player payloads are 1968. This is metadata debt, not a blocker for role derivation.

## Decision

BIE may continue toward 1968 draft preparation only through a rules-first workflow:

1. Pre-draft role coverage audit.
2. Role-balanced draft board.
3. Roster-template validation.
4. Post-draft roster legality validation after Strat assigns the roster.
