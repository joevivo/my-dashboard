# BIE Case Study: Union Resistance 1980

## Team Context

Team: Union Resistance 1980

Owner/Manager: John Brown

League Result: Lost the Finals in Auto League 475685

Record: 97-65

Home Ballpark: Yankee Stadium 1980

Initial Salary Cap: $80,000,000

Roster Value: $79,620,000

## Why This Case Matters

Union Resistance is useful because it is not an Aquarium Drinkers team and not a user-built team.

It provides a baseline against a successful outside roster construction.

This team nearly won its league, so BIE should not treat structural deviations as automatic flaws.

## Actual Team Shape

Union Resistance was a high-offense roster with low-cost starter volume and substantial relief usage.

Reported simulated team totals:

- Runs: 984
- Home Runs: 226
- Team BA: .306
- Team OBP: .359
- Team SLG: .484
- Team ERA: 4.16
- Team WHIP: 1.38

## BIE Evaluator Result

Command context:

- Ballpark: Yankee Stadium 1980
- Archetype: premium-anchor
- Cap: $80M

Evaluator result after slot-aware name matching and full defensive eligibility support:

- Players resolved: 24
- Rows unresolved: 0
- Salary total: $79.62M
- Archetype match score: 80/100
- Required hitter positions: covered

## Salary Allocation

BIE calculated:

- Hitters: $61.92M
- Starters: $6.15M
- Relief: $11.55M
- Total: $79.62M

## Structural Tensions

Against the premium-anchor archetype, BIE identified:

- hitter salary is $11.92M above the archetype's expected ceiling
- starter salary is $9.85M below the archetype's expected floor

These are structural tensions, not automatic defects.

The actual team result shows that a successful Yankee Stadium roster can violate BIE's current premium-anchor salary bands.

## Product Lesson

This case showed that BIE should not treat archetype mismatch as roster failure.

Better interpretation:

- The roster is hitter-heavy.
- The roster is starter-light.
- The roster has meaningful relief investment.
- The roster covers required hitter positions.
- The roster has many model-risk players.
- The roster was still highly successful.

This suggests BIE needs room for successful non-standard constructions.

## Candidate Archetype Hypothesis

Union Resistance may represent an archetype not yet formalized in BIE:

Offense-First Bullpen Leverage

Possible characteristics:

- extreme hitter spend
- cheap starter volume
- meaningful relief spend
- high run production
- tolerance for thin starter cards
- strong enough bullpen to absorb workload pressure
- sufficient defensive flexibility

This is a hypothesis, not a recommendation.

## Discipline Note

BIE should not say:

"Move money from hitters to starters."

BIE should say:

"This roster is much more hitter-heavy and starter-light than current archetype expectations. Given its strong actual result, treat it as a successful alternate construction candidate."

## Impact on 1968 Draft Preparation

For the 1968 draft goal, this case study matters because it warns against overfitting to neat budget bands.

When reviewing 1968 candidate rosters, BIE should support decisions by showing:

- roster shape
- archetype fit
- structural tensions
- role dependencies
- park context
- model-risk flags

BIE should not pretend that one archetype range defines the only successful roster shape.

## Next Analytical Question

Find at least one more successful non-Aquarium 1980 roster and compare:

- hitter spend
- starter spend
- relief spend
- ballpark
- runs scored
- ERA/WHIP
- postseason result
- BIE archetype fit
