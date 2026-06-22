import json
import re
import sys
from pathlib import Path

from artist_query_core import ArtistQueryEngine, canonical_key

ROOT = Path(__file__).resolve().parents[4]

FAMILIES_FILE = ROOT / "data/music/curated/artistFamilies.json"
REVIEW_STATUS_FILE = ROOT / "data/music/curated/artistFamilyReviewStatus.json"
LIBRARY_SONGS_FILE = ROOT / "data/music/live/history/2026-06-20_130925Z/apple_library_songs.json"
RELATIONSHIPS_MD = ROOT / "data/music/live/apple_library_relationships.md"
ARTIST_INVENTORY_FILE = ROOT / "data/music/live/apple_library_artist_inventory.json"

OUT_DIR = ROOT / "data/music/live"
OUT_FILE = OUT_DIR / "artist_universe.json"


def load_json(path: Path) -> dict | list:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def load_library_song_artists() -> set[str]:
    data = load_json(LIBRARY_SONGS_FILE)
    artists = set()

    for item in data.get("response", {}).get("data", []):
        artist = item.get("attributes", {}).get("artistName")
        if artist:
            artists.add(artist.strip())

    return artists


def load_artist_inventory() -> list[dict]:
    if not ARTIST_INVENTORY_FILE.exists():
        return []
    data = load_json(ARTIST_INVENTORY_FILE)
    return data.get("artists", [])


def load_artist_inventory() -> list[dict]:
    if not ARTIST_INVENTORY_FILE.exists():
        return []
    data = load_json(ARTIST_INVENTORY_FILE)
    return data.get("artists", [])


def load_relationship_report_artists() -> set[str]:
    if not RELATIONSHIPS_MD.exists():
        return set()

    text = RELATIONSHIPS_MD.read_text(encoding="utf-8", errors="replace")
    artists = set()

    for line in text.splitlines():
        match = re.match(r"^- ([^:]+): \d+ albums \|", line)
        if match:
            artist = match.group(1).strip()
            if artist:
                artists.add(artist)

    return artists


def load_family_index() -> dict:
    families = load_json(FAMILIES_FILE)
    index = {}

    for family in families:
        for member in family.get("members", []):
            index[member.lower().strip()] = {
                "familyName": family.get("familyName"),
                "primaryArtist": family.get("primaryArtist"),
                "relationshipType": family.get("relationshipType"),
            }

    return index


def load_review_status() -> dict:
    if not REVIEW_STATUS_FILE.exists():
        return {}

    raw = load_json(REVIEW_STATUS_FILE)
    normalized = {}

    for artist, value in raw.items():
        if isinstance(value, dict):
            normalized[artist.lower().strip()] = value
        else:
            normalized[artist.lower().strip()] = {"status": value}

    return normalized


def main():
    limit = None
    top = None
    output_file = OUT_FILE

    if "--limit" in sys.argv:
        idx = sys.argv.index("--limit")
        limit = int(sys.argv[idx + 1])

    if "--top" in sys.argv:
        idx = sys.argv.index("--top")
        top = int(sys.argv[idx + 1])

    if "--output" in sys.argv:
        idx = sys.argv.index("--output")
        output_file = OUT_DIR / sys.argv[idx + 1]

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    library_song_artists = load_library_song_artists()
    relationship_report_artists = load_relationship_report_artists()
    artist_inventory = load_artist_inventory()

    inventory_artists = {
        row.get("artist", "").strip()
        for row in artist_inventory
        if row.get("artist")
    }

    library_artists = library_song_artists | relationship_report_artists | inventory_artists

    family_index = load_family_index()
    review_status = load_review_status()
    engine = ArtistQueryEngine()

    universe = []

    artists_to_process = sorted(library_artists)

    if top:
        ranked_inventory = sorted(
            artist_inventory,
            key=lambda row: (
                row.get("archivePlays") or 0,
                row.get("libraryAlbumCount") or 0,
                row.get("artist") or "",
            ),
            reverse=True,
        )
        artists_to_process = [
            row["artist"]
            for row in ranked_inventory
            if row.get("artist")
        ][:top]
    elif limit:
        artists_to_process = artists_to_process[:limit]

    for artist in artists_to_process:
        try:
            result = engine.query_artist(artist)
        except Exception as error:
            result = {"query": artist, "error": str(error)}

        returned_artist = result.get("artist") or artist
        artist_key = returned_artist.lower().strip()
        query_key = artist.lower().strip()

        family = family_index.get(query_key) or family_index.get(artist_key)

        review = review_status.get(query_key) or review_status.get(artist_key)
        evidence = {
            "actualPlays": result.get("actualPlays", 0),
            "actualSkips": result.get("actualSkips", 0),
            "hoursListened": result.get("hoursListened", 0),
            "libraryEvidenceRecords": result.get("libraryEvidenceRecords", 0),
            "yearsActive": result.get("yearsActive", 0),
            "firstPlayedDate": result.get("firstPlayedDate"),
            "latestPlayedDate": result.get("latestPlayedDate"),
        }

        source_presence = {
            "appleLibrarySongs": artist in library_song_artists,
            "appleLibraryRelationshipsReport": artist in relationship_report_artists,
            "appleLibraryArtistInventory": artist in inventory_artists,
        }

        relationship = {
            "familyName": family.get("familyName") if family else None,
            "primaryArtist": family.get("primaryArtist") if family else None,
            "relationshipType": family.get("relationshipType") if family else None,
        }

        signals = {
            "isFamilyMember": family is not None,
            "isReviewedStandalone": bool(review and review.get("status") == "reviewed_standalone"),
            "isUnclassified": family is None and review is None,
            "isLibraryOnly": (evidence.get("actualPlays") or 0) == 0 and (evidence.get("libraryEvidenceRecords") or 0) > 0,
            "isHighPriorityReview": (
                family is None
                and review is None
                and (
                    (evidence.get("actualPlays") or 0) >= 250
                    or (evidence.get("yearsActive") or 0) >= 10
                    or (evidence.get("libraryEvidenceRecords") or 0) >= 50
                )
            ),
        }

        universe.append({
            "artist": returned_artist,
            "canonicalKey": canonical_key(returned_artist),
            "identity": {
                "displayName": returned_artist,
                "queryName": artist,
                "aliases": sorted({artist, returned_artist}),
            },
            "evidence": evidence,
            "relationship": relationship,
            "review": review,
            "signals": signals,
            "provenance": [
                name for name, present in {
                    "apple_library_songs": source_presence["appleLibrarySongs"],
                    "apple_library_relationships_report": source_presence["appleLibraryRelationshipsReport"],
                    "apple_library_artist_inventory": source_presence["appleLibraryArtistInventory"],
                    "artist_query_core": True,
                    "artistFamilies": family is not None,
                    "artistFamilyReviewStatus": review is not None,
                }.items()
                if present
            ],

            # Legacy compatibility fields. Remove after downstream consumers migrate.
            "query": artist,
            "sourcePresence": source_presence,
            "metrics": evidence,
            "family": family,
            "reviewStatus": review,
            "error": result.get("error"),
        })

    universe.sort(
        key=lambda row: (
            row["metrics"].get("actualPlays") or 0,
            row["metrics"].get("libraryEvidenceRecords") or 0,
            row["metrics"].get("yearsActive") or 0,
        ),
        reverse=True,
    )

    payload = {
        "version": "artist_universe_v2",
        "sources": [
            str(LIBRARY_SONGS_FILE.relative_to(ROOT)),
            str(RELATIONSHIPS_MD.relative_to(ROOT)),
        ],
        "appleLibrarySongArtists": len(library_song_artists),
        "relationshipReportArtists": len(relationship_report_artists),
        "artistInventoryArtists": len(inventory_artists),
        "artistCount": len(universe),
        "availableArtistCount": len(library_artists),
        "limit": limit,
        "top": top,
        "artists": universe,
    }

    output_file.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    print(f"Wrote {output_file}")
    print(f"Artists processed: {len(universe)}")
    print(f"Artists available: {len(library_artists)}")
    if limit:
        print(f"Limit: {limit}")
    if top:
        print(f"Top: {top}")
    print()
    if top:
        print(f"# Top 20 Processed Artists")
        print(f"Selection mode: top {top} by Apple inventory ranking")
    elif limit:
        print("# Top 20 Processed Artists")
        print(f"Selection mode: first {limit} artists alphabetically")
    else:
        print("# Top 20 Artists")
    for idx, row in enumerate(universe[:20], start=1):
        m = row["metrics"]
        family = row["family"]["familyName"] if row.get("family") else "-"
        print(
            f"{idx:>2}. {row['artist']} | plays={m['actualPlays']} | "
            f"evidence={m['libraryEvidenceRecords']} | years={m['yearsActive']} | family={family}"
        )


if __name__ == "__main__":
    main()
