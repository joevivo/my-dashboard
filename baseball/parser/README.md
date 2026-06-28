# BIE Parser

The parser converts authenticated Strat Baseball 365 card HTML into structured card evidence.

The parser is not an intelligence engine. It preserves printed/authenticated card evidence so later layers can reason about baseball concepts.

## Parser v0.1 Scope

Parser v0.1 parses a controlled six-card sample:

Hitters:
- 35273 Hernandez, Keith
- 31286 Brett, George
- 32392 Cooper, Cecil

Pitchers:
- 40040 Reuss, Jerry
- 37920 McGraw, Tug
- 32405 Corbett, Doug

## Parser Boundary

Allowed:
- source provenance
- player identity
- role
- balance
- hitter traits
- pitcher traits
- raw printed result evidence tables

Not allowed:
- GBX interpretation
- FBX interpretation
- ballpark interpretation
- draft value
- simulation
- rankings
- strategy recommendations

## Local-only parsed output

Parsed card evidence is written under:

```text
data/baseball/parsed/
