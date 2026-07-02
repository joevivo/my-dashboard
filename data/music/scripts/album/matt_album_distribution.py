import csv
from collections import Counter
from pathlib import Path

SOURCE = Path("C:/Users/joevi/apple-music-sanitized/apple-music-daily-track-summary.csv")

albums = Counter()

with SOURCE.open("r", encoding="utf-8-sig", newline="") as f:
    reader = csv.DictReader(f)

    for row in reader:
        track = str(row.get("Track Description") or "")

        if not track.startswith("matt pond PA - "):
            continue

        album = str(row.get("Album") or "").strip()

        if album:
            albums[album] += 1

print("# matt pond PA Album Distribution")
print()

for album, count in albums.most_common():
    print(f"{count:4}  {album}")
