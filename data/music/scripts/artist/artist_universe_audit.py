import json
from pathlib import Path

UNIVERSE = Path("data/music/live/artist_universe.json")

data = json.loads(UNIVERSE.read_text(encoding="utf-8"))

artists = data["artists"]

family = 0
reviewed = 0
unclassified = 0
errors = 0
zero_play_library = 0
plays_no_family = 0

for row in artists:
    metrics = row.get("metrics", {})

    plays = metrics.get("actualPlays") or 0
    evidence = metrics.get("libraryEvidenceRecords") or 0

    if row.get("family"):
        family += 1

    if row.get("reviewStatus"):
        reviewed += 1

    if not row.get("family") and not row.get("reviewStatus"):
        unclassified += 1

    if row.get("error"):
        errors += 1

    if plays == 0 and evidence > 0:
        zero_play_library += 1

    if plays > 0 and not row.get("family"):
        plays_no_family += 1

print("# Artist Universe Audit")
print()
print(f"Artists                : {len(artists)}")
print(f"Family members         : {family}")
print(f"Reviewed standalone    : {reviewed}")
print(f"Unclassified           : {unclassified}")
print(f"Query errors           : {errors}")
print(f"Library only           : {zero_play_library}")
print(f"Plays but no family    : {plays_no_family}")

print()
print("# Top Unclassified")

rows = [
    r for r in artists
    if not r.get("family")
    and not r.get("reviewStatus")
]

rows.sort(
    key=lambda r: (
        r["metrics"].get("actualPlays", 0),
        r["metrics"].get("libraryEvidenceRecords", 0),
        r["metrics"].get("yearsActive", 0),
    ),
    reverse=True,
)

for row in rows[:25]:
    m = row["metrics"]
    print(
        f"{row['artist']:<35} "
        f"plays={m.get('actualPlays',0):>5} "
        f"evidence={m.get('libraryEvidenceRecords',0):>4} "
        f"years={m.get('yearsActive',0):>2}"
    )
