from __future__ import annotations

from collections import Counter
from pathlib import Path
import json
from typing import Any


SEMANTICS_DIR = Path("data/baseball/parsed/strat365/1980/result-semantics")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig", errors="replace"))


def main() -> None:
    paths = sorted(SEMANTICS_DIR.glob("*.result-semantics.json"))

    role_counts: Counter[str] = Counter()
    status_counts: Counter[str] = Counter()
    base_outcome_counts: Counter[str] = Counter()
    dependency_counts: Counter[str] = Counter()
    contextual_counts: Counter[str] = Counter()

    total_entries = 0
    total_outcome_rows = 0
    warnings = 0

    for path in paths:
        data = read_json(path)
        role_counts[data.get("role")] += 1
        warnings += len(data.get("warnings", []))

        for table in data.get("tables", []):
            for entry in table.get("entries", []):
                total_entries += 1

                for outcome in entry.get("outcomes", []):
                    total_outcome_rows += 1

                    semantics = outcome.get("resultSemantics", {})
                    status_counts[semantics.get("semanticStatus")] += 1
                    base_outcome_counts[semantics.get("baseOutcomeType")] += 1

                    contextual_counts[
                        "contextual" if semantics.get("isContextual") else "fixed"
                    ] += 1

                    for dependency in semantics.get("dependencies", []):
                        dependency_counts[dependency] += 1

    print("BIE Result Semantics Inventory v0")
    print("=" * 72)
    print(f"Result-semantics files: {len(paths)}")
    print(f"Role counts: {dict(role_counts)}")
    print(f"Warnings: {warnings}")
    print(f"Total entries: {total_entries}")
    print(f"Total outcome rows: {total_outcome_rows}")
    print(f"Semantic status counts: {dict(status_counts)}")
    print(f"Contextual counts: {dict(contextual_counts)}")
    print()

    print("Base outcome counts:")
    for key, count in base_outcome_counts.most_common():
        print(f"  {key}: {count}")

    print()
    print("Dependency counts:")
    for key, count in dependency_counts.most_common():
        print(f"  {key}: {count}")

    print("=" * 72)


if __name__ == "__main__":
    main()
