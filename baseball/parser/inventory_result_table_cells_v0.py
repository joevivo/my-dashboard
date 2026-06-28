from __future__ import annotations

from collections import Counter, defaultdict
from html import unescape
from pathlib import Path
import json
import re
from typing import Any


UNIVERSE_PATH = Path("data/baseball/raw/strat365/1980/players/1980_players_universe.json")
CARDS_DIR = Path("data/baseball/raw/strat365/authenticated/1980/cards")
OUTPUT_PATH = Path("data/baseball/parsed/strat365/1980/result_table_cell_inventory_v0.json")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig", errors="replace"))


def clean_html(value: str) -> str:
    value = re.sub(r"<br\s*/?>", " ", value, flags=re.I)
    value = re.sub(r"<[^>]+>", " ", value)
    value = unescape(value)
    value = re.sub(r"\s+", " ", value).strip()
    return value


def extract_tables(html: str) -> list[str]:
    return re.findall(r"<table\b.*?</table>", html, flags=re.I | re.S)


def extract_rows(table_html: str) -> list[list[str]]:
    rows: list[list[str]] = []
    for row_html in re.findall(r"<tr\b.*?</tr>", table_html, flags=re.I | re.S):
        cells = re.findall(r"<t[dh]\b.*?</t[dh]>", row_html, flags=re.I | re.S)
        rows.append([clean_html(cell) for cell in cells])
    return rows


def result_table_numbers(role: str) -> list[int]:
    if role == "hitter":
        return [7, 8, 9, 10, 11, 12]
    if role == "pitcher":
        return [6, 7, 8, 9, 10, 11]
    raise ValueError(f"Unsupported role: {role}")


def main() -> None:
    universe = read_json(UNIVERSE_PATH)
    players = universe.get("players", [])

    role_counts: Counter[str] = Counter()
    total_table_counts: Counter[str] = Counter()
    row_count_patterns: dict[str, Counter[int]] = defaultdict(Counter)
    row_length_patterns: dict[str, Counter[str]] = defaultdict(Counter)
    first_row_patterns: dict[str, Counter[str]] = defaultdict(Counter)
    continuation_rows: Counter[str] = Counter()
    dice_rows: Counter[str] = Counter()
    failures: list[str] = []
    examples: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for player in players:
        player_id = int(player["playerId"])
        role = player["role"]
        role_counts[role] += 1

        html_path = CARDS_DIR / f"{player_id}.html"
        html = html_path.read_text(encoding="utf-8", errors="replace")
        tables = extract_tables(html)

        total_table_counts[f"{role}:{len(tables)}"] += 1

        for table_number in result_table_numbers(role):
            key = f"{role}:table[{table_number}]"

            if table_number > len(tables):
                failures.append(f"{player_id}: missing table[{table_number}]")
                continue

            rows = extract_rows(tables[table_number - 1])
            row_count_patterns[key][len(rows)] += 1
            row_length_patterns[key][",".join(str(len(row)) for row in rows)] += 1

            if rows:
                first_row_patterns[key]["|".join(rows[0])] += 1

            for row in rows:
                if row and row[0] == "":
                    continuation_rows[key] += 1
                elif row and re.match(r"^[#>$@]*\d+-", row[0]):
                    dice_rows[key] += 1

            if len(examples[key]) < 3:
                examples[key].append(
                    {
                        "playerId": player_id,
                        "playerName": player.get("playerName"),
                        "rowCount": len(rows),
                        "rowLengths": [len(row) for row in rows],
                        "firstRows": rows[:5],
                    }
                )

    inventory = {
        "roleCounts": dict(role_counts),
        "totalTableCounts": dict(total_table_counts),
        "rowCountPatterns": {k: dict(v) for k, v in row_count_patterns.items()},
        "rowLengthPatterns": {k: dict(v.most_common(20)) for k, v in row_length_patterns.items()},
        "firstRowPatterns": {k: dict(v.most_common(10)) for k, v in first_row_patterns.items()},
        "diceRows": dict(dice_rows),
        "continuationRows": dict(continuation_rows),
        "failures": failures,
        "examples": dict(examples),
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(inventory, indent=2), encoding="utf-8")

    print("BIE Result Table Cell Inventory v0")
    print("=" * 72)
    print(f"Players: {len(players)}")
    print(f"Role counts: {dict(role_counts)}")
    print(f"Total table counts: {dict(total_table_counts)}")
    print(f"Failures: {len(failures)}")
    print()
    print("Row count patterns:")
    for key in sorted(row_count_patterns):
        print(f"  {key}: {dict(row_count_patterns[key])}")
    print()
    print("Dice rows:")
    for key in sorted(dice_rows):
        print(f"  {key}: {dice_rows[key]}")
    print()
    print("Continuation rows:")
    for key in sorted(continuation_rows):
        print(f"  {key}: {continuation_rows[key]}")
    print()
    print(f"Wrote: {OUTPUT_PATH}")
    print("=" * 72)

    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
