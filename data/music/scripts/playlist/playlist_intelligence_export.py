import json
import zipfile
from pathlib import Path
from collections import Counter, defaultdict
from statistics import median

base = Path.home() / "Downloads" / "apple-music-working" / "Apple_Media_Services_python" / "Apple_Media_Services" / "Apple Music Activity"

target_playlists = [
    "500 Songs",
    "deck & chill",
    "let’s go streaking!",
    "sirens",
    "not the original artist",
    "road trip",
    "rubik's cube",
    "Above the fruited plain",
]

output_path = Path("data/music/playlist_intelligence.json")

def read_zipped_json(path):
    with zipfile.ZipFile(path) as z:
        with z.open(z.namelist()[0]) as f:
            return json.load(f)

def norm(value):
    return (value or "").strip().lower()

def song_key(track):
    return (
        norm(track.get("Artist", "Unknown")),
        norm(track.get("Title", "Unknown")),
    )

def song_obj(track):
    return {
        "artist": track.get("Artist", "Unknown"),
        "song": track.get("Title", "Unknown"),
        "album": track.get("Album", "Unknown"),
        "plays": int(track.get("Track Play Count") or 0),
    }

tracks = read_zipped_json(base / "Apple Music Library Tracks.json.zip")
playlists = read_zipped_json(base / "Apple Music Library Playlists.json.zip")

track_by_id = {
    t.get("Track Identifier"): t
    for t in tracks
    if t.get("Track Identifier") is not None
}

playlist_tracks = {}

for target in target_playlists:
    matched = next(
        (p for p in playlists if norm(p.get("Title")) == norm(target)),
        None
    )

    if not matched:
        playlist_tracks[target] = []
        continue

    playlist_tracks[target] = [
        track_by_id[track_id]
        for track_id in matched.get("Playlist Item Identifiers", [])
        if track_id in track_by_id
    ]

playlist_summaries = []

for name, pts in playlist_tracks.items():
    artists = Counter(t.get("Artist", "Unknown") for t in pts)
    albums = Counter(t.get("Album", "Unknown") for t in pts)
    plays = [int(t.get("Track Play Count") or 0) for t in pts]

    playlist_summaries.append({
        "name": name,
        "songCount": len(pts),
        "artistCount": len(artists),
        "albumCount": len(albums),
        "totalPlays": sum(plays),
        "averagePlays": round(sum(plays) / len(plays), 1) if plays else 0,
        "medianPlays": round(median(plays), 1) if plays else 0,
        "zeroPlayCount": sum(1 for p in plays if p == 0),
        "lowPlayCount": sum(1 for p in plays if 1 <= p <= 5),
        "highPlayCount": sum(1 for p in plays if p >= 25),
        "topArtists": [
            {"artist": artist, "songCount": count}
            for artist, count in artists.most_common(10)
        ],
        "signatureSongs": [],
        "bridgeSongs": [],
        "exclusiveSongCount": 0,
        "sharedSongCount": 0,
        "exclusivityScore": 0,
        "playlistWorldSummary": "",
    })

artist_to_playlists = defaultdict(set)
song_to_playlists = defaultdict(set)
song_examples = {}

for playlist_name, pts in playlist_tracks.items():
    for track in pts:
        artist = track.get("Artist", "Unknown")
        artist_to_playlists[artist].add(playlist_name)

        skey = song_key(track)
        song_to_playlists[skey].add(playlist_name)
        song_examples[skey] = song_obj(track)

shared_core_artists = [
    {
        "artist": artist,
        "playlists": sorted(list(names)),
        "playlistCount": len(names),
    }
    for artist, names in artist_to_playlists.items()
    if len(names) >= 2
]

shared_core_artists = sorted(
    shared_core_artists,
    key=lambda x: (-x["playlistCount"], x["artist"].lower())
)

bridge_songs = []

for skey, names in song_to_playlists.items():
    if len(names) >= 2:
        item = song_examples[skey]
        item["playlists"] = sorted(list(names))
        item["playlistCount"] = len(names)
        bridge_songs.append(item)

bridge_songs = sorted(
    bridge_songs,
    key=lambda x: (-x["playlistCount"], x["artist"].lower(), x["song"].lower())
)

playlist_summary_by_name = {
    item["name"]: item
    for item in playlist_summaries
}

for name, pts in playlist_tracks.items():
    summary = playlist_summary_by_name[name]
    exclusive_count = 0
    shared_count = 0
    playlist_bridge_songs = []

    for track in pts:
        skey = song_key(track)
        playlist_count = len(song_to_playlists[skey])

        if playlist_count == 1:
            exclusive_count += 1
        else:
            shared_count += 1
            item = song_obj(track)
            item["playlists"] = sorted(list(song_to_playlists[skey]))
            item["playlistCount"] = playlist_count
            playlist_bridge_songs.append(item)

    summary["exclusiveSongCount"] = exclusive_count
    summary["sharedSongCount"] = shared_count
    summary["exclusivityScore"] = round((exclusive_count / len(pts)) * 100, 1) if pts else 0
    summary["bridgeSongs"] = sorted(
        playlist_bridge_songs,
        key=lambda x: (-x["playlistCount"], -x["plays"], x["artist"].lower(), x["song"].lower())
    )[:10]
    summary["playlistWorldSummary"] = (
        f"{name} is {summary['exclusivityScore']}% exclusive "
        f"with {exclusive_count} playlist-unique songs and {shared_count} bridge songs."
    )

playlist_signatures = []

for name, pts in playlist_tracks.items():
    candidates = []

    for track in pts:
        skey = song_key(track)
        item = song_obj(track)
        playlist_count = len(song_to_playlists[skey])

        candidates.append({
            **item,
            "playlistCount": playlist_count,
            "signatureScore": item["plays"] - ((playlist_count - 1) * 10),
        })

    top_tracks = sorted(
        candidates,
        key=lambda x: (x["playlistCount"], -x["signatureScore"], -x["plays"], x["artist"].lower(), x["song"].lower())
    )[:5]

    summary_signature_songs = []

    for track in top_tracks:
        reason = "Characteristic candidate: playlist-unique song with play evidence"
        if track["playlistCount"] > 1:
            reason = "Characteristic candidate: shared song retained due to strong play evidence"

        signature_item = {
            "playlist": name,
            "artist": track["artist"],
            "song": track["song"],
            "album": track["album"],
            "plays": track["plays"],
            "playlistCount": track["playlistCount"],
            "signatureScore": track["signatureScore"],
            "reason": reason,
        }

        playlist_signatures.append(signature_item)
        summary_signature_songs.append({
            "artist": track["artist"],
            "song": track["song"],
            "album": track["album"],
            "plays": track["plays"],
            "playlistCount": track["playlistCount"],
            "signatureScore": track["signatureScore"],
            "reason": reason,
        })

    playlist_summary_by_name[name]["signatureSongs"] = summary_signature_songs

data = {
    "generatedBy": "playlist_intelligence_export.py",
    "playlists": playlist_summaries,
    "sharedCoreArtists": shared_core_artists,
    "bridgeSongs": bridge_songs,
    "playlistSignatures": playlist_signatures,
}

output_path.parent.mkdir(parents=True, exist_ok=True)

with output_path.open("w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print(f"Wrote {output_path}")
print(f"Playlists: {len(playlist_summaries)}")
print(f"Shared core artists: {len(shared_core_artists)}")
print(f"Bridge songs: {len(bridge_songs)}")
print(f"Playlist signatures: {len(playlist_signatures)}")
