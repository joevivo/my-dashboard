# BIE 1968 Role-Balanced Draft Board v0

## Purpose

This document records the first role-balanced 1968 draft-board artifact.

The goal is to turn the global hybrid ranking into human-usable draft pools that protect roster legality.

This is not an autonomous drafter and does not produce a final team.

## New Artifacts

- Builder: `baseball/parser/build_1968_role_balanced_draft_board_v0.py`
- Verifier: `baseball/parser/verify_1968_role_balanced_draft_board_v0.py`
- Local JSON board: `data/baseball/parsed/strat365/1968/draft-boards/1968.role-balanced-draft-board-v0.json`
- Local Markdown board: `data/baseball/parsed/strat365/1968/draft-boards/1968.role-balanced-draft-board-v0.md`

## Board Coverage

| Coverage | Count |
|---|---:|
| Players | 537 |
| Hitters | 325 |
| Pitchers | 212 |
| Primary catchers | 50 |
| Starter-endurance pitchers | 152 |
| Pure relievers | 60 |
| Closer-qualified pitchers | 26 |
| Card-backed players | 156 |

The verifier passed all bucket and legality-coverage checks.

## Draft Buckets

The board emits these draft-assist pools:

- Premium hitters
- Primary catchers
- Starter-endurance pitchers
- Pure relievers
- Closer-qualified pitchers
- Cheap hitter values
- Cheap pitcher values
- Card-backed pitchers

## Leading Bucket Examples

| Bucket | Leading Players |
|---|---|
| Premium hitters | Gates Brown, Carl Yastrzemski, Merv Rettenmund, Willie McCovey, Willie Horton |
| Primary catchers | Bill Freehan, Pat Corrales, Tom Satriano, Andy Etchebarren, Frank Fernandez |
| Starter-endurance pitchers | Luis Tiant, Dave McNally, Bob Gibson, Jim Nash, Steve Blass |
| Pure relievers | Lindy McDaniel, Moe Drabowsky, Vicente Romo, Joe Hoerner, Frank Linzy |
| Closer-qualified pitchers | Lindy McDaniel, Vicente Romo, Joe Hoerner, Andy Messersmith, Steve Hamilton |
| Cheap hitter values | Sonny Jackson, Tom Tresh, Jerry Adair, Bud Harrelson, Hector Torres |
| Cheap pitcher values | Gary Wagner, John Morris, John Boozer, Bill Landis, Dennis Higgins |
| Card-backed pitchers | Luis Tiant, Lindy McDaniel, Dave McNally, Bob Gibson, Vicente Romo |

## Interpretation

The role-balanced board should be used as a draft-assist report, not as a direct ranking.

A legal 1968 draft plan must protect these minimums:

- 13 hitters
- 11 pitchers
- 2 primary catchers
- 5 starter-endurance pitchers
- 4 pure relievers
- 1 closer-endurance pitcher

## Current Limitation

This board does not yet assemble a full roster template, enforce a salary cap, or model live draft availability.

The next artifact should be a salary-aware roster-template builder that selects a legal 25-player candidate roster from these buckets.
