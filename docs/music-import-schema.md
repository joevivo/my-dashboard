# Music Import Schema

## Purpose

This file documents the CSV format used by the Music Library album importer.

## File Format

Save album imports as:

CSV UTF-8 (Comma delimited) (*.csv)

## Required Columns

| Column | Required | Notes |
|---|---:|---|
| artist | Yes | Artist name |
| album | Yes | Album title |
| year | Recommended | Use numeric year only |
| rating | Optional | Suggested 1-10 scale |
| favoriteTracks | Optional | Use pipe delimiter |
| tags | Optional | Use pipe delimiter |
| owned | Optional | TRUE/FALSE |
| notes | Optional | Free text |

## Important Rules

- The album column must be named `album`, not `title`.
- Use pipes inside list fields: `track one|track two`.
- Do not manually type quotes into Excel cells.
- Save final import files as CSV UTF-8.
