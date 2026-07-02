import json
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from apple.apple_object_normalizer import normalize_apple_object
from warehouse.warehouse_writer import write_warehouse_dataset

SNAPSHOT_ID = "2026-06-24_231929Z"
SOURCE = Path(f"data/music/live/history/{SNAPSHOT_ID}/apple_recent_played.json")

data = json.loads(SOURCE.read_text(encoding="utf-8"))
items = data.get("response", {}).get("data", [])

rows = [
    normalize_apple_object(
        item,
        snapshot_id=SNAPSHOT_ID,
        captured_at=data.get("capturedAt"),
        rank=index,
        source="apple_music_recent_played",
    )
    for index, item in enumerate(items, start=1)
]

out_file = write_warehouse_dataset(
    "apple_recent_objects",
    rows,
    snapshot_id=SNAPSHOT_ID,
    source="apple_music_recent_played",
    generated_at=data.get("capturedAt"),
)

print(f"Wrote {len(rows)} rows to {out_file}")
