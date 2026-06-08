from pathlib import Path
from zipfile import ZipFile
from collections import Counter
from datetime import datetime
import json
import sys

if len(sys.argv) != 3:
    print("Usage: python library_range_summary.py YYYY-MM-DD YYYY-MM-DD")
    sys.exit(1)

start_date = datetime.strptime(sys.argv[1], "%Y-%m-%d").date()
end_date = datetime.strptime(sys.argv[2], "%Y-%m-%d").date()

path = (
    Path.home()
    / "Downloads"
    / "apple-music-working"
    / "Apple_Media_Services_python"
    / "Apple_Media_Services"
    / "Apple Music Activity"
    / "Apple Music Library Tracks.json.zip"
)

with ZipFile(path, "r") as z:
    with z.open("Apple Music Library Tracks.json") as f:
        data = json.load(f)

matches = []

for row in data:
    played = row.get("Last Played Date")

    if not played:
        continue

    try:
        played_date = datetime.strptime(
            str(played)[:10],
            "%Y-%m-%d"
        ).date()
    except Exception:
        continue

    if start_date <= played_date <= end_date:
        matches.append(row)

album_counts = Counter()
artist_counts = Counter()

for row in matches:
    album = row.get("Album")
    artist = row.get("Artist")

    if album:
        album_counts[album] += 1

    if artist:
        artist_counts[artist] += 1

top_albums = [
    {"album": album, "count": count}
    for album, count in album_counts.most_common(15)
]

top_artists = [
    {"artist": artist, "count": count}
    for artist, count in artist_counts.most_common(15)
]

memory_read = []

if not matches:
    memory_read.append("No library-track evidence found for this period.")
elif artist_counts:
    top_artist, top_artist_count = artist_counts.most_common(1)[0]

    memory_read.append(f"A possible anchor for this period is {top_artist}.")
    memory_read.append(
        f"{top_artist} appears on {top_artist_count} tracks with last-played dates in this range."
    )

    if top_albums:
        album_anchor_text = ", ".join(
            f"{item['album']} ({item['count']} tracks)"
            for item in top_albums[:5]
        )
        memory_read.append(f"Possible album anchors: {album_anchor_text}.")

    memory_read.append(
        "Caution: this is reconstruction from library Last Played Date, not complete play-count history."
    )

result = {
    "startDate": str(start_date),
    "endDate": str(end_date),
    "tracksMatched": len(matches),
    "topAlbums": top_albums,
    "topArtists": top_artists,
    "memoryRead": memory_read,
    "sourceNote": "Reconstruction from Apple Music Library Tracks Last Played Date.",
}

print(json.dumps(result, indent=2))