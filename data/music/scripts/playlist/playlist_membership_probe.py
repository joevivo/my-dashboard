import json
import sys
import zipfile
from pathlib import Path

base = Path.home() / "Downloads" / "apple-music-working" / "Apple_Media_Services_python" / "Apple_Media_Services" / "Apple Music Activity"

tracks_zip = base / "Apple Music Library Tracks.json.zip"
playlists_zip = base / "Apple Music Library Playlists.json.zip"

artist_query = " ".join(sys.argv[1:]).strip() or "R.E.M."

def read_zipped_json(path):
    with zipfile.ZipFile(path) as z:
        name = z.namelist()[0]
        with z.open(name) as f:
            return json.load(f)

def text(value):
    return str(value or "").strip()

def matches_artist(track, query):
    q = query.lower()
    artist = text(track.get("Artist")).lower()
    album_artist = text(track.get("Album Artist")).lower()
    return q in artist or q in album_artist

tracks = read_zipped_json(tracks_zip)
playlists = read_zipped_json(playlists_zip)

track_by_id = {
    item.get("Track Identifier"): item
    for item in tracks
    if item.get("Track Identifier") is not None
}

matches = []

for playlist in playlists:
    title = playlist.get("Title", "")
    ids = playlist.get("Playlist Item Identifiers") or []
    found = []

    for track_id in ids:
        track = track_by_id.get(track_id)
        if not track:
            continue

        if matches_artist(track, artist_query):
            found.append({
                "song": track.get("Title", ""),
                "artist": track.get("Artist", ""),
                "album": track.get("Album", ""),
                "track_id": track_id,
            })

    if found:
        matches.append({
            "playlist": title,
            "container_type": playlist.get("Container Type", ""),
            "count": len(found),
            "songs": found[:20],
        })

summary = {
    "artist": artist_query,
    "playlistCount": len(matches),
    "trackLinks": sum(item["count"] for item in matches),
    "matches": matches,
}

print(json.dumps(summary, indent=2, ensure_ascii=False))
