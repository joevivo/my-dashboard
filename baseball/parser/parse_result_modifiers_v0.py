from __future__ import annotations

from pathlib import Path
import json
import re
from typing import Any


SPLIT_RANGE_DIR = Path("data/baseball/parsed/strat365/1980/split-ranges")
OUTPUT_DIR = Path("data/baseball/parsed/strat365/1980/result-modifiers")

SCHEMA_VERSION = "bie.result-modifiers.v0"
PARSER_VERSION = "bie-result-modifier-parser-v0.1"

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


def parse_entry_token(token: str | None) -> dict[str, Any]:
    if not token:
        return {
            "entryToken": token,
            "entryTokenMarkers": [],
            "printedDiceToken": None,
            "tokenStatus": "missing",
        }

    markers = [marker for marker in ENTRY_TOKEN_MARKERS if marker in token]

    cleaned = token
    for marker in ENTRY_TOKEN_MARKERS:
        cleaned = cleaned.replace(marker, "")

    match = re.match(r"^(\d+)-$", cleaned)

    return {
        "entryToken": token,
        "entryTokenMarkers": markers,
        "printedDiceToken": cleaned,
        "tokenStatus": "parsed" if match else "unmatched",
    }


def parse_outcome_label_markers(raw_label: str | None) -> list[str]:
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


def parse_file(path: Path) -> dict[str, Any]:
    source = read_json(path)

    output: dict[str, Any] = {
        "schemaVersion": SCHEMA_VERSION,
        "parserVersion": PARSER_VERSION,
        "sourceSchemaVersion": source.get("schemaVersion"),
        "sourceParserVersion": source.get("parserVersion"),
        "sourceFile": str(path).replace("\\", "/"),
        "player": source.get("player"),
        "role": source.get("role"),
        "tables": [],
        "warnings": [],
    }

    for table in source.get("tables", []):
        parsed_table = {
            "tableNumber": table.get("tableNumber"),
            "side": table.get("side"),
            "entries": [],
        }

        for entry in table.get("entries", []):
            token = first_row_token(entry.get("rawRows", []))
            token_info = parse_entry_token(token)

            if token_info["tokenStatus"] != "parsed":
                output["warnings"].append(
                    {
                        "warning": "entry_token_not_parsed",
                        "tableNumber": table.get("tableNumber"),
                        "side": table.get("side"),
                        "diceRoll": entry.get("diceRoll"),
                        "entryToken": token,
                    }
                )

            parsed_entry = {
                "diceRoll": entry.get("diceRoll"),
                "rawRows": entry.get("rawRows", []),
                "entryTokenEvidence": token_info,
                "outcomes": [],
            }

            for outcome in entry.get("outcomes", []):
                raw_label = outcome.get("rawLabel")

                parsed_entry["outcomes"].append(
                    {
                        "rawOutcome": outcome.get("rawOutcome"),
                        "rawLabel": raw_label,
                        "rangeText": outcome.get("rangeText"),
                        "normalized": outcome.get("normalized"),
                        "splitRange": outcome.get("splitRange"),
                        "outcomeLabelMarkers": parse_outcome_label_markers(raw_label),
                    }
                )

            parsed_table["entries"].append(parsed_entry)

        output["tables"].append(parsed_table)

    return output


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    paths = sorted(SPLIT_RANGE_DIR.glob("*.split-ranges.json"))

    parsed = 0
    failed = 0
    total_warnings = 0

    for path in paths:
        try:
            parsed_card = parse_file(path)
            player_id = parsed_card.get("player", {}).get("playerId")
            if not player_id:
                raise ValueError(f"Missing playerId in {path}")

            output_path = OUTPUT_DIR / f"{player_id}.result-modifiers.json"
            output_path.write_text(json.dumps(parsed_card, indent=2), encoding="utf-8")

            parsed += 1
            total_warnings += len(parsed_card.get("warnings", []))
        except Exception as exc:
            failed += 1
            print(f"FAILED {path}: {exc}")

    print("BIE Result Modifier Parser v0")
    print("=" * 72)
    print(f"Source files: {len(paths)}")
    print(f"Parsed files: {parsed}")
    print(f"Failed files: {failed}")
    print(f"Warnings: {total_warnings}")
    print(f"Output: {OUTPUT_DIR}")
    print("=" * 72)

    if failed or total_warnings:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
