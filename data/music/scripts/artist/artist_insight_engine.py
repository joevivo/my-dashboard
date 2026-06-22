import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
DEFAULT_INPUT = ROOT / "data/music/live/artist_universe_v2_top25_facts.json"
DEFAULT_OUTPUT = ROOT / "data/music/live/artist_universe_v2_top25_insights.json"


def get_arg(flag: str, default: Path) -> Path:
    if flag not in sys.argv:
        return default
    idx = sys.argv.index(flag)
    return ROOT / sys.argv[idx + 1]


def build_insights(row: dict) -> list[dict]:
    artist = row.get("artist")
    evidence = row.get("evidence") or {}
    facts = row.get("facts") or {}
    relationship = row.get("relationship") or {}
    review = row.get("review") or {}

    plays = evidence.get("actualPlays") or 0
    years = evidence.get("yearsActive") or 0
    evidence_records = evidence.get("libraryEvidenceRecords") or 0

    insights = []

    if facts.get("needsReview"):
        insights.append({
            "type": "needs_artist_review",
            "severity": "high",
            "summary": f"{artist} is a high-priority unresolved artist.",
            "reason": (
                f"{artist} has {plays} actual plays, "
                f"{evidence_records} library evidence records, "
                f"and {years} active years but has no family or standalone review."
            ),
        })

    if facts.get("hasFamily"):
        insights.append({
            "type": "known_relationship",
            "severity": "info",
            "summary": f"{artist} is connected to {relationship.get('familyName')}.",
            "reason": (
                f"The artist is assigned to a {relationship.get('relationshipType')} "
                f"relationship with primary artist {relationship.get('primaryArtist')}."
            ),
        })

    if facts.get("isReviewedStandalone"):
        insights.append({
            "type": "reviewed_standalone",
            "severity": "info",
            "summary": f"{artist} has been reviewed as standalone.",
            "reason": review.get("notes") or "The artist has been manually reviewed as a standalone identity.",
        })

    if facts.get("isHighVolume") and facts.get("isLongRunning"):
        insights.append({
            "type": "permanent_companion_candidate",
            "severity": "medium",
            "summary": f"{artist} shows high-volume long-running persistence.",
            "reason": f"{artist} has {plays} actual plays across {years} active years.",
        })

    elif facts.get("isLongRunning") and facts.get("isHighEvidence"):
        insights.append({
            "type": "persistent_catalog_presence",
            "severity": "medium",
            "summary": f"{artist} shows persistent catalog presence.",
            "reason": (
                f"{artist} has {evidence_records} library evidence records "
                f"across {years} active years."
            ),
        })

    if facts.get("isLibraryOnly"):
        insights.append({
            "type": "collection_only_artist",
            "severity": "low",
            "summary": f"{artist} appears in the library without matched play history.",
            "reason": (
                f"{artist} has {evidence_records} library evidence records "
                "but no matched actual plays."
            ),
        })

    return insights


def main() -> int:
    input_file = get_arg("--input", DEFAULT_INPUT)
    output_file = get_arg("--output", DEFAULT_OUTPUT)

    payload = json.loads(input_file.read_text(encoding="utf-8-sig"))
    artists = payload.get("artists", [])

    insight_counts = {}

    for row in artists:
        insights = build_insights(row)
        row["insights"] = insights

        for insight in insights:
            insight_counts[insight["type"]] = insight_counts.get(insight["type"], 0) + 1

    payload["insightEngine"] = {
        "version": "artist_insight_engine_v1",
        "artistCount": len(artists),
        "insightCounts": insight_counts,
    }

    output_file.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    print(f"Wrote {output_file}")
    print()
    print("# Insight Summary")
    for key, value in sorted(insight_counts.items()):
        print(f"{key}: {value}")

    print()
    print("# High / Medium Insights")
    for row in artists:
        for insight in row.get("insights", []):
            if insight.get("severity") in {"high", "medium"}:
                print(f"{row['artist']} | {insight['type']} | {insight['summary']}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
