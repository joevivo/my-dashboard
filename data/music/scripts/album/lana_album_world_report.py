import csv
from collections import Counter
from pathlib import Path

ARTIST = "Lana Del Rey"
SOURCE = Path("C:/Users/joevi/apple-music-sanitized/apple-music-daily-track-summary.csv")

albums = Counter()

with SOURCE.open("r", encoding="utf-8-sig", newline="") as f:
    reader = csv.DictReader(f)

    for row in reader:
        desc = str(row.get("Track Description") or "")
        album = str(row.get("Album") or "").strip()

        if not desc.startswith(ARTIST + " - "):
            continue

        if album:
            albums[album] += 1

print(f"# Album World: {ARTIST}")
print()

for album, count in albums.most_common(25):
    print(f"{count:5}  {album}")
