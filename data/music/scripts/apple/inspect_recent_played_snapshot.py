import json
from collections import Counter
from pathlib import Path

SNAPSHOT = Path("data/music/live/history/2026-06-24_231929Z/apple_recent_played.json")

data = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
items = data["response"]["data"]

print()
print("Recent Played Snapshot")
print("----------------------")
print(f"Captured: {data['capturedAt']}")
print(f"Items: {len(items)}")
print()

counts = Counter(item["type"] for item in items)

print("Object Types")
for t, c in counts.most_common():
    print(f"  {t:12} {c}")

print()
print("First 20 Objects")
print("----------------")

for item in items[:20]:
    attrs = item.get("attributes", {})
    name = attrs.get("name", "")
    artist = attrs.get("artistName", "")
    kind = item["type"]

    if artist:
        print(f"{kind:12} | {artist} | {name}")
    else:
        print(f"{kind:12} | {name}")
