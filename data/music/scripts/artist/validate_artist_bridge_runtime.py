from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys


ARTIST_DIR = Path(__file__).resolve().parent
SCRIPTS_DIR = ARTIST_DIR.parent
REPO_ROOT = Path(__file__).resolve().parents[4]

sys.path.insert(0, str(ARTIST_DIR))
sys.path.insert(0, str(SCRIPTS_DIR))

from artist_bridge_runtime import (  # noqa: E402
    BRIDGE_PATH,
    build_artist_bridge,
    comparative_standing_from_bridge,
)
from artist_query_core import ArtistQueryEngine  # noqa: E402


assert BRIDGE_PATH.exists()

bridge = build_artist_bridge("Sugar")

assert set(bridge) == {
    "artist",
    "facts",
    "historical",
    "live",
    "relationshipState",
}

assert bridge["relationshipState"] == "persistent"
assert len(bridge["facts"]) == 2

live = bridge["live"]

assert set(live) == {
    "comparativeStanding",
    "heavyRotationCount",
    "heavyRotationObjects",
    "historicalObservationCount",
    "historicalSnapshotCount",
    "historicalUniqueObjectCount",
    "recentObjectCount",
    "recentObjects",
    "snapshotHistory",
}

standing = comparative_standing_from_bridge(bridge)

assert standing is not None
assert standing["schemaVersion"] == (
    "music.artist-comparative-standing.response.v0"
)
assert standing["entityType"] == "artist"

missing_bridge = build_artist_bridge(
    "Intentionally Missing Artist"
)

assert missing_bridge["relationshipState"] == "unknown"
assert missing_bridge["facts"] == []

engine = ArtistQueryEngine()
legacy = engine.query_artist("Sugar")

environment = os.environ.copy()
environment["PYTHONIOENCODING"] = "utf-8"
environment["PYTHONUTF8"] = "1"

output = subprocess.check_output(
    [
        sys.executable,
        "-B",
        "data/music/scripts/artist_query_summary.py",
        "Sugar",
    ],
    cwd=REPO_ROOT,
    env=environment,
)

integrated = json.loads(output.decode("utf-8"))
canonical = integrated["canonicalArtistSummary"]

assert len(legacy) == 26
assert len(integrated) == 27

for key, value in legacy.items():
    assert integrated[key] == value
    assert canonical["compatibility"][key] == value

assert canonical["compatibility"]["bridge"] == bridge
assert canonical["comparativeStanding"] == standing

recent_apple = canonical["summary"]["recentApple"]

assert (
    recent_apple["current"]["objects"]["recent"]
    == live["recentObjects"]
)

assert (
    recent_apple["current"]["objects"]["heavyRotation"]
    == live["heavyRotationObjects"]
)

snapshot_history = live["snapshotHistory"]

assert (
    recent_apple["historicalSnapshots"]["topObjects"]
    == snapshot_history["topObjects"]
)

coverage_source_ids = {
    row["sourceId"]
    for row in canonical["coverage"]
}

assert "apple_recent_objects" in coverage_source_ids
assert "apple_snapshot_warehouse" in coverage_source_ids
assert "artist_comparative_standing" in coverage_source_ids

assert canonical["family"]["status"] == "available"
assert canonical["family"]["familyName"] == "Bob Mould Family"

print("ARTIST_BRIDGE_FIXTURES: 6/6")
print("BRIDGE_DIRECT_IMPORT: PASS")
print("BRIDGE_RELATIONSHIP_PARITY: PASS")
print("RECENT_APPLE_CANONICAL_PROJECTION: PASS")
print("COMPARATIVE_STANDING_CANONICAL_PROJECTION: PASS")
print("CANONICAL_BRIDGE_COMPATIBILITY: PASS")
print("CLI_LEGACY_FIELD_EQUALITY: 26/26")
print("CLI_CANONICAL_BRIDGE_INTEGRATION: PASS")
print("VALIDATION_PASS")
