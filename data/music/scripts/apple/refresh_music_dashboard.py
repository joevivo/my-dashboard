import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[4]

COMMANDS = [
    ["python", "data/music/scripts/apple/apple_dashboard_snapshot.py"],
    ["python", "data/music/scripts/apple/normalize_recent_objects.py"],
    ["python", "data/music/scripts/apple/normalize_heavy_rotation_objects.py"],
    ["python", "data/music/scripts/dashboard/music_dashboard_builder.py"],
]


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
    print("# Refreshing Music dashboard live data")
    print(f"# Repo root: {REPO_ROOT}")

    for command in COMMANDS:
        run_command(command)

    print("")
    print("# Music dashboard refresh complete")


if __name__ == "__main__":
    main()
