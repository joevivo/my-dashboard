import json
import zipfile
import duckdb
from pathlib import Path

base = Path.home() / "Downloads" / "apple-music-working" / "Apple_Media_Services_python" / "Apple_Media_Services" / "Apple Music Activity"
db_path = Path("data/music/music.db")

playlists = [
    "500 Songs",
    "deck & chill",
    "let’s go streaking!",
]

def read_zipped_json(path):
    with zipfile.ZipFile(path) as z:
        with z.open(z.namelist()[0]) as f:
            return json.load(f)

def norm(value):
    return (value or "").strip().lower()

tracks = read_zipped_json(base / "Apple Music Library Tracks.json.zip")
playlist_data = read_zipped_json(base / "Apple Music Library Playlists.json.zip")

track_by_id = {
    t.get("Track Identifier"): t
    for t in tracks
    if t.get("Track Identifier") is not None
}

playlist_songs = {}

for target in playlists:
    matched = next((p for p in playlist_data if norm(p.get("Title")) == norm(target)), None)
    songs = set()

    if matched:
        for track_id in matched.get("Playlist Item Identifiers", []):
            track = track_by_id.get(track_id)
            if track:
                songs.add((norm(track.get("Artist")), norm(track.get("Title"))))

    playlist_songs[target] = songs

con = duckdb.connect(str(db_path))

for playlist, songs in playlist_songs.items():
    print(f"\n=== {playlist} ===")
    print(f"Playlist songs: {len(songs)}")

    values = ",".join(["(?, ?)"] * len(songs))
    params = []
    for artist, song in songs:
        params.extend([artist, song])

    base_cte = f"""
    WITH playlist_songs(artist_name, song_name) AS (
        VALUES {values}
    ),
    matched_events AS (
        SELECT
            a.song_name,
            a.album_name,
            a.artist_name,
            a.container_name,
            a.container_type,
            a.source_type,
            a.event_timestamp,
            LEAST(a.play_duration_ms, 3600000) AS capped_duration_ms
        FROM apple_music_play_activity a
        JOIN playlist_songs p
          ON lower(a.song_name) = p.song_name
    )
    """

    footprint = con.execute(
        base_cte + """
        SELECT
            COUNT(*) AS events,
            COUNT(DISTINCT song_name) AS distinct_songs,
            SUM(capped_duration_ms) / 1000.0 / 3600.0 AS capped_hours,
            MIN(event_timestamp) AS first_seen,
            MAX(event_timestamp) AS last_seen
        FROM matched_events
        """,
        params,
    ).fetchone()

    print("\nFootprint")
    print(footprint)

    print("\nContainer Types")
    rows = con.execute(
        base_cte + """
        SELECT
            COALESCE(container_type, '<blank>') AS container_type,
            COUNT(*) AS events,
            SUM(capped_duration_ms) / 1000.0 / 3600.0 AS capped_hours
        FROM matched_events
        GROUP BY COALESCE(container_type, '<blank>')
        ORDER BY events DESC
        """,
        params,
    ).fetchall()

    for row in rows:
        print(row)

    print("\nSource Types")
    rows = con.execute(
        base_cte + """
        SELECT
            COALESCE(source_type, '<blank>') AS source_type,
            COUNT(*) AS events,
            SUM(capped_duration_ms) / 1000.0 / 3600.0 AS capped_hours
        FROM matched_events
        GROUP BY COALESCE(source_type, '<blank>')
        ORDER BY events DESC
        """,
        params,
    ).fetchall()

    for row in rows:
        print(row)

    print("\nTop Containers")
    rows = con.execute(
        base_cte + """
        SELECT
            COALESCE(container_name, '<blank>') AS container_name,
            COALESCE(container_type, '<blank>') AS container_type,
            COUNT(*) AS events
        FROM matched_events
        GROUP BY
            COALESCE(container_name, '<blank>'),
            COALESCE(container_type, '<blank>')
        ORDER BY events DESC
        LIMIT 15
        """,
        params,
    ).fetchall()

    for row in rows:
        print(row)

    print("\nTop Footprint Songs")
    rows = con.execute(
        base_cte + """
        SELECT
            artist_name,
            song_name,
            COUNT(*) AS events,
            SUM(capped_duration_ms) / 1000.0 / 3600.0 AS capped_hours,
            COUNT(DISTINCT COALESCE(container_type, '<blank>')) AS context_types
        FROM matched_events
        GROUP BY artist_name, song_name
        ORDER BY events DESC
        LIMIT 20
        """,
        params,
    ).fetchall()

    for row in rows:
        print(row)

con.close()
