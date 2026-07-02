import csv
from collections import defaultdict
from pathlib import Path

WAREHOUSE = Path("data/music/live/apple_snapshot_warehouse.csv")
OUT_MD = Path("data/music/live/apple_snapshot_diff.md")

def key(row):
    return (
        row["source"],
        row["entity_type"],
        row["entity_id"] or row["catalog_or_global_id"] or row["name"],
    )

def label(row):
    if row["artist"]:
        return f'{row["artist"]} — {row["name"]}'
    return row["name"]

rows = list(csv.DictReader(WAREHOUSE.open(encoding="utf-8")))

folders = sorted({row["snapshot_folder"] for row in rows})
if len(folders) < 2:
    OUT_MD.write_text("# Apple Snapshot Diff\n\nNeed at least two snapshots.\n", encoding="utf-8")
    print("Need at least two snapshots.")
    raise SystemExit

prev_folder, curr_folder = folders[-2], folders[-1]

prev = {key(row): row for row in rows if row["snapshot_folder"] == prev_folder}
curr = {key(row): row for row in rows if row["snapshot_folder"] == curr_folder}

entered = [curr[k] for k in curr.keys() - prev.keys()]
left = [prev[k] for k in prev.keys() - curr.keys()]
stayed = [curr[k] for k in curr.keys() & prev.keys()]

def group(items):
    grouped = defaultdict(list)
    for row in items:
        grouped[row["source"]].append(row)
    return grouped

lines = [
    "# Apple Snapshot Diff",
    "",
    f"Previous: `{prev_folder}`",
    f"Current: `{curr_folder}`",
    "",
    f"Stayed: `{len(stayed)}`",
    f"Entered: `{len(entered)}`",
    f"Left: `{len(left)}`",
    "",
]

for title, items in [("Entered", entered), ("Left", left)]:
    lines += [f"## {title}", ""]
    grouped = group(items)
    if not grouped:
        lines.append("None.")
        lines.append("")
        continue
    for source in sorted(grouped):
        lines.append(f"### {source}")
        for row in grouped[source]:
            lines.append(f'- {row["entity_type"]}: {label(row)}')
        lines.append("")

OUT_MD.write_text("\n".join(lines), encoding="utf-8")
print(f"Saved {OUT_MD}")
print(OUT_MD.read_text(encoding="utf-8"))
