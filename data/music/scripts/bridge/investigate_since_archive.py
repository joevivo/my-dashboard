import json
from pathlib import Path

from artist_bridge import bridge_artist

warehouse = Path("data/music/live/warehouse")

recent = json.loads(
    (warehouse / "apple_recent_objects.json").read_text(encoding="utf-8")
)

artists = sorted({
    row["artistName"]
    for row in recent["rows"]
    if row.get("artistName")
})

print("# Since Archive Investigation")
print()
print(f"Artists found in live warehouse: {len(artists)}")
print()

results = []

for artist in artists:
    result = bridge_artist(artist)
    results.append(result)

results.sort(
    key=lambda r: (
        r["historical"].get("actualPlays") or 0,
        r["live"].get("recentObjectCount") or 0,
    ),
    reverse=True,
)

for result in results:

    h = result["historical"]
    l = result["live"]

    print("=" * 70)
    print(result["artist"])
    print("=" * 70)

    print(
        f"Relationship : {result['relationshipState']}"
    )

    print(
        f"Historical   : "
        f"{h.get('actualPlays',0)} plays | "
        f"{h.get('yearsActive',0)} years"
    )

    print(
        f"Live         : "
        f"{l.get('recentObjectCount',0)} recent | "
        f"{l.get('heavyRotationCount',0)} heavy"
    )

    facts = result.get("facts", [])

    if facts:
        print("Facts:")
        for fact in facts:
            value = fact.get("value")
            suffix = f" ({value})" if value is not None else ""
            print(f"  • {fact.get('statement')}{suffix}")

    if l["recentObjects"]:
        print("Albums:")

        for item in l["recentObjects"]:
            print(f"  • {item['name']}")

    print()

print("Finished.")
