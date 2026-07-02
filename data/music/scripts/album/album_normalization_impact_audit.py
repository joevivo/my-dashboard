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

groups = defaultdict(list)

for album_name, event_count in rows:
    canonical = canonical_candidate(album_name)
    groups[canonical].append((album_name, event_count))

affected_events = 0
affected_groups = []

for canonical, variants in groups.items():
    if len(variants) < 2:
        continue

    total_events = sum(count for _, count in variants)

    affected_events += total_events

    affected_groups.append(
        (canonical, len(variants), total_events)
    )

affected_groups.sort(key=lambda x: x[2], reverse=True)

print()
print("# Album Normalization Impact Audit")
print()
print(f"Canonical groups with variants: {len(affected_groups):,}")
print(f"Events affected: {affected_events:,}")
print()

print("Top 50 impacted albums")
print()

for canonical, variant_count, total_events in affected_groups[:50]:
    print(
        f"{canonical} | "
        f"{variant_count} variants | "
        f"{total_events} events"
    )
