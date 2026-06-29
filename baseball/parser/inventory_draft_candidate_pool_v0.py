from __future__ import annotations

from pathlib import Path
import json
from typing import Any


SIGNAL_PATH = Path("data/baseball/parsed/strat365/1980/draft-signals/1980.salary-adjusted-draft-signals.json")


def get_score(row: dict[str, Any], *path: str) -> float:
    value: Any = row
    for key in path:
        value = value.get(key, {})
    return float(value or 0)


def neutral(row: dict[str, Any]) -> float:
    return get_score(row, "neutralDraftScore", "score")


def balanced(row: dict[str, Any]) -> float:
    return get_score(row, "salaryValue", "balancedValueScore", "score")


def value(row: dict[str, Any]) -> float:
    return get_score(row, "salaryValue", "valuePercentile", "score")


def salary_m(row: dict[str, Any]) -> float:
    return get_score(row, "salary", "millions", "decimal")


def role_detail(row: dict[str, Any]) -> str:
    if row.get("role") == "hitter":
        return row.get("hitter", {}).get("primaryPosition", "(pos?)")
    return row.get("pitcher", {}).get("pitchingRole", "(role?)")


def label(row: dict[str, Any]) -> str:
    player = row.get("player", {})
    return (
        f'{player.get("playerName")} team={player.get("team")} '
        f'{role_detail(row)} salary={row.get("salary", {}).get("raw")} '
        f'neutral={neutral(row):.1f} value={balanced(row):.1f} '
        f'v_pct={value(row):.1f} rank={row.get("salaryAdjustedRank")}'
    )


def print_section(title: str, rows: list[dict[str, Any]], *, limit: int = 20) -> None:
    print()
    print(title)
    print("-" * 112)
    for row in rows[:limit]:
        print(label(row))


def candidate_sections(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    anchors = [
        row for row in rows
        if neutral(row) >= 85
    ]

    balanced_targets = [
        row for row in rows
        if balanced(row) >= 70
    ]

    premium_values = [
        row for row in rows
        if neutral(row) >= 65 and salary_m(row) <= 3.0
    ]

    cheap_viable_depth = [
        row for row in rows
        if neutral(row) >= 50 and salary_m(row) <= 1.0
    ]

    fades = [
        row for row in rows
        if neutral(row) < 25 and balanced(row) < 25
    ]

    return {
        "anchors": sorted(anchors, key=lambda row: neutral(row), reverse=True),
        "balanced_targets": sorted(balanced_targets, key=lambda row: balanced(row), reverse=True),
        "premium_values": sorted(premium_values, key=lambda row: (balanced(row), neutral(row)), reverse=True),
        "cheap_viable_depth": sorted(cheap_viable_depth, key=lambda row: (balanced(row), neutral(row)), reverse=True),
        "fades": sorted(fades, key=lambda row: (balanced(row), neutral(row))),
    }


def main() -> None:
    data = json.loads(SIGNAL_PATH.read_text(encoding="utf-8-sig", errors="replace"))

    hitters = data.get("hitters", [])
    pitchers = data.get("pitchers", [])

    hitter_sections = candidate_sections(hitters)
    pitcher_sections = candidate_sections(pitchers)

    print("BIE Draft Candidate Pool Inventory v0")
    print("=" * 112)
    print(f"Schema: {data.get('schemaVersion')}")
    print(f"Rankable hitters: {len(hitters)}")
    print(f"Rankable pitchers: {len(pitchers)}")
    print()
    print("Thresholds")
    print("-" * 112)
    print("anchors: neutral >= 85")
    print("balanced targets: balanced value >= 70")
    print("premium values: neutral >= 65 and salary <= 3.00M")
    print("cheap viable depth: neutral >= 50 and salary <= 1.00M")
    print("fades: neutral < 25 and balanced value < 25")

    print_section("Hitter anchors", hitter_sections["anchors"])
    print_section("Hitter balanced targets", hitter_sections["balanced_targets"])
    print_section("Hitter premium values", hitter_sections["premium_values"])
    print_section("Hitter cheap viable depth", hitter_sections["cheap_viable_depth"])
    print_section("Hitter fades", hitter_sections["fades"])

    print_section("Pitcher anchors", pitcher_sections["anchors"])
    print_section("Pitcher balanced targets", pitcher_sections["balanced_targets"])
    print_section("Pitcher premium values", pitcher_sections["premium_values"])
    print_section("Pitcher cheap viable depth", pitcher_sections["cheap_viable_depth"])
    print_section("Pitcher fades", pitcher_sections["fades"])

    print("=" * 112)


if __name__ == "__main__":
    main()
