# BIE Parser Contract v0

## Purpose

The parser converts authenticated Strat Baseball 365 card HTML into structured card evidence.

The parser is not an intelligence engine.

Its job is to preserve what is printed or directly encoded on the authenticated card page, with provenance, so later layers can reason about GBX, FBX, ballpark effects, drafting, simulation, and roster strategy.

## Current Evidence Foundation

Season: 1980  
Source: Strat Baseball 365 authenticated card pages  
Universe size: 721 players  
Role split:
- Hitters: 442
- Pitchers: 279

Authenticated capture status:
- HTML files: 721
- Metadata files: 721
- Validated metadata statuses: 721
- Capture validation: FULL AUTHENTICATED CAPTURE VALIDATED

Authenticated card HTML and auth state are local-only and gitignored.

## Parser Boundary

### Parser may extract

The parser may extract facts directly present in authenticated card HTML.

Common fields:
- playerId
- playerName
- season
- team
- role
- sourceHtmlPath
- sourceMetadataPath
- sourceSha256
- capturedAt
- captureStatus
- balance
- rawCardText
- rawTables or equivalent card sections
- parsedAt
- parserVersion

Hitter fields:
- batting side / bats, if present
- defense text
- running text
- stealing / bunting / hit-and-run text, if present
- injury or supplemental printed traits, if present
- printed hitter card result cells

Pitcher fields:
- throwing hand
- pitcher marker text
- hold
- starter rating
- relief rating
- endurance or role text
- balk / wild pitch / error / fielding text, if present
- printed pitcher card result cells

Result-cell fields:
- source column
- source row / dice range, if determinable
- raw result text
- normalized result label only when normalization is lossless
- modifiers exactly as printed
- provenance pointer back to source section

### Parser may not infer

The parser must not infer or calculate:

- GBX meaning
- FBX meaning
- ballpark single / homer effects
- player value
- draft ranking
- simulation outcomes
- matchup recommendations
- defensive value
- run expectancy
- probability weights beyond directly printed dice ranges
- league strategy
- canonical baseball intelligence

Those belong to later layers.

## Parser Output Principle

The parser output must support this audit trail:

Authenticated HTML -> Parsed Card Evidence -> Canonical Baseball -> Intelligence

Every parsed field should either:
1. map directly to source HTML / metadata, or
2. be marked as parser metadata, such as parserVersion or parsedAt.

## Initial Parser Sample Set

Controlled sample for parser v0.1:

Hitters:
- 35273 Hernandez, Keith
- 31286 Brett, George
- 32392 Cooper, Cecil

Pitchers:
- 40040 Reuss, Jerry
- 37920 McGraw, Tug
- 32405 Corbett, Doug

Reason:
- includes known authenticated hitter evidence
- includes cards that exposed validation edge cases
- includes role-aware pitcher evidence
- includes Keith Hernandez, the original authentication proof card

## Acceptance Criteria for Parser v0.1

Parser v0.1 is accepted only when:

1. It parses the controlled sample set.
2. It rejects gated public shells.
3. It preserves player identity and role.
4. It extracts role-specific card traits.
5. It captures raw printed result evidence.
6. It writes structured JSON for each parsed card.
7. It includes source provenance for every parsed card.
8. It does not calculate intelligence metrics.
9. It does not interpret GBX, FBX, ballpark, or strategy.
10. It can be rerun deterministically.

## Non-Goals for Parser v0.1

Parser v0.1 will not:

- parse all 721 cards
- generate rankings
- evaluate draft value
- simulate games
- calculate card probabilities beyond obvious printed dice ranges
- normalize baseball outcomes aggressively
- power the UI
- modify existing Strat tools

## Next Layer After Parser

Only after parser v0.1 is accepted should we define:

- canonical card evidence schema
- full 721-card parse run
- GBX / FBX interpretation model
- ballpark-condition model
- player comparison intelligence
- draft intelligence
