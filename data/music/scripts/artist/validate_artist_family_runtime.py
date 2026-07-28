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

from artist_family_runtime import (  # noqa: E402
    FAMILIES_PATH,
    build_family_metrics,
    canonical_artist_key,
    resolve_artist_family,
)
from artist_query_core import ArtistQueryEngine  # noqa: E402


assert FAMILIES_PATH.exists()
assert canonical_artist_key("Hüsker Dü") == "husker du"
assert canonical_artist_key("The Eagles") == "eagles"
assert canonical_artist_key("Love & Rockets") == "love and rockets"

family = resolve_artist_family("Sugar")

assert family is not None
assert family["familyName"] == "Bob Mould Family"
assert family["primaryArtist"] == "Bob Mould"

synthetic_family = {
    "familyName": "Synthetic Family",
    "primaryArtist": "Primary",
    "members": ["Primary", "The Eagles", "Eagles", "Other"],
}

results = {
    "Primary": {
        "artist": "Primary",
        "actualPlays": 10,
        "actualSkips": 1,
        "hoursListened": 1.25,
        "listeningDurationMs": 1000,
        "libraryEvidenceRecords": 2,
        "firstPlayedDate": "2020-01-01",
        "latestPlayedDate": "2021-01-01",
        "timeline": [{"year": 2020}, {"year": 2021}],
    },
    "The Eagles": {
        "artist": "Eagles",
        "actualPlays": 5,
        "actualSkips": 2,
        "hoursListened": 2.35,
        "listeningDurationMs": 2000,
        "libraryEvidenceRecords": 3,
        "firstPlayedDate": "2019-01-01",
        "latestPlayedDate": "2022-01-01",
        "timeline": [{"year": 2021}, {"year": 2022}],
    },
    "Eagles": {
        "artist": "Eagles",
        "actualPlays": 999,
        "timeline": [{"year": 1999}],
    },
    "Other": {
        "artist": "Other",
        "hoursListened": 0.25,
        "listeningDurationMs": 500,
        "libraryEvidenceRecords": 1,
        "firstPlayedDate": "2023-01-01",
        "latestPlayedDate": "2023-12-01",
        "timeline": [{"year": 2023}],
    },
}

metrics = build_family_metrics(
    synthetic_family,
    results.get,
)

assert metrics is not None
assert metrics["actualPlays"] == 15
assert metrics["actualSkips"] == 3
assert metrics["hoursListened"] == 3.9
assert metrics["listeningDurationMs"] == 3500
assert metrics["libraryEvidenceRecords"] == 6
assert metrics["yearsActive"] == 4
assert metrics["firstPlayedDate"] == "2019-01-01"
assert metrics["latestPlayedDate"] == "2023-12-01"
assert len(metrics["membersMatched"]) == 3
assert metrics["familyAmplificationFactor"] == 1.5

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

assert canonical["family"]["status"] == "available"
assert canonical["family"]["familyName"] == "Bob Mould Family"
assert canonical["family"]["metrics"] is not None
assert canonical["scope"]["familyName"] == "Bob Mould Family"

print("ARTIST_FAMILY_FIXTURES: 5/5")
print("AUTHORITATIVE_FAMILY_SOURCE: PASS")
print("NORMALIZATION_AND_ALIAS_PARITY: PASS")
print("FAMILY_DEDUPLICATION: PASS")
print("FAMILY_METRIC_ROLLUP: PASS")
print("CANONICAL_FAMILY_STATUS_AVAILABLE: PASS")
print("CLI_LEGACY_FIELD_EQUALITY: 26/26")
print("CLI_CANONICAL_FAMILY_INTEGRATION: PASS")
print("VALIDATION_PASS")
