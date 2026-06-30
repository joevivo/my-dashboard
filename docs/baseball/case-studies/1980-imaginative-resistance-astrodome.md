# BIE Case Study: Imaginative Resistance 1980

## Team Context

Team: Imaginative Resistance

Owner: imagination

Manager: Daniel Altshuler

League Result: Won the Championship in Auto League 475685

Record: 90-72

Home Ballpark: Astrodome 1980

Initial Salary Cap: $80,000,000

Roster Value: $79,900,000

Cash Available: $100,000

Source Team URL: https://365.strat-o-matic.com/team/1820660

## Why This Case Matters

Imaginative Resistance is a strong contrast to Union Resistance.

Union Resistance was a Yankee Stadium finalist with extreme hitter spend, very cheap starter spend, and meaningful relief investment.

Imaginative Resistance won the same league from Astrodome 1980 with a much more run-suppression-oriented construction.

This gives BIE a second successful outside roster shape to inspect before preparing for the 1968 draft.

## Actual Team Shape

Imaginative Resistance was a lower-power, pitching-supported roster.

Reported simulated team totals:

- Runs: 750
- Home Runs: 84
- Team BA: .277
- Team OBP: .337
- Team SLG: .387
- Team ERA: 3.47
- Team WHIP: 1.29
- Runs Allowed: 630
- Home Runs Allowed: 128

## BIE Import Result

The Strat365 team roster importer successfully converted the public team page into a BIE roster-template CSV.

Importer/evaluator result:

- Players resolved: 24
- Rows unresolved: 0
- Salary total: $79.90M

This validates the URL-based case-study workflow.

## Archetype Comparison

BIE compared the imported roster against current 1980 roster archetypes:

| Archetype | Score | Errors | Warnings |
|---|---:|---:|---:|
| value-spine | 68 | 0 | 5 |
| pitching-supported | 74 | 0 | 4 |
| premium-anchor | 74 | 0 | 4 |

The current evaluator sees the team as tied between pitching-supported and premium-anchor.

Given Astrodome 1980 and the actual run-suppression profile, pitching-supported is the better analytical reading.

## Salary Allocation

BIE calculated:

- Hitters: $48.84M
- Starters: $24.47M
- Relief: $6.59M
- Total: $79.90M

## Structural Tensions

Against current archetype ranges, BIE identified:

- hitter salary above the value-spine and pitching-supported ranges
- starter salary slightly above the value-spine range and above the premium-anchor range
- relief salary below all current archetype ranges
- relief count thin at 3
- high number of model-risk players: 13

These are structural tensions, not automatic defects.

The actual championship result shows that a successful Astrodome roster can win with low relief spend if the starter group is strong enough and the offensive environment is controlled.

## Product Lesson

This case confirms that BIE should treat successful rosters as evidence for archetype refinement, not as simple pass/fail examples.

Imaginative Resistance suggests that BIE's current pitching-supported archetype may need a variant with:

- strong starter investment
- low bullpen investment
- contact/on-base offense rather than power offense
- park-driven run suppression
- enough defense to survive a low-scoring environment

## Candidate Archetype Hypothesis

Imaginative Resistance may represent a variant of pitching-supported construction:

Starter-Forward Run Suppression

Possible characteristics:

- above-average starter spend
- relatively thin bullpen
- modest power
- high-contact offense
- park-supported run prevention
- lower run scoring than offense-first builds
- enough run differential to win despite fewer explosive offensive events

This is a hypothesis, not a recommendation.

## Comparison to Union Resistance

| Case | Result | Park | Runs | HR | ERA | WHIP | Hitter $ | Starter $ | Relief $ |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| Union Resistance | Lost Finals | Yankee Stadium 1980 | 984 | 226 | 4.16 | 1.38 | $61.92M | $6.15M | $11.55M |
| Imaginative Resistance | Won Championship | Astrodome 1980 | 750 | 84 | 3.47 | 1.29 | $48.84M | $24.47M | $6.59M |

The two successful rosters reached the finals through very different constructions.

That is the important BIE lesson.

## Impact on 1968 Draft Preparation

For the 1968 draft goal, this case reinforces that BIE should compare possible roster shapes instead of forcing one universal budget model.

When we prepare 1968, BIE should ask:

- Is the ballpark amplifying offense or suppressing runs?
- Does the roster need elite bats, elite starters, or bullpen leverage?
- Is a thin bullpen acceptable because the starter group carries enough innings?
- Is the offense built for power, OBP, contact, or platoon advantage?
- Are structural tensions actual weaknesses or intentional construction choices?

## Discipline Note

BIE should not say:

"Increase relief spend."

BIE should say:

"This championship roster spent less on relief than current archetypes expect. Given the actual result, this may represent a viable starter-forward run-suppression construction."

## Next Analytical Question

Import and evaluate at least one more successful team from the same league, preferably from a different ballpark.

The goal is not to copy any one champion.

The goal is to build a small library of successful roster shapes that BIE can use when evaluating 1968 draft options.
