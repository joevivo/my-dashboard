# Music Section Information Architecture

Date: 2026-06-05

## Purpose

The Music section is organized around the user's relationship to music rather than around individual widgets or reports.

New Music features should be assigned to one of four top-level groups before implementation.

---

## Library

User-curated collections and artifacts.

Current features:

* Artists
* Albums
* Playlists
* Shows
* Listening Eras

Question answered:

"What do I intentionally keep and curate?"

---

## Intelligence

Insights derived from listening history and analysis.

Current features:

* Music Overview (currently Music Dashboard)
* Music Intelligence

Planned features:

* Constants
* Changes
* Rediscovery
* Constellations

Question answered:

"What does the listening data reveal?"

---

## Discovery

Browsing and exploration tools.

Current features:

* Explore
* Tag Browser
* Recently Added
* Artist Spotlight (experimental)

Question answered:

"What should I explore next?"

Note:

Artist Spotlight has not yet demonstrated significant value and should remain a low-priority feature until a clearer use case emerges.

---

## Data

Import and maintenance infrastructure.

Current features:

* Imported Music

Potential future features:

* Import Status
* Data Quality
* Source Management

Question answered:

"How does information enter and move through the system?"

---

## Guiding Principle

Music features should follow:

Import
→ Normalize
→ Analyze
→ Present

Avoid creating dashboards or visualizations before the underlying intelligence model exists.
