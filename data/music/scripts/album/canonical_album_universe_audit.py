import re
import duckdb

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
    SELECT DISTINCT album_name
    FROM apple_music_play_activity
    WHERE album_name IS NOT NULL
      AND TRIM(album_name) <> ''
      AND UPPER(TRIM(album_name)) <> 'UNKNOWN'
""").fetchall()

raw_titles = set()
canonical_titles = set()

for (album_name,) in rows:
    raw_titles.add(album_name)
    canonical_titles.add(canonical_candidate(album_name))

print()
print("# Canonical Album Universe Audit")
print()
print(f"Raw Album Titles:        {len(raw_titles):,}")
print(f"Canonical Candidates:   {len(canonical_titles):,}")
print(f"Reduction:              {len(raw_titles) - len(canonical_titles):,}")

if len(raw_titles):
    pct = (
        (len(raw_titles) - len(canonical_titles))
        / len(raw_titles)
    ) * 100

    print(f"Reduction Percent:      {pct:.2f}%")
