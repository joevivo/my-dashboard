import json
import zipfile
import sys
from pathlib import Path
from collections import Counter, defaultdict

base = Path.home() / "Downloads" / "apple-music-working" / "Apple_Media_Services_python" / "Apple_Media_Services" / "Apple Music Activity"

DEFAULT_PLAYLISTS = [
    "500 Songs",
    "deck & chill",
    "let’s go streaking!",
]

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

def song_label(track):
    return f'{track.get("Artist","Unknown")} - {track.get("Title","Unknown")}'

tracks = read_zipped_json(base / "Apple Music Library Tracks.json.zip")
playlists = read_zipped_json(base / "Apple Music Library Playlists.json.zip")

track_by_id = {
    t.get("Track Identifier"): t
    for t in tracks
    if t.get("Track Identifier") is not None
}

playlist_names = sys.argv[1:] if len(sys.argv) > 1 else DEFAULT_PLAYLISTS

playlist_data = {}

for target in playlist_names:
    matched_playlist = None

    for playlist in playlists:
        if norm(playlist.get("Title")) == norm(target):
            matched_playlist = playlist
            break

    if not matched_playlist:
        print(f"WARNING: playlist not found: {target}")
        continue

    playlist_tracks = []

    for track_id in matched_playlist.get("Playlist Item Identifiers", []):
        track = track_by_id.get(track_id)
        if track:
            playlist_tracks.append(track)

    playlist_data[target] = playlist_tracks

print("\nPlaylist Summary")
for name, pts in playlist_data.items():
    artists = Counter(t.get("Artist", "Unknown") for t in pts)
    albums = Counter(t.get("Album", "Unknown") for t in pts)
    plays = [int(t.get("Track Play Count") or 0) for t in pts]

    print(f"\n{name}")
    print(f"  Songs: {len(pts)}")
    print(f"  Artists: {len(artists)}")
    print(f"  Albums: {len(albums)}")
    print(f"  Total Plays: {sum(plays):,}")
    print(f"  Avg Plays: {sum(plays)/len(plays):.1f}" if plays else "  Avg Plays: 0.0")

song_to_playlists = defaultdict(set)
song_examples = {}
artist_to_playlists = defaultdict(set)

for name, pts in playlist_data.items():
    for track in pts:
        skey = song_key(track)
        song_to_playlists[skey].add(name)
        song_examples[skey] = song_label(track)

        artist_to_playlists[track.get("Artist", "Unknown")].add(name)

print("\nSongs in Multiple Playlists")
multi_songs = [
    (song_examples[skey], sorted(list(names)))
    for skey, names in song_to_playlists.items()
    if len(names) >= 2
]

for label, names in sorted(multi_songs, key=lambda x: (-len(x[1]), x[0].lower())):
    print(f"  {label}")
    print(f"     {', '.join(names)}")

print("\nArtists in All Playlists")
all_playlist_count = len(playlist_data)

artists_all = [
    artist for artist, names in artist_to_playlists.items()
    if len(names) == all_playlist_count
]

for artist in sorted(artists_all, key=str.lower):
    print(f"  {artist}")

print("\nArtists in Multiple Playlists")
multi_artists = [
    (artist, sorted(list(names)))
    for artist, names in artist_to_playlists.items()
    if len(names) >= 2
]

for artist, names in sorted(multi_artists, key=lambda x: (-len(x[1]), x[0].lower())):
    print(f"  {artist}")
    print(f"     {', '.join(names)}")

print("\nUnique Artists by Playlist")
for name in playlist_data:
    unique = [
        artist for artist, names in artist_to_playlists.items()
        if names == {name}
    ]

    print(f"\n{name}")
    print(f"  Unique Artists: {len(unique)}")
    for artist in sorted(unique, key=str.lower)[:40]:
        print(f"     {artist}")
