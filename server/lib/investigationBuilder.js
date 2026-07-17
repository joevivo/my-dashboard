export function buildArtistInvestigation(artistResult = {}) {
  const canonicalKey = (artistResult.artist ?? "")
    .toLowerCase()
    .replace(/\s+/g, "-");

  const soloPlays = artistResult.actualPlays ?? 0;
  const familyPlays = artistResult.familyMetrics?.actualPlays ?? null;
  const amplification =
    familyPlays && soloPlays ? Number((familyPlays / soloPlays).toFixed(2)) : null;

  const evidenceFacts = [
    artistResult.libraryEvidenceRecords
      ? {
          id: "fact-library-span",
          statement: `Library evidence contains ${artistResult.libraryEvidenceRecords} records across ${artistResult.yearsActive ?? "unknown"} represented years.`,
          sourceEvidenceIds: ["library-evidence-records"],
          factType: "evidence-coverage",
          source: "investigation_builder"
        }
      : null,
    soloPlays
      ? {
          id: "fact-play-activity-strength",
          statement: `Play Activity records ${soloPlays} actual plays and ${artistResult.actualSkips ?? 0} skips.`,
          sourceEvidenceIds: ["solo-plays", "hours-listened"],
          factType: "activity-summary",
          source: "investigation_builder"
        }
      : null,
    artistResult.bridge?.live?.recentObjectCount
      ? {
          id: "fact-live-apple-music-present",
          statement: `${artistResult.bridge.live.recentObjectCount} Recent Apple Objects were captured for this artist.`,
          sourceEvidenceIds: ["live_apple_music_warehouse"],
          factType: "recent-apple-evidence",
          source: "investigation_builder"
        }
      : null
  ].filter(Boolean);

  const bridgeFacts = (artistResult.bridge?.facts ?? []).map((fact, index) => ({
    id: `bridge-fact-${fact.type ?? index}`,
    statement: fact.statement,
    evidence: fact.value !== undefined
      ? [{ label: fact.type ?? "Bridge Fact", value: fact.value }]
      : [],
    sourceEvidenceIds: fact.evidence ?? [],
    factType: `bridge-${fact.type ?? "fact"}`,
    source: "evidence_bridge",
    sourceFactType: fact.type ?? "fact"
  }));

  const familyFacts = amplification
    ? [
        {
          id: "fact-family-amplification",
          statement: `Family amplification factor is ${amplification}×.`,
          evidence: [
            { label: "Solo Plays", value: soloPlays },
            { label: "Family Plays", value: familyPlays }
          ],
          sourceEvidenceIds: ["solo-plays", "family-plays"],
          factType: "derived-relationship",
          source: "investigation_builder"
        }
      ]
    : [];

  const familyReasoningTrace = amplification
    ? [
        {
          step: 1,
          operation: "resolve_identity",
          result: artistResult.family
            ? `Matched ${artistResult.artist ?? "artist"} to curated family ${artistResult.family.familyName}.`
            : `No curated family mapping found for ${artistResult.artist ?? "artist"}.`
        },
        {
          step: 2,
          operation: "collect_evidence",
          result: `Collected solo plays (${soloPlays}) and family plays (${familyPlays}).`
        },
        {
          step: 3,
          operation: "derive_fact",
          result: `Computed family amplification factor: ${amplification}×.`
        }
      ]
    : [];

  const bridgeReasoningTrace = bridgeFacts.map((fact, index) => ({
    step: familyReasoningTrace.length + index + 1,
    operation: "merge_bridge_fact",
    result: fact.statement
  }));

  return {
    question: {
      originalQuery: artistResult.query ?? "",
      normalizedQuery: (artistResult.query ?? "").toLowerCase(),
      investigationType: "artist"
    },

    entity: {
      type: "artist",
      displayName: artistResult.artist ?? "",
      canonicalKey
    },

    identity: {
      resolvedName: artistResult.artist ?? "",
      canonicalKey,
      aliases: [],
      familyName: artistResult.family?.familyName ?? null,
      familyMembers: artistResult.family?.members ?? [],
      relationshipType: artistResult.family?.relationshipType ?? null,
      matchConfidence: artistResult.family ? "high" : "medium",
      notes: artistResult.family ? ["Curated family mapping found."] : []
    },

    evidence: [
      {
        id: "solo-plays",
        label: "Solo Plays",
        value: soloPlays,
        source: artistResult.playActivitySource ?? "apple_music_daily_track_summary",
        provenance: "Solo artist play count from Apple Music daily track summary.",
        confidence: "high"
      },
      {
        id: "family-plays",
        label: "Family Plays",
        value: familyPlays,
        source: "derived_family_rollup",
        provenance: "Aggregated play count across curated artist-family members.",
        confidence: artistResult.familyMetrics ? "high" : "low"
      },
      {
        id: "hours-listened",
        label: "Hours Listened",
        value: artistResult.hoursListened,
        source: artistResult.playActivitySource ?? "apple_music_daily_track_summary",
        provenance: "Listening duration from Apple Music daily track summary.",
        confidence: "high"
      },
      {
        id: "library-evidence-records",
        label: "Library Evidence Records",
        value: artistResult.libraryEvidenceRecords,
        source: artistResult.source ?? "apple_music_library_tracks",
        provenance: "Library evidence records matched to the artist identity.",
        confidence: "medium"
      }
    ],

    facts: [...evidenceFacts, ...familyFacts, ...bridgeFacts],

    hypotheses: [],
    insights: [],
    confidence: {},
    reasoningTrace: [...familyReasoningTrace, ...bridgeReasoningTrace],
    openQuestions: [],
    suggestedInvestigations: []
  };
}
