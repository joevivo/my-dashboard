import csv
import json
import zipfile
from collections import Counter, defaultdict
from pathlib import Path

BASE = Path(r"C:\Users\joevi\ams\Apple_Media_Services\Apple Music Activity")
OUT = Path(r"C:\Users\joevi\apple-music-sanitized")

PLAYLIST_ZIP = BASE / "Apple Music Library Playlists.json.zip"
TRACKS_ZIP = BASE / "Apple Music Library Tracks.json.zip"

OUT_INVENTORY = OUT / "apple-music-playlist-inventory.csv"
OUT_TRACKS = OUT / "apple-music-playlist-tracks.csv"
OUT_ARTISTS = OUT / "apple-music-playlist-artist-summary.csv"
OUT_SONGS = OUT / "apple-music-playlist-song-summary.csv"
OUT_SUMMARY = OUT / "apple-music-playlist-extraction-summary.md"


def load_json_from_zip(path):
    with zipfile.ZipFile(path) as zf:
        member = next(name for name in zf.namelist() if name.lower().endswith(".json"))
        with zf.open(member) as handle:
            return json.load(handle)


def clean(value):
    return str(value or "").strip()


def parse_items(raw):
    if isinstance(raw, list):
        return [clean(item) for item in raw if clean(item)]

    if isinstance(raw, str):
        for sep in ["|", ",", ";"]:
            if sep in raw:
                return [part.strip() for part in raw.split(sep) if part.strip()]
        return [raw.strip()] if raw.strip() else []

    return []


def write_csv(path, rows, fieldnames):
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def compact_counter(counter, limit=12):
    return " | ".join(f"{name} ({count})" for name, count in counter.most_common(limit))


def main():
    OUT.mkdir(parents=True, exist_ok=True)

    playlists = load_json_from_zip(PLAYLIST_ZIP)
    tracks = load_json_from_zip(TRACKS_ZIP)

    track_by_id = {}
    for track in tracks:
        track_id = clean(track.get("Track Identifier"))
        if not track_id:
            continue

        track_by_id[track_id] = {
            "track_id": track_id,
            "title": clean(track.get("Title")),
            "artist": clean(track.get("Artist")),
            "album": clean(track.get("Album")),
            "album_artist": clean(track.get("Album Artist")),
            "genre": clean(track.get("Genre")),
            "track_year": clean(track.get("Track Year")),
            "track_play_count": clean(track.get("Track Play Count")),
            "last_played_date": clean(track.get("Last Played Date")),
            "date_added_to_library": clean(track.get("Date Added To Library")),
            "release_date": clean(track.get("Release Date")),
        }

    inventory_rows = []
    track_rows = []

    artist_playlist_counts = defaultdict(Counter)
    song_playlist_counts = defaultdict(Counter)

    total_refs = 0
    missing_refs = 0

    for playlist in playlists:
        playlist_id = clean(playlist.get("Container Identifier"))
        playlist_title = clean(playlist.get("Title"))
        playlist_type = clean(playlist.get("Container Type"))
        item_ids = parse_items(playlist.get("Playlist Item Identifiers"))

        matched = []
        missing = 0

        for position, item_id in enumerate(item_ids, start=1):
            total_refs += 1
            track = track_by_id.get(item_id)

            if not track:
                missing += 1
                missing_refs += 1
                continue

            row = {
                "playlist_id": playlist_id,
                "playlist_title": playlist_title,
                "item_position": position,
                **track,
            }

            matched.append(row)
            track_rows.append(row)

            if track["artist"]:
                artist_playlist_counts[track["artist"]][playlist_title] += 1

            if track["artist"] or track["title"]:
                song_playlist_counts[(track["artist"], track["title"])][playlist_title] += 1

        artist_counts = Counter(row["artist"] for row in matched if row["artist"])
        album_counts = Counter(row["album"] for row in matched if row["album"])

        inventory_rows.append(
            {
                "playlist_id": playlist_id,
                "playlist_title": playlist_title,
                "container_type": playlist_type,
                "item_reference_count": len(item_ids),
                "matched_track_count": len(matched),
                "missing_track_count": missing,
                "unique_artist_count": len(artist_counts),
                "unique_album_count": len(album_counts),
                "top_artists": compact_counter(artist_counts),
                "top_albums": compact_counter(album_counts),
                "added_date": clean(playlist.get("Added Date")),
                "playlist_items_modified_date": clean(playlist.get("Playlist Items Modified Date")),
            }
        )

    artist_rows = []
    for artist, playlist_counter in artist_playlist_counts.items():
        artist_rows.append(
            {
                "artist": artist,
                "playlist_track_memberships": sum(playlist_counter.values()),
                "playlist_count": len(playlist_counter),
                "playlists": compact_counter(playlist_counter, limit=25),
            }
        )

    song_rows = []
    for (artist, title), playlist_counter in song_playlist_counts.items():
        song_rows.append(
            {
                "artist": artist,
                "title": title,
                "playlist_memberships": sum(playlist_counter.values()),
                "playlist_count": len(playlist_counter),
                "playlists": compact_counter(playlist_counter, limit=25),
            }
        )

    inventory_rows.sort(key=lambda row: row["matched_track_count"], reverse=True)
    track_rows.sort(key=lambda row: (row["playlist_title"].lower(), row["item_position"]))
    artist_rows.sort(key=lambda row: row["playlist_track_memberships"], reverse=True)
    song_rows.sort(key=lambda row: row["playlist_memberships"], reverse=True)

    write_csv(
        OUT_INVENTORY,
        inventory_rows,
        [
            "playlist_id",
            "playlist_title",
            "container_type",
            "item_reference_count",
            "matched_track_count",
            "missing_track_count",
            "unique_artist_count",
            "unique_album_count",
            "top_artists",
            "top_albums",
            "added_date",
            "playlist_items_modified_date",
        ],
    )

    write_csv(
        OUT_TRACKS,
        track_rows,
        [
            "playlist_id",
            "playlist_title",
            "item_position",
            "track_id",
            "title",
            "artist",
            "album",
            "album_artist",
            "genre",
            "track_year",
            "track_play_count",
            "last_played_date",
            "date_added_to_library",
            "release_date",
        ],
    )

    write_csv(
        OUT_ARTISTS,
        artist_rows,
        ["artist", "playlist_track_memberships", "playlist_count", "playlists"],
    )

    write_csv(
        OUT_SONGS,
        song_rows,
        ["artist", "title", "playlist_memberships", "playlist_count", "playlists"],
    )

    match_rate = ((total_refs - missing_refs) / total_refs * 100) if total_refs else 0

    summary = [
        "# Apple Music Playlist Intelligence Extraction",
        "",
        "## Outputs",
        "",
        f"- `{OUT_INVENTORY}`",
        f"- `{OUT_TRACKS}`",
        f"- `{OUT_ARTISTS}`",
        f"- `{OUT_SONGS}`",
        "",
        "## Counts",
        "",
        f"- Library playlists: {len(playlists):,}",
        f"- Library tracks: {len(track_by_id):,}",
        f"- Playlist item references: {total_refs:,}",
        f"- Matched playlist-track rows: {len(track_rows):,}",
        f"- Missing playlist item references: {missing_refs:,}",
        f"- Playlist item match rate: {match_rate:.1f}%",
        f"- Artist summary rows: {len(artist_rows):,}",
        f"- Song summary rows: {len(song_rows):,}",
        "",
        "## Top Playlists",
        "",
    ]

    for row in inventory_rows[:20]:
        summary.append(
            f"- {row['playlist_title']} — {row['matched_track_count']:,} tracks; "
            f"{row['unique_artist_count']:,} artists"
        )

    OUT_SUMMARY.write_text("\n".join(summary), encoding="utf-8")

    print("\n".join(summary))


if __name__ == "__main__":
    main()