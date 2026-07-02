import csv
import json
import zipfile
from collections import Counter
from pathlib import Path

BASE = Path(r"C:\Users\joevi\ams\Apple_Media_Services\Apple Music Activity")
OUT_DIR = Path(r"C:\Users\joevi\apple-music-sanitized")

PLAYLIST_ZIP = BASE / "Apple Music Library Playlists.json.zip"
TRACKS_ZIP = BASE / "Apple Music Library Tracks.json.zip"
OUT_MD = OUT_DIR / "apple-music-playlist-preview.md"

ARTIST_TARGETS = [
    "Matt Pond PA",
    "The Lemonheads",
    "The Cure",
    "The Breeders",
    "The Replacements",
    "Billie Holiday",
    "Misfits",
    "The Misfits",
    "Wang Chung",
    "Peter Gabriel",
    "Pearl Jam",
]

SONG_TARGETS = [
    ("Wang Chung", "To Live and Die in L.A."),
    ("The Lemonheads", "Confetti"),
    ("Matt Pond PA", "KC"),
    ("Matt Pond PA", "New Hampshire"),
    ("Toad the Wet Sprocket", "Fall Down"),
    ("The Cure", "In Between Days"),
    ("The Breeders", "Cannonball"),
    ("Peter Gabriel", "Here Comes the Flood"),
    ("Pearl Jam", "Black"),
    ("The Police", "Hungry for You"),
]


def load_json_from_zip(path):
    with zipfile.ZipFile(path) as zf:
        member = next(name for name in zf.namelist() if name.lower().endswith(".json"))
        with zf.open(member) as handle:
            return json.load(handle)


def parse_items(raw):
    if isinstance(raw, list):
        return [str(item).strip() for item in raw if str(item).strip()]

    if isinstance(raw, str):
        for sep in ["|", ",", ";"]:
            if sep in raw:
                return [part.strip() for part in raw.split(sep) if part.strip()]
        return [raw.strip()] if raw.strip() else []

    return []


def norm(value):
    return str(value or "").strip().lower()


def playlist_summary(rows, limit=12):
    counts = Counter(row["playlist_title"] for row in rows if row["playlist_title"])
    return counts.most_common(limit)


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    playlists = load_json_from_zip(PLAYLIST_ZIP)
    tracks = load_json_from_zip(TRACKS_ZIP)

    track_by_id = {}
    for track in tracks:
        track_id = str(track.get("Track Identifier", "")).strip()
        if not track_id:
            continue

        track_by_id[track_id] = {
            "track_id": track_id,
            "title": str(track.get("Title", "")).strip(),
            "artist": str(track.get("Artist", "")).strip(),
            "album": str(track.get("Album", "")).strip(),
            "album_artist": str(track.get("Album Artist", "")).strip(),
            "play_count": str(track.get("Track Play Count", "")).strip(),
            "last_played": str(track.get("Last Played Date", "")).strip(),
        }

    playlist_rows = []
    membership_rows = []

    for playlist in playlists:
        playlist_id = str(playlist.get("Container Identifier", "")).strip()
        playlist_title = str(playlist.get("Title", "")).strip()
        item_ids = parse_items(playlist.get("Playlist Item Identifiers"))

        matched = []

        for item_id in item_ids:
            track = track_by_id.get(item_id)
            if not track:
                continue

            row = {
                "playlist_id": playlist_id,
                "playlist_title": playlist_title,
                **track,
            }
            matched.append(row)
            membership_rows.append(row)

        artists = Counter(row["artist"] for row in matched if row["artist"])

        playlist_rows.append(
            {
                "playlist_id": playlist_id,
                "title": playlist_title,
                "matched_count": len(matched),
                "unique_artists": len(artists),
                "top_artists": artists,
            }
        )

    lines = []
    lines.append("# Apple Music Playlist Intelligence Preview")
    lines.append("")
    lines.append("## Inventory")
    lines.append("")
    lines.append(f"- Library playlists: {len(playlists):,}")
    lines.append(f"- Library tracks: {len(tracks):,}")
    lines.append(f"- Playlist membership rows: {len(membership_rows):,}")
    lines.append(f"- Unique tracks appearing in playlists: {len(set(row['track_id'] for row in membership_rows)):,}")
    lines.append(f"- Playlists with at least one matched track: {sum(1 for row in playlist_rows if row['matched_count'] > 0):,}")
    lines.append(f"- Playlists with zero matched tracks: {sum(1 for row in playlist_rows if row['matched_count'] == 0):,}")
    lines.append("")

    lines.append("## Top Playlists by Track Count")
    lines.append("")
    for playlist in sorted(playlist_rows, key=lambda row: row["matched_count"], reverse=True)[:25]:
        top_artists = ", ".join(
            f"{artist} ({count})"
            for artist, count in playlist["top_artists"].most_common(3)
        )
        lines.append(
            f"- {playlist['title']} — {playlist['matched_count']:,} tracks; "
            f"{playlist['unique_artists']:,} artists; top: {top_artists}"
        )
    lines.append("")

    lines.append("## Target Artist Playlist Membership")
    lines.append("")
    for artist in ARTIST_TARGETS:
        rows = [row for row in membership_rows if norm(row["artist"]) == norm(artist)]
        playlists_hit = playlist_summary(rows)
        lines.append(f"### {artist}")
        lines.append(f"- Playlist track memberships: {len(rows):,}")
        lines.append(f"- Playlists containing artist: {len(set(row['playlist_title'] for row in rows if row['playlist_title'])):,}")
        for playlist_title, count in playlists_hit:
            lines.append(f"  - {playlist_title}: {count}")
        lines.append("")

    lines.append("## Target Song Playlist Membership")
    lines.append("")
    for artist, title in SONG_TARGETS:
        rows = [
            row for row in membership_rows
            if norm(row["artist"]) == norm(artist)
            and norm(row["title"]) == norm(title)
        ]
        playlists_hit = playlist_summary(rows)
        lines.append(f"### {artist} — {title}")
        lines.append(f"- Playlist memberships: {len(rows):,}")
        for playlist_title, count in playlists_hit:
            lines.append(f"  - {playlist_title}: {count}")
        lines.append("")

    text = "\n".join(lines)
    OUT_MD.write_text(text, encoding="utf-8")

    print(text)
    print()
    print(f"Wrote preview report: {OUT_MD}")


if __name__ == "__main__":
    main()
