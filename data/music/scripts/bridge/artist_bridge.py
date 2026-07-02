import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
SCRIPTS_DIR = SCRIPT_DIR.parent
ARTIST_DIR = SCRIPTS_DIR / "artist"
WAREHOUSE = Path("data/music/live/warehouse")

if str(ARTIST_DIR) not in sys.path:
    sys.path.insert(0, str(ARTIST_DIR))

from artist_query_core import ArtistQueryEngine


ENGINE = ArtistQueryEngine()


def load_historical_artist(name):
    result = ENGINE.query_artist(name)

    return {
        "artist": result.get("artist"),
        "query": result.get("query"),
        "actualPlays": result.get("actualPlays"),
        "actualSkips": result.get("actualSkips"),
        "hoursListened": result.get("hoursListened"),
        "yearsActive": result.get("yearsActive"),
        "firstPlayedDate": result.get("firstPlayedDate"),
        "latestPlayedDate": result.get("latestPlayedDate"),
        "source": result.get("source"),
        "classification": result.get("classification"),
    }


def load_live_artist(name):
    target = name.strip().lower()

    recent_file = WAREHOUSE / "apple_recent_objects.json"
    heavy_file = WAREHOUSE / "apple_heavy_rotation_objects.json"

    recent_rows = []
    heavy_rows = []

    if recent_file.exists():
        recent = json.loads(recent_file.read_text(encoding="utf-8"))
        recent_rows = recent.get("rows", [])

    if heavy_file.exists():
        heavy = json.loads(heavy_file.read_text(encoding="utf-8"))
        heavy_rows = heavy.get("rows", [])

    recent_matches = [
        row for row in recent_rows
        if str(row.get("artistName") or "").strip().lower() == target
    ]

    heavy_matches = [
        row for row in heavy_rows
        if str(row.get("artistName") or "").strip().lower() == target
    ]

    return {
        "recentObjectCount": len(recent_matches),
        "heavyRotationCount": len(heavy_matches),
        "recentObjects": [
            {
                "objectType": row.get("objectType"),
                "name": row.get("name"),
                "rank": row.get("rank"),
                "source": row.get("source"),
                "capturedAt": row.get("capturedAt"),
            }
            for row in recent_matches
        ],
        "heavyRotationObjects": [
            {
                "objectType": row.get("objectType"),
                "name": row.get("name"),
                "rank": row.get("rank"),
                "source": row.get("source"),
                "capturedAt": row.get("capturedAt"),
            }
            for row in heavy_matches
        ],
    }


def classify_relationship(historical, live):
    has_historical = bool(historical.get("actualPlays") or historical.get("yearsActive"))
    has_live = bool(live.get("recentObjectCount") or live.get("heavyRotationCount"))

    if has_historical and has_live:
        return "persistent"
    if has_historical and not has_live:
        return "historical-only"
    if not has_historical and has_live:
        return "emerging"
    return "unknown"


def build_bridge_facts(historical, live):
    facts = []

    has_historical = bool(historical.get("actualPlays") or historical.get("yearsActive"))
    has_live = bool(live.get("recentObjectCount") or live.get("heavyRotationCount"))

    if has_historical and has_live:
        facts.append({
            "type": "continuity",
            "statement": "Relationship continues beyond the historical archive.",
            "evidence": ["historical_artist_summary", "live_apple_music_warehouse"],
        })

    if live.get("recentObjectCount", 0) > 1:
        facts.append({
            "type": "recent_activity",
            "statement": "Multiple recent listening objects detected.",
            "value": live.get("recentObjectCount"),
            "evidence": ["apple_recent_objects"],
        })

    if live.get("heavyRotationCount", 0) > 0:
        facts.append({
            "type": "heavy_rotation",
            "statement": "Artist currently appears in heavy rotation.",
            "value": live.get("heavyRotationCount"),
            "evidence": ["apple_heavy_rotation_objects"],
        })

    return facts


def bridge_artist(name):
    historical = load_historical_artist(name)
    live = load_live_artist(name)

    return {
        "artist": name,
        "historical": historical,
        "live": live,
        "relationshipState": classify_relationship(historical, live),
        "facts": build_bridge_facts(historical, live),
    }


if __name__ == "__main__":
    artist = " ".join(sys.argv[1:]).strip() or "Matt Pond PA"
    print(json.dumps(bridge_artist(artist), indent=2, ensure_ascii=False))
