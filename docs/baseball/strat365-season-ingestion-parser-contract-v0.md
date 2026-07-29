# Strat365 League-Season Parser Contract v0

## Purpose

Define the first parser boundary between an immutable Strat365 raw-capture run and a structured, non-canonical league-season snapshot that BIE can use for evidence-backed conversation.

This contract applies to the completed league-night run for league `479336`, player set `1968`, and league date `2026-07-21`.

## Architectural boundary

The parser must:

1. Read the authoritative `run-manifest.json`.
2. Read the frozen `game-capture-plan.json` only for immutable request-contract validation.
3. Select source artifacts exclusively from current manifest ledger references.
4. Never discover active inputs by scanning filenames.
5. Never read recovery manifests as active parser inputs.
6. Never modify raw bodies, response headers, metadata, the frozen plan, or the run manifest.
7. Write only to a separate parsed or staging location.
8. Keep canonical promotion eligibility equal to `NO`.

## Authoritative run

Run directory:

`data/baseball/raw/strat365/1968/season-ingestion/league-479336/2026-07-21/capture-20260722T181249Z`

Frozen-plan SHA-256:

`38D42C302BB7D982895C00F8EE11C8D6001D800793E38ECB46E078A7A11A8C9F`

Completed-manifest SHA-256:

`998C1AC76627FFCBCFAB2B869FD6740C831C545F7514854B4CCD3AD648742DBC`

## Required input inventory

The manifest must contain exactly 55 captured requests:

- 1 `leagueScores`
- 18 `gameRecap`
- 18 `gamePlayByPlay`
- 18 `gameReplay`

The 54 game requests must cover games 1 through 18, with exactly one request from each game source family.

Each manifest request must reference:

- one immutable raw response body;
- one immutable response-headers file;
- one immutable metadata file.

Expected active artifact references:

- 55 bodies;
- 55 response-header files;
- 55 metadata files;
- 165 unique active artifacts.

## Request identity

The manifest ledger is authoritative for `requestId`.

Game metadata does not need to duplicate `requestId`.

A game request is identified through the correlated combination of:

- manifest `requestId`;
- `gameId`;
- `sourceFamily`;
- `requestedUrl`;
- `effectiveUrl`;
- raw-response path;
- response-headers path;
- metadata path;
- byte count;
- raw-body SHA-256;
- semantic and source validation evidence.

The parser must not reject valid metadata solely because it lacks a redundant `requestId` property.

## Input acceptance gates

Before parsing HTML, the parser must confirm:

- frozen-plan hash matches the authoritative hash;
- manifest hash matches the accepted completed checkpoint;
- frozen plan remains frozen;
- canonical promotion eligibility is `NO`;
- all 54 game requests correlate between plan and manifest;
- all 55 requests are captured;
- all game requests have attempt count 1;
- all required HTTP statuses are 200;
- no active request references a recovery artifact;
- all active artifact files exist;
- body byte counts match the manifest;
- body SHA-256 values match the manifest;
- metadata JSON parses;
- semantic validation is `PASS`;
- source validation is `PASS`;
- effective URL matches requested URL;
- no unexpected redirect is recorded.

The parser must fail closed if any required gate fails.

## Initial structured output

The first structured output must be a non-canonical league snapshot containing:

### Run provenance

- parser schema version;
- source run directory;
- league ID;
- player-set year;
- league date;
- frozen-plan SHA-256;
- manifest SHA-256;
- parser timestamp;
- canonical promotion eligibility `NO`.

### League identity

- expected team count;
- discovered team IDs;
- team names where source evidence supports them;
- unresolved identity fields explicitly represented as unknown.

### Series

For each of the six opening-night series:

- series key;
- two team IDs;
- game IDs;
- game count;
- source completeness;
- evidence references.

### Games

For each of the 18 games:

- game ID;
- series key;
- team IDs;
- home and away identity when supported;
- final score;
- winner and loser;
- inning or final-state evidence;
- recap availability;
- play-by-play availability;
- replay availability;
- source validation status;
- source artifact references.

### Evidence and uncertainty

Every derived fact must distinguish:

- directly captured source evidence;
- parser-derived values;
- unresolved or unavailable values;
- validation failures.

## Conversational readiness

After the initial parser passes validation, BIE may discuss:

- all 18 completed games;
- opening-night scores and winners;
- the six opening series;
- league-wide opening-night results;
- team performance supported by the captured game evidence;
- recap and play-by-play observations;
- the user's team once its team ID is explicitly mapped.

The parser must not claim to know the next opponent after the current series unless a future schedule or team-schedule source supports that conclusion.

The parser must not provide roster-matchup analysis until authoritative roster and player identity sources are correlated.

## Output boundary

Initial parsed output is evidence-backed staging data, not canonical data.

Permitted initial destination family:

`data/baseball/parsed/strat365/1968/season-ingestion/league-479336/2026-07-21/`

Prohibited during the initial parser step:

- canonical promotion;
- canonical file replacement;
- roster inference unsupported by source evidence;
- schedule inference unsupported by source evidence;
- staging, committing, or pushing without explicit approval.

## Failure behavior

The parser must exit nonzero and avoid publishing a completed output if:

- any authoritative control hash changes;
- a required request is absent;
- a required artifact is absent;
- a body hash or byte count differs;
- semantic or source validation fails;
- source-family coverage is incomplete;
- duplicate game or request identity is found;
- parsed game facts conflict across sources without an explicit conflict record.

Partial diagnostic output may be written only to a temporary path and must not be promoted as a completed league snapshot.

## Regression fixture

The companion fixture is:

`data/baseball/fixtures/strat365-season-ingestion-parser-contract-v0.json`

It defines the authoritative run expectations and minimum conversational-readiness boundary for the first parser implementation.
