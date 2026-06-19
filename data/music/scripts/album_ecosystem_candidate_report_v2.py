import json
import re
import zipfile
from collections import defaultdict
from math import log2
from pathlib import Path

SOURCE = Path("C:/Users/joevi/Downloads/apple-music-working/Apple_Media_Services_python/Apple_Media_Services/Apple Music Activity/Apple Music Library Tracks.json.zip")

ARTIST_ALIASES = {
    "death cab for cutie": "Death Cab for Cutie",
    "toad the wet sprocket": "Toad the Wet Sprocket",
    "r.e.m.": "R.E.M.",
}

COMPILATION_TERMS = [
    "greatest",
    "best of",
    "anthology",
    "chronicles",
    "hits",
    "soundtrack",
    "collection",
    "disc 1",
    "disc 2",
    "disc one",
    "disc two",
    "various artists",
    "singles",
    "galore",
    "staring at the sea",
    "hit [",
]

def clean(value):
    return str(value or "").strip()


def normalize_artist(value):
    artist = clean(value)
    key = artist.lower()
    return ARTIST_ALIASES.get(key, artist)


def normalize_album(value):
    album = clean(value)
    album = re.sub(r"\s+", " ", album).strip()
    return album


def is_compilation_album(album):
    album_lower = album.lower()
    return any(term in album_lower for term in COMPILATION_TERMS)


def entropy(values):
    total = sum(values)

    if total <= 0:
        return 0

    score = 0

    for value in values:
        if value <= 0:
            continue

        p = value / total
        score -= p * log2(p)

    return score


def normalized_entropy(values):
    if len(values) <= 1:
        return 0

    return entropy(values) / log2(len(values))


with zipfile.ZipFile(SOURCE) as z:
    rows = json.loads(z.read(z.namelist()[0]))

artist_albums = defaultdict(lambda: defaultdict(int))
excluded = defaultdict(int)

for row in rows:
    artist = normalize_artist(row.get("Album Artist") or row.get("Artist"))
    album = normalize_album(row.get("Album"))

    if not artist or not album:
        continue

    try:
        plays = int(row.get("Track Play Count") or 0)
    except ValueError:
        plays = 0

    if plays <= 0:
        continue

    if is_compilation_album(album):
        excluded[album] += plays
        continue

    artist_albums[artist][album] += plays

candidates = []

for artist, albums in artist_albums.items():
    sorted_albums = sorted(
        albums.items(),
        key=lambda item: item[1],
        reverse=True,
    )

    if len(sorted_albums) < 3:
        continue

    top_albums = sorted_albums[:10]
    values = [count for _, count in top_albums]
    total = sum(values)

    if total < 100:
        continue

    top_album, top_count = top_albums[0]
    top_two = sum(values[:2])
    anchor_threshold = top_count * 0.25

    candidates.append({
        "artist": artist,
        "total": total,
        "top_album": top_album,
        "top_count": top_count,
        "top_share": top_count / total if total else 0,
        "top_two_share": top_two / total if total else 0,
        "width_25": sum(1 for value in values if value >= anchor_threshold),
        "albums_over_100": sum(1 for value in values if value >= 100),
        "evenness": normalized_entropy(values),
        "albums": top_albums,
    })

candidates.sort(
    key=lambda row: (
        row["width_25"],
        row["evenness"],
        row["total"],
    ),
    reverse=True,
)

print("# Top 25 Album Ecosystem Candidates v2")
print()
print("Source: Apple Music Library Tracks JSON")
print("Caveat: uses library Track Play Count grouped by Artist + Album.")
print("Filter: excludes obvious compilations, greatest hits, soundtracks, singles collections, and disc artifacts.")
print("This is candidate discovery, not final play-activity truth.")
print()

for index, row in enumerate(candidates[:25], start=1):
    print(f"{index}. {row['artist']}")
    print(f"   total: {row['total']}")
    print(f"   top album: {row['top_album']} ({row['top_count']})")
    print(f"   top share: {row['top_share']:.1%}")
    print(f"   top two share: {row['top_two_share']:.1%}")
    print(f"   width >= 25% anchor: {row['width_25']}")
    print(f"   albums >= 100 plays: {row['albums_over_100']}")
    print(f"   evenness: {row['evenness']:.2f}")
    print("   albums:")

    for album, count in row["albums"][:8]:
        print(f"     - {album}: {count}")

    print()
