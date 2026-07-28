from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]

COMPONENT_PATH = (
    REPO_ROOT
    / "src"
    / "music"
    / "components"
    / "MusicTimeMachine.jsx"
)

APP_PATH = REPO_ROOT / "src" / "App.jsx"
MUSIC_LIBRARY_PATH = REPO_ROOT / "src" / "MusicLibrary.jsx"

PERIOD_SCRIPT = (
    REPO_ROOT
    / "data"
    / "music"
    / "scripts"
    / "period_intelligence.py"
)


def check(
    condition: bool,
    message: str,
) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    source = COMPONENT_PATH.read_text(
        encoding="utf-8"
    )

    app_source = APP_PATH.read_text(
        encoding="utf-8"
    )

    music_library_source = MUSIC_LIBRARY_PATH.read_text(
        encoding="utf-8"
    )

    required_fragments = (
        "/api/music/query/period",
        "rangeRead?.summary",
        "rangeRead?.period",
        "rangeRead?.coverage",
        "rangeRead?.activity",
        "rangeRead?.libraryEvidence",
        "rangeRead?.recentAppleObservations",
        "rangeRead?.confidence",
        "libraryEvidence.artistJourneys",
        "libraryEvidence.memoryRead",
        "activity.topArtists",
        "activity.topAlbums",
        "activity.topTracks",
        "libraryEvidence.topArtists",
        "libraryEvidence.topAlbums",
        "recentApple.artists",
        "recentApple.albums",
        "Library Evidence records, not Actual Plays",
        "Recent Apple Objects are observations",
    )

    prohibited_fragments = (
        "/api/music/time-machine",
        "rangeRead.topAlbums",
        "rangeRead.topArtists",
        "rangeRead.tracksMatched",
        "rangeRead.artistJourneys",
        "rangeRead.memoryRead",
        "rangeRead.legacy",
        "getArtistJourneyType",
        "month.label",
        "month.headline",
        "month.context",
        "month.totalPlays",
        "musicTimeMachineMonthOptions",
        "historicalMoments",
        "Historical Moments",
        "FeaturedMemoryCard",
        "JSON.stringify",
        "<pre",
    )

    for fragment in required_fragments:
        check(
            fragment in source,
            f"Required structured UI fragment is missing: {fragment}",
        )

    for fragment in prohibited_fragments:
        check(
            fragment not in source,
            f"Prohibited legacy or inferred fragment remains: {fragment}",
        )

    check(
        "journeyType: selectedJourney.status" in source,
        "Artist dossier compatibility must use backend status.",
    )

    check(
        "value === null || value === undefined" in source,
        "Unavailable values must remain distinct from zero.",
    )

    for status in (
        "searched_no_evidence",
        "not_searched",
        "unavailable",
        "stale",
        "unsupported_for_period",
    ):
        check(
            status in source,
            f"Coverage state is not represented: {status}",
        )

    navigation_requirements = (
        'import MusicTimeMachine from "./music/components/MusicTimeMachine";',
        '["Music", "Music Library"]',
        '["MusicTimeMachine", "Music Time Machine"]',
        'setActiveView("MusicTimeMachine")',
        'activeView === "MusicTimeMachine"',
        "<MusicTimeMachine />",
        "Investigate listening evidence across a selected period.",
    )

    for fragment in navigation_requirements:
        check(
            fragment in app_source,
            f"Time Machine navigation seam is missing: {fragment}",
        )

    check(
        app_source.count(
            'import MusicTimeMachine from "./music/components/MusicTimeMachine";'
        )
        == 1,
        "MusicTimeMachine must have exactly one App import.",
    )

    check(
        app_source.count("<MusicTimeMachine />") == 1,
        "MusicTimeMachine must have exactly one application mount.",
    )

    check(
        'import MusicTimeMachine from "./music/components/MusicTimeMachine";'
        not in music_library_source,
        "MusicLibrary retained an unused MusicTimeMachine import.",
    )

    result = subprocess.run(
        [
            sys.executable,
            str(PERIOD_SCRIPT),
            "2020-03-01",
            "2020-04-30",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )

    check(
        result.returncode == 0,
        (
            "Period Intelligence probe failed: "
            f"{result.stderr.strip()}"
        ),
    )

    payload = json.loads(result.stdout)

    required_top_level = (
        "schemaVersion",
        "period",
        "summary",
        "coverage",
        "activity",
        "libraryEvidence",
        "recentAppleObservations",
        "confidence",
    )

    for field in required_top_level:
        check(
            field in payload,
            f"Live Period Intelligence response is missing {field}.",
        )

    check(
        payload["schemaVersion"]
        == "music.period-intelligence.v1",
        "Unexpected Period Intelligence schema version.",
    )

    check(
        isinstance(payload["coverage"], list),
        "Coverage must be an array.",
    )

    print("MUSIC_TIME_MACHINE_STRUCTURED_UI_VALIDATION: PASS")
    print("CANONICAL_PERIOD_ROUTE: PASS")
    print("STRUCTURED_V1_FIELDS: PASS")
    print("LEGACY_FLAT_FIELD_REFERENCES: 0")
    print("FRONTEND_RELATIONSHIP_CLASSIFICATIONS: 0")
    print("UNDEFINED_CURATED_MONTH_REFERENCES: 0")
    print("HISTORICAL_MOMENTS_REMOVED: PASS")
    print("DEDICATED_NAVIGATION_DESTINATION: PASS")
    print("APPLICATION_IMPORT_COUNT: 1")
    print("APPLICATION_MOUNT_COUNT: 1")
    print("MUSIC_LIBRARY_UNUSED_IMPORT_REMOVED: PASS")
    print("UNAVAILABLE_ZERO_DISTINCTION: PASS")
    print("COVERAGE_ZERO_STATES: PASS")
    print("ACTUAL_LISTENING_LIBRARY_SEPARATION: PASS")
    print("RECENT_APPLE_PLAY_LABELING_PROHIBITED: PASS")
    print("LIVE_PERIOD_RESPONSE_PROBE: PASS")
    print(
        "LIVE_PERIOD_SCHEMA_VERSION: "
        f"{payload['schemaVersion']}"
    )
    print(
        "LIVE_PERIOD_COVERAGE_ENTRY_COUNT: "
        f"{len(payload['coverage'])}"
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())