# Music Identity Contract v1

## Status

Draft contract for Sprint 3.

No UI implementation should depend on this contract until it is reviewed and accepted.

---

## Purpose

This contract defines how Defending Sisyphus Music resolves identity before facts, insights, or classifications are trusted.

Core rule:

Identity first, behavior second.

A metric can be accurate but still misleading if attached to the wrong entity identity.

---

## Identity Responsibilities

The identity layer must answer:

- What entity was requested?
- What entity was resolved?
- What canonical key represents it?
- What source names matched it?
- What aliases or variants were considered?
- Does a family rollup apply?
- Is the identity resolved, partial, ambiguous, or not found?
- What lowers identity confidence?
- What must be reviewed before facts or insights are trusted?

---

## Supported Entity Types

Initial supported entity types:

- artist
- artistFamily
- album
- song
- playlist
- date
- cohort

Future entity types may be added only after their identity rules are documented.

---

## Required Identity Fields

Every resolved entity should expose these fields where available:

- entityType
- displayName
- canonicalKey
- resolvedName
- matchedSourceNames
- aliases
- matchMode
- matchConfidence
- identityStatus
- identityWarnings
- sourceFamiliesUsed

Allowed identityStatus values:

- resolved
- resolvedWithWarnings
- partial
- ambiguous
- notFound
- needsReview

Allowed matchConfidence values:

- high
- medium
- low
- notFound

---

## Canonical Key Rules

Canonical keys must be stable and deterministic.

General rules:

- Lowercase.
- Trim leading and trailing whitespace.
- Normalize punctuation where safe.
- Normalize ampersand and 'and' variants where documented.
- Remove unsafe display-only characters.
- Preserve disambiguating terms when needed.

Canonical keys are identifiers, not display names.

Display names should preserve human-readable capitalization and punctuation.

---

## Artist Identity

Artist identity resolves a requested artist name to a canonical artist entity.

Required artist identity fields:

- entityType: artist
- displayName
- canonicalKey
- resolvedName
- matchedSourceNames
- aliases
- matchMode
- matchConfidence
- identityStatus

Allowed match modes:

- exactSourceName
- exactAlias
- normalizedExact
- curatedAlias
- familyMemberMatch
- unresolved

High confidence artist identity:

- Exact source-name match or curated alias match.
- No conflicting canonical entity.
- No unresolved family or alias warning.

Medium confidence artist identity:

- Normalized exact match.
- Diacritic, punctuation, ampersand, or leading-article normalization involved.
- Artist may also belong to a family rollup.

Low confidence artist identity:

- Multiple plausible artists.
- Mojibake affects the name.
- Match depends on partial text.
- Source evidence is weak or inconsistent.

Not found:

- No source evidence found for the requested artist or alias.
- Not found must not be treated as proof that the artist is unimportant.

---

## Artist Family Identity

Artist family identity resolves a canonical relationship group across solo, band, and collaboration identities.

Required artist family fields:

- entityType: artistFamily
- displayName
- canonicalKey
- familyName
- primaryArtist
- familyMembers
- matchedMembers
- unmatchedMembers
- aliases
- matchConfidence
- identityStatus

Family rollup applies when:

- A curated family mapping exists.
- The requested artist is a known member of the family.
- The investigation scope requests or permits family-level interpretation.

Family rollup does not automatically apply when:

- The user explicitly requests standalone artist interpretation.
- The relationship is only speculative.
- The family mapping is missing.
- The collaboration should remain separate.

Family rollup must expose:

- Solo/canonical artist metrics.
- Family-level metrics.
- Member distribution.
- Family amplification where calculable.
- Which members were included.
- Which candidate members were excluded or unresolved.

High confidence family identity:

- Explicit curated family mapping exists.
- Members are known and documented.
- Source names map cleanly to members.

Medium confidence family identity:

- Curated family exists but member coverage is partial.
- Some source names require normalization.
- Some aliases or collaborations need review.

Low confidence family identity:

- Proposed family only.
- Missing curated mapping.
- Collaboration boundaries are unclear.
- Multiple family interpretations are plausible.

---

## Album Identity

Album identity must be resolved as:

Artist Identity + Canonical Album Title

Album title alone is insufficient.

Required album identity fields:

- entityType: album
- displayName
- canonicalKey
- artistCanonicalKey
- artistDisplayName
- rawAlbumTitles
- canonicalAlbumTitle
- albumVariants
- normalizationRulesApplied
- matchConfidence
- identityStatus

Canonical album collapse is allowed for:

- Remasters.
- Deluxe editions.
- Anniversary editions.
- Bonus track versions.
- Expanded editions.
- Year-specific reissues where core album identity is stable.

Canonical album collapse is not automatically allowed for:

- Live albums.
- Soundtracks.
- Compilations.
- Greatest hits collections.
- Different albums with same title by different artists.
- Albums where bonus or edition content materially changes identity.

High confidence album identity:

- Artist identity is high confidence.
- Canonical album title maps cleanly across variants.
- Variants fit approved normalization rules.

Medium confidence album identity:

- Artist identity is resolved but album variants need review.
- Edition markers were removed by known rules.
- Album metadata differs across sources.

Low confidence album identity:

- Artist identity is weak.
- Album title is generic.
- Album may be live, compilation, soundtrack, or materially different edition.
- Multiple canonical album candidates exist.

---

## Song Identity

Song identity must be resolved as:

Artist Identity + Canonical Song Title

Song title alone is insufficient.

Required song identity fields:

- entityType: song
- displayName
- canonicalKey
- artistCanonicalKey
- artistDisplayName
- rawSongTitles
- canonicalSongTitle
- songVariants
- matchConfidence
- identityStatus

Song identity rules:

- Artist-aware matching is required.
- Same-title songs by different artists must remain separate.
- Song variants may be grouped only when the musical work is clearly the same.
- Live, demo, remix, acoustic, and alternate versions require explicit treatment.

High confidence song identity:

- Artist identity is high confidence.
- Exact or normalized song title match.
- No conflicting same-title entity.

Medium confidence song identity:

- Artist identity is resolved but title variants exist.
- Context rows must be joined from DuckDB.
- Source names differ but map plausibly.

Low confidence song identity:

- Same-title collision exists.
- Artist identity is weak.
- Match depends on partial or ambiguous text.
- Context evidence is missing or sparse.

---

## Playlist Identity

Playlist identity resolves user-created or generated playlist objects.

Required playlist identity fields:

- entityType: playlist
- displayName
- canonicalKey
- rawPlaylistName
- playlistClassification
- sourcePlaylistIds
- matchConfidence
- identityStatus

Allowed playlist classifications:

- intentional
- generated
- imported
- unknown

Playlist identity rules:

- Intentional playlists are primary playlist-intelligence evidence.
- Generated playlists are supporting evidence unless explicitly promoted.
- Playlist identity does not prove actual listening.
- Playlist identity may support playlist placement and cohort analysis.

---

## Date Identity

Date identity resolves a calendar date or date range used for listening investigation.

Required date identity fields:

- entityType: date
- displayName
- canonicalKey
- startDate
- endDate
- timezone
- matchConfidence
- identityStatus

Date identity rules:

- Dates must be represented as absolute dates.
- Relative dates must be resolved before investigation.
- Timezone must be explicit when relevant.

---

## Cohort Identity

Cohort identity resolves a group of entities for comparison or playlist analysis.

Required cohort identity fields:

- entityType: cohort
- displayName
- canonicalKey
- cohortMembers
- cohortDefinition
- inclusionRules
- exclusionRules
- matchConfidence
- identityStatus

Cohort identity rules:

- Cohort membership must be explicit.
- Generated cohorts must document their rule.
- Curated cohorts must document their source.
- Cohort metrics must preserve member-level traceability.

---

## Identity Warnings

Identity warnings should be exposed before facts and insights are trusted.

Standard warnings:

- curatedFamilyMissing
- aliasOnlyMatch
- normalizedOnlyMatch
- multipleCandidates
- mojibakeDetected
- metadataVariant
- albumVariantNeedsReview
- sameTitleCollision
- sourceLimited
- liveOnlyEvidence
- libraryOnlyEvidence
- playlistOnlyEvidence
- unresolvedFamilyMember
- unresolvedAlbumVariant
- unresolvedSongVariant

---

## Identity Confidence Rules

High confidence:

- Canonical entity is resolved.
- Match source is exact or curated.
- No conflicting candidate exists.
- Source evidence supports the entity type.

Medium confidence:

- Canonical entity is resolved but normalization was required.
- Alias/family/album mapping is involved.
- Source evidence is adequate but incomplete.

Low confidence:

- Entity is weakly matched.
- Multiple candidates exist.
- Mojibake or metadata variants affect matching.
- Source evidence is sparse.
- Relationship requires review.

Not found:

- Entity is not found in the relevant source family.
- Not found is a source result, not a relationship judgment.

---

## Interaction With Source Registry

Identity can define what an entity is.

Identity cannot prove listening behavior by itself.

Rules:

- Curated identity seeds define identity, not listening behavior.
- Apple Music daily track summary proves actual listening, not family membership by itself.
- Library Tracks prove library evidence, not actual listening.
- Library Playlists prove playlist placement, not actual listening.
- DuckDB context enriches behavior, but does not resolve artist identity by itself.
- Live endpoints prove endpoint-visible objects at snapshot time, not durable relationships by themselves.

---

## Interaction With Investigation Packets

The investigation packet identity block must include:

- resolvedName
- canonicalKey
- matchConfidence
- notes

Recommended packet identity fields:

- aliases
- familyName
- familyMembers
- matchedSourceNames
- unresolvedNames
- identityWarnings
- identityStatus
- matchMode

Any packet with low or medium identity confidence must expose open questions or suggested investigations.

---

## Non-Goals

This contract does not implement identity logic.

This contract does not alter curated seed files.

This contract does not rewrite source datasets.

This contract does not define Friction, Momentum, Emerging Core Artist, Dormant Relationship, Return Signal, or Catalog Ecosystem formulas.

This contract does not start UI work.

---

## Acceptance Criteria

This contract is accepted when:

- Supported entity types are documented.
- Required identity fields are documented.
- Artist, family, album, song, playlist, date, and cohort identity rules are documented.
- Identity confidence rules are explicit.
- Identity warnings are standardized.
- Album identity uses Artist Identity + Canonical Album Title.
- Song identity uses Artist Identity + Canonical Song Title.
- Family rollup rules are explicit.
- Source registry boundaries are preserved.
- No UI implementation is started.
