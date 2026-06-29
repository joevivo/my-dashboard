from __future__ import annotations

from collections import Counter
from fractions import Fraction
from pathlib import Path
import json
from typing import Any


SEMANTICS_DIR = Path("data/baseball/parsed/strat365/1980/result-semantics")
OUTPUT_DIR = Path("data/baseball/parsed/strat365/1980/result-probabilities")

SCHEMA_VERSION = "bie.result-probabilities.v0"
PARSER_VERSION = "bie-result-probability-parser-v0.1"

DICE_2D6_NUMERATORS = {
    2: 1,
    3: 2,
    4: 3,
    5: 4,
    6: 5,
    7: 6,
    8: 5,
    9: 4,
    10: 3,
    11: 2,
    12: 1,
}


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig", errors="replace"))


def fraction_payload(value: Fraction) -> dict[str, Any]:
    return {
        "numerator": value.numerator,
        "denominator": value.denominator,
        "decimal": round(float(value), 12),
    }


def column_index(role: str, table_number: int) -> int:
    if role == "hitter":
        if table_number in (7, 10):
            return 1
        if table_number in (8, 11):
            return 2
        if table_number in (9, 12):
            return 3

    if role == "pitcher":
        if table_number in (6, 9):
            return 1
        if table_number in (7, 10):
            return 2
        if table_number in (8, 11):
            return 3

    raise ValueError(f"Unknown role/table layout: role={role} table={table_number}")


def split_probability(outcome: dict[str, Any]) -> tuple[str, Fraction | None, dict[str, Any]]:
    split = outcome.get("splitRange", {})
    range_kind = split.get("rangeKind")

    if range_kind == "none":
        return "exact", Fraction(1, 1), {
            "rangeKind": "none",
            "weight": fraction_payload(Fraction(1, 1)),
        }

    if range_kind == "d20_closed":
        width = split.get("width")
        if not isinstance(width, int):
            return "unresolved_closed_split", None, {
                "rangeKind": range_kind,
                "rangeText": split.get("rangeText"),
                "reason": "closed split missing integer width",
            }

        return "exact", Fraction(width, 20), {
            "rangeKind": range_kind,
            "rangeText": split.get("rangeText"),
            "low": split.get("low"),
            "high": split.get("high"),
            "width": width,
            "weight": fraction_payload(Fraction(width, 20)),
        }

    if range_kind == "d20_open_high":
        return "unresolved_open_split", None, {
            "rangeKind": range_kind,
            "rangeText": split.get("rangeText"),
            "low": split.get("low"),
            "high": split.get("high"),
            "width": split.get("width"),
            "reason": "open-ended split preserved as printed; no upper bound inferred",
        }

    return "unresolved_unknown_split", None, {
        "rangeKind": range_kind,
        "rangeText": split.get("rangeText"),
        "reason": "unknown split range kind",
    }


def add_probability(
    role: str,
    table_number: int,
    dice_roll: int,
    outcome: dict[str, Any],
) -> dict[str, Any]:
    col_weight = Fraction(1, 3)
    dice_weight = Fraction(DICE_2D6_NUMERATORS[dice_roll], 36)
    cell_weight = col_weight * dice_weight

    split_status, split_weight, split_payload = split_probability(outcome)

    probability = {
        "probabilityScope": "within_card_side",
        "probabilityStatus": split_status,
        "columnIndexWithinSide": column_index(role, table_number),
        "columnWeight": fraction_payload(col_weight),
        "diceRoll": dice_roll,
        "dice2d6Weight": fraction_payload(dice_weight),
        "cellWeightBeforeSplit": fraction_payload(cell_weight),
        "splitWeight": split_payload,
        "finalWeight": None,
        "note": "Weights are within a batter/pitcher handedness side. They do not include batter-card vs pitcher-card roll selection.",
    }

    if split_weight is not None:
        probability["finalWeight"] = fraction_payload(cell_weight * split_weight)

    parsed = dict(outcome)
    parsed["resultProbability"] = probability
    return parsed


def parse_file(path: Path) -> dict[str, Any]:
    source = read_json(path)
    role = source.get("role")

    output = {
        "schemaVersion": SCHEMA_VERSION,
        "parserVersion": PARSER_VERSION,
        "sourceSchemaVersion": source.get("schemaVersion"),
        "sourceParserVersion": source.get("parserVersion"),
        "sourceFile": str(path).replace("\\", "/"),
        "player": source.get("player"),
        "role": role,
        "probabilityBasis": {
            "scope": "within_card_side",
            "columnWeight": "1/3",
            "diceWeight": "2d6 distribution over rows 2-12",
            "splitWeight": "d20 width / 20 when exact",
            "doesNotInclude": ["batter_card_vs_pitcher_card_selection", "park_effect_resolution", "defensive_x_chart_resolution"],
        },
        "tables": [],
        "warnings": [],
    }

    for table in source.get("tables", []):
        table_number = int(table.get("tableNumber"))
        parsed_table = {
            "tableNumber": table_number,
            "side": table.get("side"),
            "columnIndexWithinSide": column_index(role, table_number),
            "entries": [],
        }

        for entry in table.get("entries", []):
            dice_roll = int(entry.get("diceRoll"))
            parsed_entry = {
                "diceRoll": dice_roll,
                "rawRows": entry.get("rawRows", []),
                "entryTokenEvidence": entry.get("entryTokenEvidence"),
                "outcomes": [],
            }

            for outcome in entry.get("outcomes", []):
                parsed_outcome = add_probability(role, table_number, dice_roll, outcome)

                status = parsed_outcome["resultProbability"]["probabilityStatus"]
                if status != "exact":
                    output["warnings"].append(
                        {
                            "warning": "unresolved_probability",
                            "probabilityStatus": status,
                            "tableNumber": table_number,
                            "diceRoll": dice_roll,
                            "rawOutcome": outcome.get("rawOutcome"),
                            "atomKey": outcome.get("resultAtom", {}).get("atomKey"),
                        }
                    )

                parsed_entry["outcomes"].append(parsed_outcome)

            parsed_table["entries"].append(parsed_entry)

        output["tables"].append(parsed_table)

    return output


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    paths = sorted(SEMANTICS_DIR.glob("*.result-semantics.json"))

    parsed = 0
    failed = 0
    total_entries = 0
    total_outcome_rows = 0
    total_warnings = 0

    status_counts: Counter[str] = Counter()

    for path in paths:
        try:
            result = parse_file(path)
            player_id = result.get("player", {}).get("playerId")
            if not player_id:
                raise ValueError(f"Missing playerId in {path}")

            for table in result.get("tables", []):
                for entry in table.get("entries", []):
                    total_entries += 1
                    for outcome in entry.get("outcomes", []):
                        total_outcome_rows += 1
                        status_counts[outcome["resultProbability"]["probabilityStatus"]] += 1

            total_warnings += len(result.get("warnings", []))

            output_path = OUTPUT_DIR / f"{player_id}.result-probabilities.json"
            output_path.write_text(json.dumps(result, indent=2), encoding="utf-8")

            parsed += 1
        except Exception as exc:
            failed += 1
            print(f"FAILED {path}: {exc}")

    print("BIE Result Probability Parser v0")
    print("=" * 72)
    print(f"Source files: {len(paths)}")
    print(f"Parsed files: {parsed}")
    print(f"Failed files: {failed}")
    print(f"Total entries: {total_entries}")
    print(f"Total outcome rows: {total_outcome_rows}")
    print(f"Warnings: {total_warnings}")
    print(f"Probability status counts: {dict(status_counts)}")
    print(f"Output: {OUTPUT_DIR}")
    print("=" * 72)

    if (
        parsed != 721
        or failed != 0
        or total_entries != 47586
        or total_outcome_rows != 54748
        or status_counts.get("exact") != 54739
        or status_counts.get("unresolved_open_split") != 9
        or total_warnings != 9
    ):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
