from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import argparse
import json
import re
from typing import Any


PARSER_VERSION = "bie-result-label-normalizer-v0.1"
DEFAULT_SEASON = 1980

RESULT_CELLS_DIR = Path("data/baseball/parsed/strat365/1980/result-cells")
OUTPUT_DIR = Path("data/baseball/parsed/strat365/1980/normalized-result-labels")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig", errors="replace"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def normalize_label(raw_label: str) -> dict[str, Any]:
    label = (raw_label or "").strip()

    if label == "strikeout":
        return {"normalizedLabel": "STRIKEOUT"}

    if label == "WALK":
        return {"normalizedLabel": "WALK"}

    if label == "HBP":
        return {"normalizedLabel": "HBP"}

    if label == "+ injury":
        return {"normalizedLabel": "INJURY_FLAG"}

    if label == "lineout":
        return {"normalizedLabel": "LINEOUT"}

    if label == "lo max":
        return {"normalizedLabel": "LINEOUT_MAX"}

    if label in {"HR", "HOMERUN"}:
        return {"normalizedLabel": "HOME_RUN", "rawVariant": label}

    if label in {"SI*", "SI**", "SINGLE*", "SINGLE**"}:
        return {"normalizedLabel": "SINGLE", "rawVariant": label}

    match = re.match(r"^SINGLE\(([^)]+)\)$", label)
    if match:
        return {"normalizedLabel": "SINGLE", "fieldLocation": match.group(1)}

    if label in {"DO", "DO**", "DOUBLE**"}:
        return {"normalizedLabel": "DOUBLE", "rawVariant": label}

    match = re.match(r"^DO\(([^)]+)\)$", label)
    if match:
        return {
            "normalizedLabel": "DOUBLE",
            "rawVariant": label,
            "fieldLocation": match.group(1),
        }

    match = re.match(r"^DOUBLE\(([^)]+)\)$", label)
    if match:
        return {"normalizedLabel": "DOUBLE", "fieldLocation": match.group(1)}

    if label in {"TR", "TRIPLE"}:
        return {"normalizedLabel": "TRIPLE", "rawVariant": label}

    match = re.match(r"^gb\(([^)]+)\)([ABC])(\+?)$", label)
    if match:
        return {
            "normalizedLabel": "GROUNDBALL",
            "position": match.group(1),
            "grade": match.group(2),
            "plus": bool(match.group(3)),
        }

    match = re.match(r"^GB\(([^)]+)\)X$", label)
    if match:
        return {"normalizedLabel": "GROUNDBALL_X", "position": match.group(1)}

    match = re.match(r"^fly\(([^)]+)\)([ABC])(\?)?$", label)
    if match:
        return {
            "normalizedLabel": "FLYBALL",
            "position": match.group(1),
            "depth": match.group(2),
            "question": bool(match.group(3)),
        }

    match = re.match(r"^FB\(([^)]+)\)X$", label)
    if match:
        return {"normalizedLabel": "FLYBALL_X", "position": match.group(1)}

    match = re.match(r"^popout\(([^)]+)\)$", label)
    if match:
        return {"normalizedLabel": "POPOUT", "position": match.group(1)}

    match = re.match(r"^foulout\(([^)]+)\)$", label)
    if match:
        return {"normalizedLabel": "FOULOUT", "position": match.group(1)}

    if label == "CATCH-X":
        return {"normalizedLabel": "CATCHER_X"}

    if label == "(blank)":
        return {"normalizedLabel": "BLANK"}

    return {"normalizedLabel": "UNMATCHED"}


def normalize_raw_outcome(raw_outcome: list[str]) -> dict[str, Any]:
    raw_label = raw_outcome[0] if raw_outcome else "(empty)"

    if raw_label == "":
        raw_label = "(blank)"

    normalized = normalize_label(raw_label)

    range_text = None
    if len(raw_outcome) > 1 and raw_outcome[1]:
        range_text = raw_outcome[1]

    return {
        "rawOutcome": raw_outcome,
        "rawLabel": raw_label,
        "rangeText": range_text,
        "normalized": normalized,
    }


def normalize_player(path: Path) -> tuple[dict[str, Any], int, int]:
    data = read_json(path)

    normalized_tables: list[dict[str, Any]] = []
    outcome_count = 0
    unmatched_count = 0

    for table in data.get("tables", []):
        normalized_entries: list[dict[str, Any]] = []

        for entry in table.get("entries", []):
            normalized_outcomes = []

            for raw_outcome in entry.get("rawOutcomes", []):
                outcome_count += 1
                normalized_outcome = normalize_raw_outcome(raw_outcome)
                normalized_outcomes.append(normalized_outcome)

                if normalized_outcome["normalized"]["normalizedLabel"] == "UNMATCHED":
                    unmatched_count += 1

            normalized_entries.append(
                {
                    "diceRoll": entry.get("diceRoll"),
                    "rawModifiers": entry.get("rawModifiers", ""),
                    "rawRows": entry.get("rawRows", []),
                    "rawOutcomes": entry.get("rawOutcomes", []),
                    "normalizedOutcomes": normalized_outcomes,
                }
            )

        normalized_tables.append(
            {
                "tableNumber": table.get("tableNumber"),
                "sourcePointer": table.get("sourcePointer"),
                "side": table.get("side"),
                "column": table.get("column"),
                "entryCount": table.get("entryCount"),
                "entries": normalized_entries,
            }
        )

    result = {
        "schemaVersion": "bie.normalized-result-labels.v0",
        "parserVersion": PARSER_VERSION,
        "parsedAt": utc_now(),
        "source": data.get("source", {}),
        "player": data.get("player", {}),
        "role": data.get("role"),
        "tables": normalized_tables,
    }

    return result, outcome_count, unmatched_count


def configure_paths(season: int) -> None:
    global RESULT_CELLS_DIR, OUTPUT_DIR

    RESULT_CELLS_DIR = Path("data/baseball/parsed/strat365") / str(season) / "result-cells"
    OUTPUT_DIR = Path("data/baseball/parsed/strat365") / str(season) / "normalized-result-labels"


def select_paths(paths: list[Path], player_ids: list[int] | None) -> list[Path]:
    if not player_ids:
        return paths

    wanted = {str(player_id) for player_id in player_ids}
    selected = []
    found = set()

    for path in paths:
        player_id = path.name.replace(".result-cells.json", "")
        if player_id in wanted:
            selected.append(path)
            found.add(player_id)

    missing = sorted(wanted - found)
    if missing:
        raise ValueError(f"Player IDs not found in result-cell outputs: {missing}")

    return selected


def main() -> None:
    parser = argparse.ArgumentParser(description="Normalize Strat365 printed result labels.")
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
        help="Optional targeted player IDs from the selected season result-cell outputs.",
    )
    args = parser.parse_args()

    configure_paths(args.season)

    paths = select_paths(sorted(RESULT_CELLS_DIR.glob("*.result-cells.json")), args.player_ids)

    if not paths:
        raise FileNotFoundError(f"No result cell files found in {RESULT_CELLS_DIR}")

    parsed_count = 0
    failed_count = 0
    total_outcomes = 0
    total_unmatched = 0

    print("BIE Normalized Result Label Parser v0")
    print("=" * 72)
    print(f"Season: {args.season}")
    print(f"Result-cell files selected: {len(paths)}")

    for path in paths:
        player_id = path.name.replace(".result-cells.json", "")

        try:
            normalized, outcome_count, unmatched_count = normalize_player(path)
            output_path = OUTPUT_DIR / f"{player_id}.normalized-result-labels.json"
            write_json(output_path, normalized)

            player = normalized.get("player", {})

            print(
                f"NORMALIZED {player.get('playerId')} {player.get('playerName')} "
                f"role={normalized.get('role')} outcomes={outcome_count} unmatched={unmatched_count}"
            )

            parsed_count += 1
            total_outcomes += outcome_count
            total_unmatched += unmatched_count

        except Exception as exc:
            print(f"FAILED {player_id} error={exc}")
            failed_count += 1

    print("-" * 72)
    print(f"Normalized files: {parsed_count}")
    print(f"Failed: {failed_count}")
    print(f"Total outcome rows: {total_outcomes}")
    print(f"Unmatched outcome rows: {total_unmatched}")
    print(f"Output: {OUTPUT_DIR}")
    print("=" * 72)

    if failed_count or total_unmatched:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
