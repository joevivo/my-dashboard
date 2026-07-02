import json
import zipfile
from pathlib import Path
from collections import Counter

base = Path.home() / "Downloads" / "apple-music-working" / "Apple_Media_Services_python" / "Apple_Media_Services" / "Apple Music Activity"

def read_zipped_json(path):
    with zipfile.ZipFile(path) as z:
        with z.open(z.namelist()[0]) as f:
            return json.load(f)

tracks = read_zipped_json(base / "Apple Music Library Tracks.json.zip")
playlists = read_zipped_json(base / "Apple Music Library Playlists.json.zip")

track_by_id = {
    t.get("Track Identifier"): t
    for t in tracks
    if t.get("Track Identifier") is not None
}

rows = []

for playlist in playlists:

    title = (playlist.get("Title") or "").strip()

    if not title:
        continue

    track_ids = playlist.get("Playlist Item Identifiers", [])

    artists = set()
    albums = set()
    total_plays = 0

    for track_id in track_ids:
        track = track_by_id.get(track_id)

        if not track:
            continue

        artists.add(track.get("Artist", "Unknown"))
        albums.add(track.get("Album", "Unknown"))
        total_plays += int(track.get("Track Play Count") or 0)

    rows.append(
        (
            title,
            len(track_ids),
            len(artists),
            len(albums),
            total_plays,
        )
    )

rows.sort(key=lambda x: x[1], reverse=True)

print(
    f'{"Playlist":45} {"Songs":>6} {"Artists":>8} {"Albums":>8} {"Plays":>10}'
)

print("-" * 85)

for title, songs, artists, albums, plays in rows:
    print(
        f'{title[:45]:45} {songs:6} {artists:8} {albums:8} {plays:10,}'
    )
