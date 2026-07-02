from pathlib import Path
from zipfile import ZipFile
from collections import Counter, defaultdict
from datetime import datetime
import json

path = (
    Path.home()
    / "Downloads"
    / "apple-music-working"
    / "Apple_Media_Services_python"
    / "Apple_Media_Services"
    / "Apple Music Activity"
    / "Apple Music Library Tracks.json.zip"
)

with ZipFile(path, "r") as z:
    with z.open("Apple Music Library Tracks.json") as f:
        data = json.load(f)

artist_year_counts = defaultdict(Counter)
artist_total_counts = Counter()
artist_first_seen = {}
artist_latest_seen = {}

for row in data:
    played = row.get("Last Played Date")
    artist = row.get("Artist")

    if not played or not artist:
        continue

    try:
        played_date = datetime.strptime(str(played)[:10], "%Y-%m-%d").date()
    except Exception:
        continue

    year = str(played_date.year)

    artist_year_counts[artist][year] += 1
    artist_total_counts[artist] += 1

    if artist not in artist_first_seen or played_date < artist_first_seen[artist]:
        artist_first_seen[artist] = played_date

    if artist not in artist_latest_seen or played_date > artist_latest_seen[artist]:
        artist_latest_seen[artist] = played_date

rows = []

for artist, year_counts in artist_year_counts.items():
    active_years = len(year_counts)
    total_tracks = artist_total_counts[artist]

    if active_years < 5:
        continue

    peak_year, peak_count = year_counts.most_common(1)[0]

    rows.append({
        "artist": artist,
        "activeYears": active_years,
        "totalTracks": total_tracks,
        "firstSeen": str(artist_first_seen[artist]),
        "latestSeen": str(artist_latest_seen[artist]),
        "peakYear": peak_year,
        "peakYearTracks": peak_count,
        "timeline": [
            {"year": year, "count": count}
            for year, count in sorted(year_counts.items())
        ],
    })

rows.sort(
    key=lambda row: (
        -row["activeYears"],
        -row["totalTracks"],
        row["artist"].lower(),
    )
)

result = {
    "question": "Who never leaves?",
    "sourceNote": "Reconstruction from Apple Music Library Tracks Last Played Date.",
    "count": len(rows),
    "rows": rows,
}

print(json.dumps(result, indent=2))
