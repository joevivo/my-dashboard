# Strat365 Manual League Raw-Capture Harvester Design v0

**Status:** Approved
**Approved by:** Ginto
**Approval date:** 2026-07-22
**Governing contract:** `strat365-league-season-ingestion-source-contract-v0`
**Reference fixture:** Auto League 479336, 2026-07-21
**Implementation state:** Design only

## 1. Objective

Define the first manual, league-date-scoped process for capturing immutable
Strat-O-Matic 365 raw HTML and associated response metadata.

This design does not authorize parsing, normalization, canonical promotion,
reconciliation implementation, or unattended scheduling.

## 2. Proposed artifacts

- Harvester: `baseball/harvester/capture_strat365_league_night_raw_v0.ps1`
- Run-spec schema: `data/baseball/config/strat365/capture-run-schema-v0.json`
- Opening Night run spec: `data/baseball/config/strat365/league-479336-2026-07-21-capture-run-v0.json`

Proposed invocation:

```powershell
.\baseball\harvester\capture_strat365_league_night_raw_v0.ps1 `
    -RunSpecPath .\data\baseball\config\strat365\league-479336-2026-07-21-capture-run-v0.json
```

## 3. Run-specification boundary

The executable must not hardcode league ID, player-set year, team IDs,
league date, expected game count, expected series count, or source pages.

The run specification will provide:

- schema version;
- base URI;
- player-set year;
- league ID and league date;
- expected team, game, and series counts;
- team IDs;
- required source families;
- batting, pitching, and transaction pagination seeds;
- raw capture-root policy.

## 4. Raw run directory

Each execution creates a unique directory:

`data/baseball/raw/strat365/{year}/season-ingestion/league-{leagueId}/{leagueDate}/capture-{utcTimestamp}/`

A run contains:

- `run-spec.json`;
- `run-manifest.json`;
- `run-summary.json`;
- raw response bodies;
- response headers;
- one metadata record per response attempt.

Existing run directories and files must never be overwritten.

## 5. Execution sequence

1. Validate the run specification and output path.
2. Create the immutable run directory.
3. Capture the dated league scores page.
4. Extract and deduplicate game links and game IDs.
5. Evaluate preliminary final, game, duplicate, and series signals.
6. Discover and validate team IDs, pagination links, and required source routes.
7. Freeze a deduplicated capture plan before bulk source capture.
8. Capture recap, play-by-play, and replay for every discovered game.
9. Capture required league, statistics, leader, transaction, and team pages.
10. Follow approved pagination with duplicate-URL, route-scope, and maximum-page guards.
11. Write metadata, manifest, validation results, and summary.
12. Evaluate the complete-night gate and stop without promotion.

The frozen capture plan must record every planned request, source family,
identifier, pagination coordinate, and required or optional status. Discovered
league, team, and game identifiers must match the run specification and scores
evidence before their routes are admitted to the plan.

The final manifest must distinguish planned, attempted, captured, failed, and
skipped requests. Newly discovered links must not silently expand the capture
scope after the plan is frozen.

## 6. Transport

The Windows implementation will use unauthenticated direct HTTP GET through:

`curl.exe --ssl-no-revoke`

It must follow redirects, retain response headers separately, report the
effective URL and HTTP status, and preserve body bytes without normalization.

Retries must retain attempt-specific evidence and must not overwrite an
earlier response or metadata record.

## 7. Permitted extraction

The harvester may extract only navigation and validation evidence:

- game IDs and game links;
- team IDs and team links;
- pagination links and terminal signals;
- final indicators and series identities;
- route-specific semantic markers.

It must not emit normalized players, standings, transactions, innings,
plate appearances, boxscore rows, or statistical records.

## 8. Validation

Validation has three levels:

1. Transport: successful HTTP response, nonempty bytes, effective URL, hash.
2. Source: route-specific semantic markers and known false-negative fixes.
3. Night: expected unique finals, series coverage, required sources, and pagination.

The leaders page must not require HTML tables.

The team schedule must not require active-player markers.

Recap validation must not reuse scores-page variables.

Game-ID contiguity is reported as a signal and is not the sole completeness gate.

## 9. Failure behavior

A failed or partial run must preserve all evidence already captured.

Proposed exit codes:

- `0`: raw capture and all configured gates passed;
- `2`: league night incomplete;
- `3`: required source or pagination validation failed;
- `4`: invalid run specification or unsafe output path;
- `5`: unexpected execution failure.

Canonical-promotion eligibility is always `NO` for this v0 harvester.

## 10. Acceptance criteria

The Opening Night positive fixture must discover 18 unique games, capture
all three game routes for each game, capture all configured source families,
prove pagination completion, reproduce stored SHA-256 values, and pass the
complete-night gate.

A negative fixture must retain raw evidence while failing the complete-night gate.

Terminal output must end with a compact `# RESULT SUMMARY`.

## 11. Approval

Ginto approved this amended manual harvester design on 2026-07-22.

This approval authorizes implementation only of:

- the manual PowerShell raw-capture harvester;
- the run-specification schema and Opening Night fixture;
- immutable raw response and header storage;
- response metadata, capture plans, manifests, and summaries;
- source-specific and complete-night validation;
- positive and negative raw-capture verification.

Parser implementation, normalized schemas, reconciliation, canonical promotion,
frontend or backend integration, and unattended scheduling remain separately gated.
