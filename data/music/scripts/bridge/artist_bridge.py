import csv
import json
import sys
from collections import Counter
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
SCRIPTS_DIR = SCRIPT_DIR.parent
ARTIST_DIR = SCRIPTS_DIR / "artist"
WAREHOUSE = Path("data/music/live/warehouse")
SNAPSHOT_WAREHOUSE = Path(
    "data/music/live/apple_snapshot_warehouse.csv"
)

if str(ARTIST_DIR) not in sys.path:
    sys.path.insert(0, str(ARTIST_DIR))

from artist_query_core import ArtistQueryEngine, canonical_key


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

    snapshot_history = load_snapshot_history_artist(name)

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
        "snapshotHistory": snapshot_history,
        "historicalObservationCount": (
            snapshot_history.get("observationCount", 0)
        ),
        "historicalSnapshotCount": (
            snapshot_history.get("snapshotCount", 0)
        ),
        "historicalUniqueObjectCount": (
            snapshot_history.get("uniqueObjectCount", 0)
        ),
    }


def load_snapshot_history_artist(name):
    target = canonical_key(name)

    empty_result = {
        "status": "unavailable",
        "observationCount": 0,
        "snapshotCount": 0,
        "uniqueObjectCount": 0,
        "firstObservedAt": None,
        "latestObservedAt": None,
        "topObjects": [],
        "source": "apple_snapshot_warehouse",
    }

    if not SNAPSHOT_WAREHOUSE.exists():
        return empty_result

    matches = []

    with SNAPSHOT_WAREHOUSE.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as handle:
        for row in csv.DictReader(handle):
            artist = str(row.get("artist") or "").strip()

            if not artist:
                continue

            if canonical_key(artist) != target:
                continue

            matches.append(row)

    if not matches:
        return {
            **empty_result,
            "status": "searched_no_evidence",
        }

    snapshot_folders = {
        str(row.get("snapshot_folder") or "").strip()
        for row in matches
        if str(row.get("snapshot_folder") or "").strip()
    }

    # Count logical observed objects by type and display name.
    # Catalog IDs can vary across snapshots for the same Apple object.
    object_keys = {
        (
            str(row.get("entity_type") or "").strip(),
            str(row.get("name") or "").strip(),
        )
        for row in matches
        if str(row.get("name") or "").strip()
    }

    object_counts = Counter(
        (
            str(row.get("entity_type") or "").strip(),
            str(row.get("name") or "").strip(),
        )
        for row in matches
        if str(row.get("name") or "").strip()
    )

    snapshot_times = sorted(
        {
            str(row.get("snapshot_time") or "").strip()
            for row in matches
            if str(row.get("snapshot_time") or "").strip()
        }
    )

    top_objects = [
        {
            "entityType": key[0] or None,
            "name": key[1],
            "observationCount": count,
        }
        for key, count in object_counts.most_common(10)
    ]

    return {
        "status": "searched_with_evidence",
        "observationCount": len(matches),
        "snapshotCount": len(snapshot_folders),
        "uniqueObjectCount": len(object_keys),
        "firstObservedAt": (
            snapshot_times[0]
            if snapshot_times
            else None
        ),
        "latestObservedAt": (
            snapshot_times[-1]
            if snapshot_times
            else None
        ),
        "topObjects": top_objects,
        "source": "apple_snapshot_warehouse",
    }


def classify_relationship(historical, live):
    has_historical = bool(historical.get("actualPlays") or historical.get("yearsActive"))
    has_live = bool(
        live.get("recentObjectCount")
        or live.get("heavyRotationCount")
        or live.get("historicalObservationCount")
    )

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
    has_live = bool(
        live.get("recentObjectCount")
        or live.get("heavyRotationCount")
        or live.get("historicalObservationCount")
    )

    if has_historical and has_live:
        facts.append({
            "type": "continuity",
            "statement": "Recent Apple evidence exists beyond the latest historical archive coverage.",
            "evidence": ["historical_artist_summary", "live_apple_music_warehouse"],
        })


    if live.get("heavyRotationCount", 0) > 0:
        facts.append({
            "type": "heavy_rotation",
            "statement": "The artist appears in the current Apple Heavy Rotation source objects.",
            "value": live.get("heavyRotationCount"),
            "evidence": ["apple_heavy_rotation_objects"],
        })

    historical_observations = live.get(
        "historicalObservationCount",
        0,
    )

    if historical_observations > 0:
        facts.append({
            "type": "recent_apple_snapshot_history",
            "statement": (
                f"{historical_observations} Recent Apple "
                "snapshot observations were found for this artist."
            ),
            "value": historical_observations,
            "evidence": ["apple_snapshot_warehouse"],
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
