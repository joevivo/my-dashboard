import json
import zipfile
from collections import Counter
from pathlib import Path

SOURCE = Path("C:/Users/joevi/Downloads/apple-music-working/Apple_Media_Services_python/Apple_Media_Services/Apple Music Activity/Apple Music Library Tracks.json.zip")

albums = Counter()

with zipfile.ZipFile(SOURCE) as z:
    rows = json.loads(z.read(z.namelist()[0]))

for row in rows:
    artist = str(row.get("Album Artist") or row.get("Artist") or "").strip()

    if artist.lower() != "the replacements":
        continue

    album = str(row.get("Album") or "").strip()

    try:
        plays = int(row.get("Track Play Count") or 0)
    except ValueError:
        plays = 0

    if album and plays > 0:
        albums[album] += plays

print("# The Replacements Album Distribution")
print()

for album, plays in albums.most_common():
    print(f"{plays:4}  {album}")
