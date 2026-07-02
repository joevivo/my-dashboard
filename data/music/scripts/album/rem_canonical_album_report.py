import re
import duckdb
from collections import defaultdict

DB_PATH = "data/music/music.db"

EDITION_PATTERNS = [
    r"\([^)]*remaster[^)]*\)",
    r"\([^)]*remastered[^)]*\)",
    r"\([^)]*deluxe[^)]*\)",
    r"\([^)]*super deluxe[^)]*\)",
    r"\([^)]*expanded[^)]*\)",
    r"\([^)]*bonus[^)]*\)",
    r"\([^)]*anniversary[^)]*\)",
    r"\([^)]*mix[^)]*\)",
    r"\([^)]*stereo[^)]*\)",
    r"\([^)]*mono[^)]*\)",
]

def canonical_candidate(album_name):
    value = str(album_name or "").strip()

    for pattern in EDITION_PATTERNS:
        value = re.sub(pattern, "", value, flags=re.IGNORECASE)

    return re.sub(r"\s+", " ", value).strip()

con = duckdb.connect(DB_PATH)

rows = con.execute("""
    SELECT
        album_name,
        COUNT(*) AS events
    FROM apple_music_play_activity
    WHERE source_type = 'LIBRARY'
      AND album_name IS NOT NULL
      AND artist_name = 'R.E.M.'
    GROUP BY album_name
""").fetchall()

canonical = defaultdict(int)

for album, events in rows:
    canonical[canonical_candidate(album)] += events

sorted_albums = sorted(
    canonical.items(),
    key=lambda x: x[1],
    reverse=True
)

print("# R.E.M. Canonical Albums")
print()

for rank, (album, events) in enumerate(sorted_albums[:25], start=1):
    print(f"{rank:2}. {events:4}  {album}")
