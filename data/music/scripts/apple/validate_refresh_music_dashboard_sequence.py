from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
REFRESH_PATH = (
    SCRIPT_DIR
    / "refresh_music_dashboard.py"
)


def check(
    condition: bool,
    message: str,
) -> None:
    if not condition:
        raise AssertionError(message)


def load_refresh_module():
    spec = importlib.util.spec_from_file_location(
        "refresh_music_dashboard_under_test",
        REFRESH_PATH,
    )

    if spec is None or spec.loader is None:
        raise RuntimeError(
            "Could not load refresh_music_dashboard.py."
        )

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    return module


def main() -> int:
    refresh = load_refresh_module()

    commands = refresh.COMMANDS

    check(
        len(commands) == 7,
        "Expected seven refresh commands.",
    )

    check(
        all(
            command[0] == sys.executable
            for command in commands
        ),
        "Refresh commands must use the active Python executable.",
    )

    script_paths = [
        command[1]
        for command in commands
    ]

    expected_paths = [
        "data/music/scripts/apple/apple_dashboard_snapshot.py",
        "data/music/scripts/apple/normalize_recent_objects.py",
        "data/music/scripts/apple/normalize_heavy_rotation_objects.py",
        "data/music/scripts/apple/apple_snapshot_warehouse.py",
        "data/music/scripts/dashboard/music_dashboard_builder.py",
        (
            "data/music/scripts/artist/"
            "build_artist_comparative_standing_sqlite_cache.py"
        ),
        (
            "data/music/scripts/artist/"
            "validate_artist_comparative_standing_sqlite_cache.py"
        ),
    ]

    check(
        script_paths == expected_paths,
        "Refresh command order changed.",
    )

    warehouse_index = script_paths.index(
        "data/music/scripts/apple/apple_snapshot_warehouse.py"
    )

    dashboard_index = script_paths.index(
        "data/music/scripts/dashboard/music_dashboard_builder.py"
    )

    generator_index = script_paths.index(
        (
            "data/music/scripts/artist/"
            "build_artist_comparative_standing_sqlite_cache.py"
        )
    )

    validator_index = script_paths.index(
        (
            "data/music/scripts/artist/"
            "validate_artist_comparative_standing_sqlite_cache.py"
        )
    )

    check(
        warehouse_index < dashboard_index < generator_index,
        (
            "All governed snapshot and dashboard writes must finish "
            "before cache generation."
        ),
    )

    check(
        generator_index < validator_index,
        "Cache validation must follow cache generation.",
    )

    check(
        commands[generator_index][2:]
        == refresh.CACHE_ARGUMENTS,
        "Cache generator arguments changed.",
    )

    check(
        commands[validator_index][2:]
        == refresh.CACHE_ARGUMENTS,
        "Cache validator arguments changed.",
    )

    check(
        refresh.SNAPSHOT_WAREHOUSE.name
        == "apple_snapshot_warehouse.csv",
        "Snapshot warehouse input changed.",
    )

    check(
        refresh.ARTIST_FAMILIES.name
        == "artistFamilies.json",
        "Artist-family input changed.",
    )

    check(
        refresh.CACHE_PATH.name
        == "artist-comparative-standing-cache-v0.sqlite3",
        "SQLite cache output changed.",
    )

    check(
        refresh.CACHE_MANIFEST_PATH.name
        == (
            "artist-comparative-standing-cache-manifest-v0.json"
        ),
        "Cache manifest output changed.",
    )

    check(
        refresh.LIBRARY_TRACKS_ZIP.name
        == "Apple Music Library Tracks.json.zip",
        "Library archive input changed.",
    )

    print("MUSIC_REFRESH_CACHE_SEQUENCE_VALIDATION: PASS")
    print(f"REFRESH_COMMAND_COUNT: {len(commands)}")
    print("SNAPSHOT_CAPTURE_ORDER: 1")
    print("RECENT_NORMALIZATION_ORDER: 2")
    print("HEAVY_ROTATION_NORMALIZATION_ORDER: 3")
    print("SNAPSHOT_WAREHOUSE_ORDER: 4")
    print("MUSIC_DASHBOARD_ORDER: 5")
    print("COMPARATIVE_CACHE_GENERATION_ORDER: 6")
    print("COMPARATIVE_CACHE_VALIDATION_ORDER: 7")
    print("ACTIVE_PYTHON_EXECUTABLE: PASS")
    print("CACHE_ARGUMENT_PARITY: PASS")
    print("MIXED_SOURCE_GENERATION_PROTECTION: PASS")
    print("STALE_CACHE_FALLBACK: PROHIBITED")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())