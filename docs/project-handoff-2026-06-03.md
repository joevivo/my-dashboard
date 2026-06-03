# Defending Sisyphus — Project Handoff

Date: 2026-06-03

## Source of Truth

Repository:
C:\Users\joevi\my-dashboard

Branch:
main

User preference:
Call user "Ginto".

---

## Startup Checklist

Run:

```powershell
git status
git log --oneline -5
npm run build
```

---

## Current Strategic Goal

The project is evolving from:

"Can we import Apple Music data?"

to:

"What information deserves to become part of a person's story?"

The problem is no longer data acquisition.

The problem is metric selection.

---

## Apple Music Status

Completed:

* Data policy
* Rollup contract
* Rollup validation
* Listening analytics prototype
* Dataset inventory

Source of record:

docs/apple-music-dataset-inventory.md

---

## Confirmed Dataset Timeline

| Dataset            | Earliest Known |
| ------------------ | -------------- |
| Favorite Stations  | 2013           |
| Liked Radio Tracks | 2013           |
| Favorites          | 2015           |
| Play Activity      | 2015           |

---

## Confirmed Dataset Counts

| Dataset        | Count   |
| -------------- | ------- |
| Radio Feedback | 128     |
| Favorites      | 526     |
| Play Activity  | 199,396 |

---

## Privacy Rules

Never expose:

* Apple ID Number
* Client IP Address
* Device Identifier
* IP City
* IP Latitude
* IP Longitude
* IP Network
* Device details
* Subscription identifiers

Never expose raw:

* track names
* artist names
* album names
* playlist names
* station descriptions

Only sanitized aggregate rollups belong in the dashboard.

---

## Music Identity Framework

### Presence

How present has music been?

Examples:

* Listening Span
* Music Companion Rate
* Active Listening Days

### Engagement

How consistently is music used?

Examples:

* Listening Hours
* Longest Streak
* Consistency Score

### Curation

How intentionally is the music world shaped?

Examples:

* Favorite Activity
* Favorites By Year
* Radio Feedback Activity

### Discovery

How is music discovered?

Examples:

* Search Usage
* Library Usage
* Radio Usage

---

## Core Metrics

* Listening Span
* Music Companion Rate
* Active Listening Days
* Favorite Activity
* Radio Feedback Activity

---

## Deferred Metrics

Not priorities right now:

* Top Songs
* Top Artists
* Top Albums
* Genre Rankings

Reason:

Identity metrics are more important than content metrics.

---

## UI Items

### Music Import

Apple Music import is not ready.

Need:

* Final rollup schema
* Metrics charter
* Sanitization workflow
* Import architecture

before enabling imports.

### Weather

Weather cards need non-emoji iconography and better use of space.

### Light Mode

Needs review for contrast, hierarchy, and readability.

### Books

Pause large-scale imports.

Review data model first.

Focus on:

* Reading identity
* Subject evolution
* Intellectual themes
* Cross-linking with notes and quotes

### Notes

Review whether Notes should evolve into:

Books → Notes → Quotes → Knowledge Graph

---

## Backend Reliability

Completed:

* Added /api/health
* Verified backend startup path
* Hardened NewsView failure messaging

Future:

* FinanceView hardening
* Retry handling
* Backend status indicator

---

## Next Session Agenda

1. Review Apple Music inventory.
2. Create apple-music-metrics-charter.md.
3. Finalize core vs secondary metrics.
4. Review Music import UI.
5. Review Books data model.
6. Review Notes architecture.
7. Review Light Mode.
8. Improve Weather card visuals.

---

## Long-Term Vision

Defending Sisyphus is a personal command center and memory archive.

Future domains:

* Music
* Books
* Notes
* Quotes
* Shows
* Calendar
* Personal history

Every metric must answer:

"What meaningful story does this tell about a person's life?"
