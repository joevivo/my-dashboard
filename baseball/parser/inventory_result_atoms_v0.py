from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
import json
from typing import Any


MODIFIER_DIR = Path("data/baseball/parsed/strat365/1980/result-modifiers")
OUTPUT_PATH = Path("data/baseball/parsed/strat365/1980/result_atom_inventory_v0.json")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig", errors="replace"))


def marker_key(markers: list[str]) -> str:
    if not markers:
        return "(none)"
    return "".join(markers)


def atom_key(
    normalized_label: str | None,
    range_kind: str | None,
    entry_markers: list[str],
    outcome_markers: list[str],
) -> str:
    return "|".join(
        [
            normalized_label or "(missing)",
            range_kind or "(missing)",
            marker_key(entry_markers),
            marker_key(outcome_markers),
        ]
    )


def main() -> None:
    paths = sorted(MODIFIER_DIR.glob("*.result-modifiers.json"))

    total_entries = 0
    total_outcome_rows = 0

    atom_counts: Counter[str] = Counter()
    atom_by_role: dict[str, Counter[str]] = defaultdict(Counter)
    atom_by_normalized_label: dict[str, Counter[str]] = defaultdict(Counter)
    atom_examples: dict[str, list[dict[str, Any]]] = defaultdict(list)

    range_kind_counts: Counter[str] = Counter()
    normalized_label_counts: Counter[str] = Counter()

    for path in paths:
        data = read_json(path)
        player = data.get("player", {})
        role = data.get("role")

        for table in data.get("tables", []):
            for entry in table.get("entries", []):
                total_entries += 1

                token_evidence = entry.get("entryTokenEvidence", {})
                entry_markers = token_evidence.get("entryTokenMarkers", [])

                for outcome in entry.get("outcomes", []):
                    total_outcome_rows += 1

                    normalized_label = outcome.get("normalized", {}).get("normalizedLabel")
                    range_kind = outcome.get("splitRange", {}).get("rangeKind")
                    outcome_markers = outcome.get("outcomeLabelMarkers", [])

                    key = atom_key(
                        normalized_label,
                        range_kind,
                        entry_markers,
                        outcome_markers,
                    )

                    atom_counts[key] += 1
                    atom_by_role[role][key] += 1
                    atom_by_normalized_label[normalized_label][key] += 1
                    normalized_label_counts[normalized_label] += 1
                    range_kind_counts[range_kind] += 1

                    if len(atom_examples[key]) < 5:
                        atom_examples[key].append(
                            {
                                "playerId": player.get("playerId"),
                                "playerName": player.get("playerName"),
                                "role": role,
                                "tableNumber": table.get("tableNumber"),
                                "side": table.get("side"),
                                "diceRoll": entry.get("diceRoll"),
                                "entryTokenEvidence": token_evidence,
                                "rawOutcome": outcome.get("rawOutcome"),
                                "rawLabel": outcome.get("rawLabel"),
                                "normalized": outcome.get("normalized"),
                                "splitRange": outcome.get("splitRange"),
                                "outcomeLabelMarkers": outcome_markers,
                            }
                        )

    result = {
        "resultModifierFiles": len(paths),
        "totalEntries": total_entries,
        "totalOutcomeRows": total_outcome_rows,
        "distinctAtoms": len(atom_counts),
        "rangeKindCounts": dict(range_kind_counts),
        "normalizedLabelCounts": dict(normalized_label_counts),
        "topAtoms": dict(atom_counts.most_common(150)),
        "atomsByRole": {
            role: dict(counter.most_common(150))
            for role, counter in sorted(atom_by_role.items())
        },
        "atomsByNormalizedLabel": {
            label: dict(counter.most_common(100))
            for label, counter in sorted(atom_by_normalized_label.items())
        },
        "atomExamples": {
            key: examples
            for key, examples in atom_examples.items()
        },
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(result, indent=2), encoding="utf-8")

    print("BIE Result Atom Inventory v0")
    print("=" * 72)
    print(f"Result-modifier files: {len(paths)}")
    print(f"Total entries: {total_entries}")
    print(f"Total outcome rows: {total_outcome_rows}")
    print(f"Distinct atoms: {len(atom_counts)}")
    print()
    print("Range kind counts:")
    for key, count in range_kind_counts.most_common():
        print(f"  {key}: {count}")
    print()
    print("Top atoms:")
    for key, count in atom_counts.most_common(40):
        print(f"  {key}: {count}")
    print()
    print(f"Wrote: {OUTPUT_PATH}")
    print("=" * 72)

    if total_entries != 47586 or total_outcome_rows != 54748:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
