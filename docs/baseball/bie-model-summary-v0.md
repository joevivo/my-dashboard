# BIE Model Summary v0

## Purpose

This report summarizes the current Baseball Intelligence Engine model stack for the 1980 Strat-O-Matic 365 player universe.

The goal is to distinguish:

- what signals exist
- what each signal means
- which signals are currently trustworthy
- which signals remain experimental

This is a product-facing model inventory, not a UI specification.

## Current Scope

- Season: 1980
- Player universe: 721 players
- Rankable hitters: 440
- Rankable pitchers: 279
- Ballparks: 26
- Observed calibration corpus: 3 Aquarium Drinkers observed seasons
- Observed player-seasons: 75
- Repeated observed players: 11

## Signal Stack

BIE currently uses a layered signal model.

```text
Card parsing
  -> result semantics
  -> result probabilities
  -> matchup player profiles
  -> neutral draft signals
  -> salary-adjusted draft signals
  -> defensive draft signals
  -> defense-aware draft signals
  -> ballpark-aware draft signals
  -> observed calibration reports
```

## 1. Card Parsing Signals

### What exists

- Parsed Strat card tables for hitters and pitchers
- Normalized result labels
- Result atoms
- Result modifiers
- Result semantics
- Probability summaries

### What it means

This is the deterministic card evidence layer. It converts Strat card text into structured outcomes such as singles, doubles, walks, strikeouts, groundball-X, flyball-X, ballpark checks, clutch modifiers, injury flags, and split-roll outcomes.

### Trust level

**High.**

The parser has full-corpus verification over the 1980 player universe. Current regression verifies 721 parsed player cards with zero missing parsed files and zero parser failures.

### Remaining limitations

- A small number of open split ranges remain partially unresolved.
- Some semantics are context-dependent and are intentionally tagged rather than over-modeled.
- This layer does not itself decide draft value.

## 2. Matchup Player Profiles

### What exists

- Hitter matchup profiles
- Pitcher matchup profiles
- Exact and partial matchup probability rows
- Batter handedness versus pitcher handedness splits

### What it means

This layer summarizes player card performance across batter/pitcher matchup contexts. It is the bridge between raw card outcomes and player-level draft scoring.

### Trust level

**High for structural card comparison. Medium for draft decision-making.**

The matchup corpus is broad and mechanically verified. It should be trusted for relative card-shape comparison, but not treated as a complete draft recommendation because roster construction, usage, injuries, and ballpark context are not fully represented here.

### Remaining limitations

- Partial unresolved open splits exist.
- It does not know actual league roster composition.
- It does not know manager behavior or player usage.

## 3. Neutral Draft Signal

### Source

`1980.neutral-draft-signals.json`

### What exists

- Neutral hitter draft score
- Neutral pitcher draft score
- Component scores from card-derived matchup profiles
- Neutral ranks before salary, defense, or ballpark adjustments

### What it means

The neutral draft signal is the baseline card-quality ranking. It asks: ignoring salary, defense, roster construction, and ballpark, which cards look strongest?

### Trust level

**Medium-high.**

It is useful as a pure card-strength baseline. It should not be used alone for drafting because Strat 365 is salary-capped, defense-sensitive, and ballpark-dependent.

### Product use

- Identify raw card strength
- Separate true card quality from later adjustments
- Detect expensive stars that are strong but may not be efficient

## 4. Salary-Adjusted Draft Signal

### Source

`1980.salary-adjusted-draft-signals.json`

### What exists

- Salary-adjusted rank
- Salary value score
- Neutral score retained for comparison
- Player salary parsed into raw, millions, and dollars

### What it means

The salary-adjusted signal asks whether a player offers useful card value relative to salary. It is the first product-oriented layer because Strat roster construction is constrained by an $80M cap.

### Trust level

**Medium.**

This is valuable for surfacing cheap or efficient players. It is also risky because low salary can make flawed players look attractive unless defense, usage, and roster role are considered.

### Product use

- Find low-cost role players
- Find salary-efficient pitchers
- Detect potential value traps
- Compare stars versus balanced roster construction

## 5. Defensive Draft Signal

### Source

`1980.defensive-draft-signals.json`

### What exists

- Hitter defensive position scores
- Best defensive position
- Position count
- Pitcher hold, balk, wild pitch, and defensive scores
- Defense unavailable flags

### What it means

The defensive signal evaluates player defensive contribution independent of hitting or pitching card value.

### Trust level

**Medium-high for defensive inventory. Medium for total player value.**

The defensive metadata is useful and verified, but its current value model is still generalized. It does not yet model team-specific GBX/FBX/CATCH-X exposure or roster-specific position scarcity.

### Product use

- Identify defensive anchors
- Detect hidden value in premium-position defenders
- Penalize bat-only players when defense matters
- Support roster construction checks

## 6. Defense-Aware Draft Signal

### Source

`1980.defense-aware-draft-signals.json`

### What exists

- Defense-aware draft rank
- Defense-aware draft score
- Salary-adjusted score retained
- Defensive score retained
- Defense neutralization flag

### What it means

The defense-aware signal combines salary-adjusted value with defensive value.

Current model weighting:

- Hitters: 75% salary-adjusted draft score + 25% best-position defensive score
- Pitchers: 85% salary-adjusted draft score + 15% pitcher defensive score

### Trust level

**Medium-high as the current primary draft baseline.**

This is currently the best general-purpose BIE draft ranking because it combines card value, salary, and defense. It should still be treated as a baseline rather than a final draft board.

### Product use

- Primary draft baseline
- Identify players with balanced value
- Compare offensive/pitching card value against defensive contribution
- Flag players whose rank depends heavily on defensive lift

### Remaining limitations

- Does not yet use team-specific GBX/FBX/CATCH-X exposure.
- Does not yet apply ballpark fit.
- Does not yet enforce roster construction or position scarcity.
- Does not yet distinguish starter workload from relief workload.

## 7. Ballpark-Aware Draft Signal

### Source

`1980.ballpark-aware-draft-signals.json`

### What exists

- Ballpark-aware rank
- Defense-aware rank retained
- Ballpark fit profiles by park
- Ballpark rank movement

### What it means

The ballpark-aware signal adds a context layer for each 1980 ballpark. It does not rewrite the card evidence. It adjusts ranking based on how player card opportunities interact with park single and home run factors.

Current model principle:

- Separate ballpark-context layer
- Does not modify deterministic card evidence
- Uses average left/right park factors in v0

### Trust level

**Medium. Experimental for final recommendations.**

The signal is useful for identifying park fit and park movement, but observed Aquarium results show that positive park movement alone does not guarantee strong actual output.

### Product use

- Identify park-fit candidates
- Identify players hurt by a specific park
- Explain rank movement from defense-aware to ballpark-aware
- Separate structural card quality from contextual park fit

### Remaining limitations

- Uses average L/R park factors in v0.
- Does not yet use projected league handedness mix.
- Does not yet model roster construction or platoon deployment.
- Observed calibration suggests this should be supporting evidence, not a draft verdict.

## 8. Observed Calibration Signals

### Sources

- `report_observed_player_batch_calibration_v0.py`
- `report_observed_player_aggregate_calibration_v0.py`

### What exists

- Observed player-season calibration
- Aggregate player calibration across repeated observed seasons
- Strong model / strong actual grouping
- Strong model / weak actual grouping
- Weak model / strong actual grouping
- Ballpark movement versus observed output grouping

### What it means

Observed calibration compares BIE rankings against actual simulated Strat team results. It is not yet a training set. It is an evidence layer for trust, caution, and model interpretation.

### Trust level

**Low-medium due to sample size, but strategically valuable.**

Three Aquarium teams are enough to reveal product and model issues. They are not enough to produce statistical certainty.

### Early findings

- Gossage is the strongest repeated-player validation signal so far.
- Positive Comiskey movement often failed to produce strong observed hitter results.
- Negative park movement did not prevent Hernandez or Gossage from producing strong outcomes.
- Repeated players are more valuable evidence than isolated player-seasons.

## Trust Summary

| Signal | Trust | Product Role | Caution |
|---|---:|---|---|
| Card parser | High | Deterministic evidence foundation | Does not imply draft value by itself |
| Result semantics/probabilities | High | Outcome math and card comparison | Some context remains tagged, not fully modeled |
| Matchup profiles | High/Medium | Player card shape comparison | Not roster- or usage-aware |
| Neutral draft signal | Medium-high | Raw card strength | Ignores salary, defense, park |
| Salary-adjusted signal | Medium | Cap-efficiency lens | Can overrate flawed cheap players |
| Defensive signal | Medium-high | Defensive inventory | Not yet exposure-weighted |
| Defense-aware signal | Medium-high | Current primary baseline | Still not roster- or park-final |
| Ballpark-aware signal | Medium/Experimental | Park-fit context | Supporting evidence only |
| Observed calibration | Low-medium | Trust and caution layer | Small sample size |

## Product Principles

1. Deterministic card evidence should remain separate from interpretive rankings.
2. Salary, defense, and ballpark layers should be explainable individually.
3. Ballpark movement is context, not proof.
4. Observed results should calibrate trust but not overfit the model.
5. Draft output should explain why a player is useful, risky, overpriced, or context-dependent.

## Recommended Next Product Step

Build a draft candidate explanation report that uses the current signal stack to explain top players by role.

The report should explain:

- card strength
- salary value
- defense
- park fit
- risk
