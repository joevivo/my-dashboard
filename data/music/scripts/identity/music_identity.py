import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
ALBUM_DIR = SCRIPTS_DIR / "album"

for path in [SCRIPTS_DIR, ALBUM_DIR]:
    path_text = str(path)
    if path_text not in sys.path:
        sys.path.append(path_text)

from album_normalization import (  # noqa: E402
    canonical_album_key,
    canonical_album_title,
    resolve_album_identity,
)
from music_normalization import normalize_text  # noqa: E402


def resolve_album(album_title, artist_name=None):
    identity = resolve_album_identity(album_title, artist_name)

    return {
        "type": "album",
        "artist": identity.get("artist") or artist_name or "",
        "rawTitle": album_title or "",
        "displayName": identity.get("displayName") or canonical_album_title(album_title, artist_name),
        "canonicalKey": canonical_album_key(album_title, artist_name),
        "confidence": identity.get("confidence", "normalized"),
        "aliases": identity.get("aliases", []),
        "notes": identity.get("notes", ""),
    }


def resolve_artist(artist_name):
    return {
        "type": "artist",
        "rawName": artist_name or "",
        "displayName": str(artist_name or "").strip(),
        "canonicalKey": normalize_text(artist_name),
        "confidence": "normalized",
        "aliases": [],
        "notes": "Artist identity resolver placeholder; family-aware migration pending.",
    }
