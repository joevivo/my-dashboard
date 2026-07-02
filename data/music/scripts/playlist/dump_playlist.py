import json
import zipfile
from pathlib import Path

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

for playlist in playlists:
    if playlist.get("Title", "").strip().lower() == "500 songs":
        print(f'Playlist: {playlist.get("Title")}')
        print()

        for track_id in playlist.get("Playlist Item Identifiers", []):
            track = track_by_id.get(track_id)

            if not track:
                continue

            artist = track.get("Artist", "Unknown")
            song = track.get("Title", "Unknown")

            print(f"{artist} - {song}")

        break
