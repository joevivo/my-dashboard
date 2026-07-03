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

    rows_by_artist = {}
    for row in rows:
        artist = row.get("artistName") or row.get("artist") or row.get("name")
        if not artist:
            continue
        rows_by_artist.setdefault(artist, []).append(row)

    activity = []

    for item in artists:
        artist = item["artist"]
        count = item["count"]
        artist_rows = rows_by_artist.get(artist, [])

        album_names = []
        source_types = set()

        for row in artist_rows:
            source_types.add(row.get("objectType") or "unknown")
            if row.get("objectType") in ["albums", "library-albums"] and row.get("name"):
                album_names.append(row["name"])

        unique_albums = []
        for name in album_names:
            if name not in unique_albums:
                unique_albums.append(name)

        if count >= 3:
            priority = "High"
            why = "Concentrated current listening signal."
        elif count == 2:
            priority = "Medium"
            why = "Repeated current listening signal."
        else:
            priority = "Low"
            why = "Single current listening signal."

        if unique_albums:
            context = "Recent album context: " + ", ".join(unique_albums[:2])
        elif source_types:
            context = "Recent source types: " + ", ".join(sorted(source_types)[:3])
        else:
            context = "Recent Apple live source evidence is available."

        activity.append({
            "artist": artist,
            "recentObjectCount": count,
            "priority": priority,
            "status": f"{priority}-priority current signal",
            "whyItMatters": why,
            "evidence": f"{count} recent Apple live object{'s' if count != 1 else ''}.",
            "context": context,
            "confidence": "Source-backed current signal; not a relationship classification.",
            "investigationHint": f"Open {artist} to compare live evidence with actual plays, skips, albums, and family identity.",
            "nextStep": "Open Artist Intelligence",
            "source": "apple_music_recent_played",
        })

    return activity


def load_recent_rows_from_snapshot(snapshot_id):
    if not snapshot_id:
        return []

    raw_path = LIVE_DIR / "history" / snapshot_id / "apple_recent_played.json"
    if not raw_path.exists():
        return []

    with raw_path.open("r", encoding="utf-8") as f:
        raw = json.load(f)

    captured_at = raw.get("capturedAt")
    rows = []

    for index, item in enumerate(raw.get("response", {}).get("data", []), start=1):
        attributes = item.get("attributes", {})
        play_params = attributes.get("playParams") or {}

        rows.append(normalize_row({
            "snapshotId": snapshot_id,
            "capturedAt": captured_at,
            "rank": index,
            "appleId": item.get("id"),
            "objectType": item.get("type"),
            "name": attributes.get("name"),
            "artistName": attributes.get("artistName"),
            "releaseDate": attributes.get("releaseDate"),
            "genreNames": attributes.get("genreNames") or [],
            "trackCount": attributes.get("trackCount"),
            "url": attributes.get("url"),
            "playParamsKind": play_params.get("kind"),
            "source": "apple_music_recent_played",
        }))

    return rows


def previous_recent_snapshot_id(current_snapshot_id):
    history_dir = LIVE_DIR / "history"

    if not history_dir.exists():
        return None

    snapshot_ids = sorted([
        path.name
        for path in history_dir.iterdir()
        if path.is_dir() and (path / "apple_recent_played.json").exists()
    ])

    if not snapshot_ids:
        return None

    if not current_snapshot_id:
        return snapshot_ids[-1]

    previous = [
        snapshot_id
        for snapshot_id in snapshot_ids
        if snapshot_id < current_snapshot_id
    ]

    return previous[-1] if previous else None


def whats_changed(current_rows, current_snapshot_id):
    previous_snapshot_id = previous_recent_snapshot_id(current_snapshot_id)

    if not previous_snapshot_id:
        return {
            "status": "Unavailable",
            "headline": "No previous comparable snapshot found.",
            "note": "Run another live refresh to enable snapshot comparison.",
            "currentSnapshotId": current_snapshot_id,
            "previousSnapshotId": None,
            "newArtists": [],
            "departedArtists": [],
            "changedArtists": [],
        }

    previous_rows = load_recent_rows_from_snapshot(previous_snapshot_id)

    current_artists = ranked_artists(current_rows)
    previous_artists = ranked_artists(previous_rows)

    current_map = {
        item["artist"]: item["count"]
        for item in current_artists
    }
    previous_map = {
        item["artist"]: item["count"]
        for item in previous_artists
    }

    new_artists = [
        {"artist": artist, "currentCount": current_map[artist]}
        for artist in current_map
        if artist not in previous_map
    ]

    departed_artists = [
        {"artist": artist, "previousCount": previous_map[artist]}
        for artist in previous_map
        if artist not in current_map
    ]

    changed_artists = []

    for artist in current_map:
        if artist not in previous_map:
            continue

        current_count = current_map[artist]
        previous_count = previous_map[artist]
        delta = current_count - previous_count

        if delta:
            changed_artists.append({
                "artist": artist,
                "previousCount": previous_count,
                "currentCount": current_count,
                "delta": delta,
            })

    changed_artists = sorted(
        changed_artists,
        key=lambda item: (-abs(item["delta"]), item["artist"])
    )

    headline = (
        f"{len(new_artists)} new, "
        f"{len(changed_artists)} changed, "
        f"{len(departed_artists)} no longer visible versus previous snapshot."
    )

    return {
        "status": "Calculated",
        "headline": headline,
        "note": "Compares current Apple recent-played artist evidence with the previous usable live snapshot.",
        "currentSnapshotId": current_snapshot_id,
        "previousSnapshotId": previous_snapshot_id,
        "newArtists": new_artists[:8],
        "departedArtists": departed_artists[:8],
        "changedArtists": changed_artists[:8],
    }



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
        "whatsChanged": whats_changed(recent_rows, recent.get("snapshotId")),
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
