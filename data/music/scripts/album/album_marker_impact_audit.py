import re
import duckdb
from collections import defaultdict

DB_PATH = "data/music/music.db"

MARKERS = {
    "edition": [
        "deluxe",
        "remaster",
        "remastered",
        "expanded",
        "bonus",
        "anniversary",
        "mix",
        "stereo",
        "mono",
    ],
    "album_type": [
        "live",
        "soundtrack",
        "motion picture",
        "television soundtrack",
        "score",
        "box set",
        "single",
        "demo",
        "instrumental",
    ],
    "review": [
        "acoustic",
        "remix",
        "re-recorded",
        "radio edit",
        "video version",
        "feat.",
        "uk",
        "white album",
    ],
}

def classify(album_name):
    text = str(album_name or "").lower()

    markers = re.findall(r"\((.*?)\)", text)

    for marker in markers:
        for category, terms in MARKERS.items():
            if any(term in marker for term in terms):
                return category

    return "none"

con = duckdb.connect(DB_PATH)

rows = con.execute("""
    SELECT album_name, COUNT(*) as events
    FROM apple_music_play_activity
    WHERE album_name IS NOT NULL
      AND TRIM(album_name) <> ''
      AND UPPER(TRIM(album_name)) <> 'UNKNOWN'
    GROUP BY album_name
""").fetchall()

totals = defaultdict(int)
albums = defaultdict(int)

for album_name, events in rows:
    category = classify(album_name)
    totals[category] += events
    albums[category] += 1

print("# Album Marker Impact Audit")
print()

for category in sorted(totals.keys()):
    print(
        f"{category:12} "
        f"albums={albums[category]:5} "
        f"events={totals[category]:7}"
    )
