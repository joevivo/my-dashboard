import re
import sys
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


def main():
    target = " ".join(sys.argv[1:]).strip()

    if not target:
        print('Usage: python album_raw_vs_canonical_compare.py "Album Name"')
        sys.exit(1)

    con = duckdb.connect(DB_PATH)

    rows = con.execute("""
        SELECT
            album_name,
            COUNT(*) as events,
            MIN(event_timestamp) as first_seen,
            MAX(event_timestamp) as last_seen
        FROM apple_music_play_activity
        WHERE album_name IS NOT NULL
          AND TRIM(album_name) <> ''
          AND UPPER(TRIM(album_name)) <> 'UNKNOWN'
        GROUP BY album_name
    """).fetchall()

    matches = []

    for album_name, events, first_seen, last_seen in rows:
        if canonical_candidate(album_name).lower() == target.lower():
            matches.append((album_name, events, first_seen, last_seen))

    matches.sort(key=lambda row: row[1], reverse=True)

    print(f"# Raw vs Canonical Album Comparison: {target}")
    print()

    total = 0

    for album_name, events, first_seen, last_seen in matches:
        total += events
        print(f"{events:5}  {album_name}")
        print(f"       first: {first_seen}")
        print(f"       last:  {last_seen}")

    print()
    print(f"Canonical total: {total}")


if __name__ == "__main__":
    main()
