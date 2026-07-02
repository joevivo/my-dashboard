import json
import re
import zipfile
from collections import Counter
from pathlib import Path

SOURCE = Path("C:/Users/joevi/Downloads/apple-music-working/Apple_Media_Services_python/Apple_Media_Services/Apple Music Activity/Apple Music Library Tracks.json.zip")

TITLE_ALIASES = {
    "let it be replacements": "Let It Be",
    "let it be": "Let It Be",
    "pleased to meet me": "Pleased to Meet Me",
    "dont tell a soul": "Don't Tell a Soul",
    "sorry ma i forgot to take out the trash": "Sorry Ma, I Forgot to Take Out the Trash",
    "sorry ma forgot to take out the trash": "Sorry Ma, I Forgot to Take Out the Trash",
    "stink": "Stink",
    "all for nothing": "All for Nothing",
}


def normalize_key(value):
    value = str(value or "").lower()
    value = value.replace("&", " and ")
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def canonical_album(album):
    album = str(album or "").strip()

    album = re.sub(r"\s*\(Expanded Edition\)", "", album, flags=re.I)
    album = re.sub(r"\s*\(Deluxe Edition\)", "", album, flags=re.I)
    album = re.sub(r"\s*\(Remastered\)", "", album, flags=re.I)
    album = re.sub(r"\s*\[Disc\s+\d+\]", "", album, flags=re.I)

    key = normalize_key(album)

    if key in TITLE_ALIASES:
        return TITLE_ALIASES[key]

    return re.sub(r"\s+", " ", album).strip()


albums = Counter()

with zipfile.ZipFile(SOURCE) as z:
    rows = json.loads(z.read(z.namelist()[0]))

for row in rows:
    artist = str(row.get("Album Artist") or row.get("Artist") or "").strip()

    if artist.lower() != "the replacements":
        continue

    album = canonical_album(row.get("Album"))

    try:
        plays = int(row.get("Track Play Count") or 0)
    except ValueError:
        plays = 0

    if album and plays > 0:
        albums[album] += plays

print("# The Replacements Canonical Album Distribution")
print()

total = sum(albums.values())
anchor = albums.most_common(1)[0][1]

for album, plays in albums.most_common():
    share = plays / total if total else 0
    anchor_share = plays / anchor if anchor else 0

    print(
        f"{plays:4}  "
        f"{share:5.1%}  "
        f"{anchor_share:5.1%}  "
        f"{album}"
    )

print()
print(f"total: {total}")
print(f"anchor: {anchor}")

print()
print("albums >= 50% anchor:",
      sum(1 for _, p in albums.items() if p >= anchor * 0.50))

print("albums >= 25% anchor:",
      sum(1 for _, p in albums.items() if p >= anchor * 0.25))

print("albums >= 10% anchor:",
      sum(1 for _, p in albums.items() if p >= anchor * 0.10))
