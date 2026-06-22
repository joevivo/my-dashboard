import csv
import json
from pathlib import Path
from collections import Counter

HISTORY_DIR = Path("data/music/live/history")
OUT_FILE = Path("data/music/live/apple_library_relationships.md")
OUT_JSON = Path("data/music/live/apple_library_artist_inventory.json")
PLAY_SUMMARY = Path.home() / "apple-music-sanitized" / "apple-music-daily-track-summary.csv"

def latest_snapshot_dir():
    return sorted([p for p in HISTORY_DIR.iterdir() if p.is_dir()])[-1]

def norm(s):
    return (s or "").strip().lower()

folder = latest_snapshot_dir()
albums_path = folder / "apple_library_albums.json"

payload = json.loads(albums_path.read_text(encoding="utf-8"))
albums = payload.get("response", {}).get("data", [])

library_counts = Counter()
examples = {}

for item in albums:
    attrs = item.get("attributes", {})
    artist = attrs.get("artistName", "")
    album = attrs.get("name", "")
    if artist:
        library_counts[artist] += 1
        examples.setdefault(artist, []).append(album)

play_counts = Counter()

if PLAY_SUMMARY.exists():
    with PLAY_SUMMARY.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        cols = {c.lower(): c for c in reader.fieldnames or []}

        artist_col = cols.get("artist") or cols.get("artist name") or cols.get("artist_name")
        plays_col = cols.get("plays") or cols.get("play count") or cols.get("play_count")

        if artist_col and plays_col:
            for row in reader:
                artist = (row.get(track_col, "").split(" - ", 1)[0]).strip()
                try:
                    plays = int(float(row.get(plays_col, 0) or 0))
                except ValueError:
                    plays = 0
                if artist:
                    play_counts[artist] += plays

lines = [
    "# Apple Library Relationships",
    "",
    f"Snapshot: `{folder.name}`",
    f"Library artists: `{len(library_counts)}`",
    "",
    "## Top Artists by Apple Library Album Footprint",
    "",
]

for artist, count in library_counts.most_common(30):
    plays = play_counts.get(artist, 0)
    sample = "; ".join(examples.get(artist, [])[:5])
    lines.append(f"- {artist}: {count} albums | archive plays: {plays} | examples: {sample}")

lines += [
    "",
    "## Potential Collection-Heavy Artists",
    "",
    "Artists with large Apple library footprint but comparatively low matched archive play count.",
    "",
]

for artist, count in library_counts.most_common(50):
    plays = play_counts.get(artist, 0)
    if count >= 5 and plays < 100:
        lines.append(f"- {artist}: {count} albums | archive plays: {plays}")

inventory = {
    "snapshot": folder.name,
    "artistCount": len(library_counts),
    "artists": [
        {
            "artist": artist,
            "libraryAlbumCount": count,
            "archivePlays": play_counts.get(artist, 0),
            "albumExamples": examples.get(artist, [])[:10],
        }
        for artist, count in library_counts.most_common()
    ],
}

OUT_JSON.write_text(json.dumps(inventory, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
OUT_FILE.write_text("\n".join(lines), encoding="utf-8")
print(f"Saved {OUT_JSON}")
print(f"Saved {OUT_FILE}")
print(OUT_FILE.read_text(encoding="utf-8"))


