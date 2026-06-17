from __future__ import annotations

import csv
import json
import re
import sys
import unicodedata
from collections import Counter
from datetime import datetime
from pathlib import Path
from zipfile import ZipFile


ARTIST_ALIASES = {
    "husker du": "husker du",
    "h?sker d?": "husker du",
    "love & rockets": "love and rockets",
    "love and rockets": "love and rockets",
    "the scorpions": "scorpions",
    "scorpions": "scorpions",
    "the eagles": "eagles",
    "eagles": "eagles",
}

PLAY_ACTIVITY_SOURCE = Path("C:/Users/joevi/apple-music-sanitized/apple-music-daily-track-summary.csv")


def norm(value: object) -> str:
    text = str(value or "").strip().lower()
    text = unicodedata.normalize("NFD", text)
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    text = text.replace("&", " and ")
    text = re.sub(r"[^a-z0-9]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def strip_leading_article(value: str) -> str:
    return re.sub(r"^the\s+", "", value).strip()


def canonical_key(value: object) -> str:
    normalized = norm(value)
    aliased = ARTIST_ALIASES.get(normalized, normalized)
    stripped = strip_leading_article(aliased)
    return ARTIST_ALIASES.get(stripped, stripped)


def match_rank(query: str, artist: str) -> int | None:
    q = canonical_key(query)
    a = canonical_key(artist)

    if not q or not a:
        return None

    if q == a:
        return 1

    # Short queries are too ambiguous for prefix/word/contains matching.
    # Example: "no" should not resolve to "Noah Cyrus".
    if len(q) < 3:
        return None

    if a.startswith(q):
        return 2

    artist_words = set(a.split())
    query_words = set(q.split())

    if query_words and query_words.issubset(artist_words):
        return 3

    # Avoid bad short substring matches like "no" -> Brian Eno.
    if len(q) >= 4 and q in a:
        return 4

    return None


def parse_track_artist(track_description: object) -> str | None:
    value = str(track_description or "").strip()

    if " - " not in value:
        return None

    artist = value.split(" - ", 1)[0].strip()
    if not artist:
        return None

    if artist.upper() in {"UNKNOWN", "N/A", "NONE", "NULL"}:
        return None

    return artist


def parse_int(value: object) -> int:
    try:
        return int(float(str(value or "0").strip() or "0"))
    except Exception:
        return 0


def load_play_activity_summary(query: str) -> dict:
    if not PLAY_ACTIVITY_SOURCE.exists():
        return {
            "actualPlays": None,
            "actualSkips": None,
            "listeningDurationMs": None,
            "playActivitySource": "missing",
        }

    actual_plays = 0
    actual_skips = 0
    listening_duration_ms = 0

    with PLAY_ACTIVITY_SOURCE.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)

        for row in reader:
            artist = parse_track_artist(row.get("Track Description"))
            if match_rank(query, artist) is None:
                continue

            actual_plays += parse_int(row.get("Play Count"))
            actual_skips += parse_int(row.get("Skip Count"))
            listening_duration_ms += parse_int(row.get("Play Duration Milliseconds"))

    return {
        "actualPlays": actual_plays,
        "actualSkips": actual_skips,
        "hoursListened": round(listening_duration_ms / 1000 / 60 / 60, 1),
        "listeningDurationMs": listening_duration_ms,
        "playActivitySource": "apple_music_daily_track_summary",
    }


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

    ranked_matches = []

    for row in data:
        artist = row.get("Artist")
        rank = match_rank(query, artist)

        if rank is None:
            continue

        played_date = parse_date(row.get("Last Played Date"))
        if not played_date:
            continue

        title = row.get("Title") or row.get("Name") or row.get("Song Name")
        album = row.get("Album")

        ranked_matches.append({
            "rank": rank,
            "artist": artist,
            "title": title,
            "album": album,
            "played_date": played_date,
            "year": str(played_date.year),
        })

    if ranked_matches:
        best_rank = min(item["rank"] for item in ranked_matches)
        matches = [item for item in ranked_matches if item["rank"] == best_rank]
    else:
        matches = []

    artist_counts = Counter(item["artist"] for item in matches if item["artist"])
    canonical_artist = artist_counts.most_common(1)[0][0] if artist_counts else query

    years = sorted({item["year"] for item in matches})
    dates = sorted(item["played_date"] for item in matches)

    top_songs = Counter(item["title"] for item in matches if item["title"])
    top_albums = Counter(item["album"] for item in matches if item["album"])
    year_counts = Counter(item["year"] for item in matches)

    play_activity = load_play_activity_summary(query)

    result = {
        "artist": canonical_artist,
        "query": query,
        "libraryEvidenceRecords": len(matches),
        "actualPlays": play_activity["actualPlays"],
        "actualSkips": play_activity["actualSkips"],
        "hoursListened": play_activity["hoursListened"],
        "listeningDurationMs": play_activity["listeningDurationMs"],
        "playActivitySource": play_activity["playActivitySource"],
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
        "matchRank": min((item["rank"] for item in matches), default=None),
    }

    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())



