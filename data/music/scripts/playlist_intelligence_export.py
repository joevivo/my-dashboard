import json
import zipfile
from pathlib import Path
from collections import Counter, defaultdict
from statistics import median

base = Path.home() / "Downloads" / "apple-music-working" / "Apple_Media_Services_python" / "Apple_Media_Services" / "Apple Music Activity"

target_playlists = [
    "500 Songs",
    "deck & chill",
    "let’s go streaking!",
]

output_path = Path("data/music/playlist_intelligence.json")

def read_zipped_json(path):
    with zipfile.ZipFile(path) as z:
        with z.open(z.namelist()[0]) as f:
            return json.load(f)

def norm(value):
    return (value or "").strip().lower()

def song_key(track):
    return (
        norm(track.get("Artist", "Unknown")),
        norm(track.get("Title", "Unknown")),
    )

def song_obj(track):
    return {
        "artist": track.get("Artist", "Unknown"),
        "song": track.get("Title", "Unknown"),
        "album": track.get("Album", "Unknown"),
        "plays": int(track.get("Track Play Count") or 0),
    }

tracks = read_zipped_json(base / "Apple Music Library Tracks.json.zip")
playlists = read_zipped_json(base / "Apple Music Library Playlists.json.zip")

track_by_id = {
    t.get("Track Identifier"): t
    for t in tracks
    if t.get("Track Identifier") is not None
}

playlist_tracks = {}

for target in target_playlists:
    matched = next(
        (p for p in playlists if norm(p.get("Title")) == norm(target)),
        None
    )

    if not matched:
        playlist_tracks[target] = []
        continue

    playlist_tracks[target] = [
        track_by_id[track_id]
        for track_id in matched.get("Playlist Item Identifiers", [])
        if track_id in track_by_id
    ]

playlist_summaries = []

for name, pts in playlist_tracks.items():
    artists = Counter(t.get("Artist", "Unknown") for t in pts)
    albums = Counter(t.get("Album", "Unknown") for t in pts)
    plays = [int(t.get("Track Play Count") or 0) for t in pts]

    playlist_summaries.append({
        "name": name,
        "songCount": len(pts),
        "artistCount": len(artists),
        "albumCount": len(albums),
        "totalPlays": sum(plays),
        "averagePlays": round(sum(plays) / len(plays), 1) if plays else 0,
        "medianPlays": round(median(plays), 1) if plays else 0,
        "zeroPlayCount": sum(1 for p in plays if p == 0),
        "lowPlayCount": sum(1 for p in plays if 1 <= p <= 5),
        "highPlayCount": sum(1 for p in plays if p >= 25),
        "topArtists": [
            {"artist": artist, "songCount": count}
            for artist, count in artists.most_common(10)
        ],
    })

artist_to_playlists = defaultdict(set)
song_to_playlists = defaultdict(set)
song_examples = {}

for playlist_name, pts in playlist_tracks.items():
    for track in pts:
        artist = track.get("Artist", "Unknown")
        artist_to_playlists[artist].add(playlist_name)

        skey = song_key(track)
        song_to_playlists[skey].add(playlist_name)
        song_examples[skey] = song_obj(track)

shared_core_artists = [
    {
        "artist": artist,
        "playlists": sorted(list(names)),
        "playlistCount": len(names),
    }
    for artist, names in artist_to_playlists.items()
    if len(names) >= 2
]

shared_core_artists = sorted(
    shared_core_artists,
    key=lambda x: (-x["playlistCount"], x["artist"].lower())
)

bridge_songs = []

for skey, names in song_to_playlists.items():
    if len(names) >= 2:
        item = song_examples[skey]
        item["playlists"] = sorted(list(names))
        item["playlistCount"] = len(names)
        bridge_songs.append(item)

bridge_songs = sorted(
    bridge_songs,
    key=lambda x: (-x["playlistCount"], x["artist"].lower(), x["song"].lower())
)

playlist_signatures = []

for name, pts in playlist_tracks.items():
    # v0 placeholder: use highest-played songs as provisional signatures.
    # This is intentionally not final intelligence logic.
    top_tracks = sorted(
        [song_obj(t) for t in pts],
        key=lambda x: (-x["plays"], x["artist"].lower(), x["song"].lower())
    )[:5]

    for track in top_tracks:
        playlist_signatures.append({
            "playlist": name,
            "artist": track["artist"],
            "song": track["song"],
            "album": track["album"],
            "plays": track["plays"],
            "reason": "Provisional signature: high-play representative song",
        })

data = {
    "generatedBy": "playlist_intelligence_export.py",
    "playlists": playlist_summaries,
    "sharedCoreArtists": shared_core_artists,
    "bridgeSongs": bridge_songs,
    "playlistSignatures": playlist_signatures,
}

output_path.parent.mkdir(parents=True, exist_ok=True)

with output_path.open("w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print(f"Wrote {output_path}")
print(f"Playlists: {len(playlist_summaries)}")
print(f"Shared core artists: {len(shared_core_artists)}")
print(f"Bridge songs: {len(bridge_songs)}")
print(f"Playlist signatures: {len(playlist_signatures)}")

