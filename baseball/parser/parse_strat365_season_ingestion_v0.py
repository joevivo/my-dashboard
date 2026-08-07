from __future__ import annotations

import argparse
import hashlib
import html
import re
import json
from pathlib import Path
from typing import Any


GAME_SOURCE_FAMILIES = (
    'gamePlayByPlay',
    'gameRecap',
    'gameReplay',
)
LEAGUE_SCORE_FAMILY = 'leagueScores'
LEAGUE_INVENTORY_METADATA_FAMILIES = {
    'leagueScores',
    'teamSchedule',
}
def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as source:
        for block in iter(lambda: source.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest().upper()


def pick(record: Any, *names: str) -> Any:
    if not isinstance(record, dict):
        return None
    normalized = {str(key).lower(): value for key, value in record.items()}
    for name in names:
        if name.lower() in normalized:
            return normalized[name.lower()]
    return None


def derive_manifest_expectations(
    manifest: dict[str, Any],
) -> tuple[dict[str, int], set[int], int]:
    requests = pick(manifest, 'requests')

    if not isinstance(requests, list) or not requests:
        raise ValueError(
            'Run manifest exposes no request inventory.'
        )

    actual_family_counts: dict[str, int] = {}
    expected_game_ids: set[int] = set()

    for request in requests:
        if not isinstance(request, dict):
            raise ValueError(
                'Run manifest request inventory contains '
                'a non-object row.'
            )

        family = str(
            pick(request, 'sourceFamily') or 'UNKNOWN'
        )
        actual_family_counts[family] = (
            actual_family_counts.get(family, 0) + 1
        )

        if family in GAME_SOURCE_FAMILIES:
            game_id = pick(request, 'gameId')

            if game_id is None:
                raise ValueError(
                    f'{family} request is missing gameId.'
                )

            expected_game_ids.add(int(game_id))

    expected_game_count = len(expected_game_ids)

    if expected_game_count < 1:
        raise ValueError(
            'Run manifest exposes no game-page identities.'
        )

    expected_families = {
        family: expected_game_count
        for family in GAME_SOURCE_FAMILIES
    }
    expected_families[LEAGUE_SCORE_FAMILY] = 1

    if actual_family_counts != expected_families:
        raise ValueError(
            'Run manifest source-family inventory is not '
            'one leagueScores row plus three pages per game: '
            f'{actual_family_counts}'
        )

    return (
        expected_families,
        expected_game_ids,
        sum(expected_families.values()),
    )

def resolve_artifact(value: Any, repo_root: Path, run_directory: Path) -> Path | None:
    if value is None or not str(value).strip():
        return None
    candidate = Path(str(value).replace('\\', '/'))
    if candidate.is_absolute():
        return candidate.resolve()
    repo_candidate = (repo_root / candidate).resolve()
    if repo_candidate.exists():
        return repo_candidate
    return (run_directory / candidate).resolve()


def clean_html(fragment: str) -> str:
    without_scripts = re.sub(
        r"(?is)<script\b.*?</script>|<style\b.*?</style>",
        " ",
        fragment,
    )
    without_tags = re.sub(r"(?is)<[^>]+>", " ", without_scripts)
    return " ".join(html.unescape(without_tags).split())


def parse_league_inventory(
    body_path: Path,
    league_id: str,
    expected_game_ids: set[int],
) -> list[dict[str, Any]]:
    expected_game_ids = {
        int(game_id)
        for game_id in expected_game_ids
    }
    expected_game_count = len(expected_game_ids)

    if expected_game_count < 1:
        raise ValueError(
            'Expected game inventory is empty.'
        )

    source = body_path.read_text(encoding='utf-8')
    tables = re.findall(
        r'(?is)<table\b[^>]*>(.*?)</table>',
        source,
    )

    if len(tables) == 1:
        row_matches = list(
            re.finditer(
                r'(?is)<tr\b[^>]*>(.*?)</tr>',
                tables[0],
            )
        )
        recap_route_pattern = re.compile(
            rf'/game/{re.escape(league_id)}/(\d+)',
            re.IGNORECASE,
        )
        games: list[dict[str, Any]] = []

        for row_match in row_matches:
            row_source = row_match.group(1)
            route_game_ids = sorted(
                {
                    int(match.group(1))
                    for match in recap_route_pattern.finditer(
                        row_source
                    )
                    if int(match.group(1))
                    in expected_game_ids
                }
            )

            if not route_game_ids:
                continue

            if len(route_game_ids) != 1:
                raise ValueError(
                    'Team-schedule row exposes multiple '
                    f'captured game IDs: {route_game_ids}'
                )

            cells = [
                clean_html(cell_match.group(1))
                for cell_match in re.finditer(
                    r'(?is)<t[dh]\b[^>]*>(.*?)</t[dh]>',
                    row_source,
                )
            ]
            result_text = ' '.join(
                cell for cell in cells if cell
            )

            if not result_text:
                raise ValueError(
                    'Team-schedule row has no result text.'
                )

            game_index = len(games)
            game_id = route_game_ids[0]

            games.append(
                {
                    'blockIndex': game_index + 1,
                    'seriesIndex': game_index // 3 + 1,
                    'seriesGameNumber': game_index % 3 + 1,
                    'seriesGameLabel': (
                        cells[0]
                        if cells and cells[0]
                        else f'Game {game_index + 1}'
                    ),
                    'gameId': game_id,
                    'resultText': result_text,
                    'inventorySourceType': (
                        'TEAM_SCHEDULE_SINGLE_TABLE'
                    ),
                }
            )

        actual_game_ids = {
            int(game['gameId'])
            for game in games
        }

        if (
            len(games) != expected_game_count
            or actual_game_ids != expected_game_ids
        ):
            raise ValueError(
                'Team-schedule game inventory differs from '
                'the locked manifest: '
                f'missing={sorted(expected_game_ids - actual_game_ids)}, '
                f'extra={sorted(actual_game_ids - expected_game_ids)}, '
                f'rows={len(games)}'
            )

        return games

    expected_table_count = expected_game_count * 3

    if len(tables) != expected_table_count:
        raise ValueError(
            f'Expected either one team-schedule table or '
            f'{expected_table_count} league-score tables; '
            f'found {len(tables)}.'
        )

    if len(tables) % 3 != 0:
        raise ValueError(
            'League-score tables do not form '
            'three-table blocks.'
        )

    games = []
    route_pattern = re.compile(
        rf'/game/(?:playbyplay/|replay/)?'
        rf'{re.escape(league_id)}/(\d+)',
        re.IGNORECASE,
    )

    for table_index in range(0, len(tables), 3):
        block_number = table_index // 3 + 1
        block_source = ''.join(
            tables[table_index:table_index + 3]
        )
        route_game_ids = sorted(
            {
                int(match.group(1))
                for match in route_pattern.finditer(
                    block_source
                )
            }
        )

        if len(route_game_ids) != 1:
            raise ValueError(
                f'Block {block_number} exposes '
                f'{len(route_game_ids)} game IDs.'
            )

        label = clean_html(tables[table_index])
        result_text = clean_html(
            tables[table_index + 1]
        )

        if not result_text:
            raise ValueError(
                f'Block {block_number} has no result text.'
            )

        games.append(
            {
                'blockIndex': block_number,
                'seriesIndex': table_index // 9 + 1,
                'seriesGameNumber': (
                    table_index // 3 % 3 + 1
                ),
                'seriesGameLabel': label,
                'gameId': route_game_ids[0],
                'resultText': result_text,
                'inventorySourceType': (
                    'FULL_LEAGUE_THREE_TABLE_BLOCK'
                ),
            }
        )

    actual_game_ids = {
        int(game['gameId'])
        for game in games
    }

    if (
        len(games) != expected_game_count
        or actual_game_ids != expected_game_ids
    ):
        raise ValueError(
            'Full-league game inventory differs from '
            'the locked manifest: '
            f'missing={sorted(expected_game_ids - actual_game_ids)}, '
            f'extra={sorted(actual_game_ids - expected_game_ids)}, '
            f'rows={len(games)}'
        )

    return games

def parse_table_rows(table_body: str) -> list[list[str]]:
    rows: list[list[str]] = []
    for row_match in re.finditer(r"(?is)<tr\b[^>]*>(.*?)</tr>", table_body):
        cells = [
            clean_html(cell_match.group(1))
            for cell_match in re.finditer(
                r"(?is)<t[dh]\b[^>]*>(.*?)</t[dh]>",
                row_match.group(1),
            )
        ]
        rows.append(cells)
    return rows


def extract_last_h3(fragment: str) -> str:
    matches = list(re.finditer(r"(?is)<h3\b[^>]*>(.*?)</h3\s*>", fragment))
    if not matches:
        raise ValueError("Team context does not contain an h3 team name.")
    value = clean_html(matches[-1].group(1))
    if not value:
        raise ValueError("Team h3 is blank.")
    return value


def parse_pitcher_outs(value: str) -> int:
    whole_text, separator, fraction_text = value.partition(".")
    whole = int(whole_text)
    fraction = int(fraction_text) if separator else 0
    if fraction not in {0, 1, 2}:
        raise ValueError(f"Invalid innings-pitched value: {value}")
    return whole * 3 + fraction


def parse_player_identity(identity: str) -> tuple[str | None, str]:
    match = re.fullmatch(r"(?P<prefix>[A-Z]+)\s*-\s*(?P<name>.+)", identity)
    if match is None:
        return None, identity
    return match.group("prefix"), match.group("name").strip()


def parse_hitter_table(table_body: str) -> list[dict[str, Any]]:
    rows = parse_table_rows(table_body)
    expected_header = ["Hitters", "P", "AB", "R", "H", "RBI", "BA"]
    if not rows or rows[0] != expected_header:
        raise ValueError(f"Unexpected hitter header: {rows[0] if rows else None}")

    players: list[dict[str, Any]] = []
    for source_row_index, cells in enumerate(rows[1:], start=2):
        if not cells or not cells[0]:
            continue
        if cells[0].lower() in {"total", "totals"}:
            continue
        if len(cells) != 7:
            raise ValueError(f"Hitter row has {len(cells)} cells: {cells}")

        substitution_prefix, display_name = parse_player_identity(cells[0])
        players.append(
            {
                "displayName": display_name,
                "rawIdentity": cells[0],
                "substitutionPrefix": substitution_prefix,
                "position": cells[1],
                "atBats": int(cells[2]),
                "runs": int(cells[3]),
                "hits": int(cells[4]),
                "runsBattedIn": int(cells[5]),
                "displayedBattingAverage": cells[6],
                "sourceRowIndex": source_row_index,
                "rawCells": cells,
            }
        )

    return players


def parse_pitcher_table(table_body: str) -> list[dict[str, Any]]:
    rows = parse_table_rows(table_body)
    expected_header = [
        "Pitchers",
        "Decision",
        "IP",
        "H",
        "R",
        "ER",
        "BB",
        "SO",
        "HR",
        "PC",
        "ERA",
    ]
    if not rows or rows[0] != expected_header:
        raise ValueError(f"Unexpected pitcher header: {rows[0] if rows else None}")

    players: list[dict[str, Any]] = []
    for source_row_index, cells in enumerate(rows[1:], start=2):
        if not cells or not cells[0]:
            continue
        if cells[0].lower() in {"total", "totals"}:
            continue
        if len(cells) != 11:
            raise ValueError(f"Pitcher row has {len(cells)} cells: {cells}")

        substitution_prefix, display_name = parse_player_identity(cells[0])
        players.append(
            {
                "displayName": display_name,
                "rawIdentity": cells[0],
                "substitutionPrefix": substitution_prefix,
                "decision": cells[1] or None,
                "inningsPitched": cells[2],
                "inningsPitchedOuts": parse_pitcher_outs(cells[2]),
                "hitsAllowed": int(cells[3]),
                "runsAllowed": int(cells[4]),
                "earnedRuns": int(cells[5]),
                "walks": int(cells[6]),
                "strikeouts": int(cells[7]),
                "homeRunsAllowed": int(cells[8]),
                "pitchCount": int(cells[9]),
                "displayedEarnedRunAverage": cells[10],
                "sourceRowIndex": source_row_index,
                "rawCells": cells,
            }
        )

    return players


def parse_replay_orientation(source: str) -> tuple[str, str]:
    opening = re.search(
        r"(?is)<table\b(?=[^>]*\bclass\s*=\s*[\"\x27][^\"\x27]*\bcleft\b[^\"\x27]*[\"\x27])[^>]*>",
        source,
    )
    if opening is None:
        raise ValueError("Replay cleft title table was not found.")

    prefix = clean_html(source[opening.start():opening.start() + 6000])
    title_match = re.match(
        r"(?is)^(?P<away>.+?)\s+at\s+(?P<home>.+?)\s+Game\s+\d+\s+Team\b",
        prefix,
    )
    if title_match is None:
        raise ValueError("Replay away-at-home title could not be parsed.")

    return (
        title_match.group("away").strip(),
        title_match.group("home").strip(),
    )


def parse_display_integer(value: str, field_name: str) -> int:
    match = re.fullmatch(r"\s*(\d+)(?:\s*\?)?\s*", value)
    if match is None:
        raise ValueError(f"Invalid {field_name} value: {value!r}")
    return int(match.group(1))


def parse_recap_team_line(row: list[str], innings: int) -> dict[str, Any]:
    expected_cell_count = innings + 4
    if len(row) != expected_cell_count:
        raise ValueError(
            f"Expected {expected_cell_count} line-score cells; "
            f"found {len(row)}: {row}"
        )

    raw_inning_cells = row[1:1 + innings]
    raw_totals_cells = row[1 + innings:]
    inning_runs: list[int | None] = []

    for inning_index, raw_value in enumerate(raw_inning_cells, start=1):
        normalized = raw_value.strip()

        if normalized in {"-", "x", "X"}:
            inning_runs.append(None)
            continue

        inning_runs.append(
            parse_display_integer(
                normalized,
                f"inning {inning_index} run",
            )
        )

    runs = parse_display_integer(raw_totals_cells[0], "run total")
    hits = parse_display_integer(raw_totals_cells[1], "hit total")
    errors = parse_display_integer(raw_totals_cells[2], "error total")

    calculated_runs = sum(
        value for value in inning_runs if value is not None
    )

    if calculated_runs != runs:
        raise ValueError(
            f"Inning runs sum to {calculated_runs}, not {runs}: {row}"
        )

    return {
        "shortLabel": row[0],
        "inningRuns": inning_runs,
        "runs": runs,
        "hits": hits,
        "errors": errors,
        "rawInningCells": raw_inning_cells,
        "rawTotalsCells": raw_totals_cells,
        "rawCells": row,
    }


def parse_recap_game(
    game_id: int,
    recap_path: Path,
    replay_path: Path,
) -> dict[str, Any]:
    recap_source = recap_path.read_text(encoding="utf-8")
    replay_source = replay_path.read_text(encoding="utf-8")

    table_matches = list(
        re.finditer(r"(?is)<table\b[^>]*>(.*?)</table>", recap_source)
    )
    if len(table_matches) != 6:
        raise ValueError(f"Game {game_id} recap has {len(table_matches)} tables.")

    tables = [match.group(1) for match in table_matches]
    line_rows = parse_table_rows(tables[0])
    final_pattern = re.compile(r"(?i)^FINAL(?:\s*\(\d+\))?$")
    header_rows = [row for row in line_rows if row and final_pattern.fullmatch(row[0])]
    team_rows = [
        row
        for row in line_rows
        if len(row) >= 4 and not final_pattern.fullmatch(row[0])
    ]

    if len(header_rows) != 1 or len(team_rows) != 2:
        raise ValueError(f"Game {game_id} has an invalid line-score structure.")

    header_numbers = re.findall(r"(?<!\d)\d+(?!\d)", header_rows[0][1])
    innings = len(header_numbers)
    if innings < 1:
        raise ValueError(f"Game {game_id} exposes no inning headers.")

    away_context = recap_source[table_matches[1].end():table_matches[2].start()]
    home_context = recap_source[table_matches[3].end():table_matches[4].start()]
    away_name = extract_last_h3(away_context)
    home_name = extract_last_h3(home_context)

    replay_away, replay_home = parse_replay_orientation(replay_source)
    if away_name != replay_away or home_name != replay_home:
        raise ValueError(
            f"Game {game_id} recap/replay orientation mismatch: "
            f"{away_name} at {home_name} versus {replay_away} at {replay_home}."
        )

    away_line = parse_recap_team_line(team_rows[0], innings)
    home_line = parse_recap_team_line(team_rows[1], innings)
    away_line["name"] = away_name
    home_line["name"] = home_name

    if away_line["runs"] == home_line["runs"]:
        raise ValueError(f"Game {game_id} has a tied final score.")

    winner = away_name if away_line["runs"] > home_line["runs"] else home_name
    loser = home_name if winner == away_name else away_name

    return {
        "gameId": game_id,
        "innings": innings,
        "extraInnings": innings > 9,
        "awayTeam": away_line,
        "homeTeam": home_line,
        "winnerTeam": winner,
        "loserTeam": loser,
        "decisionSummaryText": clean_html(tables[1]),
        "awayHitters": parse_hitter_table(tables[2]),
        "awayPitchers": parse_pitcher_table(tables[3]),
        "homeHitters": parse_hitter_table(tables[4]),
        "homePitchers": parse_pitcher_table(tables[5]),
        "replayOrientation": {
            "awayTeam": replay_away,
            "homeTeam": replay_home,
            "match": True,
        },
    }


def parse_table_rows_with_attributes(table_body: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    for row_match in re.finditer(
        r"(?is)<tr\b(?P<attributes>[^>]*)>(?P<body>.*?)</tr>",
        table_body,
    ):
        cells: list[dict[str, str]] = []

        for cell_match in re.finditer(
            r"(?is)<t[dh]\b(?P<attributes>[^>]*)>(?P<body>.*?)</t[dh]>",
            row_match.group("body"),
        ):
            cells.append(
                {
                    "text": clean_html(cell_match.group("body")),
                    "attributes": cell_match.group("attributes").strip(),
                }
            )

        rows.append(
            {
                "rowAttributes": row_match.group("attributes").strip(),
                "cells": cells,
            }
        )

    return rows


def parse_play_by_play(
    body_path: Path,
    expected_innings: int,
) -> dict[str, Any]:
    source = body_path.read_text(encoding="utf-8")
    table_matches = list(
        re.finditer(r"(?is)<table\b[^>]*>(.*?)</table>", source)
    )

    if len(table_matches) != 3:
        raise ValueError(
            f"Expected three play-by-play tables; found {len(table_matches)}."
        )

    final_rows = parse_table_rows(table_matches[0].group(1))
    decision_summary_text = clean_html(table_matches[1].group(1))

    rows = parse_table_rows_with_attributes(table_matches[2].group(1))
    expected_header = [
        "O,B",
        "Batter",
        "Roll",
        "Result",
        "Baserunners",
        "Misc.",
        "PCF",
    ]

    ordered_records: list[dict[str, Any]] = []
    boundary_header_positions: list[int] = []
    marker_sequence: list[tuple[str, int]] = []

    current_half: str | None = None
    current_inning: int | None = None

    inning_marker_count = 0
    event_count = 0
    control_count = 0
    unknown_control_count = 0

    for source_row_index, row in enumerate(rows, start=1):
        cells = row["cells"]
        cell_texts = [cell["text"] for cell in cells]

        if cell_texts == expected_header:
            boundary_header_positions.append(source_row_index)
            continue

        if len(cells) == 1:
            marker_match = re.fullmatch(
                r"(?P<half>TOP|BOTTOM) OF INNING (?P<inning>\d+)",
                cell_texts[0],
            )

            if marker_match is None:
                raise ValueError(
                    f"Unrecognized one-cell play-by-play row: {cell_texts}"
                )

            current_half = marker_match.group("half")
            current_inning = int(marker_match.group("inning"))
            marker_sequence.append((current_half, current_inning))

            ordered_records.append(
                {
                    "sequence": len(ordered_records) + 1,
                    "recordType": "INNING_MARKER",
                    "inning": current_inning,
                    "half": current_half,
                    "sourceRowIndex": source_row_index,
                    "rawText": cell_texts[0],
                    "rowAttributes": row["rowAttributes"],
                    "cellAttributes": [
                        cell["attributes"] for cell in cells
                    ],
                }
            )

            inning_marker_count += 1
            continue

        if current_half is None or current_inning is None:
            raise ValueError(
                f"Play-by-play row precedes the first inning marker: {cell_texts}"
            )

        if len(cells) == 7:
            state_text = cell_texts[0]
            state_match = re.fullmatch(
                r"(?P<outs>[0-2])(?:\s+(?P<bases>[123]+))?",
                state_text,
            )

            outs_before = None
            occupied_bases_before: list[int] = []

            if state_match is not None:
                outs_before = int(state_match.group("outs"))
                bases_text = state_match.group("bases")

                if bases_text:
                    occupied_bases_before = [
                        int(value) for value in bases_text
                    ]

            ordered_records.append(
                {
                    "sequence": len(ordered_records) + 1,
                    "recordType": "EVENT",
                    "inning": current_inning,
                    "half": current_half,
                    "outsBasesBefore": state_text,
                    "outsBefore": outs_before,
                    "occupiedBasesBefore": occupied_bases_before,
                    "batter": cell_texts[1] or None,
                    "roll": cell_texts[2] or None,
                    "result": cell_texts[3] or None,
                    "baserunners": cell_texts[4] or None,
                    "miscellaneous": cell_texts[5] or None,
                    "pcf": cell_texts[6] or None,
                    "sourceRowIndex": source_row_index,
                    "rawCells": cell_texts,
                    "rowAttributes": row["rowAttributes"],
                    "cellAttributes": [
                        cell["attributes"] for cell in cells
                    ],
                }
            )

            event_count += 1
            continue

        if len(cells) == 2:
            control_text = cell_texts[1] or cell_texts[0]
            control_type = "OTHER_CONTROL"
            control_details: dict[str, Any] = {}

            substitution_match = re.fullmatch(
                r"(?i)SUBSTITUTION at (?P<position>[^:]+): (?P<participant>.+)",
                control_text,
            )

            injury_match = re.fullmatch(
                r"(?i)INJURY: (?P<participant>.+?) for (?P<games>\d+) more games",
                control_text,
            )

            if substitution_match is not None:
                control_type = "SUBSTITUTION"
                control_details = {
                    "position": substitution_match.group("position").strip(),
                    "participantText": substitution_match.group("participant").strip(),
                }
            elif injury_match is not None:
                control_type = "INJURY"
                control_details = {
                    "participantText": injury_match.group("participant").strip(),
                    "additionalGames": int(injury_match.group("games")),
                }
            else:
                unknown_control_count += 1

            ordered_records.append(
                {
                    "sequence": len(ordered_records) + 1,
                    "recordType": "CONTROL",
                    "controlType": control_type,
                    "inning": current_inning,
                    "half": current_half,
                    "text": control_text,
                    "details": control_details,
                    "sourceRowIndex": source_row_index,
                    "rawCells": cell_texts,
                    "rowAttributes": row["rowAttributes"],
                    "cellAttributes": [
                        cell["attributes"] for cell in cells
                    ],
                }
            )

            control_count += 1
            continue

        raise ValueError(
            f"Unsupported play-by-play row shape with {len(cells)} cells: "
            f"{cell_texts}"
        )

    if boundary_header_positions != [1, len(rows)]:
        raise ValueError(
            f"Expected boundary headers at rows 1 and {len(rows)}; "
            f"found {boundary_header_positions}."
        )

    expected_half = "TOP"
    expected_inning = 1

    for half, inning in marker_sequence:
        if half != expected_half or inning != expected_inning:
            raise ValueError(
                f"Unexpected inning-marker order at {half} {inning}; "
                f"expected {expected_half} {expected_inning}."
            )

        if half == "TOP":
            expected_half = "BOTTOM"
        else:
            expected_half = "TOP"
            expected_inning += 1

    if not marker_sequence:
        raise ValueError("No inning markers were parsed.")

    maximum_inning = max(
        inning for _, inning in marker_sequence
    )

    if maximum_inning != expected_innings:
        raise ValueError(
            f"Play-by-play maximum inning {maximum_inning} does not match "
            f"recap innings {expected_innings}."
        )

    final_half, final_inning = marker_sequence[-1]

    return {
        "schemaVersion": "strat365-play-by-play-v0",
        "finalRows": final_rows,
        "decisionSummaryText": decision_summary_text,
        "header": expected_header,
        "sourceRowCount": len(rows),
        "boundaryHeaderCount": len(boundary_header_positions),
        "inningMarkerCount": inning_marker_count,
        "eventCount": event_count,
        "controlCount": control_count,
        "unknownControlCount": unknown_control_count,
        "orderedRecordCount": len(ordered_records),
        "maximumInning": maximum_inning,
        "expectedInnings": expected_innings,
        "expectedInningsMatch": True,
        "finalHalfInning": {
            "half": final_half,
            "inning": final_inning,
        },
        "orderedRecords": ordered_records,
    }



def normalize_match_text(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def normalized_text_contains(text: str, value: str) -> bool:
    normalized_value = normalize_match_text(value)
    if not normalized_value:
        return False

    normalized_text = f" {normalize_match_text(text)} "
    return f" {normalized_value} " in normalized_text


def team_is_mentioned(
    text: str,
    full_name: str,
    short_label: str,
) -> bool:
    return (
        normalized_text_contains(text, full_name)
        or normalized_text_contains(text, short_label)
    )


def recap_team_lines_match(
    parsed: dict[str, Any],
    expected: dict[str, Any],
) -> bool:
    return (
        parsed["shortLabel"] == expected["shortLabel"]
        and parsed["inningRuns"] == expected["inningRuns"]
        and parsed["runs"] == expected["runs"]
        and parsed["hits"] == expected["hits"]
        and parsed["errors"] == expected["errors"]
    )


def reconcile_game_sources(game_record: dict[str, Any]) -> dict[str, Any]:
    game_id = int(game_record["gameId"])
    innings = int(game_record["innings"])
    play_by_play = game_record["playByPlay"]
    final_rows = play_by_play["finalRows"]

    final_pattern = re.compile(r"(?i)^FINAL(?:\s*\(\d+\))?$")
    header_rows = [
        row for row in final_rows if row and final_pattern.fullmatch(row[0])
    ]
    team_rows = [
        row
        for row in final_rows
        if len(row) >= 4 and not final_pattern.fullmatch(row[0])
    ]

    if len(header_rows) != 1 or len(team_rows) != 2:
        raise ValueError(
            f"Game {game_id} has an invalid play-by-play final table."
        )

    expected_header = f"FINAL ({innings})" if innings > 9 else "FINAL"
    final_header_match = header_rows[0][0] == expected_header

    play_by_play_away = parse_recap_team_line(team_rows[0], innings)
    play_by_play_home = parse_recap_team_line(team_rows[1], innings)

    team_order_match = (
        play_by_play_away["shortLabel"]
        == game_record["awayTeam"]["shortLabel"]
        and play_by_play_home["shortLabel"]
        == game_record["homeTeam"]["shortLabel"]
    )

    away_team_line_match = recap_team_lines_match(
        play_by_play_away,
        game_record["awayTeam"],
    )
    home_team_line_match = recap_team_lines_match(
        play_by_play_home,
        game_record["homeTeam"],
    )

    decision_summary_exact_match = (
        play_by_play["decisionSummaryText"]
        == game_record["decisionSummaryText"]
    )

    league_result_text = game_record["leagueInventory"]["resultText"]
    winner_name = game_record["winnerTeam"]
    loser_name = game_record["loserTeam"]

    if winner_name == game_record["awayTeam"]["name"]:
        winner_short = game_record["awayTeam"]["shortLabel"]
        winner_runs = int(game_record["awayTeam"]["runs"])
        loser_short = game_record["homeTeam"]["shortLabel"]
        loser_runs = int(game_record["homeTeam"]["runs"])
    else:
        winner_short = game_record["homeTeam"]["shortLabel"]
        winner_runs = int(game_record["homeTeam"]["runs"])
        loser_short = game_record["awayTeam"]["shortLabel"]
        loser_runs = int(game_record["awayTeam"]["runs"])

    league_winner_mention = team_is_mentioned(
        league_result_text,
        winner_name,
        winner_short,
    )
    league_loser_mention = team_is_mentioned(
        league_result_text,
        loser_name,
        loser_short,
    )

    score_pattern = re.compile(
        rf"(?<!\d){winner_runs}\s*[-–]\s*{loser_runs}(?!\d)",
        re.IGNORECASE,
    )
    league_score_match = score_pattern.search(league_result_text) is not None

    # The league inventory headline is non-authoritative presentation text.
    # Structured score, box-score, decision, play-by-play, and replay evidence
    # determine game identity and outcome. Team-name omission in the headline
    # must never block reconciliation.
    league_winner_omission_accepted = (
        not league_winner_mention
        and league_score_match
    )

    league_loser_omission_accepted = (
        not league_loser_mention
        and league_score_match
    )

    league_result_outcome_match = league_score_match

    replay_orientation_match = bool(
        game_record["replayOrientation"]["match"]
    )
    play_by_play_innings_match = bool(
        play_by_play["expectedInningsMatch"]
        and int(play_by_play["maximumInning"]) == innings
    )
    unknown_control_free = (
        int(play_by_play["unknownControlCount"]) == 0
    )

    reconciliation_pass = all(
        [
            final_header_match,
            team_order_match,
            away_team_line_match,
            home_team_line_match,
            decision_summary_exact_match,
            league_result_outcome_match,
            replay_orientation_match,
            play_by_play_innings_match,
            unknown_control_free,
        ]
    )

    if not reconciliation_pass:
        raise ValueError(
            f"Game {game_id} failed cross-source reconciliation."
        )

    return {
        "status": "RECONCILED",
        "leagueNarrativeTextAuthoritative": False,
        "leagueNarrativeRole": "NON_AUTHORITATIVE_PRESENTATION_TEXT",
        "finalHeaderMatch": final_header_match,
        "teamOrderMatch": team_order_match,
        "awayTeamLineMatch": away_team_line_match,
        "homeTeamLineMatch": home_team_line_match,
        "decisionSummaryExactMatch": decision_summary_exact_match,
        "leagueWinnerMention": league_winner_mention,
        "leagueLoserMention": league_loser_mention,
        "leagueScoreMatch": league_score_match,
        "leagueWinnerOmissionAccepted": (
            league_winner_omission_accepted
        ),
        "leagueLoserOmissionAccepted": (
            league_loser_omission_accepted
        ),
        "leagueWinnerOmissionReason": (
            "NARRATIVE_HEADLINE_OMITS_WINNER_TEAM"
            if league_winner_omission_accepted
            else None
        ),
        "leagueResultOutcomeMatch": league_result_outcome_match,
        "recapReplayOrientationMatch": replay_orientation_match,
        "playByPlayAttached": True,
        "playByPlayInningsMatch": play_by_play_innings_match,
        "unknownControlFree": unknown_control_free,
        "canonicalPromotionAuthorized": False,
    }


def main() -> int:
    argument_parser = argparse.ArgumentParser(
        description='Validate one locked Strat365 season-ingestion run.'
    )
    argument_parser.add_argument('--run-directory', required=True)
    argument_parser.add_argument('--repo-root', required=True)
    arguments = argument_parser.parse_args()

    repo_root = Path(arguments.repo_root).resolve()
    run_directory = Path(arguments.run_directory).resolve()
    failures: list[str] = []

    lock_path = run_directory / 'capture-lock-and-promotion-decision-v1.json'
    manifest_path = run_directory / 'run-manifest.json'
    metadata_directory = run_directory / 'metadata'

    if not run_directory.is_dir():
        failures.append('Run directory is missing.')
    if not lock_path.is_file():
        failures.append('Capture lock is missing.')
    if not manifest_path.is_file():
        failures.append('Run manifest is missing.')
    if not metadata_directory.is_dir():
        failures.append('Metadata directory is missing.')

    expected_families: dict[str, int] = {}
    expected_game_ids: set[int] = set()
    expected_game_count = 0
    expected_artifact_count = 0

    if manifest_path.is_file():
        try:
            manifest = json.loads(
                manifest_path.read_text(encoding='utf-8')
            )
            (
                expected_families,
                expected_game_ids,
                expected_artifact_count,
            ) = derive_manifest_expectations(manifest)
            expected_game_count = len(expected_game_ids)
        except Exception as error:
            failures.append(
                'Run manifest expectation derivation '
                f'failed: {error}'
            )

    lock_status = 'UNKNOWN'
    if lock_path.is_file():
        lock = json.loads(lock_path.read_text(encoding='utf-8'))
        nested_lock = pick(lock, 'captureLock')
        lock_status = str(
            pick(nested_lock, 'status') if isinstance(nested_lock, dict)
            else pick(lock, 'status')
        )
        if lock_status != 'LOCKED':
            failures.append(f'Capture status is {lock_status}, not LOCKED.')

    metadata_files = sorted(
        metadata_directory.glob('*.json')
    )
    if (
        expected_artifact_count
        and len(metadata_files) != expected_artifact_count
    ):
        failures.append(
            f'Expected {expected_artifact_count} '
            f'metadata files; found {len(metadata_files)}.'
        )

    family_counts: dict[str, int] = {}
    game_ids: set[str] = set()
    body_paths: set[str] = set()
    header_paths: set[str] = set()
    body_hash_checks = 0
    body_byte_checks = 0
    league_body_path: Path | None = None
    league_metadata_name: str | None = None
    league_inventory: list[dict[str, Any]] = []
    staging_output = "NOT_WRITTEN"
    staging_sha256 = "NOT_WRITTEN"
    files_modified_by_parser = 0
    game_sources: dict[int, dict[str, dict[str, Any]]] = {}
    game_records: list[dict[str, Any]] = []
    game_file_paths: list[str] = []
    recap_hitter_row_count = 0
    recap_pitcher_row_count = 0
    recap_substitution_row_count = 0
    recap_extra_inning_game_count = 0
    play_by_play_inning_marker_count = 0
    play_by_play_event_row_count = 0
    play_by_play_control_row_count = 0
    play_by_play_unknown_control_count = 0
    play_by_play_ordered_record_count = 0
    reconciled_game_count = 0
    reconciliation_winner_mention_count = 0
    reconciliation_winner_omission_accepted_count = 0
    reconciliation_loser_mention_count = 0
    reconciliation_score_match_count = 0
    reconciliation_decision_match_count = 0
    complete_night_reconciliation_ready = False

    for metadata_path in metadata_files:
        try:
            metadata = json.loads(metadata_path.read_text(encoding='utf-8'))
        except Exception as error:
            failures.append(f'{metadata_path.name}: invalid JSON: {error}')
            continue

        family = str(pick(metadata, 'sourceFamily') or 'UNKNOWN')
        family_counts[family] = family_counts.get(family, 0) + 1

        game_id = pick(metadata, 'gameId')
        if game_id is not None:
            game_ids.add(str(game_id))

        body_path = resolve_artifact(
            pick(metadata, 'rawResponsePath', 'responseBodyPath', 'bodyPath'),
            repo_root,
            run_directory,
        )
        header_path = resolve_artifact(
            pick(metadata, 'responseHeadersPath', 'rawHeadersPath', 'headersPath'),
            repo_root,
            run_directory,
        )

        if body_path is None or not body_path.is_file():
            failures.append(f'{metadata_path.name}: response body is missing.')
            continue
        body_paths.add(str(body_path).lower())

        if family in LEAGUE_INVENTORY_METADATA_FAMILIES:
            if league_body_path is not None:
                failures.append(
                    "Multiple league-inventory metadata rows were resolved."
                )
            else:
                league_body_path = body_path
                league_metadata_name = metadata_path.name
                family_counts[LEAGUE_SCORE_FAMILY] = (
                    family_counts.get(LEAGUE_SCORE_FAMILY, 0) + 1
                )
                if family != LEAGUE_SCORE_FAMILY:
                    family_counts[family] -= 1
                    if family_counts[family] == 0:
                        del family_counts[family]

        if family in {"gameRecap", "gamePlayByPlay", "gameReplay"} and game_id is not None:
            game_key = int(game_id)
            game_sources.setdefault(game_key, {})[family] = {
                "metadataFile": metadata_path.name,
                "bodyPath": body_path,
                "bodySha256": sha256(body_path),
            }

        if header_path is None or not header_path.is_file():
            failures.append(f'{metadata_path.name}: response headers are missing.')
        else:
            header_paths.add(str(header_path).lower())

        expected_hash = pick(
            metadata,
            'bodySha256',
            'rawBodySha256',
            'rawResponseSha256',
            'responseBodySha256',
            'contentSha256',
            'sha256',
        )
        if expected_hash is not None:
            body_hash_checks += 1
            if sha256(body_path) != str(expected_hash).upper():
                failures.append(f'{metadata_path.name}: body SHA256 mismatch.')

        expected_bytes = pick(
            metadata,
            'bodyByteCount',
            'rawResponseByteCount',
            'responseBodyByteCount',
            'contentByteCount',
            'byteCount',
        )
        if expected_bytes is not None:
            body_byte_checks += 1
            if body_path.stat().st_size != int(expected_bytes):
                failures.append(f'{metadata_path.name}: body byte-count mismatch.')

    if expected_families and family_counts != expected_families:
        failures.append(
            f'Unexpected source-family inventory: {family_counts}'
        )

    try:
        metadata_game_ids = {
            int(game_id)
            for game_id in game_ids
        }
    except ValueError:
        metadata_game_ids = set()
        failures.append(
            'Metadata game IDs are not all integers.'
        )

    if (
        expected_game_ids
        and metadata_game_ids != expected_game_ids
    ):
        failures.append(
            'Metadata game-ID inventory differs from '
            'the run manifest: '
            f'missing={sorted(expected_game_ids - metadata_game_ids)}, '
            f'extra={sorted(metadata_game_ids - expected_game_ids)}'
        )

    artifact_checks = {
        'unique bodies': len(body_paths),
        'unique header files': len(header_paths),
        'body hash checks': body_hash_checks,
        'body byte checks': body_byte_checks,
    }

    if expected_artifact_count:
        for label, actual_count in artifact_checks.items():
            if actual_count != expected_artifact_count:
                failures.append(
                    f'Expected {expected_artifact_count} '
                    f'{label}; found {actual_count}.'
                )

    identity_match = re.search(
        r"/strat365/(?P<season>[^/]+)/season-ingestion/"
        r"league-(?P<league>\d+)/(?P<date>\d{4}-\d{2}-\d{2})/capture-",
        run_directory.as_posix(),
    )

    if identity_match is None:
        failures.append("Run path does not expose season, league, and date.")
        season = "UNKNOWN"
        league_id = "UNKNOWN"
        league_date = "UNKNOWN"
    else:
        season = identity_match.group("season")
        league_id = identity_match.group("league")
        league_date = identity_match.group("date")

    if league_body_path is None:
        failures.append("leagueScores response body was not resolved.")

    if not failures and league_body_path is not None:
        try:
            league_inventory = parse_league_inventory(
                league_body_path,
                league_id,
                expected_game_ids,
            )
        except Exception as error:
            failures.append(f"League inventory parse failed: {error}")

    if not failures:
        inventory_game_ids = {int(game["gameId"]) for game in league_inventory}
        source_game_ids = set(game_sources)

        if inventory_game_ids != expected_game_ids:
            failures.append(
                'League inventory differs from '
                'the run manifest: '
                f'missing={sorted(expected_game_ids - inventory_game_ids)}, '
                f'extra={sorted(inventory_game_ids - expected_game_ids)}'
            )

        if source_game_ids != inventory_game_ids:
            failures.append(
                "Game-source inventory differs from league inventory: "
                f"missing={sorted(inventory_game_ids - source_game_ids)}, "
                f"extra={sorted(source_game_ids - inventory_game_ids)}"
            )

    if not failures:
        required_families = {"gameRecap", "gamePlayByPlay", "gameReplay"}

        for inventory_game in league_inventory:
            game_id = int(inventory_game["gameId"])
            source_bundle = game_sources[game_id]
            missing_families = sorted(required_families - set(source_bundle))

            if missing_families:
                failures.append(
                    f"Game {game_id} lacks source families: {missing_families}"
                )
                continue

            try:
                game_record = parse_recap_game(
                    game_id,
                    source_bundle["gameRecap"]["bodyPath"],
                    source_bundle["gameReplay"]["bodyPath"],
                )
            except Exception as error:
                failures.append(f"Game {game_id} recap parse failed: {error}")
                continue

            try:
                play_by_play = parse_play_by_play(
                    source_bundle["gamePlayByPlay"]["bodyPath"],
                    int(game_record["innings"]),
                )
            except Exception as error:
                failures.append(
                    f"Game {game_id} play-by-play parse failed: {error}"
                )
                continue

            game_record["playByPlay"] = play_by_play

            game_record["schemaVersion"] = "strat365-game-v0"
            game_record["season"] = season
            game_record["leagueId"] = league_id
            game_record["leagueDate"] = league_date
            game_record["leagueInventory"] = inventory_game
            game_record["sources"] = {
                family: {
                    "metadataFile": source_bundle[family]["metadataFile"],
                    "bodyPath": source_bundle[family]["bodyPath"].relative_to(repo_root).as_posix(),
                    "bodySha256": source_bundle[family]["bodySha256"],
                }
                for family in sorted(source_bundle)
            }
            game_record["warnings"] = []
            game_record["reconciliation"] = reconcile_game_sources(game_record)
            game_records.append(game_record)

        if len(game_records) != len(league_inventory):
            failures.append(
                f"Expected {len(league_inventory)} recap game records; "
                f"created {len(game_records)}."
            )

        recap_hitter_row_count = sum(
            len(game["awayHitters"]) + len(game["homeHitters"])
            for game in game_records
        )
        recap_pitcher_row_count = sum(
            len(game["awayPitchers"]) + len(game["homePitchers"])
            for game in game_records
        )
        recap_substitution_row_count = sum(
            1
            for game in game_records
            for player in (
                game["awayHitters"]
                + game["homeHitters"]
                + game["awayPitchers"]
                + game["homePitchers"]
            )
            if player["substitutionPrefix"] is not None
        )
        recap_extra_inning_game_count = sum(
            1 for game in game_records if game["extraInnings"]
        )

    if not failures:
        play_by_play_inning_marker_count = sum(
            game["playByPlay"]["inningMarkerCount"]
            for game in game_records
        )
        play_by_play_event_row_count = sum(
            game["playByPlay"]["eventCount"]
            for game in game_records
        )
        play_by_play_control_row_count = sum(
            game["playByPlay"]["controlCount"]
            for game in game_records
        )
        play_by_play_unknown_control_count = sum(
            game["playByPlay"]["unknownControlCount"]
            for game in game_records
        )
        play_by_play_ordered_record_count = sum(
            game["playByPlay"]["orderedRecordCount"]
            for game in game_records
        )

    if not failures:
        reconciled_game_count = sum(
            1
            for game in game_records
            if game["reconciliation"]["status"] == "RECONCILED"
        )
        reconciliation_winner_mention_count = sum(
            1
            for game in game_records
            if game["reconciliation"]["leagueWinnerMention"]
        )
        reconciliation_winner_omission_accepted_count = sum(
            1
            for game in game_records
            if game["reconciliation"]["leagueWinnerOmissionAccepted"]
        )
        reconciliation_loser_mention_count = sum(
            1
            for game in game_records
            if game["reconciliation"]["leagueLoserMention"]
        )
        reconciliation_score_match_count = sum(
            1
            for game in game_records
            if game["reconciliation"]["leagueScoreMatch"]
        )
        reconciliation_decision_match_count = sum(
            1
            for game in game_records
            if game["reconciliation"]["decisionSummaryExactMatch"]
        )
        complete_night_reconciliation_ready = (
            expected_game_count > 0
            and len(game_records) == expected_game_count
            and reconciled_game_count == expected_game_count
        )

    if not failures:
        output_path = (
            repo_root
            / "data"
            / "baseball"
            / "parsed"
            / "strat365"
            / season
            / "season-ingestion"
            / f"league-{league_id}"
            / league_date
            / "league-night-v0.json"
        )

        source_body_relative = league_body_path.relative_to(repo_root).as_posix()

        game_directory = output_path.parent / "games"
        game_directory.mkdir(parents=True, exist_ok=True)

        for game_record in game_records:
            game_path = game_directory / f"game-{game_record['gameId']}-v0.json"
            game_payload = (
                json.dumps(
                    game_record,
                    ensure_ascii=False,
                    indent=2,
                    sort_keys=True,
                )
                + "\n"
            ).encode("utf-8")

            if not game_path.exists() or game_path.read_bytes() != game_payload:
                temporary_game_path = game_path.with_suffix(".json.tmp")
                temporary_game_path.write_bytes(game_payload)
                temporary_game_path.replace(game_path)
                files_modified_by_parser += 1

            game_file_paths.append(game_path.relative_to(repo_root).as_posix())

        staging_record = {
            "schemaVersion": "strat365-league-night-v0",
            "season": season,
            "leagueId": league_id,
            "leagueDate": league_date,
            "gameCount": len(league_inventory),
            "structuredGameCount": len(game_records),
            "playByPlaySummary": {
                "inningMarkerCount": play_by_play_inning_marker_count,
                "eventCount": play_by_play_event_row_count,
                "controlCount": play_by_play_control_row_count,
                "unknownControlCount": play_by_play_unknown_control_count,
                "orderedRecordCount": play_by_play_ordered_record_count,
            },
            "reconciliationSummary": {
                "reconciledGameCount": reconciled_game_count,
                "leagueWinnerMentionCount": (
                    reconciliation_winner_mention_count
                ),
                "leagueWinnerOmissionAcceptedCount": (
                    reconciliation_winner_omission_accepted_count
                ),
                "leagueLoserMentionCount": (
                    reconciliation_loser_mention_count
                ),
                "leagueScoreMatchCount": (
                    reconciliation_score_match_count
                ),
                "decisionSummaryExactMatchCount": (
                    reconciliation_decision_match_count
                ),
                "completeNightReady": (
                    complete_night_reconciliation_ready
                ),
                "canonicalPromotionAuthorized": False,
            },
            "gameFiles": game_file_paths,
            "gameSummaries": [
                {
                    "gameId": game["gameId"],
                    "awayTeam": game["awayTeam"]["name"],
                    "awayRuns": game["awayTeam"]["runs"],
                    "homeTeam": game["homeTeam"]["name"],
                    "homeRuns": game["homeTeam"]["runs"],
                    "winnerTeam": game["winnerTeam"],
                    "innings": game["innings"],
                }
                for game in game_records
            ],
            "games": league_inventory,
            "source": {
                "sourceFamily": "leagueScores",
                "metadataFile": league_metadata_name,
                "bodyPath": source_body_relative,
                "bodySha256": sha256(league_body_path),
            },
            "warnings": [],
            "canonicalPromotionAuthorized": False,
        }

        payload = (
            json.dumps(
                staging_record,
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
            + "\n"
        ).encode("utf-8")

        output_path.parent.mkdir(parents=True, exist_ok=True)

        if not output_path.exists() or output_path.read_bytes() != payload:
            temporary_path = output_path.with_suffix(".json.tmp")
            temporary_path.write_bytes(payload)
            temporary_path.replace(output_path)
            files_modified_by_parser += 1

        staging_output = output_path.relative_to(repo_root).as_posix()
        staging_sha256 = sha256(output_path)

    family_summary = ','.join(
        f'{name}={family_counts.get(name, 0)}'
        for name in sorted(expected_families)
    )

    print('# RESULT SUMMARY')
    preflight_status = 'PASS' if not failures else 'FAIL'
    print(f'LOCKED_INPUT_PREFLIGHT: {preflight_status}')
    print(f'CAPTURE_LOCK_STATUS: {lock_status}')
    print(f'METADATA_FILE_COUNT: {len(metadata_files)}')
    print(f'SOURCE_FAMILY_COUNTS: {family_summary}')
    print(f'EXPECTED_GAME_COUNT: {expected_game_count}')
    print(
        f'EXPECTED_ARTIFACT_COUNT: '
        f'{expected_artifact_count}'
    )
    print(f'UNIQUE_GAME_ID_COUNT: {len(game_ids)}')
    print(f'UNIQUE_BODY_PATH_COUNT: {len(body_paths)}')
    print(f'UNIQUE_HEADER_PATH_COUNT: {len(header_paths)}')
    print(f'BODY_HASH_CHECK_COUNT: {body_hash_checks}')
    print(f'BODY_BYTE_COUNT_CHECK_COUNT: {body_byte_checks}')
    print(
        f"LEAGUE_INVENTORY_STATUS: "
        f"{'PASS' if len(league_inventory) == expected_game_count else 'FAIL'}"
    )
    print(f"LEAGUE_INVENTORY_GAME_COUNT: {len(league_inventory)}")
    print(
        "LEAGUE_INVENTORY_GAME_IDS: "
        + ",".join(str(game["gameId"]) for game in league_inventory)
    )
    print(f"PARSED_STAGING_FILE: {staging_output}")
    print(f"PARSED_STAGING_SHA256: {staging_sha256}")
    print(
        f"RECAP_GAME_RECORD_STATUS: "
        f"{'PASS' if len(game_records) == len(league_inventory) else 'FAIL'}"
    )
    print(f"RECAP_GAME_RECORD_COUNT: {len(game_records)}")
    print(f"RECAP_HITTER_PLAYER_ROW_COUNT: {recap_hitter_row_count}")
    print(f"RECAP_PITCHER_PLAYER_ROW_COUNT: {recap_pitcher_row_count}")
    print(f"RECAP_SUBSTITUTION_ROW_COUNT: {recap_substitution_row_count}")
    print(f"RECAP_EXTRA_INNING_GAME_COUNT: {recap_extra_inning_game_count}")
    print(f"PARSED_GAME_FILE_COUNT: {len(game_file_paths)}")
    print(
        f"PLAY_BY_PLAY_RECORD_STATUS: "
        f"{'PASS' if play_by_play_event_row_count == 1368 else 'FAIL'}"
    )
    print(
        f"PLAY_BY_PLAY_INNING_MARKER_COUNT: "
        f"{play_by_play_inning_marker_count}"
    )
    print(f"PLAY_BY_PLAY_EVENT_ROW_COUNT: {play_by_play_event_row_count}")
    print(
        f"PLAY_BY_PLAY_CONTROL_ROW_COUNT: "
        f"{play_by_play_control_row_count}"
    )
    print(
        f"PLAY_BY_PLAY_UNKNOWN_CONTROL_COUNT: "
        f"{play_by_play_unknown_control_count}"
    )
    print(
        f"PLAY_BY_PLAY_ORDERED_RECORD_COUNT: "
        f"{play_by_play_ordered_record_count}"
    )
    print(
        f"CROSS_SOURCE_RECONCILIATION_STATUS: "
        f"{'PASS' if complete_night_reconciliation_ready else 'FAIL'}"
    )
    print(f"RECONCILED_GAME_COUNT: {reconciled_game_count}")
    print(
        f"LEAGUE_WINNER_MENTION_COUNT: "
        f"{reconciliation_winner_mention_count}"
    )
    print(
        f"LEAGUE_WINNER_OMISSION_ACCEPTED_COUNT: "
        f"{reconciliation_winner_omission_accepted_count}"
    )
    print(
        f"LEAGUE_LOSER_MENTION_COUNT: "
        f"{reconciliation_loser_mention_count}"
    )
    print(
        f"LEAGUE_SCORE_MATCH_COUNT: "
        f"{reconciliation_score_match_count}"
    )
    print(
        f"DECISION_SUMMARY_EXACT_MATCH_COUNT: "
        f"{reconciliation_decision_match_count}"
    )
    print(
        f"COMPLETE_NIGHT_RECONCILIATION_READY: "
        f"{'YES' if complete_night_reconciliation_ready else 'NO'}"
    )
    print(f'FAILURE_COUNT: {len(failures)}')
    for failure in failures[:20]:
        print(f'FAILURE_DETAIL: {failure}')
    if not failures:
        print('FAILURE_DETAIL: none')
    print('LIVE_REQUESTS_EXECUTED: 0')
    print(f'FILES_MODIFIED_BY_PARSER: {files_modified_by_parser}')

    return 0 if not failures else 1


if __name__ == '__main__':
    raise SystemExit(main())
