import json
import zipfile
import sys
from pathlib import Path
from statistics import median
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

play_counts = []
artists = Counter()
albums = Counter()
songs = []
duration_ms = 0

target_playlist = sys.argv[1] if len(sys.argv) > 1 else "500 Songs"

for playlist in playlists:
    if playlist.get("Title","").strip().lower() == target_playlist.strip().lower():
        for track_id in playlist.get("Playlist Item Identifiers", []):
            track = track_by_id.get(track_id)

            if not track:
                continue

            plays = int(track.get("Track Play Count") or 0)
            artist = track.get("Artist","Unknown")
            album = track.get("Album","Unknown")
            title = track.get("Title","Unknown")

            play_counts.append(plays)

            artists[artist] += 1
            albums[album] += 1

            songs.append((plays, artist, title, album))

            duration_ms += int(track.get("Track Duration") or 0)

        break

print(f"Songs: {len(play_counts)}")
print(f"Distinct Artists: {len(artists)}")
print(f"Distinct Albums: {len(albums)}")
print(f"Total Plays: {sum(play_counts):,}")
print(f"Average Plays: {sum(play_counts)/len(play_counts):.1f}")
print(f"Median Plays: {median(play_counts):.1f}")
print(f"Hours: {duration_ms/1000/3600:.1f}")

print("\nTop Artists")
for artist,count in artists.most_common(20):
    print(f"{count:3}  {artist}")

print("\nMost Played Songs")
for plays, artist, title, album in sorted(songs, reverse=True)[:25]:
    print(f"{plays:4}  {artist} - {title}")

print("\nLeast Played Songs")
for plays, artist, title, album in sorted(songs)[:25]:
    print(f"{plays:4}  {artist} - {title}")

print("\nPlay Count Distribution")

buckets = {
    "0 plays": 0,
    "1-5 plays": 0,
    "6-10 plays": 0,
    "11-25 plays": 0,
    "26-50 plays": 0,
    "51+ plays": 0,
}

for plays in play_counts:
    if plays == 0:
        buckets["0 plays"] += 1
    elif plays <= 5:
        buckets["1-5 plays"] += 1
    elif plays <= 10:
        buckets["6-10 plays"] += 1
    elif plays <= 25:
        buckets["11-25 plays"] += 1
    elif plays <= 50:
        buckets["26-50 plays"] += 1
    else:
        buckets["51+ plays"] += 1

for label, count in buckets.items():
    print(f"{label:12} {count:3}")

print(f"\nArtist + Albums with 2+ songs in {target_playlist}")

artist_albums = Counter()
artist_album_titles = {}

for plays, artist, title, album in songs:
    key = (artist, album)
    artist_albums[key] += 1
    artist_album_titles.setdefault(key, []).append(title)

for (artist, album), count in artist_albums.most_common():
    if count >= 2:
        print(f"{count:3}  {artist} — {album}")
        for title in sorted(artist_album_titles[(artist, album)]):
            print(f"     - {title}")



print(f"\nArtists with 5+ songs in {target_playlist}")

artist_titles = {}

for plays, artist, title, album in songs:
    artist_titles.setdefault(artist, []).append((title, album, plays))

for artist, count in artists.most_common():
    if count >= 5:
        print(f"{count:3}  {artist}")
        for title, album, plays in sorted(artist_titles[artist]):
            print(f"     - {title} [{album}] ({plays} plays)")
