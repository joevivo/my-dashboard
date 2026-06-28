from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
import json
import re
from typing import Any


SPLIT_RANGE_DIR = Path("data/baseball/parsed/strat365/1980/split-ranges")
OUTPUT_PATH = Path("data/baseball/parsed/strat365/1980/result_modifier_inventory_v0.json")


ENTRY_TOKEN_MARKERS = ["#", ">", "$", "@"]
OUTCOME_LABEL_MARKERS = ["**", "*", "+", "?"]


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig", errors="replace"))


def first_row_token(raw_rows: list[dict[str, Any]]) -> str | None:
    if not raw_rows:
        return None

    cells = raw_rows[0].get("cells", [])
    if not cells:
        return None

    token = cells[0]
    if token is None:
        return None

    return str(token).strip()


def classify_entry_token_markers(token: str | None) -> list[str]:
    if not token:
        return []

    markers: list[str] = []
    for marker in ENTRY_TOKEN_MARKERS:
        if marker in token:
            markers.append(marker)

    return markers


def classify_outcome_label_markers(raw_label: str | None) -> list[str]:
    if raw_label is None:
        return []

    markers: list[str] = []

    if "**" in raw_label:
        markers.append("**")
    elif "*" in raw_label:
        markers.append("*")

    if "+" in raw_label:
        markers.append("+")

    if "?" in raw_label:
        markers.append("?")

    return markers


def main() -> None:
    paths = sorted(SPLIT_RANGE_DIR.glob("*.split-ranges.json"))

    total_entries = 0
    total_outcome_rows = 0

    entries_with_entry_markers = 0
    outcome_rows_with_label_markers = 0

    entry_token_counts: Counter[str] = Counter()
    entry_token_marker_counts: Counter[str] = Counter()
    entry_marker_by_role: dict[str, Counter[str]] = defaultdict(Counter)
    entry_marker_by_normalized_label: dict[str, Counter[str]] = defaultdict(Counter)

    outcome_label_marker_counts: Counter[str] = Counter()
    outcome_label_marker_by_normalized_label: dict[str, Counter[str]] = defaultdict(Counter)

    raw_label_counts: Counter[str] = Counter()
    raw_label_by_normalized_label: dict[str, Counter[str]] = defaultdict(Counter)

    entry_examples_by_marker: dict[str, list[dict[str, Any]]] = defaultdict(list)
    outcome_examples_by_marker: dict[str, list[dict[str, Any]]] = defaultdict(list)

    malformed_entry_tokens: list[dict[str, Any]] = []

    for path in paths:
        data = read_json(path)
        player = data.get("player", {})
        role = data.get("role")

        for table in data.get("tables", []):
            for entry in table.get("entries", []):
                total_entries += 1

                token = first_row_token(entry.get("rawRows", []))
                entry_token_counts[token] += 1

                if token and not re.match(r"^[#>$@]?\d+-$", token):
                    if len(malformed_entry_tokens) < 25:
                        malformed_entry_tokens.append(
                            {
                                "playerId": player.get("playerId"),
                                "playerName": player.get("playerName"),
                                "role": role,
                                "tableNumber": table.get("tableNumber"),
                                "side": table.get("side"),
                                "diceRoll": entry.get("diceRoll"),
                                "entryToken": token,
                                "rawRows": entry.get("rawRows", []),
                            }
                        )

                entry_markers = classify_entry_token_markers(token)
                if entry_markers:
                    entries_with_entry_markers += 1

                entry_normalized_labels = sorted(
                    set(
                        outcome.get("normalized", {}).get("normalizedLabel")
                        for outcome in entry.get("outcomes", [])
                    )
                )

                for marker in entry_markers:
                    entry_token_marker_counts[marker] += 1
                    entry_marker_by_role[role][marker] += 1

                    for label in entry_normalized_labels:
                        entry_marker_by_normalized_label[label][marker] += 1

                    if len(entry_examples_by_marker[marker]) < 12:
                        entry_examples_by_marker[marker].append(
                            {
                                "playerId": player.get("playerId"),
                                "playerName": player.get("playerName"),
                                "role": role,
                                "tableNumber": table.get("tableNumber"),
                                "side": table.get("side"),
                                "diceRoll": entry.get("diceRoll"),
                                "entryToken": token,
                                "rawRows": entry.get("rawRows", []),
                                "normalizedLabels": entry_normalized_labels,
                            }
                        )

                for outcome in entry.get("outcomes", []):
                    total_outcome_rows += 1

                    raw_label = outcome.get("rawLabel")
                    normalized_label = outcome.get("normalized", {}).get("normalizedLabel")
                    outcome_markers = classify_outcome_label_markers(raw_label)

                    raw_label_counts[raw_label] += 1
                    raw_label_by_normalized_label[normalized_label][raw_label] += 1

                    if outcome_markers:
                        outcome_rows_with_label_markers += 1

                    for marker in outcome_markers:
                        outcome_label_marker_counts[marker] += 1
                        outcome_label_marker_by_normalized_label[normalized_label][marker] += 1

                        if len(outcome_examples_by_marker[marker]) < 12:
                            outcome_examples_by_marker[marker].append(
                                {
                                    "playerId": player.get("playerId"),
                                    "playerName": player.get("playerName"),
                                    "role": role,
                                    "tableNumber": table.get("tableNumber"),
                                    "side": table.get("side"),
                                    "diceRoll": entry.get("diceRoll"),
                                    "entryToken": token,
                                    "rawOutcome": outcome.get("rawOutcome"),
                                    "rawLabel": raw_label,
                                    "normalizedLabel": normalized_label,
                                    "rangeText": outcome.get("rangeText"),
                                    "splitRange": outcome.get("splitRange"),
                                }
                            )

    result = {
        "splitRangeFiles": len(paths),
        "totalEntries": total_entries,
        "totalOutcomeRows": total_outcome_rows,
        "entriesWithEntryTokenMarkers": entries_with_entry_markers,
        "outcomeRowsWithLabelMarkers": outcome_rows_with_label_markers,
        "entryTokenMarkerCounts": dict(entry_token_marker_counts),
        "entryMarkerByRole": {
            role: dict(counter)
            for role, counter in sorted(entry_marker_by_role.items())
        },
        "entryMarkerByNormalizedLabel": {
            label: dict(counter)
            for label, counter in sorted(entry_marker_by_normalized_label.items())
        },
        "outcomeLabelMarkerCounts": dict(outcome_label_marker_counts),
        "outcomeLabelMarkerByNormalizedLabel": {
            label: dict(counter)
            for label, counter in sorted(outcome_label_marker_by_normalized_label.items())
        },
        "topEntryTokens": dict(entry_token_counts.most_common(100)),
        "topRawLabels": dict(raw_label_counts.most_common(100)),
        "topRawLabelsByNormalizedLabel": {
            label: dict(counter.most_common(50))
            for label, counter in sorted(raw_label_by_normalized_label.items())
        },
        "entryExamplesByMarker": {
            marker: examples
            for marker, examples in sorted(entry_examples_by_marker.items())
        },
        "outcomeExamplesByMarker": {
            marker: examples
            for marker, examples in sorted(outcome_examples_by_marker.items())
        },
        "malformedEntryTokens": malformed_entry_tokens,
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(result, indent=2), encoding="utf-8")

    print("BIE Result Modifier Inventory v0")
    print("=" * 72)
    print(f"Split-range files: {len(paths)}")
    print(f"Total entries: {total_entries}")
    print(f"Total outcome rows: {total_outcome_rows}")
    print(f"Entries with entry-token markers: {entries_with_entry_markers}")
    print(f"Outcome rows with label markers: {outcome_rows_with_label_markers}")
    print(f"Malformed entry tokens: {len(malformed_entry_tokens)}")
    print()
    print("Entry-token marker counts:")
    for marker, count in entry_token_marker_counts.most_common():
        print(f"  {marker}: {count}")
    print()
    print("Outcome-label marker counts:")
    for marker, count in outcome_label_marker_counts.most_common():
        print(f"  {marker}: {count}")
    print()
    print("Entry-token marker by role:")
    for role in sorted(entry_marker_by_role):
        print(f"  {role}: {dict(entry_marker_by_role[role])}")
    print()
    print("Outcome-label marker by normalized label:")
    for label in sorted(outcome_label_marker_by_normalized_label):
        print(f"  {label}: {dict(outcome_label_marker_by_normalized_label[label])}")
    print()
    print(f"Wrote: {OUTPUT_PATH}")
    print("=" * 72)

    if malformed_entry_tokens:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
