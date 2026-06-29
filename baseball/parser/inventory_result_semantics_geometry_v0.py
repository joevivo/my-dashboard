from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
import json


SEMANTICS_DIR = Path("data/baseball/parsed/strat365/1980/result-semantics")


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig", errors="replace"))


def main() -> None:
    paths = sorted(SEMANTICS_DIR.glob("*.result-semantics.json"))

    role_counts = Counter()
    table_counts = Counter()
    side_counts = Counter()
    role_table_sides = defaultdict(Counter)
    dice_counts = Counter()

    for path in paths:
        data = read_json(path)
        role = data.get("role")
        role_counts[role] += 1

        for table in data.get("tables", []):
            table_number = table.get("tableNumber")
            side = table.get("side")
            table_counts[(role, table_number)] += 1
            side_counts[(role, side)] += 1
            role_table_sides[role][(table_number, side)] += 1

            for entry in table.get("entries", []):
                dice_counts[entry.get("diceRoll")] += 1

    print("BIE Result Semantics Geometry Inventory v0")
    print("=" * 72)
    print(f"Files: {len(paths)}")
    print(f"Role counts: {dict(role_counts)}")
    print()

    print("Role/table/side layout:")
    for role in sorted(role_table_sides):
        print(role)
        for key, count in sorted(role_table_sides[role].items()):
            print(f"  table={key[0]} side={key[1]} count={count}")

    print()
    print("Dice counts:")
    for dice, count in sorted(dice_counts.items()):
        print(f"  {dice}: {count}")

    print("=" * 72)


if __name__ == "__main__":
    main()
