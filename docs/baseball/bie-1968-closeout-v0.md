# BIE 1968 Closeout v0

## Status

The 1968 Strat365 draft plan is parked.

BIE should not resume 1968 draft optimization until its workflow is rules-first and roster-legality aware.

## What Was Completed

Commit:

- `003fdbc Add Strat365 1968 roster legality validator`

Added:

- `data/baseball/canonical/rules/strat365_1968_roster_rules_v1.json`
- `baseball/validation/validate_strat365_roster.py`
- `baseball/validation/run_roster_validation_regressions.py`
- `data/baseball/fixtures/rosters/1968_illegal_four_starters_v1.json`
- `data/baseball/fixtures/rosters/1968_legal_minimum_pitching_v1.json`
- `docs/baseball/bie-draft-rule-failure-debrief-v0.md`

Validated:

- A roster with only 4 starter-endurance pitchers fails.
- A legal minimum pitching roster passes.

## Root Cause

BIE treated Strat365 roster rules as background context instead of executable constraints.

The failed 1968 draft process exposed a basic legality gap:

- 1968 requires at least 5 pitchers with starter Endurance ratings.
- BIE did not validate that requirement before producing draft guidance.

## Corrected Interpretation

BIE cannot fully validate a final roster before the Strat365 draft because the actual roster is assigned after draft processing.

Therefore, BIE needs three separate phases:

1. Pre-draft coverage audit
2. Post-draft roster legality validation
3. Waiver/free-agent correction planning

## Pre-Draft Coverage Audit

Before draft submission, BIE should evaluate whether the ranked draft list has enough legal-role redundancy.

It should answer:

- Are enough starter-endurance pitchers included?
- Are enough pure relievers included?
- Is at least one closer-endurance pitcher included?
- Are at least two primary catchers included?
- Are these legal-role players spread across realistic salary tiers?
- Is the draft list structurally fragile if several targets are missed?

This is not final roster validation. It is risk assessment.

## Post-Draft Roster Validation

After Strat365 assigns the actual roster, BIE should ingest the roster and run the legality validator.

It should answer:

- Is the roster legal?
- Which rule requirements pass?
- Which rule requirements fail?
- What exact roster-role counts caused the failure?

## Waiver / Free-Agent Correction Planning

If the post-draft roster is illegal or structurally weak, BIE should evaluate add/drop options.

It should answer:

- Which available players fix legality?
- Which current players can be dropped without creating another violation?
- What is the salary impact?
- What is the strategic tradeoff?
- Which moves should happen during waivers versus later free agency?

## Policy Going Forward

BIE must fail closed.

It should not label any output as:

- draft-ready
- submission-ready
- legal roster
- recommended roster

unless the relevant legality checkpoint passes.

## Next BIE Session Prompt

Resume BIE from this closeout state.

Repo:

`C:\Users\joevi\my-dashboard`

Branch:

`main`

Workstyle:

- Call me Ginto.
- One step at a time.
- Use PowerShell commands.
- Avoid manual edits where practical.
- Prefer patch scripts or full-file generation.
- Verify current location before path-sensitive commands.
- Use scoped git status.
- Do not use `git add .`.
- Build after meaningful changes.
- Restart backend explicitly when server changes are made.

Current BIE status:

The 1968 Strat365 draft plan is parked. The prior draft failed because BIE did not validate the legal requirement for at least 5 starter-endurance pitchers.

Completed and pushed:

`003fdbc Add Strat365 1968 roster legality validator`

Before doing any new draft optimization, begin with BIE lifecycle design:

1. Pre-draft coverage audit
2. Post-draft roster legality validation
3. Waiver/free-agent correction planning

Do not attempt to repair the old 1968 draft immediately. First define the input/output shape for one of the three lifecycle phases above.

Recommended first task:

Create a pre-draft coverage audit spec that evaluates a ranked draft list for legal-role redundancy without pretending the final roster is known before the draft.
