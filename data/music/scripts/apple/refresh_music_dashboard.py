import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[4]
PYTHON = sys.executable

LIBRARY_TRACKS_ZIP = (
    Path.home()
    / "Downloads"
    / "apple-music-working"
    / "Apple_Media_Services_python"
    / "Apple_Media_Services"
    / "Apple Music Activity"
    / "Apple Music Library Tracks.json.zip"
)

SNAPSHOT_WAREHOUSE = (
    REPO_ROOT
    / "data"
    / "music"
    / "live"
    / "apple_snapshot_warehouse.csv"
)

ARTIST_FAMILIES = (
    REPO_ROOT
    / "data"
    / "music"
    / "curated"
    / "artistFamilies.json"
)

CACHE_DIRECTORY = (
    REPO_ROOT
    / "data"
    / "music"
    / "generated"
    / "comparative-standing"
)

CACHE_PATH = (
    CACHE_DIRECTORY
    / "artist-comparative-standing-cache-v0.sqlite3"
)

CACHE_MANIFEST_PATH = (
    CACHE_DIRECTORY
    / "artist-comparative-standing-cache-manifest-v0.json"
)

CACHE_ARGUMENTS = [
    str(LIBRARY_TRACKS_ZIP),
    str(SNAPSHOT_WAREHOUSE),
    str(ARTIST_FAMILIES),
    str(CACHE_PATH),
    str(CACHE_MANIFEST_PATH),
]

COMMANDS = [
    [
        PYTHON,
        "data/music/scripts/apple/apple_dashboard_snapshot.py",
    ],
    [
        PYTHON,
        "data/music/scripts/apple/normalize_recent_objects.py",
    ],
    [
        PYTHON,
        "data/music/scripts/apple/normalize_heavy_rotation_objects.py",
    ],
    [
        PYTHON,
        "data/music/scripts/apple/apple_snapshot_warehouse.py",
    ],
    [
        PYTHON,
        "data/music/scripts/dashboard/music_dashboard_builder.py",
    ],
    [
        PYTHON,
        (
            "data/music/scripts/artist/"
            "build_artist_comparative_standing_sqlite_cache.py"
        ),
        *CACHE_ARGUMENTS,
    ],
    [
        PYTHON,
        (
            "data/music/scripts/artist/"
            "validate_artist_comparative_standing_sqlite_cache.py"
        ),
        *CACHE_ARGUMENTS,
    ],
]


def validate_required_inputs() -> None:
    required_paths = (
        LIBRARY_TRACKS_ZIP,
        ARTIST_FAMILIES,
    )

    missing_paths = [
        path
        for path in required_paths
        if not path.exists()
    ]

    if missing_paths:
        formatted = ", ".join(
            str(path)
            for path in missing_paths
        )

        raise SystemExit(
            "Required Music refresh input is missing: "
            f"{formatted}"
        )


def run_command(command):
    print("")
    print(f"# Running: {' '.join(command)}")

    result = subprocess.run(
        command,
        cwd=REPO_ROOT,
        text=True,
    )

    if result.returncode != 0:
        raise SystemExit(result.returncode)


def main():
    print("# Refreshing Music dashboard and governed intelligence")
    print(f"# Repo root: {REPO_ROOT}")

    validate_required_inputs()

    for command in COMMANDS:
        run_command(command)

    print("")
    print("# Music dashboard refresh complete")
    print("# Comparative Standing cache regeneration complete")


if __name__ == "__main__":
    main()