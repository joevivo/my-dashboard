from __future__ import annotations

from collections import Counter
from pathlib import Path
import json
from typing import Any


RESULT_CELLS_DIR = Path("data/baseball/parsed/strat365/1980/result-cells")
OUTPUT_PATH = Path("data/baseball/parsed/strat365/1980/result_outcome_inventory_v0.json")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig", errors="replace"))


def main() -> None:
    paths = sorted(RESULT_CELLS_DIR.glob("*.result-cells.json"))

    role_counts: Counter[str] = Counter()
    side_counts: Counter[str] = Counter()
    raw_label_counts: Counter[str] = Counter()
    modifier_counts: Counter[str] = Counter()
    split_entry_count = 0
    total_entries = 0
    total_outcome_rows = 0

    examples: dict[str, list[dict[str, Any]]] = {}

    for path in paths:
        data = read_json(path)
        role = data.get("role", "unknown")
        player = data.get("player", {})

        role_counts[role] += 1

        for table in data.get("tables", []):
            side = table.get("side", "unknown")
            side_counts[side] += 1

            for entry in table.get("entries", []):
                total_entries += 1

                modifiers = entry.get("rawModifiers", "")
                modifier_counts[modifiers or "(none)"] += 1

                raw_outcomes = entry.get("rawOutcomes", [])
                if len(raw_outcomes) > 1:
                    split_entry_count += 1

                for outcome in raw_outcomes:
                    total_outcome_rows += 1

                    if not outcome:
                        raw_label = "(empty)"
                    else:
                        raw_label = outcome[0] or "(blank)"

                    raw_label_counts[raw_label] += 1

                    if raw_label not in examples:
                        examples[raw_label] = []

                    if len(examples[raw_label]) < 3:
                        examples[raw_label].append(
                            {
                                "playerId": player.get("playerId"),
                                "playerName": player.get("playerName"),
                                "role": role,
                                "side": side,
                                "tableNumber": table.get("tableNumber"),
                                "diceRoll": entry.get("diceRoll"),
                                "rawModifiers": modifiers,
                                "rawOutcome": outcome,
                            }
                        )

    inventory = {
        "resultCellFiles": len(paths),
        "roleCounts": dict(role_counts),
        "sideCounts": dict(side_counts),
        "totalEntries": total_entries,
        "totalOutcomeRows": total_outcome_rows,
        "splitEntryCount": split_entry_count,
        "modifierCounts": dict(modifier_counts),
        "rawLabelCounts": dict(raw_label_counts),
        "topRawLabels": raw_label_counts.most_common(100),
        "examples": examples,
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(inventory, indent=2), encoding="utf-8")

    print("BIE Result Outcome Inventory v0")
    print("=" * 72)
    print(f"Result-cell files: {len(paths)}")
    print(f"Role counts: {dict(role_counts)}")
    print(f"Total entries: {total_entries}")
    print(f"Total outcome rows: {total_outcome_rows}")
    print(f"Split entries: {split_entry_count}")
    print()
    print("Modifiers:")
    for key, value in sorted(modifier_counts.items()):
        print(f"  {key}: {value}")
    print()
    print("Top raw labels:")
    for label, count in raw_label_counts.most_common(40):
        print(f"  {label}: {count}")
    print()
    print(f"Wrote: {OUTPUT_PATH}")
    print("=" * 72)


if __name__ == "__main__":
    main()
