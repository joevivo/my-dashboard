from __future__ import annotations

from collections import Counter
from pathlib import Path
import json
from typing import Any


ATOM_DIR = Path("data/baseball/parsed/strat365/1980/result-atoms")
OUTPUT_DIR = Path("data/baseball/parsed/strat365/1980/result-semantics")
RULES_PATH = Path("baseball/semantics/printed_result_semantics_rules_v0.json")

SCHEMA_VERSION = "bie.result-semantics.v0"
PARSER_VERSION = "bie-result-semantics-parser-v0.1"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig", errors="replace"))


def copy_rule(rules: dict[str, Any], section: str, key: str | None) -> dict[str, Any]:
    if key is None:
        return {"semanticStatus": "missing_key"}

    value = rules.get(section, {}).get(key)
    if value is None:
        return {"semanticStatus": "unmapped", "key": key}

    output = dict(value)
    output["semanticStatus"] = "mapped"
    return output


def outcome_marker_rule(
    rules: dict[str, Any],
    marker: str,
    normalized_label: str | None,
) -> dict[str, Any]:
    rule = copy_rule(rules, "outcomeLabelMarkers", marker)

    if marker == "+":
        known_uses = rule.get("knownUses", {})
        rule["resolvedUse"] = known_uses.get(normalized_label, "unknown_plus_marker_use")

    return rule


def build_semantics(
    rules: dict[str, Any],
    outcome: dict[str, Any],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    warnings: list[dict[str, Any]] = []

    atom = outcome.get("resultAtom", {})
    atom_key = atom.get("atomKey")
    normalized_label = atom.get("normalizedLabel")
    range_kind = atom.get("rangeKind")
    entry_markers = atom.get("entryTokenMarkers", [])
    outcome_markers = atom.get("outcomeLabelMarkers", [])

    label_semantics = copy_rule(rules, "normalizedLabels", normalized_label)
    split_semantics = copy_rule(rules, "splitRangeKinds", range_kind)

    entry_marker_semantics = [
        copy_rule(rules, "entryTokenMarkers", marker)
        for marker in entry_markers
    ]

    outcome_marker_semantics = [
        outcome_marker_rule(rules, marker, normalized_label)
        for marker in outcome_markers
    ]

    all_sections = [label_semantics, split_semantics]
    all_sections.extend(entry_marker_semantics)
    all_sections.extend(outcome_marker_semantics)

    for section in all_sections:
        if section.get("semanticStatus") != "mapped":
            warnings.append(
                {
                    "warning": "unmapped_semantic_rule",
                    "atomKey": atom_key,
                    "section": section,
                }
            )

    dependencies = set()

    for dep in label_semantics.get("dependencies", []):
        dependencies.add(dep)

    if split_semantics.get("requiresD20Roll"):
        dependencies.add("split_roll_d20")
        dependencies.add(split_semantics.get("semanticType"))

    for section in entry_marker_semantics:
        semantic_type = section.get("semanticType")
        if semantic_type:
            dependencies.add(semantic_type)

    for section in outcome_marker_semantics:
        semantic_type = section.get("semanticType")
        if semantic_type:
            dependencies.add(semantic_type)

    dependencies.discard(None)

    semantics = {
        "atomKey": atom_key,
        "semanticStatus": "mapped" if not warnings else "partial",
        "normalizedLabel": normalized_label,
        "baseOutcomeType": label_semantics.get("baseOutcomeType"),
        "isHitCandidate": bool(label_semantics.get("isHitCandidate")),
        "isOnBaseCandidate": bool(label_semantics.get("isOnBaseCandidate")),
        "isOutCandidate": bool(label_semantics.get("isOutCandidate")),
        "isContextual": bool(
            label_semantics.get("isContextual")
            or split_semantics.get("requiresD20Roll")
            or entry_marker_semantics
            or outcome_marker_semantics
        ),
        "dependencies": sorted(dependencies),
        "labelSemantics": label_semantics,
        "splitRangeSemantics": split_semantics,
        "entryMarkerSemantics": entry_marker_semantics,
        "outcomeMarkerSemantics": outcome_marker_semantics,
    }

    return semantics, warnings


def parse_file(path: Path, rules: dict[str, Any]) -> dict[str, Any]:
    source = read_json(path)

    output: dict[str, Any] = {
        "schemaVersion": SCHEMA_VERSION,
        "parserVersion": PARSER_VERSION,
        "sourceSchemaVersion": source.get("schemaVersion"),
        "sourceParserVersion": source.get("parserVersion"),
        "sourceFile": str(path).replace("\\", "/"),
        "rulesFile": str(RULES_PATH).replace("\\", "/"),
        "rulesSchemaVersion": rules.get("schemaVersion"),
        "officialHelpSources": rules.get("officialHelpSources", []),
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
                "entryTokenEvidence": entry.get("entryTokenEvidence"),
                "outcomes": [],
            }

            for outcome in entry.get("outcomes", []):
                semantics, warnings = build_semantics(rules, outcome)
                output["warnings"].extend(warnings)

                parsed_outcome = dict(outcome)
                parsed_outcome["resultSemantics"] = semantics
                parsed_entry["outcomes"].append(parsed_outcome)

            parsed_table["entries"].append(parsed_entry)

        output["tables"].append(parsed_table)

    return output


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    rules = read_json(RULES_PATH)
    paths = sorted(ATOM_DIR.glob("*.result-atoms.json"))

    parsed = 0
    failed = 0
    total_warnings = 0
    total_entries = 0
    total_outcome_rows = 0

    status_counts: Counter[str] = Counter()
    dependency_counts: Counter[str] = Counter()

    for path in paths:
        try:
            parsed_card = parse_file(path, rules)
            player_id = parsed_card.get("player", {}).get("playerId")
            if not player_id:
                raise ValueError(f"Missing playerId in {path}")

            for table in parsed_card.get("tables", []):
                for entry in table.get("entries", []):
                    total_entries += 1
                    for outcome in entry.get("outcomes", []):
                        total_outcome_rows += 1
                        semantics = outcome.get("resultSemantics", {})
                        status_counts[semantics.get("semanticStatus")] += 1
                        for dep in semantics.get("dependencies", []):
                            dependency_counts[dep] += 1

            output_path = OUTPUT_DIR / f"{player_id}.result-semantics.json"
            output_path.write_text(json.dumps(parsed_card, indent=2), encoding="utf-8")

            parsed += 1
            total_warnings += len(parsed_card.get("warnings", []))
        except Exception as exc:
            failed += 1
            print(f"FAILED {path}: {exc}")

    print("BIE Result Semantics Parser v0")
    print("=" * 72)
    print(f"Source files: {len(paths)}")
    print(f"Parsed files: {parsed}")
    print(f"Failed files: {failed}")
    print(f"Warnings: {total_warnings}")
    print(f"Total entries: {total_entries}")
    print(f"Total outcome rows: {total_outcome_rows}")
    print(f"Semantic status counts: {dict(status_counts)}")
    print()
    print("Top dependencies:")
    for dep, count in dependency_counts.most_common(25):
        print(f"  {dep}: {count}")
    print()
    print(f"Output: {OUTPUT_DIR}")
    print("=" * 72)

    if failed or total_warnings or parsed != 721 or total_entries != 47586 or total_outcome_rows != 54748:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
