import json
from collections import Counter, defaultdict
from pathlib import Path

WAREHOUSE_FILE = Path("data/music/live/warehouse/apple_recent_objects.json")

data = json.loads(WAREHOUSE_FILE.read_text(encoding="utf-8"))
rows = data.get("rows", [])

type_counts = Counter(row.get("objectType") for row in rows)

albums = [row for row in rows if row.get("objectType") == "albums"]
playlists = [row for row in rows if "playlist" in str(row.get("objectType"))]
stations = [row for row in rows if row.get("objectType") == "stations"]

artist_album_counts = Counter(row.get("artistName") for row in albums if row.get("artistName"))

print("# Recent Activity Investigation")
print()
print(f"Snapshot: {data.get('snapshotId')}")
print(f"Captured At: {data.get('generatedAt')}")
print(f"Rows: {len(rows)}")
print()
print("## Object Mix")
for object_type, count in type_counts.most_common():
    print(f"- {object_type}: {count}")

print()
print("## Top Recent Album Artists")
for artist, count in artist_album_counts.most_common(10):
    print(f"- {artist}: {count} album object(s)")

print()
print("## Recent Albums")
for row in albums[:15]:
    artist = row.get("artistName") or "[unknown artist]"
    name = row.get("name") or "[unknown album]"
    print(f"- {artist} — {name}")

print()
print("## Recent Playlists")
for row in playlists[:15]:
    print(f"- {row.get('name')}")

print()
print("## Recent Stations")
for row in stations[:15]:
    print(f"- {row.get('name')}")

print()
print("## Derived Facts")
if len(albums) > len(playlists) and len(albums) > len(stations):
    print(f"- Album-oriented listening currently dominates recent activity ({len(albums)} albums vs {len(playlists)} playlists and {len(stations)} stations).")

if artist_album_counts:
    top_artist, top_count = artist_album_counts.most_common(1)[0]
    print(f"- {top_artist} is the most visible recent album artist with {top_count} album object(s).")

if playlists:
    print(f"- Curated playlists remain active listening contexts ({len(playlists)} playlist object(s) in recent activity).")
