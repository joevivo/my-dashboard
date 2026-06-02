# Apple Music Data Policy

This project uses Apple Music export data through a privacy-first, local-only workflow.

## Core rules

Raw Apple export files must never be committed to Git.
Sanitized Apple Music outputs must never be committed to Git.
Generated Apple Music rollup JSON files must never be committed to Git.
Only scripts and documentation belong in the repo.

## Local paths

Raw Apple export location:
C:\Users\joevi\ams

Sanitized output location:
C:\Users\joevi\apple-music-sanitized

## Repo-safe files

Allowed in Git:
- scripts/sanitizeAppleMusicExport.ps1
- scripts/buildAppleMusicRollup.ps1
- docs/apple-music-data-policy.md

Not allowed in Git:
- raw Apple CSV files
- raw Apple JSON files
- Apple export ZIP files
- extracted Apple export directories
- sanitized Apple Music CSV files
- Apple Music summary JSON files
- Apple Music dashboard rollup JSON files

## Sensitive fields

Do not show, expose, retain, import into the dashboard, or commit sensitive Apple export fields, including Apple ID/account fields, IP/location fields, device identifiers, subscription identifiers, hardware identifiers, payment identifiers, or other personal identifiers.

## Dashboard posture

The dashboard should not ingest full personal listening history by default.
Dashboard candidates must be aggregate-only and manually reviewed before React wiring.

Allowed aggregate candidates:
- total plays
- total skips
- active listening days
- active day rate
- skip rate
- favorite type counts
- year/month play trends
- capped duration hours, clearly labeled

Excluded unless explicitly re-approved:
- track names
- artist names
- album names
- playlist names
- favorite item descriptions
- recently played descriptions
- top content names
- station descriptions
- source/device/platform summaries

## Duration quality rule

Apple-reported duration fields may contain outliers.
The rollup must distinguish raw Apple-reported hours, capped/sanity-adjusted hours, duration quality status, and suspicious duration row counts.
Dashboard-facing views should prefer capped duration values unless raw values are clearly labeled as Apple-reported and needs-review.

## Current workflow

Run from the repository root:
.\scripts\sanitizeAppleMusicExport.ps1
.\scripts\buildAppleMusicRollup.ps1

## Commit rule

Before committing Apple Music-related work, run git status and confirm that only scripts or documentation are staged.
