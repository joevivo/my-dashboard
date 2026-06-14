from __future__ import annotations

import json
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from zipfile import ZipFile


def norm(value: object) -> str:
    return str(value or "").strip().lower()


def parse_date(value: object):
    if not value:
        return None
    try:
        return datetime.strptime(str(value)[:10], "%Y-%m-%d").date()
    except Exception:
        return None


def main() -> int:
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Artist name required"}))
        return 1

    query = sys.argv[1].strip()
    query_norm = norm(query)

    path = (
        Path.home()
        / "Downloads"
        / "apple-music-working"
        / "Apple_Media_Services_python"
        / "Apple_Media_Services"
        / "Apple Music Activity"
        / "Apple Music Library Tracks.json.zip"
    )

    if not path.exists():
        print(json.dumps({"error": f"Library Tracks export not found: {path}"}))
        return 1

    with ZipFile(path, "r") as z:
        with z.open("Apple Music Library Tracks.json") as f:
            data = json.load(f)

    matches = []

    for row in data:
        artist = row.get("Artist")
        if query_norm not in norm(artist):
            continue

        played_date = parse_date(row.get("Last Played Date"))
        if not played_date:
            continue

        title = row.get("Title") or row.get("Name") or row.get("Song Name")
        album = row.get("Album")

        matches.append({
            "artist": artist,
            "title": title,
            "album": album,
            "played_date": played_date,
            "year": str(played_date.year),
        })

    artist_counts = Counter(item["artist"] for item in matches if item["artist"])
    canonical_artist = artist_counts.most_common(1)[0][0] if artist_counts else query

    years = sorted({item["year"] for item in matches})
    dates = sorted(item["played_date"] for item in matches)

    top_songs = Counter(item["title"] for item in matches if item["title"])
    top_albums = Counter(item["album"] for item in matches if item["album"])
    year_counts = Counter(item["year"] for item in matches)

    result = {
        "artist": canonical_artist,
        "query": query,
        "totalPlays": len(matches),
        "yearsActive": len(years),
        "firstSeen": str(dates[0].year) if dates else "",
        "latestSeen": str(dates[-1].year) if dates else "",
        "firstPlayedDate": str(dates[0]) if dates else "",
        "latestPlayedDate": str(dates[-1]) if dates else "",
        "classification": "Library-track reconstruction",
        "notes": "Based on Apple Music Library Tracks Last Played Date. This is useful for artist lookup, but not complete event-level play history.",
        "topSongs": [
            {"song": song, "plays": count}
            for song, count in top_songs.most_common(10)
        ],
        "topAlbums": [
            {"album": album, "plays": count}
            for album, count in top_albums.most_common(10)
        ],
        "timeline": [
            {"year": year, "count": year_counts[year]}
            for year in sorted(year_counts)
        ],
        "source": "apple_music_library_tracks",
    }

    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
