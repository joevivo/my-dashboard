import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
FAMILIES_FILE = ROOT / "data" / "music" / "curated" / "artistFamilies.json"
ARTIST_QUERY_SCRIPT = ROOT / "data" / "music" / "scripts" / "artist_query_summary.py"


def run_artist_query(name: str) -> dict:
    try:
        output = subprocess.check_output(
            [sys.executable, str(ARTIST_QUERY_SCRIPT), name],
            cwd=ROOT,
        ).decode("utf-8", errors="replace")
        return json.loads(output)
    except Exception as error:
        return {"error": str(error), "query": name}


def main():
    families = json.loads(FAMILIES_FILE.read_text(encoding="utf-8"))

    print("# Artist Family Validation")
    print(f"Families: {len(families)}")
    print()

    warnings = 0

    for family in families:
        family_name = family.get("familyName", "(missing familyName)")
        relationship_type = family.get("relationshipType", "(missing relationshipType)")
        members = family.get("members", [])

        print(f"## {family_name}")
        print(f"relationshipType: {relationship_type}")
        print(f"members: {len(members)}")

        if not family.get("familyName"):
            print("  WARN missing familyName")
            warnings += 1

        if not family.get("primaryArtist"):
            print("  WARN missing primaryArtist")
            warnings += 1

        if relationship_type == "(missing relationshipType)":
            print("  WARN missing relationshipType")
            warnings += 1

        if not isinstance(members, list) or not members:
            print("  WARN missing members")
            warnings += 1
            print()
            continue

        canonical_seen = {}

        for member in members:
            result = run_artist_query(member)

            if result.get("error"):
                print(f"  WARN {member}: query error: {result['error']}")
                warnings += 1
                continue

            returned_artist = result.get("artist")
            actual_plays = result.get("actualPlays", 0)
            evidence = result.get("libraryEvidenceRecords", 0)

            print(
                f"  OK {member} -> {returned_artist} | "
                f"actualPlays={actual_plays} | libraryEvidenceRecords={evidence}"
            )

            key = str(returned_artist or member).lower().strip()
            canonical_seen.setdefault(key, []).append(member)

            if not actual_plays and not evidence:
                print(f"    WARN no play/library evidence for member: {member}")
                warnings += 1

        for key, raw_members in canonical_seen.items():
            if len(raw_members) > 1:
                print(
                    f"  WARN duplicate canonical artist: {key} "
                    f"from {raw_members}"
                )
                warnings += 1

        print()

    print(f"Warnings: {warnings}")

    if warnings:
        sys.exit(1)


if __name__ == "__main__":
    main()
