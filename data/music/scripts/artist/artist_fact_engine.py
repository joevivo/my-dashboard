import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
DEFAULT_INPUT = ROOT / "data/music/live/artist_universe_v2_top25.json"
DEFAULT_OUTPUT = ROOT / "data/music/live/artist_universe_v2_top25_facts.json"


def get_arg(flag: str, default: Path) -> Path:
    if flag not in sys.argv:
        return default
    idx = sys.argv.index(flag)
    return ROOT / sys.argv[idx + 1]


def compute_facts(row: dict) -> dict:
    evidence = row.get("evidence") or row.get("metrics") or {}
    relationship = row.get("relationship") or {}
    review = row.get("review") or row.get("reviewStatus") or {}

    actual_plays = evidence.get("actualPlays") or 0
    library_evidence = evidence.get("libraryEvidenceRecords") or 0
    years_active = evidence.get("yearsActive") or 0

    has_family = bool(relationship.get("familyName"))
    is_reviewed = bool(review and review.get("status"))

    return {
        "hasPlayHistory": actual_plays > 0,
        "hasLibraryEvidence": library_evidence > 0,
        "hasFamily": has_family,
        "isReviewed": is_reviewed,
        "isReviewedStandalone": review.get("status") == "reviewed_standalone",
        "isUnclassified": not has_family and not is_reviewed,
        "isHighVolume": actual_plays >= 500,
        "isLongRunning": years_active >= 10,
        "isHighEvidence": library_evidence >= 50,
        "needsReview": (
            not has_family
            and not is_reviewed
            and (
                actual_plays >= 250
                or years_active >= 10
                or library_evidence >= 50
            )
        ),
    }


def main() -> int:
    input_file = get_arg("--input", DEFAULT_INPUT)
    output_file = get_arg("--output", DEFAULT_OUTPUT)

    payload = json.loads(input_file.read_text(encoding="utf-8-sig"))

    artists = payload.get("artists", [])

    for row in artists:
        row["facts"] = compute_facts(row)

    payload["factEngine"] = {
        "version": "artist_fact_engine_v1",
        "artistCount": len(artists),
    }

    summary = {
        "artistsProcessed": len(artists),
        "needsReview": sum(1 for row in artists if row.get("facts", {}).get("needsReview")),
        "familyMembers": sum(1 for row in artists if row.get("facts", {}).get("hasFamily")),
        "reviewedStandalone": sum(1 for row in artists if row.get("facts", {}).get("isReviewedStandalone")),
        "highVolume": sum(1 for row in artists if row.get("facts", {}).get("isHighVolume")),
        "longRunning": sum(1 for row in artists if row.get("facts", {}).get("isLongRunning")),
        "highEvidence": sum(1 for row in artists if row.get("facts", {}).get("isHighEvidence")),
    }

    payload["factEngine"]["summary"] = summary

    output_file.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    print(f"Wrote {output_file}")
    print()
    print("# Fact Summary")
    for key, value in summary.items():
        print(f"{key}: {value}")

    print()
    print("# Needs Review")
    for row in artists:
        if row.get("facts", {}).get("needsReview"):
            e = row.get("evidence", {})
            print(
                f"{row['artist']} | "
                f"plays={e.get('actualPlays', 0)} | "
                f"evidence={e.get('libraryEvidenceRecords', 0)} | "
                f"years={e.get('yearsActive', 0)}"
            )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
