# Album Relationship Model v0

## What We Learned

Album relationships are not album play counts.

Album relationships have shape, context, persistence, and behavioral patterns.

Album normalization research demonstrated that album identity must be resolved before album relationships can be analyzed.

Canonical Album identity is therefore a prerequisite layer for Album Relationship Modeling.

---

## Candidate Relationship Types

### Core Companion Album

High-volume album relationship sustained across years.

Characteristics:

* Significant listening volume
* Repeated return behavior
* Multi-year persistence
* Appears independently of artist catalog exploration

Potential examples:

* Document
* Out of Time
* Plans
* Yankee Hotel Foxtrot

---

### Catalog-World Album

An album that participates in a larger catalog relationship.

Characteristics:

* Strong neighboring album relationships
* Part of a broader artist world
* Importance emerges from catalog context

Potential examples:

* Murmur
* Fables of the Reconstruction
* Lifes Rich Pageant
* Being There

---

### Gateway Album

Album through which a broader artist relationship is accessed.

Characteristics:

* Disproportionately large footprint
* Often precedes wider catalog exploration
* Functions as an entry point

Potential examples:

* The Photo Album
* Talon of the Hawk

---
### Core Cluster Album Relationship

A relationship carried by several major albums rather than one dominant album or a complete catalog.

Characteristics:

- Multiple high-volume albums
- Persistent overlap through time
- Concentrated in a limited subset of the catalog
- No single album fully explains the relationship

A Core Cluster differs from a Dual-Anchor relationship because more than two albums share responsibility for carrying the relationship.

A Core Cluster differs from a Catalog World because the relationship remains concentrated in a relatively small number of albums rather than spreading broadly across the catalog.

Potential example:

Wilco

- Summerteeth
- Yankee Hotel Foxtrot
- Sky Blue Sky
- A Ghost Is Born

Evidence observed during Sprint B:

- Summerteeth: 390 canonical events
- Sky Blue Sky: 273 canonical events
- Yankee Hotel Foxtrot: 271 canonical events
- A Ghost Is Born: 193 canonical events

These albums exhibit substantial overlap in listening periods and collectively appear to carry the Wilco relationship.
### Session Companion Album

Album repeatedly encountered through album-oriented listening behavior.

Characteristics:

* Album Traversals
* Album Traversal With Interruption
* Album-Contained Sessions
* Companion Album Sessions

Relationship strength emerges from session behavior rather than raw event count.

---

### Source-Limited Album

Important album relationship with incomplete visibility.

Characteristics:

* Strong evidence in one source
* Missing evidence in another source
* Relationship likely underrepresented

---

## Relationship Dimensions

Album relationships may ultimately be measured along several dimensions:

### Persistence

How long the album remains active in the archive.

### Volume

Total listening activity.

### Return Rate

How often the listener comes back after long gaps.

### Session Strength

How often the album appears in album-oriented sessions.

### Catalog Context

Whether the album stands alone or exists within a larger album ecosystem.

### Identity Stability

Whether the album survives normalization and metadata fragmentation.

---

## Architectural Stack

Raw Metadata
→ Canonical Album
→ Album Entity
→ Album Relationship
→ Album Relationship Type
→ Album Intelligence

---
### Core Cluster Album Relationship

A relationship carried by several major albums rather than one dominant album or a complete catalog.

Characteristics:

- Multiple high-volume albums
- Persistent overlap through time
- Concentrated in a limited subset of the catalog

Potential examples:

- Wilco
  - Summerteeth
  - Yankee Hotel Foxtrot
  - Sky Blue Sky
  - A Ghost Is Born

## Open Questions

* What separates a Core Companion Album from a Catalog-World Album?
* How should session behavior influence relationship classification?
* Can Album Traversals become relationship evidence?
* How should live albums be treated?
* How should box sets be treated?
* How should soundtrack albums be treated?
* How should Album Families interact with Album Relationships?

The model remains exploratory and should evolve through evidence rather than fixed thresholds.
