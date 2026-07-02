import json
import re
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from music_normalization import normalize_text


EDITION_MARKERS = [
    "deluxe edition",
    "deluxe version",
    "deluxe",
    "super deluxe edition",
    "super deluxe",
    "expanded edition",
    "expanded version",
    "expanded",
    "bonus track version",
    "bonus tracks",
    "bonus track",
    "bonus tracks edition",
    "bonus track edition",
    "special edition",
    "collector's edition",
    "legacy edition",
    "anniversary edition",
    "remaster",
    "remastered",
    "digitally remastered",
    "stereo mix",
    "mono & stereo",
    "mono",
]

ALBUM_TYPE_MARKERS = [
    "live",
    "original motion picture soundtrack",
    "music from the motion picture",
    "original soundtrack",
    "soundtrack from the motion picture",
    "original television soundtrack",
    "original motion picture score",
    "box set",
    "single",
    "demo",
    "instrumentals",
]

DANGEROUS_MARKERS = [
    "acoustic",
    "acoustic version",
    "remixes",
    "re-recorded versions",
    "radio edit",
    "video version",
    "feat.",
    "white album",
    "uk",
]


def normalize_album_title(value):
    return str(value or "").strip()


def marker_matches(marker, candidates):
    marker_key = normalize_text(marker)
    return any(normalize_text(candidate) in marker_key for candidate in candidates)


def marker_matches_edition_pattern(marker):
    marker = str(marker or "").strip().lower()

    patterns = [
        r"\b(19|20)\d{2}\s+remaster(?:ed)?\b",
        r"\bremaster(?:ed)?\s+(19|20)\d{2}\b",
        r"\b(19|20)\d{2}\s+mix\b",
        r"\b(19|20)\d{2}\s+stereo\s+mix\b",
        r"\b(19|20)\d{2}\s+mono\s+mix\b",
        r"\b\d+(st|nd|rd|th)\s+anniversary\b",
        r"\b\d+\s+year\s+anniversary\b",
    ]

    return any(re.search(pattern, marker) for pattern in patterns)


def classify_album_marker(marker):
    marker = str(marker or "").strip()

    if marker_matches_edition_pattern(marker):
        return "edition"

    if marker_matches(marker, ALBUM_TYPE_MARKERS):
        return "album_type"

    if marker_matches(marker, DANGEROUS_MARKERS):
        return "review"

    if marker_matches(marker, EDITION_MARKERS):
        return "edition"

    return "unknown"


def classify_album_edition(album_title):
    title = str(album_title or "").lower()

    for marker in EDITION_MARKERS:
        if normalize_text(marker) in normalize_text(title):
            return marker

    return "standard"


def strip_trailing_album_markers(album_title):
    title = str(album_title or "").strip()

    while True:
        match = re.search(r"\s*[\(\[]([^\)\]]+)[\)\]]\s*$", title)
        if not match:
            return title.strip()

        marker = match.group(1)
        classification = classify_album_marker(marker)

        if classification == "edition":
            title = title[: match.start()].strip()
            continue

        return title.strip()


ALBUM_IDENTITIES_PATH = Path(__file__).resolve().parents[2] / "curated" / "albumIdentities.json"


def load_album_identities():
    if not ALBUM_IDENTITIES_PATH.exists():
        return {}

    return json.loads(ALBUM_IDENTITIES_PATH.read_text(encoding="utf-8-sig"))


def build_album_alias_index():
    index = {}

    for identity_key, identity in load_album_identities().items():
        artist = identity.get("artist", "")
        display_name = identity.get("displayName", "")
        aliases = identity.get("aliases", [])

        for alias in aliases + [display_name]:
            alias_key = normalize_text(alias)
            artist_key = normalize_text(artist)
            if alias_key:
                index[(artist_key, alias_key)] = identity

    return index


ALBUM_ALIAS_INDEX = build_album_alias_index()


def resolve_album_identity(album_title, artist_name=None):
    stripped_title = strip_trailing_album_markers(album_title)
    album_key = normalize_text(stripped_title)
    artist_key = normalize_text(artist_name)

    identity = ALBUM_ALIAS_INDEX.get((artist_key, album_key))

    if identity:
        return identity

    return {
        "artist": artist_name or "",
        "displayName": stripped_title,
        "aliases": [stripped_title],
        "confidence": "normalized",
        "notes": "Resolved by generic album normalization only."
    }

def canonical_album_title(album_title, artist_name=None):
    return resolve_album_identity(album_title, artist_name).get("displayName", strip_trailing_album_markers(album_title))


def canonical_album_key(album_title, artist_name=None):
    return normalize_text(canonical_album_title(album_title, artist_name))
