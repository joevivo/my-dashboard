import argparse
import duckdb
from pathlib import Path


DEFAULT_DB = Path("data/music/music.db")
DEFAULT_MD_OUT = Path("docs/music/music-context-probe-report.md")


def sql_escape(value):
    return str(value).replace("'", "''")



def format_share(value):
    return f"{value:.1%}"


def album_root_strength(album_events, total_events):
    if total_events == 0:
        return "Not found / source-limited"

    share = album_events / total_events

    if share >= 0.45:
        return "Strong album-root"

    if share >= 0.25:
        return "Moderate album-root"

    if share >= 0.10:
        return "Weak album-root"

    return "Not album-rooted"


def context_read(counts):
    total = sum(counts.values())

    if total == 0:
        return "Not found / source-limited"

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

def md_table(headers, rows):
    lines = []
    lines.append("| " + " | ".join(headers) + " |")
    lines.append("| " + " | ".join(["---"] * len(headers)) + " |")

    for row in rows:
        lines.append("| " + " | ".join(str(cell) for cell in row) + " |")

    return lines


def query_target(con, label, target_type, pattern):
    escaped = sql_escape(pattern.lower())

    if target_type == "song":
        where = f"LOWER(COALESCE(song_name, '')) LIKE '%{escaped}%'"
    elif target_type == "album":
        where = f"LOWER(COALESCE(album_name, '')) LIKE '%{escaped}%'"
    else:
        raise ValueError(f"Unsupported target type: {target_type}")

    rows = con.execute(f"""
        SELECT
          COALESCE(container_type, '[blank]') AS container_type,
          COUNT(*) AS events,
          COUNT(DISTINCT album_name) AS distinct_albums,
          COUNT(DISTINCT song_name) AS distinct_songs,
          MIN(CAST(event_start_timestamp AS DATE)) AS first_seen,
          MAX(CAST(event_start_timestamp AS DATE)) AS latest_seen
        FROM apple_music_play_activity
        WHERE {where}
        GROUP BY 1
        ORDER BY events DESC
    """).fetchall()

    counts = {}
    first_dates = []
    latest_dates = []
    distinct_albums = 0
    distinct_songs = 0

    for row in rows:
        container_type, events, albums, songs, first_seen, latest_seen = row
        counts[container_type] = events
        distinct_albums += albums or 0
        distinct_songs += songs or 0

        if first_seen:
            first_dates.append(first_seen)

        if latest_seen:
            latest_dates.append(latest_seen)

    total = sum(counts.values())

    playlist = counts.get("PLAYLIST", 0)
    album = counts.get("ALBUM", 0)
    radio = counts.get("RADIO", 0)
    unknown = counts.get("UNKNOWN", 0)
    blank = counts.get("[blank]", 0)
    unknown_plus_blank = unknown + blank

    return {
        "label": label,
        "target_type": target_type,
        "pattern": pattern,
        "total": total,
        "playlist": playlist,
        "album": album,
        "radio": radio,
        "unknown": unknown,
        "blank": blank,
        "unknown_plus_blank": unknown_plus_blank,
        "artist": counts.get("ARTIST", 0),
        "playlist_share": (playlist / total) if total else 0,
        "album_share": (album / total) if total else 0,
        "radio_share": (radio / total) if total else 0,
        "unknown_plus_blank_share": (unknown_plus_blank / total) if total else 0,
        "distinct_albums": distinct_albums,
        "distinct_songs": distinct_songs,
        "first_seen": min(first_dates) if first_dates else "[not found]",
        "latest_seen": max(latest_dates) if latest_dates else "[not found]",
        "context_read": context_read(counts),
        "album_root_strength": album_root_strength(album, total),
        "raw_rows": rows,
    }


def render_report(results):
    lines = []
    lines.append("# Music Context Probe")
    lines.append("")
    lines.append("## Summary")
    lines.append("")

    lines.extend(md_table(
        [
            "Target",
            "Type",
            "Total",
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
            "Album Root Strength",
        ],
        [
            [
                result["label"],
                result["target_type"],
                result["total"],
                result["playlist"],
                format_share(result["playlist_share"]),
                result["album"],
                format_share(result["album_share"]),
                result["radio"],
                format_share(result["radio_share"]),
                result["unknown_plus_blank"],
                format_share(result["unknown_plus_blank_share"]),
                result["first_seen"],
                result["latest_seen"],
                result["context_read"],
                result["album_root_strength"],
            ]
            for result in results
        ],
    ))

    lines.append("")
    lines.append("## Detail")
    lines.append("")

    for result in results:
        lines.append(f"### {result['label']}")
        lines.append("")
        lines.append(f"- Type: {result['target_type']}")
        lines.append(f"- Pattern: `{result['pattern']}`")
        lines.append(f"- Total events: {result['total']}")
        lines.append(f"- Distinct albums: {result['distinct_albums']}")
        lines.append(f"- Distinct songs: {result['distinct_songs']}")
        lines.append(f"- First seen: {result['first_seen']}")
        lines.append(f"- Latest seen: {result['latest_seen']}")
        lines.append(f"- Context read: {result['context_read']}")
        lines.append("")
        lines.extend(md_table(
            [
                "Container Type",
                "Events",
                "Distinct Albums",
                "Distinct Songs",
                "First Seen",
                "Latest Seen",
            ],
            [
                [
                    row[0],
                    row[1],
                    row[2],
                    row[3],
                    row[4],
                    row[5],
                ]
                for row in result["raw_rows"]
            ],
        ))
        lines.append("")

    return lines


def main():
    parser = argparse.ArgumentParser(
        description="Probe album/playlist/radio/unknown allocation for songs and albums."
    )
    parser.add_argument("--song", action="append", default=[], help="Song title pattern. May be repeated.")
    parser.add_argument("--album", action="append", default=[], help="Album title pattern. May be repeated.")
    parser.add_argument("--db", default=str(DEFAULT_DB))
    parser.add_argument(
        "--md",
        nargs="?",
        const=str(DEFAULT_MD_OUT),
        help="Optional Markdown output path. If no path is supplied, writes to docs/music/music-context-probe-report.md.",
    )

    args = parser.parse_args()

    db = Path(args.db)

    if not db.exists():
        raise SystemExit(f"Database not found: {db}")

    targets = []

    for song in args.song:
        targets.append((song, "song", song))

    for album in args.album:
        targets.append((album, "album", album))

    if not targets:
        raise SystemExit("Provide at least one --song or --album target.")

    con = duckdb.connect(str(db), read_only=True)

    try:
        results = [
            query_target(con=con, label=label, target_type=target_type, pattern=pattern)
            for label, target_type, pattern in targets
        ]
    finally:
        con.close()

    lines = render_report(results)
    print("\n".join(lines))

    if args.md:
        out_path = Path(args.md)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"\nWrote Markdown report: {out_path}")


if __name__ == "__main__":
    main()
