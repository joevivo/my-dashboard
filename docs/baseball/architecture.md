# BIE Architecture

## Purpose

BIE transforms baseball evidence into validated, reusable intelligence.

The architecture must preserve the distinction between deterministic card truth and observed game results.

## Primary Layering

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

## Layer Responsibilities

### Raw Evidence

Stores acquired source evidence.

Examples:

- authenticated Strat 365 card HTML
- public player browser metadata
- ballpark HTML/table evidence
- future league/team/game result exports

Raw evidence is local-only when it contains authenticated or bulky source material.

### Card Evidence

Extracts facts printed or directly encoded on Strat card pages.

This layer should not infer draft value.

### Result Semantics

Normalizes printed outcomes into structured baseball outcome labels and dependencies.

Examples:

- SINGLE
- DOUBLE
- HOME_RUN
- GROUNDBALL_X
- FLYBALL_X
- ballpark_home_run_check
- ballpark_single_check

### Probability

Computes deterministic card probabilities from parsed evidence.

This is card truth, not observed performance.

### Matchup Profiles

Aggregates hitter-vs-pitcher probability behavior across the universe.

### Draft Signals

Creates draft-relevant analytical layers.

Current layers:

- neutral
- salary-adjusted
- defensive
- defense-aware
- ballpark-aware

### Context Signal Layers

Adds context without rewriting card truth.

Current context layers:

- salary
- defense
- ballpark

Future context layers:

- roster construction
- team ballpark fit
- platoon construction
- bullpen construction
- series strategy

### Observed Results

Future layer for actual played seasons.

Observed results must remain separate from deterministic card evidence.

### Calibration

Future layer that compares expected signal strength against actual performance.

## Architecture Rule

Applications consume validated BIE outputs.

Applications do not define the BIE model.
