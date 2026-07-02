import json
from collections import Counter
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[4]
LIVE_DIR = ROOT / "data" / "music" / "live"
WAREHOUSE_DIR = LIVE_DIR / "warehouse"

RECENT_PATH = WAREHOUSE_DIR / "apple_recent_objects.json"
HEAVY_PATH = WAREHOUSE_DIR / "apple_heavy_rotation_objects.json"
OUTPUT_PATH = LIVE_DIR / "music_dashboard.json"


def artwork_url(artwork, size=160):
    if not artwork:
        return None

    url = artwork.get("url")
    if not url:
        return None

    return url.replace("{w}", str(size)).replace("{h}", str(size))


def load_artwork_lookup(snapshot_id):
    if not snapshot_id:
        return {}

    raw_path = LIVE_DIR / "history" / snapshot_id / "apple_recent_played.json"
    if not raw_path.exists():
        return {}

    with raw_path.open("r", encoding="utf-8") as f:
        raw = json.load(f)

    lookup = {}
    for item in raw.get("response", {}).get("data", []):
        item_id = item.get("id")
        attributes = item.get("attributes", {})
        if item_id:
            lookup[item_id] = {
                "artworkUrl": artwork_url(attributes.get("artwork")),
                "artworkBgColor": attributes.get("artwork", {}).get("bgColor"),
            }

    return lookup


def load_dataset(path):
    if not path.exists():
        return {
            "dataset": path.stem,
            "generatedAt": None,
            "snapshotId": None,
            "source": None,
            "rowCount": 0,
            "rows": [],
        }

    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def clean_text(value):
    if value is None:
        return None

    text = str(value)
    replacements = {
        "â€™": "’",
        "â€˜": "‘",
        "â€œ": "“",
        "â€": "”",
        "â€“": "–",
        "â€”": "—",
    }

    for bad, good in replacements.items():
        text = text.replace(bad, good)

    return text


def normalize_row(row, artwork_lookup=None):
    artwork_lookup = artwork_lookup or {}
    normalized = dict(row)

    for key in ["name", "artistName", "objectType", "source", "playParamsKind", "url"]:
        normalized[key] = clean_text(normalized.get(key))

    genres = normalized.get("genreNames") or []
    normalized["genreNames"] = [clean_text(item) for item in genres if item]

    artwork = artwork_lookup.get(str(normalized.get("appleId")), {})
    normalized["artworkUrl"] = artwork.get("artworkUrl")
    normalized["artworkBgColor"] = artwork.get("artworkBgColor")

    return normalized


def ranked_artists(rows):
    counter = Counter()

    for row in rows:
        artist = row.get("artistName")
        if artist:
            counter[artist] += 1

    return [
        {"artist": artist, "count": count}
        for artist, count in counter.most_common(12)
    ]


def filter_objects(rows, object_type):
    return [
        row for row in rows
        if row.get("objectType") == object_type
    ]


def top_albums(rows):
    albums = filter_objects(rows, "albums")
    return albums[:16]


def playlists_and_stations(rows):
    playlists = [
        row for row in rows
        if row.get("objectType") in ["playlists", "library-playlists"]
    ]

    stations = [
        row for row in rows
        if row.get("objectType") == "stations"
    ]

    return {
        "playlists": playlists[:12],
        "stations": stations[:8],
    }


def relationship_activity(rows):
    artists = ranked_artists(rows)

    return [
        {
            "artist": item["artist"],
            "recentObjectCount": item["count"],
            "status": "Observed in latest Apple Music snapshot",
            "investigationHint": f"Investigate why {item['artist']} is active now.",
        }
        for item in artists
    ]


def build_dashboard():
    recent = load_dataset(RECENT_PATH)
    heavy = load_dataset(HEAVY_PATH)

    artwork_lookup = load_artwork_lookup(recent.get("snapshotId"))
    recent_rows = [normalize_row(row, artwork_lookup) for row in recent.get("rows", [])]
    heavy_rows = [normalize_row(row, artwork_lookup) for row in heavy.get("rows", [])]

    captured_at = recent.get("generatedAt") or heavy.get("generatedAt")

    dashboard = {
        "schemaVersion": 1,
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "snapshotId": recent.get("snapshotId") or heavy.get("snapshotId"),
        "capturedAt": captured_at,
        "sourceNote": "Live Apple Music observed objects captured from API snapshots. This is not complete play-count history.",
        "liveSummary": {
            "recentObjectCount": len(recent_rows),
            "heavyRotationCount": len(heavy_rows),
            "recentSource": recent.get("source"),
            "heavyRotationSource": heavy.get("source"),
        },
        "recentArtists": ranked_artists(recent_rows),
        "recentAlbums": top_albums(recent_rows),
        "heavyRotation": heavy_rows,
        "playlistsAndStations": playlists_and_stations(recent_rows + heavy_rows),
        "relationshipActivity": relationship_activity(recent_rows),
        "whatsChanged": {
            "status": "Not calculated yet",
            "note": "Snapshot comparison will be added after Dashboard v1 is rendering.",
        },
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    with OUTPUT_PATH.open("w", encoding="utf-8") as f:
        json.dump(dashboard, f, indent=2, ensure_ascii=False)

    print(f"Saved {OUTPUT_PATH}")
    print(json.dumps({
        "snapshotId": dashboard["snapshotId"],
        "capturedAt": dashboard["capturedAt"],
        "recentObjectCount": dashboard["liveSummary"]["recentObjectCount"],
        "heavyRotationCount": dashboard["liveSummary"]["heavyRotationCount"],
        "recentArtists": dashboard["recentArtists"][:5],
    }, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    build_dashboard()
