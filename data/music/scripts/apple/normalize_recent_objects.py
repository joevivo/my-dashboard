import json
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from apple.apple_object_normalizer import normalize_apple_object
from warehouse.warehouse_writer import write_warehouse_dataset


HISTORY_ROOT = Path("data/music/live/history")
SOURCE_FILE = "apple_recent_played.json"
WAREHOUSE_DATASET = "apple_recent_objects"
WAREHOUSE_SOURCE = "apple_music_recent_played"


def resolve_snapshot_id():
    if len(sys.argv) > 1 and sys.argv[1].strip():
        return sys.argv[1].strip()

    candidates = [
        path.name
        for path in HISTORY_ROOT.iterdir()
        if path.is_dir() and (path / SOURCE_FILE).exists()
    ]

    if not candidates:
        raise FileNotFoundError(f"No snapshots found with {SOURCE_FILE} under {HISTORY_ROOT}")

    return sorted(candidates)[-1]


def main():
    snapshot_id = resolve_snapshot_id()
    source = HISTORY_ROOT / snapshot_id / SOURCE_FILE

    data = json.loads(source.read_text(encoding="utf-8"))
    items = data.get("response", {}).get("data", [])

    rows = [
        normalize_apple_object(
            item,
            snapshot_id=snapshot_id,
            captured_at=data.get("capturedAt"),
            rank=index,
            source=WAREHOUSE_SOURCE,
        )
        for index, item in enumerate(items, start=1)
    ]

    out_file = write_warehouse_dataset(
        WAREHOUSE_DATASET,
        rows,
        snapshot_id=snapshot_id,
        source=WAREHOUSE_SOURCE,
        generated_at=data.get("capturedAt"),
    )

    print(f"Snapshot: {snapshot_id}")
    print(f"Wrote {len(rows)} rows to {out_file}")


if __name__ == "__main__":
    main()
