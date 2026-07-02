import json
from collections import Counter, defaultdict
from pathlib import Path

HISTORY_DIR = Path("data/music/live/history")
OUT_FILE = Path("data/music/live/apple_library_timeline.md")

def latest_snapshot_dir():
    folders = [p for p in HISTORY_DIR.iterdir() if p.is_dir()]
    return sorted(folders)[-1]

def album_label(item):
    attrs = item.get("attributes", {})
    artist = attrs.get("artistName", "")
    name = attrs.get("name", "")
    return f"{artist} — {name}".strip(" —")

folder = latest_snapshot_dir()
path = folder / "apple_library_albums.json"

payload = json.loads(path.read_text(encoding="utf-8"))
items = payload.get("response", {}).get("data", [])

albums = []
for item in items:
    attrs = item.get("attributes", {})
    date_added = attrs.get("dateAdded")
    if date_added:
        albums.append({
            "date": date_added[:10],
            "year": date_added[:4],
            "artist": attrs.get("artistName", ""),
            "name": attrs.get("name", ""),
            "label": album_label(item),
        })

albums.sort(key=lambda x: (x["date"], x["artist"], x["name"]))

year_counts = Counter(a["year"] for a in albums)
date_counts = Counter(a["date"] for a in albums)
migration_dates = {date: count for date, count in date_counts.items() if count >= 25}
artist_counts = Counter(a["artist"] for a in albums if a["artist"])

organic_albums = [a for a in albums if a["date"] not in migration_dates]
organic_year_counts = Counter(a["year"] for a in organic_albums)

lines = [
    "# Apple Library Timeline",
    "",
    f"Snapshot: `{folder.name}`",
    f"Albums with dateAdded: `{len(albums)}`",
    "",
    "## Earliest Albums",
    "",
]

for a in albums[:50]:
    lines.append(f"- {a['date']} | {a['label']}")

lines += ["", "## Likely Migration / Bulk Import Dates", ""]

for date, count in sorted(migration_dates.items(), key=lambda x: (-x[1], x[0])):
    lines.append(f"- {date}: {count} albums")

lines += ["", "## Albums Added by Year", ""]

for year in sorted(year_counts):
    lines.append(f"- {year}: {year_counts[year]}")

lines += ["", "## Organic Additions By Year (Migration Dates Removed)", ""]

for year in sorted(organic_year_counts):
    lines.append(f"- {year}: {organic_year_counts[year]}")

lines += ["", "## Top Artists by Library Album Count", ""]

for artist, count in artist_counts.most_common(25):
    lines.append(f"- {artist}: {count}")

OUT_FILE.write_text("\n".join(lines), encoding="utf-8")

print(f"Saved {OUT_FILE}")
print(OUT_FILE.read_text(encoding="utf-8"))
