import json
import time
from pathlib import Path

WAREHOUSE_ROOT = Path("data/music/live/warehouse")
SCHEMA_VERSION = 1


def utc_now():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def write_warehouse_dataset(dataset, rows, *, snapshot_id, source, generated_at=None):
    WAREHOUSE_ROOT.mkdir(parents=True, exist_ok=True)

    payload = {
        "dataset": dataset,
        "schemaVersion": SCHEMA_VERSION,
        "generatedAt": generated_at or utc_now(),
        "snapshotId": snapshot_id,
        "source": source,
        "rowCount": len(rows),
        "rows": rows,
    }

    out_file = WAREHOUSE_ROOT / f"{dataset}.json"
    out_file.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    return out_file
