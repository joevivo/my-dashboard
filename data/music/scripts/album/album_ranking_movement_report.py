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
raw_count = {album: count for album, count in rows}

canonical_counts = defaultdict(int)
canonical_variants = defaultdict(list)

for album, count in rows:
    canonical = canonical_candidate(album)
    canonical_counts[canonical] += count
    canonical_variants[canonical].append((album, count))

canonical_sorted = sorted(canonical_counts.items(), key=lambda r: r[1], reverse=True)
canonical_rank = {album: i for i, (album, _) in enumerate(canonical_sorted, start=1)}

report = []

for canonical, canonical_count in canonical_sorted:
    variants = canonical_variants[canonical]
    best_raw_album, best_raw_count = max(variants, key=lambda x: x[1])
    best_raw_rank = raw_rank.get(best_raw_album)

    gain = canonical_count - best_raw_count

    if gain <= 0:
        continue

    report.append({
        "canonical": canonical,
        "canonical_rank": canonical_rank[canonical],
        "canonical_count": canonical_count,
        "best_raw_album": best_raw_album,
        "best_raw_rank": best_raw_rank,
        "best_raw_count": best_raw_count,
        "gain": gain,
        "variant_count": len(variants),
    })

report.sort(key=lambda row: row["gain"], reverse=True)

print("# Album Ranking Movement Report")
print()
print("Albums gaining the most visibility after canonical normalization")
print()

for row in report[:75]:
    print(
        f"{row['canonical']} | "
        f"raw #{row['best_raw_rank']} ({row['best_raw_count']}) | "
        f"canonical #{row['canonical_rank']} ({row['canonical_count']}) | "
        f"+{row['gain']} events | "
        f"{row['variant_count']} variants"
    )
