import re
import duckdb
from collections import defaultdict


DB_PATH = "data/music/music.db"

EDITION_PATTERNS = [
    r"\([^)]*remaster[^)]*\)",
    r"\([^)]*remastered[^)]*\)",
    r"\([^)]*deluxe[^)]*\)",
    r"\([^)]*super deluxe[^)]*\)",
    r"\([^)]*anniversary[^)]*\)",
    r"\([^)]*bonus track[^)]*\)",
    r"\([^)]*expanded[^)]*\)",
    r"\([^)]*mix[^)]*\)",
    r"\([^)]*stereo[^)]*\)",
    r"\([^)]*mono[^)]*\)",
]


def strip_edition_markers(album_name):
    value = str(album_name or "").strip()
    candidate = value

    for pattern in EDITION_PATTERNS:
        candidate = re.sub(pattern, "", candidate, flags=re.IGNORECASE)

    candidate = re.sub(r"\s+", " ", candidate).strip()
    return candidate or value


def main():
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
        ORDER BY event_count DESC
    """).fetchall()

    raw_count = len(rows)

    groups = defaultdict(list)
    marker_count = 0

    for album_name, event_count in rows:
        canonical = strip_edition_markers(album_name)
        groups[canonical].append((album_name, event_count))

        if canonical != album_name:
            marker_count += 1

    variant_groups = {
        canonical: variants
        for canonical, variants in groups.items()
        if len(variants) > 1
    }

    print("# Album Normalization Audit v0")
    print()
    print(f"Distinct raw album titles: {raw_count}")
    print(f"Raw titles with edition markers: {marker_count}")
    print(f"Potential canonical groups with variants: {len(variant_groups)}")
    print()

    print("## Largest Variant Groups")
    print()

    sorted_groups = sorted(
        variant_groups.items(),
        key=lambda item: (len(item[1]), sum(v[1] for v in item[1])),
        reverse=True,
    )

    for canonical, variants in sorted_groups[:50]:
        total_events = sum(event_count for _, event_count in variants)
        print(f"{canonical} - {len(variants)} variants, {total_events} events")

        for album_name, event_count in sorted(variants, key=lambda item: item[1], reverse=True):
            print(f"  - {album_name} ({event_count})")

        print()


if __name__ == "__main__":
    main()
