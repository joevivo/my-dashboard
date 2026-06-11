import argparse
import csv
from collections import Counter
from datetime import datetime
from pathlib import Path

import duckdb


TABLE = "apple_music_play_activity"
ARTIST_SOURCE = Path("C:/Users/joevi/apple-music-sanitized/apple-music-daily-track-summary.csv")


def repo_root():
    return Path(__file__).resolve().parents[3]


def q(name):
    return '"' + name.replace('"', '""') + '"'


def normalize_text(value):
    return "".join(ch for ch in str(value).lower() if ch.isalnum())


def display_date(value):
    value = str(value or "").strip()

    if not value:
        return None

    if len(value) == 8 and value.isdigit():
        return f"{value[0:4]}-{value[4:6]}-{value[6:8]}"

    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).date().isoformat()
    except ValueError:
        pass

    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%m/%d/%y"):
        try:
            return datetime.strptime(value, fmt).date().isoformat()
        except ValueError:
            continue

    return None


def pick_column(fieldnames, candidates):
    normalized = {normalize_text(name): name for name in fieldnames}

    for candidate in candidates:
        hit = normalized.get(normalize_text(candidate))
        if hit:
            return hit

    for name in fieldnames:
        n = normalize_text(name)
        for candidate in candidates:
            if normalize_text(candidate) in n:
                return name

    return None


def split_artist_track(description):
    description = str(description or "").strip()

    if " - " not in description:
        return None, None

    artist, track = description.split(" - ", 1)
    return artist.strip(), track.strip()


def format_share(value):
    return f"{value:.1%}"


def md_table(headers, rows):
    lines = []
    lines.append("| " + " | ".join(headers) + " |")
    lines.append("| " + " | ".join(["---"] * len(headers)) + " |")

    for row in rows:
        lines.append("| " + " | ".join(str(cell) for cell in row) + " |")

    return lines


def context_read(counts):
    total = sum(counts.values())

    if total == 0:
        return "No DuckDB context rows"

    playlist = counts.get("PLAYLIST", 0)
    album = counts.get("ALBUM", 0)
    radio = counts.get("RADIO", 0)
    unknown = counts.get("UNKNOWN", 0) + counts.get("[blank]", 0)

    playlist_share = playlist / total
    album_share = album / total
    radio_share = radio / total
    unknown_share = unknown / total

    if album_share >= 0.45:
        if radio_share >= 0.20:
            return "Album-rooted with radio reinforcement"
        if playlist_share >= 0.20:
            return "Album-rooted with playlist reinforcement"
        return "Album-carried"

    if playlist_share >= 0.55:
        if album_share >= 0.20:
            return "Playlist-carried with album reinforcement"
        if radio_share >= 0.20:
            return "Playlist-carried with radio reinforcement"
        return "Playlist-carried"

    if radio_share >= 0.40:
        if album_share >= 0.20:
            return "Album-rooted with radio reinforcement"
        if playlist_share >= 0.20:
            return "Playlist-carried with radio reinforcement"
        return "Radio-reinforced"

    if unknown_share >= 0.50:
        return "Context-lost / unknown-heavy"

    if album_share >= 0.25 and radio_share >= 0.20:
        return "Album-rooted with radio reinforcement"

    if album_share >= 0.25 and playlist_share >= 0.20:
        return "Album-rooted with playlist reinforcement"

    if playlist_share >= 0.25 and radio_share >= 0.20:
        return "Playlist-carried with radio reinforcement"

    return "Mixed-context"


def confidence(total):
    if total == 0:
        return "Not found"
    if total < 20:
        return "Low"
    if total < 75:
        return "Medium"
    return "High"


def load_artist_song_events(source_path, artist_query, song_query):
    if not source_path.exists():
        raise SystemExit(f"Artist source not found: {source_path}")

    artist_norm = normalize_text(artist_query)
    song_norm = normalize_text(song_query)

    rows = []
    dates = []
    matched_titles = Counter()
    matched_artists = Counter()

    with source_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = reader.fieldnames or []

        if not fieldnames:
            raise SystemExit(f"No CSV headers found in {source_path}")

        date_col = pick_column(fieldnames, [
            "date",
            "Date",
            "day",
            "Play Date",
            "Event Date",
            "Last Played Date",
        ])

        desc_col = pick_column(fieldnames, [
            "Track Description",
            "track_description",
            "description",
            "Description",
            "Track",
            "Song",
        ])

        if not date_col:
            raise SystemExit(f"Could not detect date column in {source_path}. Headers: {fieldnames}")

        if not desc_col:
            raise SystemExit(f"Could not detect track description column in {source_path}. Headers: {fieldnames}")

        for row in reader:
            artist, track = split_artist_track(row.get(desc_col))

            if not artist or not track:
                continue

            if normalize_text(artist) != artist_norm:
                continue

            track_norm = normalize_text(track)

            if song_norm not in track_norm and track_norm not in song_norm:
                continue

            date = display_date(row.get(date_col))

            rows.append({
                "date": date,
                "artist": artist,
                "track": track,
                "raw": row,
            })

            if date:
                dates.append(date)

            matched_artists[artist] += 1
            matched_titles[track] += 1

    return {
        "artist": artist_query,
        "song": song_query,
        "events": rows,
        "dates": sorted(set(dates)),
        "matched_artists": matched_artists,
        "matched_titles": matched_titles,
    }


def query_duckdb_context(db_path, song_query, dates):
    if not dates:
        return {
            "rows": [],
            "counts": Counter(),
            "first_seen": "[not found]",
            "latest_seen": "[not found]",
        }

    if not db_path.exists():
        raise SystemExit(f"Database not found: {db_path}")

    con = duckdb.connect(str(db_path), read_only=True)

    placeholders = ", ".join(["?"] * len(dates))
    params = [f"%{song_query.lower()}%"] + list(dates)

    sql = f"""
        SELECT
            COALESCE(NULLIF(TRIM(container_type), ''), '[blank]') AS container_type,
            COALESCE(NULLIF(TRIM(album_name), ''), '[blank]') AS album_name,
            COALESCE(NULLIF(TRIM(song_name), ''), '[blank]') AS song_name,
            CAST(event_start_timestamp AS DATE) AS event_date
        FROM {q(TABLE)}
        WHERE LOWER(CAST(song_name AS VARCHAR)) LIKE ?
          AND CAST(event_start_timestamp AS DATE) IN ({placeholders})
        ORDER BY event_start_timestamp
    """

    rows = con.execute(sql, params).fetchall()
    counts = Counter(row[0] for row in rows)
    seen_dates = [str(row[3]) for row in rows if row[3] is not None]

    return {
        "rows": rows,
        "counts": counts,
        "first_seen": min(seen_dates) if seen_dates else "[not found]",
        "latest_seen": max(seen_dates) if seen_dates else "[not found]",
    }


def analyze_pair(spec, db_path, source_path):
    if "::" not in spec:
        raise SystemExit(f"Use ARTIST::SONG format for --artist-song. Bad value: {spec}")

    artist, song = [part.strip() for part in spec.split("::", 1)]

    identity = load_artist_song_events(source_path, artist, song)
    context = query_duckdb_context(db_path, song, identity["dates"])

    counts = context["counts"]
    total_context = sum(counts.values())
    playlist = counts.get("PLAYLIST", 0)
    album = counts.get("ALBUM", 0)
    radio = counts.get("RADIO", 0)
    unknown = counts.get("UNKNOWN", 0)
    blank = counts.get("[blank]", 0)
    unknown_plus_blank = unknown + blank

    return {
        "label": f"{artist} — {song}",
        "artist": artist,
        "song": song,
        "artist_song_events": len(identity["events"]),
        "artist_song_dates": len(identity["dates"]),
        "duckdb_context_rows": total_context,
        "playlist": playlist,
        "album": album,
        "radio": radio,
        "unknown_plus_blank": unknown_plus_blank,
        "playlist_share": (playlist / total_context) if total_context else 0,
        "album_share": (album / total_context) if total_context else 0,
        "radio_share": (radio / total_context) if total_context else 0,
        "unknown_share": (unknown_plus_blank / total_context) if total_context else 0,
        "first_seen": context["first_seen"],
        "latest_seen": context["latest_seen"],
        "context_read": context_read(counts),
        "confidence": confidence(total_context),
        "matched_titles": identity["matched_titles"],
        "matched_artists": identity["matched_artists"],
    }


def render_report(results):
    lines = []
    lines.append("# Artist-Aware Song Context Probe")
    lines.append("")
    lines.append("This report combines the sanitized artist/song daily summary with DuckDB listening context.")
    lines.append("")
    lines.append("Important limitation: DuckDB does not contain a reliable artist column, so context rows are inferred by matching song title on dates where the sanitized artist/song source confirms the artist-song pair.")
    lines.append("")
    lines.append("## Summary")
    lines.append("")

    lines.extend(md_table(
        [
            "Target",
            "Artist/Song Events",
            "Artist/Song Dates",
            "DuckDB Context Rows",
            "Playlist",
            "Playlist %",
            "Album",
            "Album %",
            "Radio",
            "Radio %",
            "Unknown + Blank",
            "Unknown %",
            "First Seen",
            "Latest Seen",
            "Context Read",
            "Confidence",
        ],
        [
            [
                result["label"],
                result["artist_song_events"],
                result["artist_song_dates"],
                result["duckdb_context_rows"],
                result["playlist"],
                format_share(result["playlist_share"]),
                result["album"],
                format_share(result["album_share"]),
                result["radio"],
                format_share(result["radio_share"]),
                result["unknown_plus_blank"],
                format_share(result["unknown_share"]),
                result["first_seen"],
                result["latest_seen"],
                result["context_read"],
                result["confidence"],
            ]
            for result in results
        ],
    ))

    lines.append("")

    for result in results:
        lines.append(f"## {result['label']}")
        lines.append("")
        lines.append(f"- Artist/song events from sanitized source: {result['artist_song_events']}")
        lines.append(f"- Artist/song dates from sanitized source: {result['artist_song_dates']}")
        lines.append(f"- DuckDB context rows inferred: {result['duckdb_context_rows']}")
        lines.append(f"- Context read: {result['context_read']}")
        lines.append(f"- Confidence: {result['confidence']}")
        lines.append("")
        lines.append("### Matched Titles")
        lines.append("")

        if result["matched_titles"]:
            for title, count in result["matched_titles"].most_common(15):
                lines.append(f"- {title}: {count}")
        else:
            lines.append("_No matched titles._")

        lines.append("")

    return lines


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--artist-song",
        action="append",
        default=[],
        help="Artist-aware song probe in ARTIST::SONG format.",
    )
    parser.add_argument(
        "--db",
        default=str(repo_root() / "data" / "music" / "music.db"),
    )
    parser.add_argument(
        "--source",
        default=str(ARTIST_SOURCE),
        help="Sanitized daily track summary CSV.",
    )
    parser.add_argument("--md")

    args = parser.parse_args()

    if not args.artist_song:
        raise SystemExit("Provide at least one --artist-song value in ARTIST::SONG format.")

    db_path = Path(args.db)
    source_path = Path(args.source)

    results = [
        analyze_pair(spec, db_path=db_path, source_path=source_path)
        for spec in args.artist_song
    ]

    lines = render_report(results)

    if args.md:
        out_path = Path(args.md)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"wrote {out_path}")
    else:
        print("\n".join(lines))


if __name__ == "__main__":
    main()
