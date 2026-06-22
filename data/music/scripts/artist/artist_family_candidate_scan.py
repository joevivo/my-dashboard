import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]

FAMILIES_FILE = ROOT / "data/music/curated/artistFamilies.json"
REVIEW_STATUS_FILE = ROOT / "data/music/curated/artistFamilyReviewStatus.json"
RELATIONSHIPS_MD = ROOT / "data/music/live/apple_library_relationships.md"
QUERY_SCRIPT = ROOT / "data/music/scripts/artist_query_summary.py"
OUT_DIR = ROOT / "data/music/audit"
OUT_JSON = OUT_DIR / "artist_family_candidate_scan.json"
OUT_MD = OUT_DIR / "artist_family_candidate_scan.md"


def run_artist_query(name: str) -> dict:
    try:
        output = subprocess.check_output(
            [sys.executable, str(QUERY_SCRIPT), name],
            cwd=ROOT,
        ).decode("utf-8", errors="replace")
        return json.loads(output)
    except Exception as error:
        return {"error": str(error), "query": name}


def load_known_members() -> set[str]:
    families = json.loads(FAMILIES_FILE.read_text(encoding="utf-8"))
    known = set()
    for family in families:
        for member in family.get("members", []):
            known.add(member.lower().strip())
    return known


def load_review_status() -> dict:
    if not REVIEW_STATUS_FILE.exists():
        return {}

    raw = json.loads(REVIEW_STATUS_FILE.read_text(encoding="utf-8-sig"))
    normalized = {}

    for artist, value in raw.items():
        if isinstance(value, dict):
            normalized[artist.lower().strip()] = value
        else:
            normalized[artist.lower().strip()] = {"status": value}

    return normalized


def load_library_artists() -> list[str]:
    text = RELATIONSHIPS_MD.read_text(encoding="utf-8", errors="replace")
    artists = []

    for line in text.splitlines():
        match = re.match(r"^- ([^:]+): \d+ albums \|", line)
        if match:
            artist = match.group(1).strip()
            if artist and artist not in artists:
                artists.append(artist)

    return artists


def score_candidate(result: dict) -> float:
    actual_plays = float(result.get("actualPlays") or 0)
    evidence = float(result.get("libraryEvidenceRecords") or 0)
    years = float(result.get("yearsActive") or 0)

    return (actual_plays * 1.0) + (evidence * 4.0) + (years * 20.0)


def classify_candidate(artist: str, result: dict) -> str:
    name = str(artist or "").lower()

    family_words = [
        "band",
        "orchestra",
        "trio",
        "quartet",
        "quintet",
        "company",
        "brothers",
        "sisters",
        "experience",
        "revolution",
        "heartbreakers",
        "attractions",
        "crickets",
        "cardinals",
    ]

    if any(word in name for word in family_words):
        return "family_candidate"

    if result.get("actualPlays", 0) >= 500 or result.get("yearsActive", 0) >= 10:
        return "standalone_or_family_review"

    return "needs_review"


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    known = load_known_members()
    review_status = load_review_status()
    reviewed = review_status
    artists = load_library_artists()

    candidates = []

    for artist in artists:
        artist_key = artist.lower().strip()

        if artist_key in known:
            continue

        if reviewed.get(artist_key, {}).get("status") == "reviewed_standalone":
            continue

        result = run_artist_query(artist)

        if result.get("error"):
            candidates.append({
                "artist": artist,
                "error": result["error"],
                "score": 0,
            })
            continue

        actual_plays = int(result.get("actualPlays") or 0)
        evidence = int(result.get("libraryEvidenceRecords") or 0)
        years = int(result.get("yearsActive") or 0)

        if actual_plays == 0 and evidence == 0:
            continue

        candidates.append({
            "artist": result.get("artist") or artist,
            "query": artist,
            "actualPlays": actual_plays,
            "libraryEvidenceRecords": evidence,
            "yearsActive": years,
            "score": round(score_candidate(result), 2),
            "candidateType": classify_candidate(result.get("artist") or artist, result),
            "firstPlayedDate": result.get("firstPlayedDate"),
            "latestPlayedDate": result.get("latestPlayedDate"),
        })

    candidates.sort(key=lambda row: row.get("score", 0), reverse=True)

    report = {
        "source": str(RELATIONSHIPS_MD.relative_to(ROOT)),
        "knownFamilyMembers": len(known),
        "reviewedStandalone": len(reviewed),
        "libraryArtistsEvaluated": len(artists),
        "candidateCount": len(candidates),
        "candidates": candidates[:100],
    }

    OUT_JSON.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    lines = [
        "# Artist Family Candidate Scan",
        "",
        f"Source: `{RELATIONSHIPS_MD.relative_to(ROOT)}`",
        f"Known family members: `{len(known)}`",
        f"Reviewed standalone artists: `{len(reviewed)}`",
        f"Library artists evaluated: `{len(artists)}`",
        f"Candidates returned: `{len(candidates[:100])}`",
        "",
        "## Top Candidates",
        "",
    ]

    for idx, row in enumerate(candidates[:50], start=1):
        lines.extend([
            f"### {idx}. {row['artist']}",
            "",
            f"- Score: `{row['score']}`",
            f"- Candidate Type: `{row.get('candidateType')}`",
            f"- Actual Plays: `{row.get('actualPlays', 0)}`",
            f"- Library Evidence Records: `{row.get('libraryEvidenceRecords', 0)}`",
            f"- Years Active: `{row.get('yearsActive', 0)}`",
            f"- First Played: `{row.get('firstPlayedDate')}`",
            f"- Latest Played: `{row.get('latestPlayedDate')}`",
            f"- Query Source: `{row.get('query', row['artist'])}`",
            "",
        ])

    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"Wrote {OUT_JSON}")
    print(f"Wrote {OUT_MD}")
    print()
    print("# Top 20 Candidates")
    for idx, row in enumerate(candidates[:20], start=1):
        print(
            f"{idx:>2}. {row['artist']}: "
            f"type={row.get('candidateType')} | "
            f"score={row['score']} | plays={row.get('actualPlays', 0)} | "
            f"evidence={row.get('libraryEvidenceRecords', 0)} | years={row.get('yearsActive', 0)}"
        )


if __name__ == "__main__":
    main()
