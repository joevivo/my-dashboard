from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
import json
import re
from typing import Any


PARSED_DIR = Path("data/baseball/parsed/strat365/1980/cards")
OUTPUT_PATH = Path("data/baseball/parsed/strat365/1980/result_evidence_inventory_v0.json")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig", errors="replace"))


def normalize_shape(text: str) -> str:
    text = re.sub(r"\s+", " ", text or "").strip()
    text = re.sub(r"\d+", "#", text)
    return text[:160]


def main() -> None:
    paths = sorted(PARSED_DIR.glob("*.parsed-card-evidence.json"))

    role_counts: Counter[str] = Counter()
    section_counts: Counter[str] = Counter()
    result_count_by_role: dict[str, Counter[int]] = defaultdict(Counter)
    source_pointer_counts: Counter[str] = Counter()
    shape_counts_by_role: dict[str, Counter[str]] = defaultdict(Counter)

    sample_by_role: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for path in paths:
        data = read_json(path)
        role = data.get("role", "unknown")
        player = data.get("player", {})
        evidence = data.get("resultEvidence", [])

        role_counts[role] += 1
        result_count_by_role[role][len(evidence)] += 1

        for item in evidence:
            section_counts[item.get("section", "unknown")] += 1
            source_pointer_counts[item.get("source", {}).get("pointer", "unknown")] += 1

            raw = item.get("rawResultText", "")
            shape = normalize_shape(raw)
            shape_counts_by_role[role][shape] += 1

        if len(sample_by_role[role]) < 3:
            sample_by_role[role].append(
                {
                    "playerId": player.get("playerId"),
                    "playerName": player.get("playerName"),
                    "role": role,
                    "sections": [item.get("section") for item in evidence],
                    "sourcePointers": [item.get("source", {}).get("pointer") for item in evidence],
                    "firstEvidencePreview": (evidence[0].get("rawResultText", "")[:300] if evidence else ""),
                }
            )

    inventory = {
        "parsedFileCount": len(paths),
        "roleCounts": dict(role_counts),
        "resultCountByRole": {role: dict(counter) for role, counter in result_count_by_role.items()},
        "sectionCounts": dict(section_counts),
        "sourcePointerCounts": dict(source_pointer_counts),
        "topShapesByRole": {
            role: counter.most_common(10)
            for role, counter in shape_counts_by_role.items()
        },
        "samplesByRole": dict(sample_by_role),
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(inventory, indent=2), encoding="utf-8")

    print("BIE Result Evidence Inventory v0")
    print("=" * 72)
    print(f"Parsed files: {len(paths)}")
    print(f"Role counts: {dict(role_counts)}")
    print(f"Result count by role: { {role: dict(counter) for role, counter in result_count_by_role.items()} }")
    print()
    print("Sections:")
    for key, value in sorted(section_counts.items()):
        print(f"  {key}: {value}")
    print()
    print("Source pointers:")
    for key, value in sorted(source_pointer_counts.items()):
        print(f"  {key}: {value}")
    print()
    print(f"Wrote: {OUTPUT_PATH}")
    print("=" * 72)


if __name__ == "__main__":
    main()
