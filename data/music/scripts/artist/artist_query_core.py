from __future__ import annotations

import csv
import json
import re
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

LIBRARY_TRACKS_ZIP = (
    Path.home()
    / "Downloads"
    / "apple-music-working"
    / "Apple_Media_Services_python"
    / "Apple_Media_Services"
    / "Apple Music Activity"
    / "Apple Music Library Tracks.json.zip"
)


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

    if len(q) < 3:
        return None

    if a.startswith(q):
        return 2

    artist_words = set(a.split())
    query_words = set(q.split())

    if query_words and query_words.issubset(artist_words):
        return 3

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

def parse_track_title(track_description: object) -> str | None:
    value = str(track_description or "").strip()

    if " - " not in value:
        return None

    title = value.split(" - ", 1)[1].strip()
    if not title:
        return None

    if title.upper() in {"UNKNOWN", "N/A", "NONE", "NULL"}:
        return None

    return title


def parse_int(value: object) -> int:
    try:
        return int(float(str(value or "0").strip() or "0"))
    except Exception:
        return 0


def parse_date(value: object):
    if not value:
        return None
    try:
        return datetime.strptime(str(value)[:10], "%Y-%m-%d").date()
    except Exception:
        return None


def load_library_tracks(path: Path = LIBRARY_TRACKS_ZIP) -> list[dict]:
    if not path.exists():
        raise FileNotFoundError(f"Library Tracks export not found: {path}")

    with ZipFile(path, "r") as z:
        with z.open("Apple Music Library Tracks.json") as f:
            return json.load(f)


def load_play_activity_rows(path: Path = PLAY_ACTIVITY_SOURCE) -> list[dict]:
    if not path.exists():
        return []

    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def load_play_activity_summary(query: str, rows: list[dict] | None = None) -> dict:
    if rows is None:
        rows = load_play_activity_rows()

    if not rows:
        return {
            "actualPlays": None,
            "actualSkips": None,
            "listeningDurationMs": None,
            "hoursListened": None,
            "playActivitySource": "missing",
            "actualTopSongs": [],
        }

    actual_plays = 0
    actual_skips = 0
    listening_duration_ms = 0
    song_play_counts = Counter()

    for row in rows:
        artist = parse_track_artist(row.get("Track Description"))
        if match_rank(query, artist) is None:
            continue

        play_count = parse_int(row.get("Play Count"))
        actual_plays += play_count
        actual_skips += parse_int(row.get("Skip Count"))
        listening_duration_ms += parse_int(row.get("Play Duration Milliseconds"))

        title = parse_track_title(row.get("Track Description"))
        if title:
            song_play_counts[title] += play_count

    return {
        "actualPlays": actual_plays,
        "actualSkips": actual_skips,
        "hoursListened": round(listening_duration_ms / 1000 / 60 / 60, 1),
        "listeningDurationMs": listening_duration_ms,
        "playActivitySource": "apple_music_daily_track_summary",
        "actualTopSongs": [
            {"song": song, "plays": count}
            for song, count in song_play_counts.most_common(10)
        ],
    }

class ArtistQueryEngine:
    def __init__(
        self,
        library_tracks: list[dict] | None = None,
        play_activity_rows: list[dict] | None = None,
    ):
        self.library_tracks = library_tracks if library_tracks is not None else load_library_tracks()
        self.play_activity_rows = play_activity_rows if play_activity_rows is not None else load_play_activity_rows()
        self.library_tracks_by_artist_key = self._build_library_track_index()
        self.play_activity_by_artist_key = self._build_play_activity_index()

    def _build_library_track_index(self) -> dict[str, list[dict]]:
        index = {}

        for row in self.library_tracks:
            artist = row.get("Artist")
            key = canonical_key(artist)
            if not key:
                continue
            index.setdefault(key, []).append(row)

        return index

    def _build_play_activity_index(self) -> dict[str, dict]:
        index = {}

        for row in self.play_activity_rows:
            artist = parse_track_artist(row.get("Track Description"))
            key = canonical_key(artist)
            if not key:
                continue

            bucket = index.setdefault(key, {
                "actualPlays": 0,
                "actualSkips": 0,
                "listeningDurationMs": 0,
            })

            bucket["actualPlays"] += parse_int(row.get("Play Count"))
            bucket["actualSkips"] += parse_int(row.get("Skip Count"))
            bucket["listeningDurationMs"] += parse_int(row.get("Play Duration Milliseconds"))

        return index

    def _play_activity_summary_for_query(self, query: str) -> dict:
        # Preserve legacy match_rank behavior for play activity.
        # Exact-key indexing is too strict for queries like:
        # - Bob Marley -> Bob Marley & The Wailers
        # - Elvis Costello -> Elvis Costello & The Attractions / Imposters
        return load_play_activity_summary(query, self.play_activity_rows)

    def query_artist(self, query: str) -> dict:
        query = str(query or "").strip()
        query_key = canonical_key(query)

        ranked_matches = []

        exact_rows = self.library_tracks_by_artist_key.get(query_key)

        if exact_rows:
            rows_to_scan = exact_rows
            force_rank = 1
        else:
            rows_to_scan = self.library_tracks
            force_rank = None

        for row in rows_to_scan:
            artist = row.get("Artist")
            rank = force_rank if force_rank is not None else match_rank(query, artist)

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

        play_activity = self._play_activity_summary_for_query(query)

        result = {
            "artist": canonical_artist,
            "query": query,
            "libraryEvidenceRecords": len(matches),
            "actualPlays": play_activity["actualPlays"],
            "actualSkips": play_activity["actualSkips"],
            "hoursListened": play_activity["hoursListened"],
            "listeningDurationMs": play_activity["listeningDurationMs"],
            "playActivitySource": play_activity["playActivitySource"],
            "actualTopSongs": play_activity.get("actualTopSongs", []),
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

        result["identity"] = {
            "query": query,
            "resolvedArtist": canonical_artist,
            "canonicalKey": query_key,
            "matchRank": min((item["rank"] for item in matches), default=None),
            "source": "artist_query_core",
            "confidence": "high" if matches else "low",
        }

        result["evidence"] = {
            "type": "Library Evidence",
            "source": "Apple Music Library Tracks Last Played Date",
            "records": result.get("libraryEvidenceRecords"),
            "yearsRepresented": result.get("yearsActive"),
            "firstPlayedDate": result.get("firstPlayedDate"),
            "latestPlayedDate": result.get("latestPlayedDate"),
            "topSongs": result.get("topSongs", []),
            "topAlbums": result.get("topAlbums", []),
            "timeline": result.get("timeline", []),
            "confidence": "high" if matches else "low",
            "notes": "Useful for artist lookup and library footprint; not complete event-level play history.",
        }

        result["activity"] = {
            "type": "Play Activity",
            "source": result.get("playActivitySource"),
            "actualPlays": result.get("actualPlays"),
            "actualSkips": result.get("actualSkips"),
            "hoursListened": result.get("hoursListened"),
            "listeningDurationMs": result.get("listeningDurationMs"),
            "actualTopSongs": result.get("actualTopSongs", []),
            "confidence": "high" if result.get("playActivitySource") != "missing" else "missing",
        }

        result["derived"] = {
            "type": "Derived Intelligence",
            "classification": result.get("classification"),
            "yearsRepresented": result.get("yearsActive"),
            "source": "Derived from Library Evidence and Play Activity",
            "confidence": "medium" if matches else "low",
        }

        result["investigation"] = {
            "type": "Investigation",
            "notes": result.get("notes"),
            "suggestedInvestigations": [],
            "openQuestions": [],
        }

        return result


def query_artist(query: str) -> dict:
    return ArtistQueryEngine().query_artist(query)




