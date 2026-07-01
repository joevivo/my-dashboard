from __future__ import annotations

from pathlib import Path
import argparse
import json
import re
from typing import Any


NORMALIZED_DIR = Path("data/baseball/parsed/strat365/1980/normalized-result-labels")
OUTPUT_DIR = Path("data/baseball/parsed/strat365/1980/split-ranges")

SCHEMA_VERSION = "bie.result-split-ranges.v0"
PARSER_VERSION = "bie-result-split-range-parser-v0.1"
DEFAULT_SEASON = 1980


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig", errors="replace"))


def parse_range(range_text: str | None) -> dict[str, Any]:
    if range_text is None:
        return {"rangeKind": "none"}

    match = re.match(r"^(\d+)-(\d+)$", range_text)
    if match:
        low = int(match.group(1))
        high = int(match.group(2))
        return {
            "rangeKind": "d20_closed",
            "rangeText": range_text,
            "low": low,
            "high": high,
            "width": high - low + 1,
        }

    match = re.match(r"^(\d+)-$", range_text)
    if match:
        low = int(match.group(1))
        return {
            "rangeKind": "d20_open_high",
            "rangeText": range_text,
            "low": low,
            "high": None,
            "width": None,
            "note": "Open-ended range printed this way in authenticated Strat365 HTML; preserved without inference.",
        }

    return {
        "rangeKind": "unmatched",
        "rangeText": range_text,
    }


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
            parsed_entry = {
                "diceRoll": entry.get("diceRoll"),
                "rawRows": entry.get("rawRows", []),
                "outcomes": [],
            }

            for outcome in entry.get("normalizedOutcomes", []):
                parsed_range = parse_range(outcome.get("rangeText"))

                if parsed_range.get("rangeKind") == "unmatched":
                    output["warnings"].append(
                        {
                            "warning": "unmatched_split_range",
                            "tableNumber": table.get("tableNumber"),
                            "side": table.get("side"),
                            "diceRoll": entry.get("diceRoll"),
                            "rawOutcome": outcome.get("rawOutcome"),
                            "rangeText": outcome.get("rangeText"),
                        }
                    )

                parsed_entry["outcomes"].append(
                    {
                        "rawOutcome": outcome.get("rawOutcome"),
                        "rawLabel": outcome.get("rawLabel"),
                        "rangeText": outcome.get("rangeText"),
                        "normalized": outcome.get("normalized"),
                        "splitRange": parsed_range,
                    }
                )

            parsed_table["entries"].append(parsed_entry)

        output["tables"].append(parsed_table)

    return output


def configure_paths(season: int) -> None:
    global NORMALIZED_DIR, OUTPUT_DIR

    NORMALIZED_DIR = Path("data/baseball/parsed/strat365") / str(season) / "normalized-result-labels"
    OUTPUT_DIR = Path("data/baseball/parsed/strat365") / str(season) / "split-ranges"


def select_paths(paths: list[Path], player_ids: list[int] | None) -> list[Path]:
    if not player_ids:
        return paths

    wanted = {str(player_id) for player_id in player_ids}
    selected = []
    found = set()

    for path in paths:
        player_id = path.name.replace(".normalized-result-labels.json", "")
        if player_id in wanted:
            selected.append(path)
            found.add(player_id)

    missing = sorted(wanted - found)
    if missing:
        raise ValueError(f"Player IDs not found in normalized-label outputs: {missing}")

    return selected


def main() -> None:
    parser = argparse.ArgumentParser(description="Parse Strat365 split ranges from normalized result labels.")
    parser.add_argument(
        "--season",
        type=int,
        default=DEFAULT_SEASON,
        help="Season to parse. Defaults to 1980 to preserve existing behavior.",
    )
    parser.add_argument(
        "--player-ids",
        nargs="+",
        type=int,
        default=None,
        help="Optional targeted player IDs from the selected season normalized-label outputs.",
    )
    args = parser.parse_args()

    configure_paths(args.season)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    paths = select_paths(sorted(NORMALIZED_DIR.glob("*.normalized-result-labels.json")), args.player_ids)

    parsed = 0
    failed = 0
    total_warnings = 0

    for path in paths:
        try:
            parsed_card = parse_file(path)
            player_id = parsed_card.get("player", {}).get("playerId")
            if not player_id:
                raise ValueError(f"Missing playerId in {path}")

            output_path = OUTPUT_DIR / f"{player_id}.split-ranges.json"
            output_path.write_text(json.dumps(parsed_card, indent=2), encoding="utf-8")

            parsed += 1
            total_warnings += len(parsed_card.get("warnings", []))
        except Exception as exc:
            failed += 1
            print(f"FAILED {path}: {exc}")

    print("BIE Split Range Parser v0")
    print("=" * 72)
    print(f"Season: {args.season}")
    print(f"Source files: {len(paths)}")
    print(f"Parsed files: {parsed}")
    print(f"Failed files: {failed}")
    print(f"Warnings: {total_warnings}")
    print(f"Output: {OUTPUT_DIR}")
    print("=" * 72)

    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
