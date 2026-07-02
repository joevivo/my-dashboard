import re
import duckdb
from collections import Counter

con = duckdb.connect("data/music/music.db")

rows = con.execute("""
    SELECT DISTINCT album_name
    FROM apple_music_play_activity
    WHERE album_name IS NOT NULL
      AND TRIM(album_name) <> ''
      AND UPPER(TRIM(album_name)) <> 'UNKNOWN'
""").fetchall()

counter = Counter()

for (album_name,) in rows:
    matches = re.findall(r"\(([^)]*)\)", album_name)

    for match in matches:
        marker = match.strip()
        if marker:
            counter[marker] += 1

print("# Album Edition Marker Audit")
print()

for marker, count in counter.most_common(100):
    print(f"{count:4}  {marker}")
