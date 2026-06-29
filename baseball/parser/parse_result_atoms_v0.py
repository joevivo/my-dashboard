from __future__ import annotations

from collections import Counter
from pathlib import Path
import json
from typing import Any


MODIFIER_DIR = Path("data/baseball/parsed/strat365/1980/result-modifiers")
OUTPUT_DIR = Path("data/baseball/parsed/strat365/1980/result-atoms")

SCHEMA_VERSION = "bie.result-atoms.v0"
PARSER_VERSION = "bie-result-atom-parser-v0.1"


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
            token_evidence = entry.get("entryTokenEvidence", {})
            entry_markers = token_evidence.get("entryTokenMarkers", [])

            parsed_entry = {
                "diceRoll": entry.get("diceRoll"),
                "rawRows": entry.get("rawRows", []),
                "entryTokenEvidence": token_evidence,
                "outcomes": [],
            }

            for outcome in entry.get("outcomes", []):
                normalized = outcome.get("normalized", {})
                split_range = outcome.get("splitRange", {})
                outcome_markers = outcome.get("outcomeLabelMarkers", [])

                normalized_label = normalized.get("normalizedLabel")
                range_kind = split_range.get("rangeKind")

                key = atom_key(
                    normalized_label,
                    range_kind,
                    entry_markers,
                    outcome_markers,
                )

                if not normalized_label:
                    output["warnings"].append(
                        {
                            "warning": "missing_normalized_label",
                            "tableNumber": table.get("tableNumber"),
                            "side": table.get("side"),
                            "diceRoll": entry.get("diceRoll"),
                            "rawOutcome": outcome.get("rawOutcome"),
                        }
                    )

                if not range_kind:
                    output["warnings"].append(
                        {
                            "warning": "missing_range_kind",
                            "tableNumber": table.get("tableNumber"),
                            "side": table.get("side"),
                            "diceRoll": entry.get("diceRoll"),
                            "rawOutcome": outcome.get("rawOutcome"),
                        }
                    )

                parsed_entry["outcomes"].append(
                    {
                        "rawOutcome": outcome.get("rawOutcome"),
                        "rawLabel": outcome.get("rawLabel"),
                        "rangeText": outcome.get("rangeText"),
                        "normalized": normalized,
                        "splitRange": split_range,
                        "outcomeLabelMarkers": outcome_markers,
                        "resultAtom": {
                            "atomKey": key,
                            "normalizedLabel": normalized_label,
                            "rangeKind": range_kind,
                            "entryTokenMarkers": entry_markers,
                            "outcomeLabelMarkers": outcome_markers,
                        },
                    }
                )

            parsed_table["entries"].append(parsed_entry)

        output["tables"].append(parsed_table)

    return output


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    paths = sorted(MODIFIER_DIR.glob("*.result-modifiers.json"))

    parsed = 0
    failed = 0
    total_warnings = 0
    total_entries = 0
    total_outcome_rows = 0
    atom_counts: Counter[str] = Counter()

    for path in paths:
        try:
            parsed_card = parse_file(path)
            player_id = parsed_card.get("player", {}).get("playerId")
            if not player_id:
                raise ValueError(f"Missing playerId in {path}")

            for table in parsed_card.get("tables", []):
                for entry in table.get("entries", []):
                    total_entries += 1
                    for outcome in entry.get("outcomes", []):
                        total_outcome_rows += 1
                        atom_counts[outcome.get("resultAtom", {}).get("atomKey")] += 1

            output_path = OUTPUT_DIR / f"{player_id}.result-atoms.json"
            output_path.write_text(json.dumps(parsed_card, indent=2), encoding="utf-8")

            parsed += 1
            total_warnings += len(parsed_card.get("warnings", []))
        except Exception as exc:
            failed += 1
            print(f"FAILED {path}: {exc}")

    print("BIE Result Atom Parser v0")
    print("=" * 72)
    print(f"Source files: {len(paths)}")
    print(f"Parsed files: {parsed}")
    print(f"Failed files: {failed}")
    print(f"Warnings: {total_warnings}")
    print(f"Total entries: {total_entries}")
    print(f"Total outcome rows: {total_outcome_rows}")
    print(f"Distinct atoms: {len(atom_counts)}")
    print(f"Output: {OUTPUT_DIR}")
    print("=" * 72)

    if (
        failed
        or total_warnings
        or parsed != 721
        or total_entries != 47586
        or total_outcome_rows != 54748
        or len(atom_counts) != 62
    ):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
