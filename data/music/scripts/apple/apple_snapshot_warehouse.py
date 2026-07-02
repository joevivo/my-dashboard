import csv
import json
from collections import Counter
from pathlib import Path

HISTORY_DIR = Path("data/music/live/history")
OUT_DIR = Path("data/music/live")
OUT_CSV = OUT_DIR / "apple_snapshot_warehouse.csv"
OUT_MD = OUT_DIR / "apple_snapshot_warehouse_summary.md"

SOURCE_FILES = {
    "library_albums": "apple_library_albums.json",
    "library_playlists": "apple_library_playlists.json",
    "library_songs": "apple_library_songs.json",
    "recent_played": "apple_recent_played.json",
    "heavy_rotation": "apple_heavy_rotation.json",
}

def normalize_type(item_type):
    return {
        "library-albums": "album",
        "albums": "album",
        "library-playlists": "playlist",
        "playlists": "playlist",
        "stations": "station",
        "library-songs": "song",
        "songs": "song",
    }.get(item_type, item_type or "unknown")

def item_name(item):
    return (item.get("attributes") or {}).get("name", "")

def artist_name(item):
    return (item.get("attributes") or {}).get("artistName", "")

def catalog_id(item):
    attrs = item.get("attributes") or {}
    play = attrs.get("playParams") or {}
    return play.get("catalogId") or play.get("globalId") or ""

rows = []

for folder in sorted(HISTORY_DIR.iterdir()):
    if not folder.is_dir():
        continue

    manifest_path = folder / "apple_snapshot_manifest.json"
    captured_at = folder.name

    if manifest_path.exists():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            captured_at = manifest.get("capturedAt") or captured_at
        except Exception:
            pass

    for source, filename in SOURCE_FILES.items():
        path = folder / filename
        if not path.exists():
            continue

        payload = json.loads(path.read_text(encoding="utf-8"))
        items = ((payload.get("response") or {}).get("data") or [])

        for position, item in enumerate(items, start=1):
            raw_type = item.get("type", "")
            rows.append({
                "snapshot_folder": folder.name,
                "snapshot_time": captured_at,
                "source": source,
                "position": position,
                "raw_type": raw_type,
                "entity_type": normalize_type(raw_type),
                "entity_id": item.get("id", ""),
                "catalog_or_global_id": catalog_id(item),
                "name": item_name(item),
                "artist": artist_name(item),
                "href": item.get("href", ""),
            })

OUT_DIR.mkdir(parents=True, exist_ok=True)

with OUT_CSV.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=[
        "snapshot_folder",
        "snapshot_time",
        "source",
        "position",
        "raw_type",
        "entity_type",
        "entity_id",
        "catalog_or_global_id",
        "name",
        "artist",
        "href",
    ])
    writer.writeheader()
    writer.writerows(rows)

source_counts = Counter(row["source"] for row in rows)
type_counts = Counter((row["source"], row["entity_type"]) for row in rows)

lines = [
    "# Apple Snapshot Warehouse Summary",
    "",
    f"Rows: `{len(rows)}`",
    "",
    "## Rows by Source",
    "",
]

for source, count in source_counts.most_common():
    lines.append(f"- {source}: {count}")

lines += ["", "## Entity Types by Source", ""]

for (source, entity_type), count in sorted(type_counts.items()):
    lines.append(f"- {source} / {entity_type}: {count}")

lines += ["", "## Heavy Rotation Items", ""]

for row in rows:
    if row["source"] == "heavy_rotation":
        label = row["name"]
        if row["artist"]:
            label = f'{row["artist"]} — {label}'
        lines.append(f'- {row["entity_type"]}: {label}')

lines += ["", "## Recently Played Items", ""]

for row in rows:
    if row["source"] == "recent_played":
        label = row["name"]
        if row["artist"]:
            label = f'{row["artist"]} — {label}'
        lines.append(f'- {row["entity_type"]}: {label}')

OUT_MD.write_text("\n".join(lines), encoding="utf-8")

print(f"Saved {OUT_CSV}")
print(f"Saved {OUT_MD}")
print(f"Rows: {len(rows)}")
