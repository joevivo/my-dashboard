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
    SELECT album_name, COUNT(*) AS event_count
    FROM apple_music_play_activity
    WHERE album_name IS NOT NULL
      AND TRIM(album_name) <> ''
      AND UPPER(TRIM(album_name)) <> 'UNKNOWN'
    GROUP BY album_name
""").fetchall()

raw_sorted = sorted(rows, key=lambda r: r[1], reverse=True)
raw_rank = {album: i for i, (album, _) in enumerate(raw_sorted, start=1)}

canonical_counts = defaultdict(int)
canonical_variants = defaultdict(list)

for album, count in rows:
    canonical = canonical_candidate(album)
    canonical_counts[canonical] += count
    canonical_variants[canonical].append((album, count))

canonical_sorted = sorted(
    canonical_counts.items(),
    key=lambda r: r[1],
    reverse=True
)

canonical_rank = {
    album: i
    for i, (album, _) in enumerate(canonical_sorted, start=1)
}

print("# Albums entering Top 100 after normalization")
print()

for album, count in canonical_sorted:
    rank = canonical_rank[album]

    if rank > 100:
        continue

    variants = canonical_variants[album]

    best_raw_album, best_raw_count = max(
        variants,
        key=lambda x: x[1]
    )

    raw_position = raw_rank.get(best_raw_album)

    if raw_position and raw_position > 100:
        print(
            f"{album} | "
            f"raw #{raw_position} ({best_raw_count}) -> "
            f"canonical #{rank} ({count})"
        )
