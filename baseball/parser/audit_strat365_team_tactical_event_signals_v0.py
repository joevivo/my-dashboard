from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any


CATEGORY_PATTERNS: dict[str, re.Pattern[str]] = {
    "hit_and_run": re.compile(
        r"\bhit[- ]and[- ]run\b",
        re.IGNORECASE,
    ),
    "stolen_base": re.compile(
        r"\bstole\b|\bstolen base\b",
        re.IGNORECASE,
    ),
    "caught_stealing": re.compile(
        r"\bcaught stealing\b",
        re.IGNORECASE,
    ),
    "pickoff": re.compile(
        r"\bpicked off\b|\bpickoff\b",
        re.IGNORECASE,
    ),
    "runner_advance": re.compile(
        r"\badvanced? to\b|"
        r"\badvances? to\b|"
        r"\btakes? second\b|"
        r"\btakes? third\b|"
        r"\bgoes? to second\b|"
        r"\bgoes? to third\b|"
        r"\bholds? at\b|"
        r"\bscores?\b",
        re.IGNORECASE,
    ),
    "runner_out_on_bases": re.compile(
        r"\bout at second\b|"
        r"\bout at third\b|"
        r"\bout at home\b|"
        r"\bthrown out\b|"
        r"\bgunned down\b|"
        r"\bcaught stealing\b|"
        r"\bpicked off\b",
        re.IGNORECASE,
    ),
    "pinch_hitter": re.compile(
        r"\bpinch[- ]hit(?:ter|ting)?\b",
        re.IGNORECASE,
    ),
    "pinch_runner": re.compile(
        r"\bpinch[- ]run(?:ner|ning)?\b",
        re.IGNORECASE,
    ),
    "defensive_substitution": re.compile(
        r"\bdefensive replacement\b|"
        r"\bdefensive substitution\b|"
        r"\bnow playing\b",
        re.IGNORECASE,
    ),
    "general_substitution": re.compile(
        r"\breplaces?\b|"
        r"\breplaced by\b|"
        r"\benters the game\b|"
        r"\bcomes into the game\b|"
        r"\bmoves? to\b|"
        r"\bswitches? from\b",
        re.IGNORECASE,
    ),
    "bullpen_change": re.compile(
        r"\bnow pitching\b|"
        r"\bpitching change\b|"
        r"\brelieves?\b|"
        r"\bcomes in to pitch\b|"
        r"\benters to pitch\b|"
        r"\breplaces? .{0,45} on the mound\b",
        re.IGNORECASE,
    ),
    "injury": re.compile(
        r"\binjur(?:y|ed|ies)\b",
        re.IGNORECASE,
    ),
    "error": re.compile(
        r"\berror\b",
        re.IGNORECASE,
    ),
    "sacrifice": re.compile(
        r"\bsacrifice\b|\bsac bunt\b",
        re.IGNORECASE,
    ),
    "double_play": re.compile(
        r"\bdouble play\b",
        re.IGNORECASE,
    ),
    "wild_pitch": re.compile(
        r"\bwild pitch\b",
        re.IGNORECASE,
    ),
    "passed_ball": re.compile(
        r"\bpassed ball\b",
        re.IGNORECASE,
    ),
    "balk": re.compile(
        r"\bbalk\b",
        re.IGNORECASE,
    ),
}


TAG_ALIASES: dict[str, str] = {
    "hit_and_run": "hit_and_run",
    "stolen_base": "stolen_base",
    "caught_stealing": "caught_stealing",
    "pickoff": "pickoff",
    "pinch_hitter": "pinch_hitter",
    "pinch_runner": "pinch_runner",
    "defensive_substitution": "defensive_substitution",
    "injury": "injury",
    "error": "error",
    "sacrifice": "sacrifice",
    "double_play": "double_play",
    "wild_pitch": "wild_pitch",
    "passed_ball": "passed_ball",
    "balk": "balk",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def text_value(value: Any) -> str:
    if value is None:
        return ""

    if isinstance(value, str):
        return value.strip()

    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def combined_text(row: dict[str, Any]) -> str:
    parts = [
        text_value(row.get(field))
        for field in (
            "text",
            "rawText",
            "result",
            "miscellaneous",
            "batter",
            "baserunners",
            "details",
        )
    ]

    return " ".join(part for part in parts if part)


def evidence_line(row: dict[str, Any], text: str) -> str:
    clean_text = " ".join(text.split())

    if len(clean_text) > 260:
        clean_text = clean_text[:260] + "..."

    occupied = row.get("occupiedBasesBefore") or []
    bases = ",".join(str(value) for value in occupied) or "<EMPTY>"

    return (
        f"date={row.get('leagueDate')}; "
        f"gameId={row.get('gameId')}; "
        f"sequence={row.get('sequence')}; "
        f"perspective={row.get('teamPerspective')}; "
        f"inning={row.get('inning')}; "
        f"half={row.get('half')}; "
        f"outsBefore={row.get('outsBefore')}; "
        f"basesBefore={bases}; "
        f"recordType={row.get('recordType')}; "
        f"controlType={row.get('controlType')}; "
        f"text={clean_text}"
    )


def sort_counter(counter: Counter[str]) -> list[tuple[str, int]]:
    return sorted(
        counter.items(),
        key=lambda item: (-item[1], item[0]),
    )


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--event-ledger", required=True)
    parser.add_argument("--expected-dataset-sha256", required=True)
    parser.add_argument("--expected-ledger-sha256", required=True)
    parser.add_argument("--sample-limit", type=int, default=3)
    return parser.parse_args()


def main() -> int:
    arguments = parse_arguments()

    dataset_path = Path(arguments.dataset).resolve()
    ledger_path = Path(arguments.event_ledger).resolve()

    try:
        if not dataset_path.is_file():
            raise ValueError(
                f"Review dataset is missing: {dataset_path}"
            )

        if not ledger_path.is_file():
            raise ValueError(
                f"Event ledger is missing: {ledger_path}"
            )

        dataset_hash = sha256(dataset_path)
        ledger_hash = sha256(ledger_path)

        if dataset_hash != arguments.expected_dataset_sha256.upper():
            raise ValueError("Review-dataset hash mismatch.")

        if ledger_hash != arguments.expected_ledger_sha256.upper():
            raise ValueError("Event-ledger hash mismatch.")

        dataset = json.loads(
            dataset_path.read_text(encoding="utf-8")
        )

        counts = dataset.get("counts") or {}

        if int(counts.get("leagueGames") or 0) != 90:
            raise ValueError("Dataset league-game count differs.")

        if int(counts.get("teamGames") or 0) != 15:
            raise ValueError("Dataset team-game count differs.")

        if int(counts.get("eventLedgerRows") or 0) != 9394:
            raise ValueError("Dataset event-ledger count differs.")

        perspective_counts: Counter[str] = Counter()
        record_type_counts: Counter[str] = Counter()
        control_type_counts: Counter[str] = Counter()
        lexical_tag_counts: Counter[str] = Counter()
        lexical_perspective_counts: Counter[str] = Counter()

        category_league_counts: Counter[str] = Counter()
        category_aquarium_counts: Counter[str] = Counter()

        samples: dict[str, list[str]] = {
            category: []
            for category in CATEGORY_PATTERNS
        }

        event_keys: set[str] = set()

        ledger_row_count = 0
        aquarium_row_count = 0
        invalid_json_count = 0
        duplicate_event_key_count = 0
        missing_event_key_count = 0
        missing_state_count = 0

        with ledger_path.open(
            "r",
            encoding="utf-8",
            newline="",
        ) as handle:
            for raw_line in handle:
                if not raw_line.strip():
                    continue

                ledger_row_count += 1

                try:
                    row = json.loads(raw_line)
                except json.JSONDecodeError:
                    invalid_json_count += 1
                    continue

                event_key = str(row.get("eventKey") or "").strip()

                if not event_key:
                    missing_event_key_count += 1
                elif event_key in event_keys:
                    duplicate_event_key_count += 1
                else:
                    event_keys.add(event_key)

                perspective = str(
                    row.get("teamPerspective") or "<BLANK>"
                )

                record_type = str(
                    row.get("recordType") or "<BLANK>"
                )

                control_type = str(
                    row.get("controlType") or "<BLANK>"
                )

                perspective_counts[perspective] += 1
                record_type_counts[record_type] += 1
                control_type_counts[control_type] += 1

                is_aquarium = perspective != "none"

                if is_aquarium:
                    aquarium_row_count += 1

                if (
                    row.get("inning") is None
                    or not str(row.get("half") or "").strip()
                    or row.get("outsBefore") is None
                ):
                    missing_state_count += 1

                tags = {
                    str(tag)
                    for tag in (row.get("lexicalTags") or [])
                }

                for tag in tags:
                    lexical_tag_counts[tag] += 1
                    lexical_perspective_counts[
                        f"{perspective}|{tag}"
                    ] += 1

                event_text = combined_text(row)

                matched_categories: set[str] = set()

                for tag in tags:
                    category = TAG_ALIASES.get(tag)

                    if category:
                        matched_categories.add(category)

                for category, pattern in CATEGORY_PATTERNS.items():
                    if pattern.search(event_text):
                        matched_categories.add(category)

                if (
                    "pitch" in control_type.lower()
                    and control_type != "<BLANK>"
                ):
                    matched_categories.add("bullpen_change")

                for category in matched_categories:
                    category_league_counts[category] += 1

                    if is_aquarium:
                        category_aquarium_counts[category] += 1

                        if (
                            len(samples[category])
                            < arguments.sample_limit
                        ):
                            samples[category].append(
                                evidence_line(row, event_text)
                            )

        if ledger_row_count != 9394:
            raise ValueError(
                "Ledger row count differs: "
                f"expected=9394; actual={ledger_row_count}"
            )

        if aquarium_row_count != 1527:
            raise ValueError(
                "Aquarium-perspective row count differs: "
                f"expected=1527; actual={aquarium_row_count}"
            )

        if invalid_json_count:
            raise ValueError(
                f"Invalid JSON ledger rows: {invalid_json_count}"
            )

        if duplicate_event_key_count:
            raise ValueError(
                "Duplicate event keys: "
                f"{duplicate_event_key_count}"
            )

        if missing_event_key_count:
            raise ValueError(
                "Missing event keys: "
                f"{missing_event_key_count}"
            )

        print("# RESULT SUMMARY")
        print("TACTICAL_EVENT_SIGNAL_AUDIT: PASS")
        print(f"REVIEW_DATASET_SHA256: {dataset_hash}")
        print(f"EVENT_LEDGER_SHA256: {ledger_hash}")
        print(f"EVENT_LEDGER_ROW_COUNT: {ledger_row_count}")
        print(
            "AQUARIUM_PERSPECTIVE_ROW_COUNT: "
            f"{aquarium_row_count}"
        )
        print(
            "INVALID_JSON_LINE_COUNT: "
            f"{invalid_json_count}"
        )
        print(
            "DUPLICATE_EVENT_KEY_COUNT: "
            f"{duplicate_event_key_count}"
        )
        print(
            "MISSING_EVENT_KEY_COUNT: "
            f"{missing_event_key_count}"
        )
        print(
            "MISSING_STATE_FIELD_COUNT: "
            f"{missing_state_count}"
        )

        for name, count in sorted(perspective_counts.items()):
            print(f"PERSPECTIVE_COUNT: {name}={count}")

        for name, count in sort_counter(record_type_counts)[:20]:
            print(f"RECORD_TYPE_COUNT: {name}={count}")

        for name, count in sort_counter(control_type_counts)[:30]:
            print(f"CONTROL_TYPE_COUNT: {name}={count}")

        for name, count in sort_counter(lexical_tag_counts):
            print(f"LEXICAL_TAG_COUNT: {name}={count}")

        for name, count in sorted(
            lexical_perspective_counts.items()
        ):
            print(
                "LEXICAL_PERSPECTIVE_COUNT: "
                f"{name}={count}"
            )

        for category in CATEGORY_PATTERNS:
            print(
                "TACTICAL_CANDIDATE_COUNT: "
                f"{category}; "
                f"league={category_league_counts[category]}; "
                f"aquarium={category_aquarium_counts[category]}"
            )

            for sample in samples[category]:
                print(
                    "TACTICAL_CANDIDATE_SAMPLE: "
                    f"category={category}; {sample}"
                )

        print("FAILURE_COUNT: 0")
        print("FAILURE_DETAIL: none")
        print("FILES_MODIFIED_BY_AUDITOR: 0")
        print("LIVE_REQUESTS_EXECUTED: 0")
        return 0

    except Exception as exc:
        print("# RESULT SUMMARY")
        print("TACTICAL_EVENT_SIGNAL_AUDIT: FAIL")
        print("FAILURE_COUNT: 1")
        print(f"FAILURE_DETAIL: {exc}")
        print("FILES_MODIFIED_BY_AUDITOR: 0")
        print("LIVE_REQUESTS_EXECUTED: 0")
        return 1


if __name__ == "__main__":
    sys.exit(main())
