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

    value = re.sub(r"\s+", " ", value).strip()
    return value


con = duckdb.connect(DB_PATH)

rows = con.execute("""
    SELECT
        album_name,
        COUNT(*) AS event_count
    FROM apple_music_play_activity
    WHERE album_name IS NOT NULL
      AND TRIM(album_name) <> ''
      AND UPPER(TRIM(album_name)) <> 'UNKNOWN'
    GROUP BY album_name
""").fetchall()

print("# TOP 50 RAW ALBUMS")
print()

raw_sorted = sorted(rows, key=lambda r: r[1], reverse=True)

for rank, (album, count) in enumerate(raw_sorted[:50], start=1):
    print(f"{rank:2}. {count:5}  {album}")

print()
print()
print("# TOP 50 CANONICAL ALBUMS")
print()

canonical_counts = defaultdict(int)

for album, count in rows:
    canonical_counts[canonical_candidate(album)] += count

canonical_sorted = sorted(
    canonical_counts.items(),
    key=lambda r: r[1],
    reverse=True,
)

for rank, (album, count) in enumerate(canonical_sorted[:50], start=1):
    print(f"{rank:2}. {count:5}  {album}")
