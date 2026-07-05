# BIE 1968 Salary-Aware Roster Template v0

## Purpose

This document records the first salary-aware 1968 roster-template artifact.

The goal is to generate a legal 25-player candidate roster from the role-balanced draft pools while staying under the 80M salary cap.

This is a draft-assist template, not a final team recommendation and not an autonomous drafter.

## New Artifacts

- Builder: `baseball/parser/build_1968_salary_aware_roster_template_v0.py`
- Verifier: `baseball/parser/verify_1968_salary_aware_roster_template_v0.py`
- Local JSON template: `data/baseball/parsed/strat365/1968/draft-boards/1968.salary-aware-roster-template-v0.json`
- Local Markdown template: `data/baseball/parsed/strat365/1968/draft-boards/1968.salary-aware-roster-template-v0.md`

## Template Summary

| Metric | Value |
|---|---:|
| Salary cap | 80.00M |
| Salary used | 80.00M |
| Salary remaining | 0.00M |
| Players | 25 |
| Hitters | 14 |
| Pitchers | 11 |
| Primary catchers | 2 |
| Starter-endurance pitchers | 5 |
| Pure relievers | 6 |
| Closer-endurance pitchers | 2 |
| Card-backed players | 15 |

## Legality Result

The verifier passed all roster legality checks:

- exactly 25 players
- 14 hitters
- 11 pitchers
- at least 2 primary catchers
- at least 5 starter-endurance pitchers
- at least 4 pure relievers
- at least 1 closer-endurance pitcher
- salary at or below 80M
- no duplicate player IDs

## Hitter Position Coverage

| Position | Count |
|---|---:|
| C | 2 |
| 1B | 2 |
| 2B | 2 |
| 3B | 1 |
| SS | 2 |
| LF | 2 |
| CF | 1 |
| RF | 2 |

The first template originally over-selected cheap shortstops. The builder now includes a hitter-depth guardrail so no hitter position has more than 2 rostered players.

## Candidate Roster Shape

The template spends heavily on selected premium hitters and a top starter, then uses low-cost role/value players to satisfy legality and salary constraints.

Notable selections include:

- Luis Tiant as the top starter-endurance anchor
- Lindy McDaniel as a closer-qualified pure reliever
- Bill Freehan and Pat Corrales as primary catchers
- Willie McCovey, Gates Brown, Felipe Alou, Bill Sudakis, and Dick McAuliffe as premium hitter/position anchors

## Current Limitation

This is a greedy v0 template. It does not yet optimize for:

- ballpark strategy
- platoon construction
- defensive substitutions
- replacement options if players are drafted by others
- hitter/pitcher budget sensitivity
- live Strat365 draft availability

## Decision

BIE is now past basic 1968 legality readiness and has a first legal salary-aware candidate roster concept.

The next useful artifact should compare multiple roster templates, such as premium-hitter heavy, ace-pitcher heavy, balanced, and value-heavy builds.
