# Strat365 League-Level Season-Ingestion Source Contract v0

**Schema version:** `strat365-league-season-ingestion-source-contract-v0`
**Status:** Approved
**Approved by:** Ginto
**Approval date:** 2026-07-22
**Reference fixture:** Auto League 479336, 1968 player set
**Evidence date:** Opening Night, 2026-07-21

## 1. Purpose and authority

This contract defines the authoritative source, transport, raw-capture, identity,
completeness, validation, provenance, reconciliation, and promotion requirements
for league-level Strat-O-Matic 365 season ingestion.

The contract governs later harvester, parser, and canonical-promotion work. The
Opening Night fixture validates the contract but must not cause league IDs, team
IDs, game counts, dates, or player-set years to be hardcoded into ingestion logic.

## 2. Current implementation boundary

This contract authorizes no implementation by itself.

The following remain deferred until explicit approval:

- the first manual league-level raw-capture harvester;
- HTML parsing and normalized record generation;
- canonical season promotion;
- unattended capture or scheduling;
- browser automation or authenticated-session handling.

## 3. Reference fixture

- League ID: `479336`
- Player set: `1968`
- Teams: `12`
- Divisions: `4`
- Designated hitter: `No`
- Salary cap: `$80M`
- Reference team ID: `1851052`
- Reference team: Aquarium Drinkers
- Owner: JoeGinto
- Manager: Joe Ginto
- Ballpark: Astrodome 1968
- Opening Night league date: `2026-07-21`
- Opening Night game IDs: `1` through `18`
- Opening Night result: `18` finals and `18` unique game links

The expected game and series counts for future nights must come from league
configuration or observed schedule context, not from a universal constant.

## 4. Transport contract

Confirmed sources use unauthenticated direct HTTP `GET`.

- Authentication cookies are not required.
- Referer headers are not required.
- Browser automation and Playwright are not required.
- Core sources are server-rendered HTML.
- No useful JSON endpoint was found for the main workflow.
- On the current Windows workstation, `curl.exe` requires `--ssl-no-revoke`.
- `--ssl-no-revoke` bypasses unavailable Schannel revocation lookup while
  retaining normal certificate validation.

Each response must record both the requested source URL and effective URL.

## 5. Confirmed source routes

### Game discovery

- `/league/scores/{leagueId}`
- `/league/scores/{leagueId}/{YYYY-MM-DD}`

### Individual games

- `/game/{leagueId}/{gameId}`
- `/game/playbyplay/{leagueId}/{gameId}`
- `/game/replay/{leagueId}/{gameId}`

### League views

- `/league/{leagueId}`
- `/league/schedule/{leagueId}`
- `/league/transactions/{leagueId}`
- `/league/stats/players/batting/{leagueId}/{positionFilter}/{sortField}/{page}`
- `/league/stats/players/pitching/{leagueId}/{roleFilter}/{sortField}/{page}`
- `/league/stats/leaders/{leagueId}`

### Transaction views

- `/league/transactions/adds/{leagueId}`
- `/league/transactions/drops/{leagueId}`
- `/league/transactions/trades/{leagueId}`
- `/league/waivers/{leagueId}`
- `/league/transactions/team/{teamId}`

### Team views

- `/team/real/{teamId}`
- `/team/sim/{teamId}`
- `/team/leftright/{teamId}`
- `/team/homeroad/{teamId}`
- `/team/fielding/{teamId}`
- `/team/misc/{teamId}`
- `/team/schedule/{teamId}`

## 6. Source responsibilities

The league scores page is the authoritative game-discovery root for a league date.

The recap/boxscore is the principal source for final score, linescore, player game
statistics, pitcher decisions, and home-run summary.

The play-by-play page is the principal source for event order, inning state,
manager decisions, substitutions, and injury references.

Replay is a required raw source but is not a substitute for recap or play-by-play.

Standings, league statistics, leaders, and team pages are cumulative official
snapshots used for reconciliation. They are not immutable game-event records.

Transactions provide dated operational history and must later be reconciled
against observed roster differences.

## 7. Immutable raw-capture contract

Raw HTTP response bodies must be retained exactly as captured and kept separate
from parsed and canonical data.

A retry or later observation must create a new capture. Existing raw files must
never be overwritten, normalized in place, or silently replaced.

Each captured response requires metadata containing:

- schema version;
- source URL;
- effective URL;
- source-route classification;
- league ID;
- team ID when applicable;
- Strat game ID when applicable;
- league date when applicable;
- UTC capture timestamp;
- HTTP status;
- byte count;
- SHA-256 of the raw response bytes;
- validation results;
- provenance linking the capture to its run and discovery context.

Failed or incomplete responses may be retained as raw evidence but must be
identified clearly as unsuccessful captures.

## 8. League-night completeness gate

A league night is eligible to advance only when all configured completeness
requirements pass.

For the Opening Night fixture, a complete night requires:

- exactly `18` unique completed game IDs;
- exactly `18` final indicators;
- all `6` expected series;
- no duplicate game IDs;
- resolvable recap, play-by-play, and replay routes for every discovered game.

Contiguous game IDs are supporting evidence only. Contiguity must never be the
sole completeness rule.

A partial, ambiguous, or internally inconsistent night must remain in raw storage
and must never be promoted into the canonical season dataset.

## 9. Canonical game identity and deduplication

The canonical game identity is:

`(leagueId, stratGameId)`

A game ID must never be treated as globally unique outside its league.

League date, participants, and source URLs are validation and reconciliation
attributes. They do not replace the canonical deduplication identity.

Repeated captures of the same game are separate source observations, not separate
canonical games.

## 10. Pagination requirements

League batting and pitching statistics must capture every available page.

Transaction history must follow all available 100-row offsets, including routes
such as `/100`, `/200`, and `/300`, until an explicit terminal condition is
observed.

Pagination completion must be proven by captured evidence. A first page alone
must not be represented as complete league coverage.

## 11. Source-specific validation rules

A valid source response requires HTTP success, nonempty raw content, expected
route identity, and source-appropriate semantic evidence.

Known invalid validator assumptions must not be repeated:

1. The leaders page is valid without HTML tables. Leader content, not table
   presence, is the semantic requirement.
2. A team schedule page does not require an active-player-count marker.
3. Recap validation must use fresh route-specific variables and must not inherit
   scores-page markers from an earlier request.
4. Pitching saves are labeled `S`, not `SV`.
5. Complete games are not exposed by the confirmed league pitching page.

Validation rules must be specific to the source type rather than based on one
shared page-layout assumption.

## 12. Reconciliation contract

Normalized game records must eventually support reconstruction of basic
cumulative team and player statistics.

Reconstructed totals must be compared with:

- official standings;
- league batting and pitching snapshots;
- team cumulative-statistics views;
- team split and miscellaneous views where applicable;
- transaction history and resulting roster differences.

A reconciliation difference must be preserved as an explicit result. Official
snapshot data must not silently overwrite reconstructed game evidence.

## 13. Promotion boundary

Raw capture, parsing, normalization, reconciliation, and canonical promotion are
separate stages.

No league night may enter the canonical season dataset unless:

- the night-completeness gate passes;
- every required raw source has capture metadata and SHA-256;
- canonical game identities are unique;
- pagination requirements pass;
- parsing succeeds under an approved schema;
- required reconciliation checks complete;
- provenance remains traceable to immutable raw captures.

The exact normalized schemas and reconciliation tolerances will be defined in
later approved contracts.

## 14. Manual harvester constraints

After this contract is approved, the first harvester will be manual and
league-date scoped.

It must:

- use direct unauthenticated HTTP GET;
- discover games from the scores source;
- capture raw sources without parsing them;
- write immutable response bodies and metadata;
- evaluate capture and night-completeness gates;
- produce a compact run summary;
- stop without canonical promotion when any required gate fails.

It must not include unattended scheduling, parser logic, or canonical mutation.

## 15. Approval

Ginto approved this v0 source contract on 2026-07-22.

The contract is now authoritative for design of the first manual league-level
raw-capture harvester. Parser implementation, canonical promotion, and unattended
scheduling remain outside the approved implementation boundary.
## BIE-authored game-story authority

Strat-O-Matic league headlines and autogenerated recap prose are
non-authoritative presentation text. They may be retained as raw provenance,
but they must not determine the canonical winner, loser, team identity, score,
or reconciliation result.

Canonical game identity and outcome must be derived from structured evidence:

- final box-score lines and team orientation;
- pitcher decisions and decision-summary evidence;
- play-by-play inning, event, substitution, and control records;
- replay orientation and final-score evidence;
- injuries, defensive errors, and official statistical rows.

BIE must generate its own evidence-backed game story rather than repeat or
depend on the source site's short narrative. The BIE game story should cover:

- decisive innings and leverage-changing events;
- starting-pitcher effectiveness and removal context;
- bullpen sequencing, workload, and decision quality;
- lineup production, substitutions, pinch hitting, and bench usage;
- defensive execution, errors, baserunning, and unearned-run context;
- injuries and immediate roster or availability implications;
- card, matchup, park, and strategic factors where supported;
- sustainable strengths, warning signs, and small-sample uncertainty;
- implications for the next series and any recommended operational decisions.

The BIE-authored story is an analytical product. It must distinguish observed
game evidence from interpretation and must not invent unsupported motivations,
managerial intentions, or causal claims.
