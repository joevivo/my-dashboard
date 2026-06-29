from __future__ import annotations

from collections import defaultdict
from pathlib import Path
import json
from typing import Any


SIGNAL_PATH = Path("data/baseball/parsed/strat365/1980/draft-signals/1980.salary-adjusted-draft-signals.json")


def score(row: dict[str, Any], path: list[str]) -> float:
    value: Any = row
    for key in path:
        value = value.get(key, {})
    return float(value or 0)


def balanced(row: dict[str, Any]) -> float:
    return score(row, ["salaryValue", "balancedValueScore", "score"])


def neutral(row: dict[str, Any]) -> float:
    return score(row, ["neutralDraftScore", "score"])


def value(row: dict[str, Any]) -> float:
    return score(row, ["salaryValue", "valuePercentile", "score"])


def salary(row: dict[str, Any]) -> str:
    return str(row.get("salary", {}).get("raw", "(salary?)"))


def player(row: dict[str, Any]) -> str:
    p = row.get("player", {})
    return f'{p.get("playerName")} team={p.get("team")} salary={salary(row)}'


def print_group(title: str, rows: list[dict[str, Any]], *, limit: int = 10) -> None:
    print()
    print(title)
    print("-" * 104)
    print("rank  bal     neutral value   player")
    for row in rows[:limit]:
        print(
            f"{row.get('salaryAdjustedRank', ''):>4} "
            f"{balanced(row):7.3f} "
            f"{neutral(row):7.3f} "
            f"{value(row):7.3f} "
            f"{player(row)}"
        )


def main() -> None:
    data = json.loads(SIGNAL_PATH.read_text(encoding="utf-8-sig", errors="replace"))

    hitters = data.get("hitters", [])
    pitchers = data.get("pitchers", [])

    hitters_by_position: dict[str, list[dict[str, Any]]] = defaultdict(list)
    pitchers_by_role_family: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for row in hitters:
        position = row.get("hitter", {}).get("primaryPosition", "(unknown)")
        hitters_by_position[position].append(row)

    for row in pitchers:
        pitching_role = row.get("pitcher", {}).get("pitchingRole", "")
        if pitching_role.startswith("S") and "/R" in pitching_role:
            role_family = "starter_relief"
        elif pitching_role.startswith("S"):
            role_family = "starter_only"
        elif pitching_role.startswith("R"):
            role_family = "relief_only"
        else:
            role_family = "unknown"
        pitchers_by_role_family[role_family].append(row)

    print("BIE Positional Salary-Adjusted Draft Inventory v0")
    print("=" * 104)
    print(f"Schema: {data.get('schemaVersion')}")
    print(f"Rankable hitters: {len(hitters)}")
    print(f"Rankable pitchers: {len(pitchers)}")

    print()
    print("Hitter position counts")
    print("-" * 104)
    for position in sorted(hitters_by_position):
        print(f"{position}: {len(hitters_by_position[position])}")

    print()
    print("Pitcher role-family counts")
    print("-" * 104)
    for role_family in sorted(pitchers_by_role_family):
        print(f"{role_family}: {len(pitchers_by_role_family[role_family])}")

    for position in sorted(hitters_by_position):
        rows = sorted(hitters_by_position[position], key=balanced, reverse=True)
        print_group(f"Top salary-adjusted hitters at {position}", rows)

    for role_family in ("starter_only", "starter_relief", "relief_only", "unknown"):
        rows = sorted(pitchers_by_role_family.get(role_family, []), key=balanced, reverse=True)
        if rows:
            print_group(f"Top salary-adjusted pitchers: {role_family}", rows)

    print("=" * 104)


if __name__ == "__main__":
    main()
