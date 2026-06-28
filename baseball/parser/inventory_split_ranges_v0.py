from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
import json
import re
from typing import Any


NORMALIZED_DIR = Path("data/baseball/parsed/strat365/1980/normalized-result-labels")
OUTPUT_PATH = Path("data/baseball/parsed/strat365/1980/split_range_inventory_v0.json")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig", errors="replace"))


def parse_range(range_text: str | None) -> dict[str, Any]:
    if range_text is None:
        return {"rangeKind": "none"}

    match = re.match(r"^(\d+)-(\d+)$", range_text)
    if match:
        low = int(match.group(1))
        high = int(match.group(2))
        return {
            "rangeKind": "d20_closed",
            "rangeText": range_text,
            "low": low,
            "high": high,
            "width": high - low + 1,
        }

    match = re.match(r"^(\d+)-$", range_text)
    if match:
        low = int(match.group(1))
        return {
            "rangeKind": "d20_open_high",
            "rangeText": range_text,
            "low": low,
            "high": None,
            "width": None,
            "note": "Open-ended range printed this way in authenticated Strat365 HTML; preserved without inference.",
        }

    return {"rangeKind": "unmatched", "rangeText": range_text}


def main() -> None:
    paths = sorted(NORMALIZED_DIR.glob("*.normalized-result-labels.json"))

    total_outcome_rows = 0
    range_kind_counts: Counter[str] = Counter()
    range_counts: Counter[str] = Counter()
    closed_width_counts: Counter[int] = Counter()
    range_by_label: dict[str, Counter[str]] = defaultdict(Counter)
    unmatched_examples: list[dict[str, Any]] = []
    open_high_examples: list[dict[str, Any]] = []

    for path in paths:
        data = read_json(path)
        player = data.get("player", {})
        role = data.get("role")

        for table in data.get("tables", []):
            for entry in table.get("entries", []):
                for outcome in entry.get("normalizedOutcomes", []):
                    total_outcome_rows += 1

                    label = outcome.get("normalized", {}).get("normalizedLabel")
                    range_text = outcome.get("rangeText")
                    parsed = parse_range(range_text)
                    kind = parsed["rangeKind"]

                    range_kind_counts[kind] += 1
                    range_by_label[label][kind] += 1

                    if range_text is not None:
                        range_counts[range_text] += 1

                    if kind == "d20_closed":
                        closed_width_counts[parsed["width"]] += 1

                    if kind == "d20_open_high" and len(open_high_examples) < 25:
                        open_high_examples.append(
                            {
                                "playerId": player.get("playerId"),
                                "playerName": player.get("playerName"),
                                "role": role,
                                "tableNumber": table.get("tableNumber"),
                                "side": table.get("side"),
                                "diceRoll": entry.get("diceRoll"),
                                "rawOutcome": outcome.get("rawOutcome"),
                                "rangeText": range_text,
                                "parsedRange": parsed,
                            }
                        )

                    if kind == "unmatched" and len(unmatched_examples) < 25:
                        unmatched_examples.append(
                            {
                                "playerId": player.get("playerId"),
                                "playerName": player.get("playerName"),
                                "role": role,
                                "tableNumber": table.get("tableNumber"),
                                "side": table.get("side"),
                                "diceRoll": entry.get("diceRoll"),
                                "rawOutcome": outcome.get("rawOutcome"),
                                "rangeText": range_text,
                            }
                        )

    result = {
        "normalizedFiles": len(paths),
        "totalOutcomeRows": total_outcome_rows,
        "rangeKindCounts": dict(range_kind_counts),
        "rangeCounts": dict(range_counts),
        "closedWidthCounts": dict(closed_width_counts),
        "rangeByLabel": {label: dict(counter) for label, counter in range_by_label.items()},
        "openHighExamples": open_high_examples,
        "unmatchedExamples": unmatched_examples,
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(result, indent=2), encoding="utf-8")

    print("BIE Split Range Inventory v0")
    print("=" * 72)
    print(f"Normalized files: {len(paths)}")
    print(f"Total outcome rows: {total_outcome_rows}")
    print(f"No-range rows: {range_kind_counts['none']}")
    print(f"D20 closed range rows: {range_kind_counts['d20_closed']}")
    print(f"D20 open-high range rows: {range_kind_counts['d20_open_high']}")
    print(f"Unmatched range rows: {range_kind_counts['unmatched']}")
    print()
    print("D20 closed width counts:")
    for width, count in sorted(closed_width_counts.items()):
        print(f"  {width}: {count}")
    print()
    print("Top ranges:")
    for range_text, count in range_counts.most_common(25):
        print(f"  {range_text}: {count}")
    print()
    print("Range kind by label:")
    for label in sorted(range_by_label):
        print(f"  {label}: {dict(range_by_label[label])}")
    print()
    print(f"Wrote: {OUTPUT_PATH}")
    print("=" * 72)

    if range_kind_counts["unmatched"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
