from pathlib import Path
from zipfile import ZipFile
from collections import Counter, defaultdict
from datetime import datetime
import json
import sys

from actual_listening.period_intelligence_adapter import (
    apply_actual_listening_to_result,
    load_actual_listening,
)

if len(sys.argv) != 3:
    print("Usage: python library_range_summary.py YYYY-MM-DD YYYY-MM-DD")
    sys.exit(1)

start_date = datetime.strptime(sys.argv[1], "%Y-%m-%d").date()
end_date = datetime.strptime(sys.argv[2], "%Y-%m-%d").date()

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

matches = []

artist_year_counts = defaultdict(Counter)
artist_first_seen = {}

for row in data:
    played = row.get("Last Played Date")

    if not played:
        continue

    try:
        played_date = datetime.strptime(str(played)[:10], "%Y-%m-%d").date()
    except Exception:
        continue

    artist = row.get("Artist")
    if artist:
        year = str(played_date.year)
        artist_year_counts[artist][year] += 1

        if artist not in artist_first_seen or played_date < artist_first_seen[artist]:
            artist_first_seen[artist] = played_date

    if start_date <= played_date <= end_date:
        matches.append(row)

album_counts = Counter()
artist_counts = Counter()
artist_album_counts = defaultdict(Counter)
artist_track_counts = defaultdict(Counter)

for row in matches:
    album = row.get("Album")
    artist = row.get("Artist")
    track = row.get("Title") or row.get("Name") or row.get("Song Name") or row.get("song_name")

    if album:
        album_counts[album] += 1

    if artist:
        artist_counts[artist] += 1

    if artist and album:
        artist_album_counts[artist][album] += 1

    if artist and track:
        artist_track_counts[artist][track] += 1

top_albums = [
    {"album": album, "count": count}
    for album, count in album_counts.most_common(15)
]

top_artists = [
    {"artist": artist, "count": count}
    for artist, count in artist_counts.most_common(15)
]

def classify_artist(year_counts):
    active_years = [year for year, count in year_counts.items() if count > 0]

    if len(active_years) >= 5:
        return "Persistence"

    sorted_years = sorted(int(year) for year in active_years)
    if len(sorted_years) >= 2 and max(sorted_years) - min(sorted_years) >= 3:
        return "Resurgence"

    return "Emergence"

artist_journeys = {}

for item in top_artists:
    artist = item["artist"]
    year_counts = artist_year_counts.get(artist, Counter())

    if not year_counts:
        continue

    max_count = max(year_counts.values())
    most_active_years = [
        year for year, count in year_counts.items()
        if count == max_count
    ]

    timeline = [
        {
            "year": year,
            "count": count,
        }
        for year, count in sorted(year_counts.items())
    ]

    artist_journeys[artist] = {
        "firstSeen": str(artist_first_seen[artist].year),
        "mostActivePeriod": ", ".join(sorted(most_active_years)),
        "status": classify_artist(year_counts),
        "topAlbums": [
            {"album": album, "count": count}
            for album, count in artist_album_counts.get(artist, Counter()).most_common(5)
        ],
        "topTracks": [
            {"track": track, "count": count}
            for track, count in artist_track_counts.get(artist, Counter()).most_common(5)
        ],
        "timeline": timeline,
    }

memory_read = []

if not matches:
    memory_read.append("No Library Evidence was found for this period.")
elif artist_counts:
    top_artist, top_artist_count = artist_counts.most_common(1)[0]
    tied_artist_count = sum(
        1
        for count in artist_counts.values()
        if count == top_artist_count
    )
    track_word = "track" if top_artist_count == 1 else "tracks"

    if tied_artist_count == 1:
        memory_read.append(f"A possible anchor for this period is {top_artist}.")
        memory_read.append(
            f"{top_artist} appears on {top_artist_count} {track_word} "
            "with last-played dates in this range."
        )
    else:
        memory_read.append(
            f"No single artist dominates this period; {tied_artist_count} artists "
            f"share the highest Library Evidence count of "
            f"{top_artist_count} {track_word}."
        )

    if top_albums:
        album_anchor_text = ", ".join(
            f"{item['album']} ({item['count']} "
            f"{'track' if item['count'] == 1 else 'tracks'})"
            for item in top_albums[:5]
        )
        memory_read.append(f"Possible album anchors: {album_anchor_text}.")

    memory_read.append(
        "Caution: this is reconstruction from library Last Played Date, "
        "not complete play-count history."
    )

coverage_status = "searched_with_evidence" if matches else "searched_no_evidence"
summary_status = "partial_coverage" if matches else "no_matching_evidence"
top_artist_name = top_artists[0]["artist"] if top_artists else None
top_artist_count = top_artists[0]["count"] if top_artists else 0
top_artist_tied = (
    len(top_artists) > 1
    and top_artists[1]["count"] == top_artist_count
)

if top_artist_name and not top_artist_tied:
    headline = f"{top_artist_name} led the available Library Evidence for this period."
elif top_artist_name:
    headline = "No single artist led the available Library Evidence for this period."
else:
    headline = "No matching Library Evidence was found for this period."

facts = []
if matches:
    facts.append({
        "factType": "library-evidence-count",
        "statement": f"The period contains {len(matches)} Library Evidence records.",
        "value": len(matches),
        "evidenceRefs": ["library-track-last-played"],
    })

suggested_investigations = []
if top_artist_name and not top_artist_tied:
    suggested_investigations.append({
        "investigationType": "artist",
        "label": f"Investigate {top_artist_name}",
        "parameters": {"artist": top_artist_name},
        "reason": "The artist uniquely led Library Evidence during the selected period.",
    })

result = {
    "schemaVersion": "music.period-intelligence.v1",
    "generatedAt": datetime.now().astimezone().isoformat(),
    "request": {
        "startDate": str(start_date),
        "endDate": str(end_date),
        "timeZone": "America/Chicago",
    },
    "period": {
        "entityType": "period",
        "canonicalKey": f"{start_date}_{end_date}_America-Chicago",
        "startDate": str(start_date),
        "endDate": str(end_date),
        "timeZone": "America/Chicago",
        "inclusiveDayCount": (end_date - start_date).days + 1,
        "label": f"{start_date} to {end_date}",
    },
    "summary": {
        "status": summary_status,
        "headline": headline,
        "narrative": (
            "Library Evidence was searched. Actual listening, Recent Apple Objects, "
            "and playback context were not searched in this implementation slice."
        ),
    },
    "coverage": [
        {
            "sourceId": "apple_daily_track_summary",
            "sourceType": "actual_listening",
            "status": "not_searched",
            "recordsExamined": None,
            "recordsMatched": None,
            "coverageStart": None,
            "coverageEnd": None,
            "capturedAt": None,
            "freshness": "unknown",
            "limitations": [
                "Actual listening activity is not yet connected to Period Intelligence."
            ],
        },
        {
            "sourceId": "apple_library_tracks_last_played",
            "sourceType": "library_evidence",
            "status": coverage_status,
            "recordsExamined": None,
            "recordsMatched": len(matches),
            "coverageStart": str(start_date),
            "coverageEnd": str(end_date),
            "capturedAt": None,
            "freshness": "unknown",
            "limitations": [
                "Last Played Date reconstruction is not complete play-count history."
            ],
        },
        {
            "sourceId": "apple_live_snapshot_warehouse",
            "sourceType": "recent_apple_observation",
            "status": "not_searched",
            "recordsExamined": None,
            "recordsMatched": None,
            "coverageStart": None,
            "coverageEnd": None,
            "capturedAt": None,
            "freshness": "unknown",
            "limitations": [
                "Recent Apple snapshot history is not yet connected to this response."
            ],
        },
        {
            "sourceId": "music_playback_context",
            "sourceType": "playback_context",
            "status": "not_searched",
            "recordsExamined": None,
            "recordsMatched": None,
            "coverageStart": None,
            "coverageEnd": None,
            "capturedAt": None,
            "freshness": "unknown",
            "limitations": [
                "Playback context attribution is not yet connected to Period Intelligence."
            ],
        },
    ],
    "activity": {
        "status": "not_searched",
        "actualPlays": None,
        "actualSkips": None,
        "listeningSeconds": None,
        "listeningHours": None,
        "uniqueArtistCount": None,
        "uniqueAlbumCount": None,
        "uniqueTrackCount": None,
        "topArtists": [],
        "topAlbums": [],
        "topTracks": [],
    },
    "libraryEvidence": {
        "status": "available",
        "recordCount": len(matches),
        "uniqueArtistCount": None,
        "uniqueAlbumCount": None,
        "uniqueTrackCount": None,
        "topArtists": top_artists,
        "topAlbums": top_albums,
        "topTracks": [],
        "artistJourneys": artist_journeys,
        "timeline": [],
        "memoryRead": memory_read,
        "sourceNote": "Reconstruction from Apple Music Library Tracks Last Played Date. This is not complete play-count history.",
    },
    "recentAppleObservations": {
        "status": "not_searched",
        "objectCount": None,
        "capturedSnapshotCount": None,
        "firstCapturedAt": None,
        "latestCapturedAt": None,
        "artists": [],
        "albums": [],
        "tracks": [],
        "playlists": [],
        "stations": [],
        "sourceNote": "Recent Apple Objects are not yet connected to this period response.",
    },
    "playbackContexts": {
        "status": "not_searched",
        "knownEventCount": None,
        "unknownEventCount": None,
        "denominator": None,
        "items": [],
    },
    "periodTags": [],
    "facts": facts,
    "insights": [],
    "confidence": {
        "level": "low",
        "reasons": [
            "Library Evidence was searched.",
            "Actual listening and playback-context sources were not searched.",
        ],
    },
    "warnings": [
        {
            "code": "ACTUAL_LISTENING_NOT_SEARCHED",
            "message": "Actual listening history was not searched for this response.",
            "sourceId": "apple_daily_track_summary",
        },
        {
            "code": "RECENT_APPLE_NOT_SEARCHED",
            "message": "Recent Apple snapshot history was not searched for this response.",
            "sourceId": "apple_live_snapshot_warehouse",
        },
        {
            "code": "PLAYBACK_CONTEXT_NOT_SEARCHED",
            "message": "Playback context was not searched for this response.",
            "sourceId": "music_playback_context",
        },
    ],
    "provenance": [
        {
            "evidenceId": "library-track-last-played",
            "sourceId": "apple_library_tracks_last_played",
            "sourceLabel": "Apple Music Library Tracks Last Played Date",
            "sourceType": "library_evidence",
            "recordCount": len(matches),
            "coverageStart": str(start_date),
            "coverageEnd": str(end_date),
            "capturedAt": None,
            "notes": [
                "Evidence records are not Actual Plays."
            ],
        },
    ],
    "suggestedInvestigations": suggested_investigations,
    "legacy": {
        "tracksMatched": len(matches),
        "topAlbums": top_albums,
        "topArtists": top_artists,
        "artistJourneys": artist_journeys,
        "memoryRead": memory_read,
        "sourceNote": "Reconstruction from Apple Music Library Tracks Last Played Date.",
    },
}

actual_listening = load_actual_listening(
    start_date,
    end_date,
)

apply_actual_listening_to_result(
    result,
    actual_listening,
)


print(json.dumps(result, indent=2))
