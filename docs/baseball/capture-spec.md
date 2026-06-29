# Capture Specification

## Purpose

The capture subsystem acquires baseball evidence.

Capture does not parse, normalize, score, rank, or infer.

Its job is to acquire evidence faithfully and record provenance.

## Capture Inputs

Examples:

- source provider
- season
- authentication/session state when required
- player list
- ballpark list
- league/team/game result source when available

## Capture Outputs

Every capture should produce:

- raw source file
- source URL
- capture timestamp
- provider
- season
- capture version
- validation status
- checksum where useful
- manifest or summary

## Current Captured Evidence

### 1980 authenticated card corpus

Status: complete and validated.

- full universe: 721 players
- hitters: 442
- pitchers: 279
- authenticated card HTML files: 721
- parsed card evidence files: 721
- warnings: 0
- failures: 0

Authenticated card HTML is local-only and gitignored.

### 1980 ballpark table

Status: captured and parsed.

- ballparks: 26
- fields: name, capacity, SI L, SI R, HR L, HR R

Raw ballpark HTML is local-only and gitignored.

## Capture Boundary

Capture may store source evidence.

Capture must not:

- normalize result labels
- compute probabilities
- rank players
- derive draft intelligence
- mix observed results into card evidence

## Future Capture Targets

- 20+ played 1980 seasons
- season/team/game/player results
- league standings and playoff outcomes where available
- 1968 card corpus
- 1968 ballparks
