from __future__ import annotations

from copy import deepcopy
import re
from typing import Any, Mapping


def _nullish(
    value: Any,
    default: Any,
) -> Any:
    return default if value is None else value


def _mapping(
    value: Any,
) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def build_artist_investigation(
    artist_result: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    source = _mapping(artist_result)

    artist = _nullish(source.get("artist"), "")
    query = _nullish(source.get("query"), "")

    canonical_key = re.sub(
        r"\s+",
        "-",
        str(artist).lower(),
    )

    solo_plays = _nullish(
        source.get("actualPlays"),
        0,
    )

    family_metrics = _mapping(
        source.get("familyMetrics")
    )

    family_plays = (
        _nullish(
            family_metrics.get("actualPlays"),
            None,
        )
        if family_metrics
        else None
    )

    amplification = (
        round(
            float(family_plays) / float(solo_plays),
            2,
        )
        if family_plays and solo_plays
        else None
    )

    evidence_facts: list[dict[str, Any]] = []

    library_records = source.get(
        "libraryEvidenceRecords"
    )

    if library_records:
        years_active = _nullish(
            source.get("yearsActive"),
            "unknown",
        )

        evidence_facts.append({
            "id": "fact-library-span",
            "statement": (
                "Library evidence contains "
                f"{library_records} records across "
                f"{years_active} represented years."
            ),
            "sourceEvidenceIds": [
                "library-evidence-records"
            ],
            "factType": "evidence-coverage",
            "source": "investigation_builder",
        })

    if solo_plays:
        actual_skips = _nullish(
            source.get("actualSkips"),
            0,
        )

        evidence_facts.append({
            "id": "fact-play-activity-strength",
            "statement": (
                f"Play Activity records {solo_plays} "
                f"actual plays and {actual_skips} skips."
            ),
            "sourceEvidenceIds": [
                "solo-plays",
                "hours-listened",
            ],
            "factType": "activity-summary",
            "source": "investigation_builder",
        })

    bridge = _mapping(source.get("bridge"))
    live = _mapping(bridge.get("live"))

    recent_object_count = live.get(
        "recentObjectCount"
    )

    if recent_object_count:
        evidence_facts.append({
            "id": "fact-live-apple-music-present",
            "statement": (
                f"{recent_object_count} Recent Apple "
                "Objects were captured for this artist."
            ),
            "sourceEvidenceIds": [
                "live_apple_music_warehouse"
            ],
            "factType": "recent-apple-evidence",
            "source": "investigation_builder",
        })

    bridge_facts: list[dict[str, Any]] = []

    raw_bridge_facts = bridge.get("facts")

    if not isinstance(raw_bridge_facts, list):
        raw_bridge_facts = []

    for index, raw_fact in enumerate(raw_bridge_facts):
        fact = _mapping(raw_fact)

        fact_type = _nullish(
            fact.get("type"),
            index,
        )

        label = _nullish(
            fact.get("type"),
            "Bridge Fact",
        )

        source_fact_type = _nullish(
            fact.get("type"),
            "fact",
        )

        evidence = (
            [{
                "label": label,
                "value": fact.get("value"),
            }]
            if "value" in fact
            else []
        )

        source_evidence_ids = _nullish(
            fact.get("evidence"),
            [],
        )

        bridge_facts.append({
            "id": f"bridge-fact-{fact_type}",
            "statement": fact.get("statement"),
            "evidence": deepcopy(evidence),
            "sourceEvidenceIds": deepcopy(
                source_evidence_ids
            ),
            "factType": (
                f"bridge-{source_fact_type}"
            ),
            "source": "evidence_bridge",
            "sourceFactType": source_fact_type,
        })

    family_facts = (
        [{
            "id": "fact-family-amplification",
            "statement": (
                "Family amplification factor is "
                f"{amplification}×."
            ),
            "evidence": [
                {
                    "label": "Solo Plays",
                    "value": solo_plays,
                },
                {
                    "label": "Family Plays",
                    "value": family_plays,
                },
            ],
            "sourceEvidenceIds": [
                "solo-plays",
                "family-plays",
            ],
            "factType": "derived-relationship",
            "source": "investigation_builder",
        }]
        if amplification
        else []
    )

    family = _mapping(source.get("family"))

    family_reasoning_trace = (
        [
            {
                "step": 1,
                "operation": "resolve_identity",
                "result": (
                    f"Matched {artist or 'artist'} "
                    "to curated family "
                    f"{family.get('familyName')}."
                    if family
                    else (
                        "No curated family mapping "
                        f"found for {artist or 'artist'}."
                    )
                ),
            },
            {
                "step": 2,
                "operation": "collect_evidence",
                "result": (
                    "Collected solo plays "
                    f"({solo_plays}) and family plays "
                    f"({family_plays})."
                ),
            },
            {
                "step": 3,
                "operation": "derive_fact",
                "result": (
                    "Computed family amplification "
                    f"factor: {amplification}×."
                ),
            },
        ]
        if amplification
        else []
    )

    bridge_reasoning_trace = [
        {
            "step": (
                len(family_reasoning_trace)
                + index
                + 1
            ),
            "operation": "merge_bridge_fact",
            "result": fact.get("statement"),
        }
        for index, fact in enumerate(bridge_facts)
    ]

    family_name = (
        _nullish(family.get("familyName"), None)
        if family
        else None
    )

    family_members = (
        _nullish(family.get("members"), [])
        if family
        else []
    )

    relationship_type = (
        _nullish(
            family.get("relationshipType"),
            None,
        )
        if family
        else None
    )

    play_activity_source = _nullish(
        source.get("playActivitySource"),
        "apple_music_daily_track_summary",
    )

    library_source = _nullish(
        source.get("source"),
        "apple_music_library_tracks",
    )

    evidence = [
        {
            "id": "solo-plays",
            "label": "Solo Plays",
            "value": solo_plays,
            "source": play_activity_source,
            "provenance": (
                "Solo artist play count from Apple "
                "Music daily track summary."
            ),
            "confidence": "high",
        },
        {
            "id": "family-plays",
            "label": "Family Plays",
            "value": family_plays,
            "source": "derived_family_rollup",
            "provenance": (
                "Aggregated play count across curated "
                "artist-family members."
            ),
            "confidence": (
                "high"
                if family_metrics
                else "low"
            ),
        },
        {
            "id": "hours-listened",
            "label": "Hours Listened",
            "value": source.get("hoursListened"),
            "source": play_activity_source,
            "provenance": (
                "Listening duration from Apple Music "
                "daily track summary."
            ),
            "confidence": "high",
        },
        {
            "id": "library-evidence-records",
            "label": "Library Evidence Records",
            "value": library_records,
            "source": library_source,
            "provenance": (
                "Library evidence records matched to "
                "the artist identity."
            ),
            "confidence": "medium",
        },
    ]

    return {
        "question": {
            "originalQuery": query,
            "normalizedQuery": str(query).lower(),
            "investigationType": "artist",
        },
        "entity": {
            "type": "artist",
            "displayName": artist,
            "canonicalKey": canonical_key,
        },
        "identity": {
            "resolvedName": artist,
            "canonicalKey": canonical_key,
            "aliases": [],
            "familyName": family_name,
            "familyMembers": deepcopy(
                family_members
            ),
            "relationshipType": relationship_type,
            "matchConfidence": (
                "high"
                if family
                else "medium"
            ),
            "notes": (
                ["Curated family mapping found."]
                if family
                else []
            ),
        },
        "evidence": evidence,
        "facts": [
            *evidence_facts,
            *family_facts,
            *bridge_facts,
        ],
        "hypotheses": [],
        "insights": [],
        "confidence": {},
        "reasoningTrace": [
            *family_reasoning_trace,
            *bridge_reasoning_trace,
        ],
        "openQuestions": [],
        "suggestedInvestigations": [],
    }


def apply_investigation_projection(
    canonical_response: Mapping[str, Any],
    investigation: Mapping[str, Any],
) -> dict[str, Any]:
    if not isinstance(canonical_response, Mapping):
        raise TypeError(
            "Canonical response must be a mapping."
        )

    if not isinstance(investigation, Mapping):
        raise TypeError(
            "Investigation must be a mapping."
        )

    result = deepcopy(dict(canonical_response))
    result["investigation"] = deepcopy(
        dict(investigation)
    )

    suggestions = investigation.get(
        "suggestedInvestigations"
    )

    result["suggestedInvestigations"] = (
        deepcopy(suggestions)
        if isinstance(suggestions, list)
        else []
    )

    return result
