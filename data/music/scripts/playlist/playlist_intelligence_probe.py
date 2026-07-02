import json
import sys
import zipfile
from pathlib import Path

base = Path.home() / "Downloads" / "apple-music-working" / "Apple_Media_Services_python" / "Apple_Media_Services" / "Apple Music Activity"

tracks_zip = base / "Apple Music Library Tracks.json.zip"
playlists_zip = base / "Apple Music Library Playlists.json.zip"

artist_query = " ".join(sys.argv[1:]).strip()

if not artist_query:
    print(json.dumps({"error": "Artist required"}))
    sys.exit(1)

def read_zipped_json(path):
    with zipfile.ZipFile(path) as z:
        name = z.namelist()[0]
        with z.open(name) as f:
            return json.load(f)

tracks = read_zipped_json(tracks_zip)
playlists = read_zipped_json(playlists_zip)

track_by_id = {
    item.get("Track Identifier"): item
    for item in tracks
    if item.get("Track Identifier") is not None
}

def is_genius_mix(playlist):
    container_type = str(
        playlist.get("Container Type", "")
    ).lower()

    title = str(
        playlist.get("Title", "")
    ).lower()

    return (
        "genius" in container_type
        or "genius" in title
    )

intentional = []
generated = []

for playlist in playlists:
    ids = playlist.get("Playlist Item Identifiers") or []
    matches = []

    for track_id in ids:
        track = track_by_id.get(track_id)

        if not track:
            continue

        artist = str(track.get("Artist", ""))
        album_artist = str(track.get("Album Artist", ""))

        if (
            artist_query.lower() in artist.lower()
            or artist_query.lower() in album_artist.lower()
        ):
            matches.append(track)

    if not matches:
        continue

    record = {
        "playlist": playlist.get("Title", ""),
        "count": len(matches),
        "songs": [
            item.get("Title", "")
            for item in matches[:10]
        ],
    }

    if is_genius_mix(playlist):
        generated.append(record)
    else:
        intentional.append(record)

intentional.sort(
    key=lambda x: x["count"],
    reverse=True,
)

generated.sort(
    key=lambda x: x["count"],
    reverse=True,
)

track_links = sum(x["count"] for x in intentional)

largest = intentional[0] if intentional else None

largest_count = largest["count"] if largest else 0

density = round(
    track_links / max(len(intentional), 1),
    2
)

world_score = round(
    largest_count / max(track_links, 1),
    3
)

if track_links <= 3:
    classification = "Sparse Curated Presence"
    classification_reason = "Very few intentional playlist links."
elif world_score >= 0.65 and largest_count >= 25:
    classification = "Dedicated World Artist"
    classification_reason = "One dominant intentional playlist carries most of the playlist relationship."
elif world_score >= 0.45 and largest_count >= 25:
    classification = "World + Context Artist"
    classification_reason = "A major artist world exists, with additional playlist context around it."
elif len(intentional) >= 10 and density <= 2:
    classification = "Distributed Identity Artist"
    classification_reason = "The artist appears across many intentional playlists without one dominant world."
elif len(intentional) >= 8:
    classification = "Context Artist"
    classification_reason = "The artist appears across many intentional playlist contexts."
else:
    classification = "Playlist Present"
    classification_reason = "The artist has some intentional playlist presence."

result = {
    "artist": artist_query,
    "intentionalPlaylistCount": len(intentional),
    "generatedPlaylistCount": len(generated),
    "trackLinks": track_links,
    "density": density,
    "worldScore": world_score,
    "classification": classification,
    "classificationReason": classification_reason,
    "largestPlaylist": largest,
    "topPlaylists": intentional[:10],
}

print(json.dumps(result, indent=2, ensure_ascii=False))
