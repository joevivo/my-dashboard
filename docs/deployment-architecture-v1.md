# Deployment Architecture v1

## Environment Model

- Localhost = dev / SQA
- Vercel = production-facing / prod-preview
- True production = future state after auth, backend, secrets, and private data controls are formalized

## Current Decision

Do not pivot away from Vercel before Aug 3.

Vercel is the right target for a polished, accessible dashboard with curated/public-safe intelligence views.

## Aug 3 Target

Vercel can host:

- Music metrics
- Playlist Intelligence
- Books
- Notes
- Static dashboards
- Public-safe curated views
- Mobile/browser validation

## Localhost Role

Localhost remains the private intelligence lab:

- Active development
- Backend-backed testing
- Raw data experimentation
- Python scripts
- DuckDB/local files
- Apple export processing
- MusicKit experiments

## Not Yet Production Ready

The current backend should not be publicly deployed yet.

Reasons:

- Express backend depends on local files
- Python scripts are runtime dependencies
- Some frontend pages hardcode localhost:4000
- No authentication model yet
- No deployed secrets strategy yet
- No MusicKit token strategy yet

## Public / Safe-ish

Allowed on Vercel if aggregated or curated:

- Music metrics
- Playlist Intelligence
- Books
- Notes
- General model documentation
- Static dashboards

## Requires Login Later

- Finance
- Calendar
- Strat tools
- Query Workbench
- Live MusicKit data
- Any personal API-backed feature

## Never Leaves Local Machine For Now

- Raw Apple exports
- Music database
- Tokens
- Credentials
- OAuth files
- .env values
- Unredacted listening events

## Promotion Path

dev local -> commit -> push main -> Vercel deploy -> validate release

## Strategic Position

Historical Archive (2013-2026)
+
Live Layer (MusicKit)
=
Music Intelligence Platform

MusicKit and backend deployment should proceed only after the Vercel/front-end release model is stable and security boundaries are explicit.
