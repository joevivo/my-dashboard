from __future__ import annotations

import argparse
import json
import re
from datetime import date
from html.parser import HTMLParser
from pathlib import Path
from typing import Any


SCHEMA = "bie.strat365.team-schedule.v0"

SPACE_RE = re.compile(r"\s+")
MONTH_DAY_RE = re.compile(r"(?P<month>\d{1,2})/(?P<day>\d{1,2})")
TEAM_ID_PATTERNS = (
    re.compile(r"/team/(\d+)(?:\D|$)", re.IGNORECASE),
    re.compile(
        r"[?&]team(?:id)?=(\d+)(?:\D|$)",
        re.IGNORECASE,
    ),
)


def clean(value: str) -> str:
    return SPACE_RE.sub(" ", value).strip()


class Cell:
    def __init__(self, tag: str) -> None:
        self.tag = tag
        self.parts: list[str] = []
        self.links: list[tuple[str, str]] = []
        self.current_href: str | None = None
        self.current_link_parts: list[str] = []

    @property
    def text(self) -> str:
        return clean("".join(self.parts))


class ScheduleHtmlParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.tables: list[list[list[Cell]]] = []
        self.table_depth = 0
        self.current_table: list[list[Cell]] | None = None
        self.current_row: list[Cell] | None = None
        self.current_cell: Cell | None = None

    def handle_starttag(
        self,
        tag: str,
        attrs: list[tuple[str, str | None]],
    ) -> None:
        attr_map = dict(attrs)

        if tag == "table":
            self.table_depth += 1

            if self.table_depth == 1:
                self.current_table = []

        elif self.table_depth == 1 and tag == "tr":
            self.current_row = []

        elif (
            self.table_depth == 1
            and tag in ("th", "td")
            and self.current_row is not None
        ):
            self.current_cell = Cell(tag)

        elif (
            self.table_depth == 1
            and tag == "a"
            and self.current_cell is not None
        ):
            self.current_cell.current_href = attr_map.get("href")
            self.current_cell.current_link_parts = []

    def handle_data(self, data: str) -> None:
        if self.current_cell is None:
            return

        self.current_cell.parts.append(data)

        if self.current_cell.current_href is not None:
            self.current_cell.current_link_parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if (
            tag == "a"
            and self.current_cell is not None
            and self.current_cell.current_href is not None
        ):
            text = clean(
                "".join(self.current_cell.current_link_parts)
            )

            self.current_cell.links.append(
                (
                    self.current_cell.current_href,
                    text,
                )
            )

            self.current_cell.current_href = None
            self.current_cell.current_link_parts = []

        elif (
            tag in ("th", "td")
            and self.table_depth == 1
            and self.current_cell is not None
            and self.current_row is not None
        ):
            self.current_row.append(self.current_cell)
            self.current_cell = None

        elif (
            tag == "tr"
            and self.table_depth == 1
            and self.current_row is not None
        ):
            if self.current_row:
                if self.current_table is None:
                    raise ValueError("Row encountered without table")

                self.current_table.append(self.current_row)

            self.current_row = None

        elif tag == "table":
            if self.table_depth == 1 and self.current_table is not None:
                self.tables.append(self.current_table)
                self.current_table = None

            self.table_depth -= 1


def extract_team_id(cell: Cell) -> str | None:
    for href, _ in cell.links:
        for pattern in TEAM_ID_PATTERNS:
            match = pattern.search(href or "")

            if match:
                return match.group(1)

    return None


def extract_team_link_text(cell: Cell) -> str | None:
    for href, text in cell.links:
        if not text:
            continue

        if extract_team_id_from_href(href) is not None:
            return text

    return None


def extract_team_id_from_href(href: str) -> str | None:
    for pattern in TEAM_ID_PATTERNS:
        match = pattern.search(href or "")

        if match:
            return match.group(1)

    return None


def parse_schedule_date(
    raw_value: str,
    as_of: date,
) -> date:
    match = MONTH_DAY_RE.search(raw_value)

    if not match:
        raise ValueError(
            f"Unable to parse schedule date: {raw_value!r}"
        )

    month = int(match.group("month"))
    day = int(match.group("day"))

    candidate = date(as_of.year, month, day)

    # Protect year-boundary schedules without assuming the source
    # always includes a year.
    if (
        as_of.month == 12
        and candidate.month == 1
    ):
        candidate = date(as_of.year + 1, month, day)

    elif (
        as_of.month == 1
        and candidate.month == 12
    ):
        candidate = date(as_of.year - 1, month, day)

    return candidate


def parse_schedule_number(raw_value: str) -> int | None:
    value = clean(raw_value)

    if not value:
        return None

    match = re.search(r"\d+", value)

    return int(match.group(0)) if match else None


def locate_schedule_table(
    parser: ScheduleHtmlParser,
) -> tuple[list[str], list[list[Cell]]]:
    candidates: list[tuple[list[str], list[list[Cell]]]] = []

    for table in parser.tables:
        for row_index, row in enumerate(table[:6]):
            headers = [cell.text for cell in row]
            normalized = [value.lower() for value in headers]

            if "date" in normalized and "opponent" in normalized:
                candidates.append(
                    (
                        headers,
                        table[row_index + 1 :],
                    )
                )
                break

    if len(candidates) != 1:
        raise ValueError(
            "Expected exactly one Date/Opponent schedule table; "
            f"found {len(candidates)}"
        )

    return candidates[0]


def parse_rows(
    headers: list[str],
    rows: list[list[Cell]],
    as_of: date,
) -> list[dict[str, Any]]:
    header_map = {
        clean(name).lower(): index
        for index, name in enumerate(headers)
    }

    required = ("date", "opponent")

    for name in required:
        if name not in header_map:
            raise ValueError(
                f"Schedule table missing required column: {name}"
            )

    number_index = header_map.get("#")
    date_index = header_map["date"]
    opponent_index = header_map["opponent"]

    parsed: list[dict[str, Any]] = []

    for row in rows:
        if (
            date_index >= len(row)
            or opponent_index >= len(row)
        ):
            continue

        raw_date = row[date_index].text
        opponent_cell = row[opponent_index]
        raw_opponent = opponent_cell.text

        if not raw_date or not raw_opponent:
            continue

        schedule_date = parse_schedule_date(raw_date, as_of)

        away = raw_opponent.lstrip().startswith("@")

        display_name = (
            extract_team_link_text(opponent_cell)
            or clean(raw_opponent.lstrip("@").strip())
        )

        opponent_team_id = extract_team_id(opponent_cell)

        schedule_number = None

        if (
            number_index is not None
            and number_index < len(row)
        ):
            schedule_number = parse_schedule_number(
                row[number_index].text
            )

        parsed.append(
            {
                "scheduleGameNumber": schedule_number,
                "scheduledDate": schedule_date.isoformat(),
                "opponentDisplayName": display_name,
                "opponentTeamId": opponent_team_id,
                "homeAway": "AWAY" if away else "HOME",
            }
        )

    if not parsed:
        raise ValueError("No schedule rows parsed")

    return parsed


def select_next_series(
    rows: list[dict[str, Any]],
    as_of: date,
) -> dict[str, Any]:
    future = [
        row
        for row in rows
        if date.fromisoformat(row["scheduledDate"]) > as_of
    ]

    if not future:
        return {
            "status": "NO_FUTURE_SERIES_FOUND",
            "scheduledDate": None,
            "opponentDisplayName": None,
            "opponentTeamId": None,
            "homeAway": None,
            "gameCount": 0,
            "scheduleGameNumbers": [],
        }

    first = future[0]

    identity = (
        first["scheduledDate"],
        first["opponentTeamId"],
        first["opponentDisplayName"],
        first["homeAway"],
    )

    series_rows: list[dict[str, Any]] = []

    for row in future:
        row_identity = (
            row["scheduledDate"],
            row["opponentTeamId"],
            row["opponentDisplayName"],
            row["homeAway"],
        )

        if row_identity != identity:
            break

        series_rows.append(row)

    game_numbers = [
        row["scheduleGameNumber"]
        for row in series_rows
        if row["scheduleGameNumber"] is not None
    ]

    return {
        "status": "FOUND",
        "scheduledDate": first["scheduledDate"],
        "opponentDisplayName": first["opponentDisplayName"],
        "opponentTeamId": first["opponentTeamId"],
        "homeAway": first["homeAway"],
        "gameCount": len(series_rows),
        "scheduleGameNumbers": game_numbers,
    }


def build_output(
    source: Path,
    league_id: str,
    team_id: str,
    team_name: str,
    as_of: date,
) -> dict[str, Any]:
    text = source.read_text(
        encoding="utf-8",
        errors="replace",
    )

    parser = ScheduleHtmlParser()
    parser.feed(text)

    headers, rows = locate_schedule_table(parser)
    parsed_rows = parse_rows(headers, rows, as_of)
    next_series = select_next_series(parsed_rows, as_of)

    return {
        "schema": SCHEMA,
        "leagueId": league_id,
        "teamId": team_id,
        "teamName": team_name,
        "asOfDate": as_of.isoformat(),
        "scheduleRowCount": len(parsed_rows),
        "nextSeries": next_series,
        "source": {
            "path": str(source),
            "sourceType": "strat365_team_schedule_html",
        },
        "governance": {
            "resultFieldsConsumed": False,
            "scoreFieldsConsumed": False,
            "scheduleIdentityOnly": True,
        },
    }


def write_json(
    path: Path,
    value: dict[str, Any],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open(
        "w",
        encoding="utf-8",
        newline="\n",
    ) as handle:
        json.dump(
            value,
            handle,
            indent=2,
            sort_keys=True,
        )
        handle.write("\n")


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Parse Strat365 team schedule HTML into a "
            "score-free upcoming-series identity contract."
        )
    )

    parser.add_argument(
        "--source",
        required=True,
        type=Path,
    )
    parser.add_argument(
        "--league-id",
        required=True,
    )
    parser.add_argument(
        "--team-id",
        required=True,
    )
    parser.add_argument(
        "--team-name",
        required=True,
    )
    parser.add_argument(
        "--as-of-date",
        required=True,
    )
    parser.add_argument(
        "--output",
        required=True,
        type=Path,
    )

    args = parser.parse_args()

    as_of = date.fromisoformat(args.as_of_date)

    output = build_output(
        source=args.source,
        league_id=args.league_id,
        team_id=args.team_id,
        team_name=args.team_name,
        as_of=as_of,
    )

    write_json(args.output, output)

    summary = {
        "status": "PASS",
        "schema": output["schema"],
        "leagueId": output["leagueId"],
        "teamId": output["teamId"],
        "scheduleRowCount": output["scheduleRowCount"],
        "nextSeriesStatus": output["nextSeries"]["status"],
        "nextSeriesDate":
            output["nextSeries"]["scheduledDate"],
        "opponentDisplayName":
            output["nextSeries"]["opponentDisplayName"],
        "opponentTeamId":
            output["nextSeries"]["opponentTeamId"],
        "homeAway":
            output["nextSeries"]["homeAway"],
        "gameCount":
            output["nextSeries"]["gameCount"],
    }

    print(json.dumps(summary, sort_keys=True))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())