import csv
from collections import Counter
from pathlib import Path

SOURCE = Path("C:/Users/joevi/apple-music-sanitized/apple-music-daily-track-summary.csv")

songs = Counter()

with SOURCE.open("r", encoding="utf-8-sig", newline="") as f:
    reader = csv.DictReader(f)

    for row in reader:
        desc = str(row.get("Track Description") or "")

        if not desc.startswith("Toad the Wet Sprocket - "):
            continue

        song = desc.replace("Toad the Wet Sprocket - ", "", 1)
        songs[song] += int(row.get("Play Count") or 0)

print("# Toad the Wet Sprocket Song Counts")
print()

for song, plays in songs.most_common(25):
    print(f"{plays:5}  {song}")
