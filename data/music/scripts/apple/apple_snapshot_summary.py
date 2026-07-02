import json
from collections import Counter
from pathlib import Path

LIVE_DIR = Path("data/music/live")
OUT_FILE = LIVE_DIR / "apple_snapshot_summary.md"

FILES = [
    ("Library Albums", "apple_library_albums.json"),
    ("Library Playlists", "apple_library_playlists.json"),
    ("Recently Played", "apple_recent_played.json"),
    ("Heavy Rotation", "apple_heavy_rotation.json"),
]

def item_name(item):
    attrs = item.get("attributes", {})
    artist = attrs.get("artistName")
    name = attrs.get("name", "(no name)")
    if artist:
        return f"{artist} — {name}"
    return name

lines = ["# Apple Snapshot Summary", ""]

manifest_path = LIVE_DIR / "apple_snapshot_manifest.json"
if manifest_path.exists():
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    lines += [f"Captured At: `{manifest.get('capturedAt')}`", ""]

for title, filename in FILES:
    path = LIVE_DIR / filename
    lines += [f"## {title}", ""]

    if not path.exists():
        lines += ["Missing file.", ""]
        continue

    payload = json.loads(path.read_text(encoding="utf-8"))
    response = payload.get("response") or {}
    items = response.get("data") or []

    type_counts = Counter(item.get("type", "unknown") for item in items)

    lines += [
        f"Status: `{payload.get('status')}`",
        f"Items: `{len(items)}`",
        "",
        "Types:",
    ]

    for item_type, count in type_counts.most_common():
        lines.append(f"- {item_type}: {count}")

    lines += ["", "First Items:"]

    for item in items[:10]:
        lines.append(f"- {item.get('type')} | {item_name(item)}")

    lines.append("")

OUT_FILE.write_text("\n".join(lines), encoding="utf-8")
print(f"Saved {OUT_FILE}")
print(OUT_FILE.read_text(encoding="utf-8"))
