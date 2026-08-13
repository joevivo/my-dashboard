#!/usr/bin/env python3

import argparse
import hashlib
import json
import re
from pathlib import Path

from bs4 import BeautifulSoup


SCHEMA_VERSION = "bie.strat365.game-replay-candidate.v0"

INNING_WORDS = {
    "first": 1,
    "second": 2,
    "third": 3,
    "fourth": 4,
    "fifth": 5,
    "sixth": 6,
    "seventh": 7,
    "eighth": 8,
    "ninth": 9,
    "tenth": 10,
    "eleventh": 11,
    "twelfth": 12,
    "thirteenth": 13,
    "fourteenth": 14,
    "fifteenth": 15,
    "sixteenth": 16,
    "seventeenth": 17,
    "eighteenth": 18,
    "nineteenth": 19,
    "twentieth": 20,
}


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest().upper()


def sha256_text(value: str) -> str:
    return hashlib.sha256(
        value.encode("utf-8")
    ).hexdigest().upper()


def normalize_text(value: str) -> str:
    return re.sub(
        r"\s+",
        " ",
        value or "",
    ).strip()


def repo_relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(
            Path.cwd().resolve()
        ).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def inning_number(token: str):
    token = token.lower().strip()

    numeric = re.match(
        r"^(\d+)(?:st|nd|rd|th)?$",
        token,
    )

    if numeric:
        return int(numeric.group(1))

    return INNING_WORDS.get(token)


def parse_inning_marker(text: str):
    text = normalize_text(text)

    match = re.search(
        r"\b(top|bottom)\b"
        r"(?:\s+of)?"
        r"(?:\s+the)?"
        r"(?:\s+inning)?"
        r"\s+"
        r"("
        r"\d+(?:st|nd|rd|th)?"
        r"|first|second|third|fourth|fifth|sixth"
        r"|seventh|eighth|ninth|tenth|eleventh"
        r"|twelfth|thirteenth|fourteenth|fifteenth"
        r"|sixteenth|seventeenth|eighteenth"
        r"|nineteenth|twentieth"
        r")\b",
        text,
        flags=re.IGNORECASE,
    )

    if not match:
        return None

    inning = inning_number(
        match.group(2)
    )

    if inning is None:
        return None

    return {
        "half": match.group(1).upper(),
        "inning": inning,
    }


def row_text(row) -> str:
    cells = [
        normalize_text(
            cell.get_text(
                " ",
                strip=True,
            )
        )
        for cell in row.find_all(
            ["td", "th"]
        )
    ]

    cells = [
        cell
        for cell in cells
        if cell
    ]

    if cells:
        return " | ".join(cells)

    return normalize_text(
        row.get_text(
            " ",
            strip=True,
        )
    )


def choose_play_table(soup):
    candidates = []

    for index, table in enumerate(
        soup.find_all("table")
    ):
        rows = table.find_all("tr")

        marker_count = sum(
            1
            for row in rows
            if parse_inning_marker(
                row_text(row)
            )
            is not None
        )

        candidates.append(
            (
                marker_count,
                len(rows),
                index,
                table,
            )
        )

    if not candidates:
        raise ValueError(
            "No tables found in play-by-play source"
        )

    candidates.sort(
        key=lambda item: (
            item[0],
            item[1],
        ),
        reverse=True,
    )

    marker_count, row_count, index, table = (
        candidates[0]
    )

    if marker_count < 1:
        raise ValueError(
            "Unable to identify inning-bearing play-by-play table"
        )

    return {
        "table": table,
        "tableIndex": index,
        "rowCount": row_count,
        "markerCount": marker_count,
    }


def parse_events(table):
    marker_count = 0
    half_innings = []
    candidate_rows = []

    current_inning = None
    current_half = None
    source_row_ordinal = 0

    for row in table.find_all("tr"):
        source_row_ordinal += 1

        text = row_text(row)

        if not text:
            continue

        marker = parse_inning_marker(text)

        if marker is not None:
            current_inning = marker["inning"]
            current_half = marker["half"]

            marker_count += 1

            half_innings.append(
                {
                    "inning": current_inning,
                    "half": current_half,
                    "sourceRowOrdinal":
                        source_row_ordinal,
                }
            )

            continue

        if current_inning is None:
            continue

        cells = [
            normalize_text(
                cell.get_text(
                    " ",
                    strip=True,
                )
            )
            for cell in row.find_all("td")
        ]

        cells = [
            value
            for value in cells
            if value
        ]

        if not cells:
            continue

        candidate_rows.append(
            {
                "inning":
                    current_inning,
                "half":
                    current_half,
                "sourceRowOrdinal":
                    source_row_ordinal,
                "sourceClasses":
                    sorted(
                        str(value)
                        for value
                        in row.get(
                            "class",
                            [],
                        )
                    ),
                "cells":
                    cells,
            }
        )

    score_pattern = re.compile(
        r"\b\d+\s*[-–]\s*\d+\b"
        r"|\bscore(?:d|s|ing)?\b",
        flags=re.IGNORECASE,
    )

    numeric_pattern = re.compile(
        r"^[\d\s.+\-–]+$"
    )

    profiles = {}

    for row in candidate_rows:
        for index, value in enumerate(
            row["cells"]
        ):
            profile = profiles.setdefault(
                index,
                {
                    "nonempty": 0,
                    "alpha": 0,
                    "numeric": 0,
                    "scorelike": 0,
                    "words": 0,
                },
            )

            profile["nonempty"] += 1

            profile["words"] += len(
                re.findall(
                    r"[A-Za-z]+",
                    value,
                )
            )

            if re.search(
                r"[A-Za-z]",
                value,
            ):
                profile["alpha"] += 1

            if numeric_pattern.fullmatch(
                value
            ):
                profile["numeric"] += 1

            if score_pattern.search(
                value
            ):
                profile["scorelike"] += 1

    ranked = []

    for index, profile in profiles.items():
        avg_words = (
            profile["words"]
            / max(
                profile["nonempty"],
                1,
            )
        )

        narrative_score = (
            profile["alpha"]
            * max(
                avg_words,
                0.1,
            )
            - profile["numeric"] * 2
            - profile["scorelike"]
        )

        ranked.append(
            (
                narrative_score,
                index,
            )
        )

    if not ranked:
        raise ValueError(
            "Unable to identify narrative event column"
        )

    ranked.sort(reverse=True)

    narrative_column = ranked[0][1]

    events = []

    for row in candidate_rows:
        cells = row["cells"]

        if len(cells) <= narrative_column:
            continue

        event_text = cells[
            narrative_column
        ]

        if not event_text:
            continue

        sequence = len(events) + 1

        events.append(
            {
                "eventSequence":
                    sequence,
                "inning":
                    row["inning"],
                "halfInning":
                    row["half"],
                "text":
                    event_text,
                "sourceRowOrdinal":
                    row[
                        "sourceRowOrdinal"
                    ],
                "sourceTextLength":
                    len(event_text),
                "sourceTextSha256":
                    sha256_text(
                        event_text
                    ),
                "sourceClasses":
                    row[
                        "sourceClasses"
                    ],
            }
        )

    return {
        "events":
            events,
        "markerCount":
            marker_count,
        "halfInnings":
            half_innings,
        "sourceDataRowCount":
            len(candidate_rows),
        "narrativeColumn":
            narrative_column,
    }


def count_safety_signals(events):
    score_like = 0
    terminal_language = 0

    score_pattern = re.compile(
        r"\b\d+\s*[-–]\s*\d+\b"
        r"|\bscore(?:d|s|ing)?\b",
        flags=re.IGNORECASE,
    )

    terminal_pattern = re.compile(
        r"\b("
        r"final"
        r"|game\s+over"
        r"|wins?"
        r"|won"
        r"|defeats?"
        r"|victory"
        r")\b",
        flags=re.IGNORECASE,
    )

    for event in events:
        text = event["text"]

        if score_pattern.search(text):
            score_like += 1

        if terminal_pattern.search(text):
            terminal_language += 1

    return {
        "scoreLikeEventCount":
            score_like,
        "terminalLanguageEventCount":
            terminal_language,
    }



def extract_hidden_result_from_recap(result_bytes):
    html = result_bytes.decode(
        "utf-8",
        errors="replace",
    )

    soup = BeautifulSoup(
        html,
        "lxml",
    )

    for table in soup.find_all("table"):
        rows = table.find_all("tr")

        for header_index, row in enumerate(rows):
            headers = [
                normalize_text(
                    cell.get_text(" ", strip=True)
                )
                for cell in row.find_all(["th", "td"])
            ]

            upper = [
                value.upper()
                for value in headers
            ]

            if not all(
                token in upper
                for token in ("R", "H", "E")
            ):
                continue

            run_index = upper.index("R")

            if run_index < 2:
                continue

            entries = []

            for data_row in rows[header_index + 1:]:
                values = [
                    normalize_text(
                        cell.get_text(" ", strip=True)
                    )
                    for cell in data_row.find_all(["th", "td"])
                ]

                if len(values) <= run_index:
                    continue

                team_index = None

                for index, value in enumerate(values[:run_index]):
                    if re.search(r"[A-Za-z]", value):
                        team_index = index
                        break

                if team_index is None:
                    continue

                inning_cells = values[
                    team_index + 1:run_index
                ]

                inning_runs = [
                    int(value)
                    for value in inning_cells
                    if re.fullmatch(r"\d+", value)
                ]

                # Regulation line scores contain at least
                # eight offensive half-innings for each team.
                if len(inning_runs) < 8:
                    continue

                team_name = values[team_index]
                runs = sum(inning_runs)

                entries.append(
                    (
                        team_name,
                        runs,
                    )
                )

                if len(entries) == 2:
                    break

            if len(entries) != 2:
                continue

            if entries[0][0] == entries[1][0]:
                continue

            if entries[0][1] == entries[1][1]:
                continue

            final_score = {
                entries[0][0]:
                    entries[0][1],
                entries[1][0]:
                    entries[1][1],
            }

            winner = (
                entries[0][0]
                if entries[0][1] > entries[1][1]
                else entries[1][0]
            )

            return {
                "winner":
                    winner,
                "finalScore":
                    final_score,
                "sourceClassification":
                    "RECAP_HTML",
            }

    raise ValueError(
        "Unable to extract authoritative result from recap line score"
    )


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--play-by-play",
        required=True,
    )

    parser.add_argument(
        "--metadata",
        required=True,
    )

    parser.add_argument(
        "--result-source",
        required=True,
    )

    parser.add_argument(
        "--result-metadata",
        required=True,
    )

    parser.add_argument(
        "--output",
        required=True,
    )

    parser.add_argument(
        "--expected-league-id",
        required=True,
    )

    parser.add_argument(
        "--expected-team-id",
        required=True,
    )

    parser.add_argument(
        "--expected-game-id",
        required=True,
    )

    args = parser.parse_args()

    pbp_path = Path(
        args.play_by_play
    )

    metadata_path = Path(
        args.metadata
    )

    result_path = Path(
        args.result_source
    )

    result_metadata_path = Path(
        args.result_metadata
    )

    output_path = Path(
        args.output
    )

    pbp_bytes = pbp_path.read_bytes()

    html = pbp_bytes.decode(
        "utf-8",
        errors="replace",
    )

    metadata = json.loads(
        metadata_path.read_text(
            encoding="utf-8"
        )
    )

    result_bytes = result_path.read_bytes()

    result_metadata = json.loads(
        result_metadata_path.read_text(
            encoding="utf-8"
        )
    )

    result_hash = sha256_bytes(
        result_bytes
    )

    result_metadata_hash = str(
        result_metadata.get(
            "sha256",
            "",
        )
    ).upper()

    if (
        result_hash
        != result_metadata_hash
    ):
        raise ValueError(
            "Result source hash does not match capture metadata"
        )

    if (
        str(
            result_metadata.get(
                "leagueId"
            )
        )
        != str(
            args.expected_league_id
        )
    ):
        raise ValueError(
            "Result source league identity mismatch"
        )

    if (
        str(
            result_metadata.get(
                "gameId"
            )
        )
        != str(
            args.expected_game_id
        )
    ):
        raise ValueError(
            "Result source game identity mismatch"
        )

    result_team_ids = [
        str(value)
        for value
        in result_metadata.get(
            "teamIds",
            [],
        )
    ]

    if (
        str(
            args.expected_team_id
        )
        not in result_team_ids
    ):
        raise ValueError(
            "Result source team identity mismatch"
        )

    hidden_result = extract_hidden_result_from_recap(
        result_bytes
    )

    actual_hash = sha256_bytes(
        pbp_bytes
    )

    metadata_hash = str(
        metadata.get(
            "sha256",
            "",
        )
    ).upper()

    if actual_hash != metadata_hash:
        raise ValueError(
            "Play-by-play hash does not match capture metadata"
        )

    if (
        str(metadata.get("leagueId"))
        != str(args.expected_league_id)
    ):
        raise ValueError(
            "League identity mismatch"
        )

    if (
        str(metadata.get("gameId"))
        != str(args.expected_game_id)
    ):
        raise ValueError(
            "Game identity mismatch"
        )

    team_ids = [
        str(value)
        for value in metadata.get(
            "teamIds",
            [],
        )
    ]

    if (
        str(args.expected_team_id)
        not in team_ids
    ):
        raise ValueError(
            "Team identity not present in capture metadata"
        )

    soup = BeautifulSoup(
        html,
        "lxml",
    )

    selected = choose_play_table(
        soup
    )

    parsed = parse_events(
        selected["table"]
    )

    events = parsed["events"]

    if not events:
        raise ValueError(
            "No replay events parsed"
        )

    for expected, event in enumerate(
        events,
        start=1,
    ):
        if (
            event["eventSequence"]
            != expected
        ):
            raise ValueError(
                "Non-contiguous event sequence"
            )

        if event["inning"] < 1:
            raise ValueError(
                "Invalid event inning"
            )

        if event["halfInning"] not in {
            "TOP",
            "BOTTOM",
        }:
            raise ValueError(
                "Invalid half-inning value"
            )

    signals = count_safety_signals(
        events
    )

    artifact = {
        "schemaVersion":
            SCHEMA_VERSION,

        "classification":
            "QUARANTINED_HISTORICAL_FIXTURE",

        "bindingEligibility":
            "READY_FOR_REAL_REPLAY_FIREWALL",

        "identity": {
            "leagueId":
                str(args.expected_league_id),
            "teamId":
                str(args.expected_team_id),
            "gameId":
                str(args.expected_game_id),
        },

        "sourceEvidence": {
            "playByPlay": {
                "path":
                    repo_relative(
                        pbp_path
                    ),
                "sha256":
                    actual_hash,
                "byteCount":
                    len(pbp_bytes),
            },

            "captureMetadata": {
                "path":
                    repo_relative(
                        metadata_path
                    ),
                "capturedAtUtc":
                    metadata.get(
                        "capturedAtUtc"
                    ),
                "httpStatus":
                    metadata.get(
                        "httpStatus"
                    ),
                "contentType":
                    metadata.get(
                        "contentType"
                    ),
                "rawResponsePath":
                    metadata.get(
                        "rawResponsePath"
                    ),
                "responseHeadersPath":
                    metadata.get(
                        "responseHeadersPath"
                    ),
                "provenance":
                    metadata.get(
                        "provenance",
                        {},
                    ),
            },
        },

        "parseStats": {
            "selectedTableIndex":
                selected["tableIndex"],
            "selectedTableRowCount":
                selected["rowCount"],
            "halfInningMarkerCount":
                parsed["markerCount"],
            "halfInningCount":
                len(
                    parsed["halfInnings"]
                ),
            "sourceDataRowCount":
                parsed[
                    "sourceDataRowCount"
                ],
            "narrativeColumn":
                parsed[
                    "narrativeColumn"
                ],
            "eventCount":
                len(events),
            "firstEventSequence":
                events[0][
                    "eventSequence"
                ],
            "lastEventSequence":
                events[-1][
                    "eventSequence"
                ],
        },

        "safetySignals": {
            **signals,
            "explicitResultFieldsIncluded":
                False,
            "eventTextSafetyAuditRequired":
                False,
            "authoritativeResultValuesIncluded":
                True,
        },

        "events":
            events,
    }

    artifact[
        "sourceEvidence"
    ][
        "authoritativeResultSource"
    ] = {
        "classification":
            "RECAP_HTML",
        "path":
            repo_relative(
                result_path
            ),
        "sha256":
            result_hash,
        "byteCount":
            len(result_bytes),
        "captureMetadata": {
            "path":
                repo_relative(
                    result_metadata_path
                ),
            "capturedAtUtc":
                result_metadata.get(
                    "capturedAtUtc"
                ),
            "httpStatus":
                result_metadata.get(
                    "httpStatus"
                ),
            "contentType":
                result_metadata.get(
                    "contentType"
                ),
            "provenance":
                result_metadata.get(
                    "provenance",
                    {},
                ),
        },
        "resultValuesIncluded":
            False,
    }

    artifact["hiddenResult"] = {
        "winner":
            hidden_result["winner"],
        "finalScore":
            hidden_result["finalScore"],
        "sourceClassification":
            hidden_result["sourceClassification"],
        "spoilerBoundary":
            "SERVER_SIDE_ONLY",
    }

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path.write_text(
        json.dumps(
            artifact,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )


if __name__ == "__main__":
    main()