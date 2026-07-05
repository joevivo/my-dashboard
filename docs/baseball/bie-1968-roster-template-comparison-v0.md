# BIE 1968 Roster Template Comparison v0

## Purpose

This document records the first multi-template roster comparison artifact for the 1968 Strat-O-Matic 365 player pool.

The comparison is intended to answer:

> Can BIE generate multiple legal 80M roster-construction concepts with different pitching/hitting budget shapes?

This is a draft-assist artifact. It is not an autonomous drafter and it is not a final team recommendation.

## Artifacts

Tracked scripts:

- `baseball/parser/build_1968_roster_template_comparison_v0.py`
- `baseball/parser/verify_1968_roster_template_comparison_v0.py`

Generated local outputs:

- `data/baseball/parsed/strat365/1968/draft-boards/1968.roster-template-comparison-v0.json`
- `data/baseball/parsed/strat365/1968/draft-boards/1968.roster-template-comparison-v0.md`

The generated draft-board outputs are local/generated artifacts and are not expected to be committed unless the repo policy changes.

## Strategy Templates

The v0 comparison currently emits four legal 25-player templates:

| Strategy | Total Salary | Hitter Salary | Pitcher Salary | Pitcher Band |
|---|---:|---:|---:|---:|
| balanced | 80.00 | 44.05 | 35.95 | 28.00-42.00 |
| premium_hitter_heavy | 80.00 | 53.78 | 26.22 | 22.00-32.00 |
| ace_pitcher_heavy | 79.99 | 24.71 | 55.28 | 45.00-60.00 |
| value_heavy | 79.74 | 53.52 | 26.22 | 24.00-36.00 |

## Legality Checks

Every template passes the current legality checks:

- 25 total players
- 14 hitters
- 11 pitchers
- at least 2 primary catchers
- at least 5 starter-endurance pitchers
- at least 4 pure relievers
- at least 1 closer-endurance pitcher
- salary at or below 80.00M
- pitcher salary within the configured strategy band
- no duplicate player IDs
- hitter coverage at C, 1B, 2B, 3B, SS, LF, CF, and RF

## Important Correction

Earlier comparison attempts produced legal but strategically unusable rosters, including hitter-heavy/value-heavy builds with roughly 74M spent on hitters and only 6M spent on pitching.

That is not a viable Strat365 construction model.

The v0 builder now uses pitcher budget bands and reserved pitcher salary logic so each strategy must carry a credible pitching spend.

## Interpretation

### Balanced

The balanced template spends meaningfully on both sides of the roster:

- 44.05M hitting
- 35.95M pitching

This is the best current baseline for general comparison.

### Premium Hitter Heavy

The premium-hitter-heavy template is hitter-forward while preserving a credible pitching floor:

- 53.78M hitting
- 26.22M pitching

This is now plausible as a hitter-forward construction concept.

### Ace Pitcher Heavy

The ace-pitcher-heavy template is clearly distinct:

- 24.71M hitting
- 55.28M pitching

This is useful as an extreme pitcher-forward reference point.

### Value Heavy

The value-heavy template is legal and salary-aware, but its budget shape is very close to premium-hitter-heavy:

- 53.52M hitting
- 26.22M pitching

For v0, this should be interpreted as a value-scored roster, not a materially budget-distinct roster. Future versions should improve this strategy by making it distinct through player overlap, value density, or salary-reserve behavior.

## Current Limitations

The comparison builder is still greedy. It does not yet perform exhaustive optimization.

It also does not yet model:

- ballpark fit
- platoon usage
- defensive substitution value
- injury risk
- bullpen usage realism beyond role legality
- live draft availability
- replacement pivots when a target is drafted
- player-card side-specific strengths

## Decision

BIE has now moved beyond simple legality readiness.

The system can produce:

1. A 1968 pre-draft role coverage audit
2. A 1968 role-balanced draft board
3. A legal salary-aware roster template
4. Multiple legal salary-banded roster-construction concepts

This is sufficient for analytical draft preparation, but not yet sufficient for autonomous drafting.

## Recommended Next Artifact

The next useful artifact is:

> 1968 roster template distinctness audit v0

That should compare the four templates by:

- player overlap
- shared premium players
- shared cheap role players
- salary allocation by role
- salary allocation by hitter position
- salary allocation by pitcher function
- card-backed share
- top replacement candidates per strategy
