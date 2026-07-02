import argparse
from pathlib import Path
import duckdb


TABLE = "apple_music_play_activity"


def repo_root():
    return Path(__file__).resolve().parents[3]


def q(name):
    return '"' + name.replace('"', '""') + '"'


def normalize(name):
    return "".join(ch for ch in name.lower() if ch.isalnum())


def pick_column(columns, candidates):
    normalized = {normalize(c): c for c in columns}

    for candidate in candidates:
        hit = normalized.get(normalize(candidate))
        if hit:
            return hit

    for col in columns:
        n = normalize(col)
        for candidate in candidates:
            if normalize(candidate) in n:
                return col

    return None


def get_schema(con):
    rows = con.execute(f"PRAGMA table_info({q(TABLE)})").fetchall()
    return [{"name": r[1], "type": r[2]} for r in rows]


def detect_columns(schema):
    columns = [c["name"] for c in schema]

    return {
        "artist": pick_column(columns, [
            "artist_name", "artist", "track_artist", "song_artist", "artistName", "Artist Name"
        ]),
        "song": pick_column(columns, [
            "song_name", "track_name", "title", "item_name", "name", "Song Name", "Track Name"
        ]),
        "album": pick_column(columns, [
            "album_name", "album", "collection_name", "release_title", "Album Name"
        ]),
        "date": pick_column(columns, [
            "event_start_timestamp", "played_at", "play_date", "date_played", "timestamp",
            "event_date", "date", "Date Played", "Last Played Date"
        ]),
        "container_type": pick_column(columns, [
            "container_type", "source_type", "play_context_type", "context_type", "Container Type"
        ]),
        "container_name": pick_column(columns, [
            "container_name", "playlist_name", "station_name", "source_name",
            "play_context_name", "context_name", "Container Name"
        ]),
    }


def text_columns(schema):
    return [
        c["name"] for c in schema
        if any(t in c["type"].upper() for t in ["VARCHAR", "TEXT", "STRING"])
    ]


def table_exists(con):
    rows = con.execute(
        """
        SELECT table_name
        FROM information_schema.tables
        WHERE table_name = ?
        """,
        [TABLE],
    ).fetchall()
    return bool(rows)


def build_where(args, detected, schema):
    clauses = []
    params = []
    notes = []

    specs = [
        ("artist", args.artist),
        ("song", args.song),
        ("album", args.album),
    ]

    fallback_cols = text_columns(schema)

    for field, value in specs:
        if not value:
            continue

        col = detected.get(field)

        if col:
            clauses.append(f"LOWER(CAST({q(col)} AS VARCHAR)) LIKE ?")
            params.append(f"%{value.lower()}%")
        else:
            if not fallback_cols:
                raise SystemExit(f"No searchable text columns found for {field} lookup.")

            pieces = []
            for fallback_col in fallback_cols:
                pieces.append(f"LOWER(CAST({q(fallback_col)} AS VARCHAR)) LIKE ?")
                params.append(f"%{value.lower()}%")

            clauses.append("(" + " OR ".join(pieces) + ")")
            notes.append(f"No reliable {field} column detected; used broad text fallback.")

    if not clauses:
        raise SystemExit("Provide --artist, --song, or --album.")

    return " AND ".join(clauses), params, notes


def count_by(con, where_sql, params, col, limit=15):
    if not col:
        return []

    sql = f"""
        SELECT
            COALESCE(NULLIF(TRIM(CAST({q(col)} AS VARCHAR)), ''), '[blank]') AS value,
            COUNT(*) AS events
        FROM {q(TABLE)}
        WHERE {where_sql}
        GROUP BY 1
        ORDER BY events DESC, value
        LIMIT ?
    """
    return con.execute(sql, params + [limit]).fetchall()


def count_by_year(con, where_sql, params, date_col):
    if not date_col:
        return []

    sql = f"""
        SELECT
            EXTRACT(year FROM TRY_CAST({q(date_col)} AS TIMESTAMP)) AS year,
            COUNT(*) AS events
        FROM {q(TABLE)}
        WHERE {where_sql}
          AND TRY_CAST({q(date_col)} AS TIMESTAMP) IS NOT NULL
        GROUP BY 1
        ORDER BY 1
    """
    return con.execute(sql, params).fetchall()


def date_range(con, where_sql, params, date_col):
    if not date_col:
        return None, None

    sql = f"""
        SELECT
            MIN(TRY_CAST({q(date_col)} AS TIMESTAMP)),
            MAX(TRY_CAST({q(date_col)} AS TIMESTAMP))
        FROM {q(TABLE)}
        WHERE {where_sql}
    """
    return con.execute(sql, params).fetchone()


def print_rows(title, rows):
    print(f"\n## {title}")
    if not rows:
        print("_No available data._")
        return

    for value, events in rows:
        print(f"- {value}: {events}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--artist")
    parser.add_argument("--song")
    parser.add_argument("--album")
    parser.add_argument("--show-schema", action="store_true")
    parser.add_argument("--limit", type=int, default=15)
    parser.add_argument(
        "--db",
        default=str(repo_root() / "data" / "music" / "music.db"),
    )

    args = parser.parse_args()

    db_path = Path(args.db)

    if not db_path.exists():
        raise SystemExit(f"Database not found: {db_path}")

    con = duckdb.connect(str(db_path), read_only=True)

    if not table_exists(con):
        print(f"Expected table not found: {TABLE}")
        print("\nAvailable tables:")
        rows = con.execute(
            "SELECT table_name FROM information_schema.tables ORDER BY table_name"
        ).fetchall()
        for row in rows:
            print(f"- {row[0]}")
        raise SystemExit(1)

    schema = get_schema(con)
    detected = detect_columns(schema)

    if args.show_schema:
        print("# Schema")
        for col in schema:
            print(f"- {col['name']} :: {col['type']}")

        print("\n# Detected Fields")
        for key, value in detected.items():
            print(f"- {key}: {value or '[not detected]'}")

        if not any([args.artist, args.song, args.album]):
            return

    where_sql, params, notes = build_where(args, detected, schema)

    total = con.execute(
        f"SELECT COUNT(*) FROM {q(TABLE)} WHERE {where_sql}",
        params,
    ).fetchone()[0]

    first_seen, latest_seen = date_range(con, where_sql, params, detected["date"])
    years = count_by_year(con, where_sql, params, detected["date"])

    print("# Music Lookup")

    if args.artist:
        print(f"- Artist query: {args.artist}")
    if args.song:
        print(f"- Song query: {args.song}")
    if args.album:
        print(f"- Album query: {args.album}")

    print("\n## Summary")
    print(f"- Total matching events: {total}")
    print(f"- First seen: {first_seen or '[unknown]'}")
    print(f"- Latest seen: {latest_seen or '[unknown]'}")
    print(f"- Years active: {len(years)}")

    if notes:
        print("\n## Notes")
        for note in notes:
            print(f"- {note}")

    print_rows("Events by Year", years)
    print_rows("Top Songs", count_by(con, where_sql, params, detected["song"], args.limit))
    print_rows("Top Albums", count_by(con, where_sql, params, detected["album"], args.limit))
    print_rows("Container Types", count_by(con, where_sql, params, detected["container_type"], args.limit))
    print_rows("Container Names", count_by(con, where_sql, params, detected["container_name"], args.limit))


if __name__ == "__main__":
    main()
