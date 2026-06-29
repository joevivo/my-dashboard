# Baseball Intelligence Engine

The Baseball Intelligence Engine, or BIE, is the durable analytical foundation behind the Strat baseball tools.

BIE is being proven as an analytical model before any UI work.

## Current Strategic Rule

Do not move BIE into UI until the 1980 model has been analytically proven.

The working sequence is:

1. Prove the 1980 card model.
2. Add salary, defense, and ballpark context.
3. Add roster-construction analysis.
4. Ingest 20+ played 1980 seasons as observed results.
5. Compare expected BIE signals against actual outcomes.
6. Calibrate.
7. Pivot the architecture to 1968.
8. Build UI only after the analytical model is proven.

## Current Layering

Raw Evidence
→ Card Evidence
→ Result Semantics
→ Probability
→ Matchup Profiles
→ Draft Signals
→ Context Signal Layers
→ Observed Results
→ Calibration
→ Applications

Applications consume BIE data. Applications do not define BIE data.

## Current Scope

- Strat-O-Matic Baseball 365
- 1980 validation season
- 1968 expansion season
- authenticated card evidence
- player roster metadata
- player defense metadata
- ballpark metadata
- draft signal modeling
- future observed-results ingestion

## Current Core Documents

- `architecture.md`
- `capture-spec.md`
- `capture-v020-status.md`
- `manager-domain-model.md`
- `roster-fixture-format-v0.md`
- `observed-results-ingestion-design-v0.md`
- `bie-parser-contract-v0.md`

## Current Committed Capabilities

- full 1980 authenticated card corpus validated
- card evidence parser
- result cell parser
- normalized result labels
- split ranges
- result modifiers
- result atoms
- printed result semantics
- result probabilities
- card probability summaries
- matchup probabilities
- matchup player profiles
- neutral draft signals
- salary-adjusted draft signals
- player roster metadata
- player defense metadata
- defensive draft signals
- defense-aware draft signals
- defense-aware candidate pool inventory
- ballpark parser
- ballpark-aware draft signals
- BIE regression runner

## Current Tech-Debt Rule

Any new signal layer should include:

- parser
- verifier
- inventory/report
- lookup if useful
- regression coverage
