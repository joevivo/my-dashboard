from __future__ import annotations

import sys
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
BRIDGE_DIR = SCRIPT_DIR.parent / "bridge"

if str(BRIDGE_DIR) not in sys.path:
    sys.path.append(str(BRIDGE_DIR))

from artist_comparative_standing_runtime import (
    load_default_artist_comparative_standing,
)
from artist_bridge import load_live_artist


assertion_count = 0


def check(condition: bool, message: str) -> None:
    global assertion_count
    assertion_count += 1

    if not condition:
        raise AssertionError(message)


def metric_map(
    response: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    return {
        metric["metricKey"]: metric
        for metric in response["metrics"]
    }


rem = load_default_artist_comparative_standing(
    "R.E.M."
)
u2 = load_default_artist_comparative_standing(
    "U2"
)
beatles = load_default_artist_comparative_standing(
    "The Beatles"
)
missing = load_default_artist_comparative_standing(
    "Comparative Standing Missing Artist Fixture"
)
unresolved = load_default_artist_comparative_standing(
    ""
)

check(
    rem["schemaVersion"]
    == "music.artist-comparative-standing.response.v0",
    "Unexpected response schema version.",
)

check(
    rem["entityType"] == "artist",
    "Response entity type changed.",
)

check(
    rem["canonicalKey"] == "rem",
    "R.E.M. canonicalKey changed.",
)

check(
    rem["displayName"] == "R.E.M.",
    "R.E.M. displayName changed.",
)

check(
    rem["status"] == "available",
    "R.E.M. response must be available.",
)

for response in (
    rem,
    u2,
    beatles,
    missing,
):
    check(
        len(response["metrics"]) == 6,
        "Every resolved response must contain six metrics.",
    )

rem_metrics = metric_map(rem)
u2_metrics = metric_map(u2)
beatles_metrics = metric_map(beatles)
missing_metrics = metric_map(missing)

check(
    rem_metrics["library_evidence_records"]["value"]
    == 323,
    "R.E.M. Library Evidence value changed.",
)

check(
    rem_metrics["library_evidence_records"]["rank"]
    == 4,
    "R.E.M. Library Evidence rank changed.",
)

check(
    rem_metrics["historical_years_represented"]["value"]
    == 14,
    "R.E.M. Years Represented value changed.",
)

check(
    rem_metrics["historical_years_represented"]["rank"]
    == 1,
    "R.E.M. Years Represented rank changed.",
)

check(
    u2_metrics["library_evidence_records"]["value"]
    == 100,
    "U2 Library Evidence value changed.",
)

check(
    u2_metrics["library_evidence_records"]["rank"]
    == 52,
    "U2 Library Evidence rank changed.",
)

check(
    beatles_metrics[
        "historical_unique_object_count"
    ]["value"]
    == 35,
    "The Beatles unique-object value changed.",
)

check(
    beatles_metrics[
        "historical_unique_object_count"
    ]["rank"]
    == 5,
    "The Beatles unique-object rank changed.",
)

for metric_key in (
    "actual_plays",
    "listening_duration_ms",
):
    metric = rem_metrics[metric_key]

    check(
        metric["status"] == "unavailable",
        f"{metric_key} must remain unavailable.",
    )

    check(
        metric["value"] is None,
        f"{metric_key} value must remain null.",
    )

    check(
        metric["rank"] is None,
        f"{metric_key} rank must remain null.",
    )

    check(
        metric["percentile"] is None,
        f"{metric_key} percentile must remain null.",
    )

for metric_key in (
    "library_evidence_records",
    "historical_years_represented",
    "recent_apple_observations",
    "historical_unique_object_count",
):
    metric = missing_metrics[metric_key]

    check(
        metric["status"] == "searched_no_evidence",
        f"Missing artist status changed: {metric_key}",
    )

    check(
        metric["value"] is None,
        f"Missing artist value became false zero: {metric_key}",
    )

    check(
        metric["rank"] is None,
        f"Missing artist rank must be null: {metric_key}",
    )

check(
    missing["status"] == "searched_no_evidence",
    "Missing artist response status changed.",
)

check(
    unresolved["status"] == "identity_unresolved",
    "Blank artist must be identity_unresolved.",
)

check(
    unresolved["canonicalKey"] is None,
    "Blank artist canonicalKey must be null.",
)

check(
    unresolved["metrics"] == [],
    "Blank artist must not enter metric populations.",
)

bridge_live = load_live_artist("R.E.M.")

check(
    "comparativeStanding" in bridge_live,
    "Bridge live response lacks Comparative Standing.",
)

bridge_response = bridge_live["comparativeStanding"]
bridge_metrics = metric_map(bridge_response)

check(
    bridge_response["canonicalKey"] == "rem",
    "Bridge canonicalKey changed.",
)

check(
    bridge_metrics["library_evidence_records"]["rank"]
    == 4,
    "Bridge recalculated or lost the governed rank.",
)

check(
    bridge_metrics["recent_apple_observations"]["value"]
    == 114,
    "Bridge recent-observation value changed.",
)

check(
    all(
        metric["entityType"] == "artist"
        for metric in bridge_response["metrics"]
    ),
    "Family population entered the artist response.",
)

print("COMPARATIVE_STANDING_RESPONSE_VALIDATION: PASS")
print(f"VALIDATION_ASSERTION_COUNT: {assertion_count}")
print("RESPONSE_SCHEMA_VERSION: music.artist-comparative-standing.response.v0")
print("BRIDGE_RESPONSE_KEY: comparativeStanding")
print("BRIDGE_SELECTION_ONLY: PASS")
print("BRIDGE_RANK_RECALCULATION: NONE")
print("SUPPORTED_METRIC_COUNT: 4")
print("UNAVAILABLE_METRIC_COUNT: 2")
print("MISSING_ARTIST_FALSE_ZERO: PROHIBITED")
print("ARTIST_FAMILY_POPULATION_SEPARATION: PASS")
print(
    "PROBE_REM_LIBRARY_RANK: "
    f"{rem_metrics['library_evidence_records']['rank']}"
)
print(
    "PROBE_REM_YEARS_RANK: "
    f"{rem_metrics['historical_years_represented']['rank']}"
)
print(
    "PROBE_U2_LIBRARY_RANK: "
    f"{u2_metrics['library_evidence_records']['rank']}"
)
print(
    "PROBE_BEATLES_UNIQUE_OBJECT_RANK: "
    f"{beatles_metrics['historical_unique_object_count']['rank']}"
)