from __future__ import annotations

import argparse
import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "strat365-league-pitcher-offense-v0"

PLAYER_ID_RE = re.compile(
    r"/player/(?P<player_id>\d+)",
    re.IGNORECASE,
)

TEAM_ID_RE = re.compile(
    r"/team/(?P<team_id>\d+)(?:[/?#'\"]|$)",
    re.IGNORECASE,
)

PITCHER_SECTION_PATTERNS = (
    "pitchers' hitting stats",
    "pitchers hitting stats",
    "pitcher batting",
)

REQUIRED_HEADER_FIELDS = (
    "Name",
    "AB",
    "H",
    "BB",
    "SO",
    "BA",
    "OBP",
    "SLG",
)

NUMERIC_INTEGER_FIELDS = (
    "AB",
    "R",
    "H",
    "2B",
    "3B",
    "HR",
    "RBI",
    "BB",
    "SO",
    "HBP",
    "SB",
    "CS",
    "E",
)

NUMERIC_DECIMAL_FIELDS = (
    "BA",
    "OBP",
    "SLG",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def normalize_space(value: str) -> str:
    return re.sub(
        r"\s+",
        " ",
        value.replace("\xa0", " "),
    ).strip()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def integer(value: str | None) -> int | None:
    if value is None:
        return None

    cleaned = normalize_space(value)

    if not cleaned or cleaned in {"-", "--"}:
        return None

    match = re.search(r"-?\d+", cleaned)

    if not match:
        return None

    return int(match.group(0))


def decimal(value: str | None) -> float | None:
    if value is None:
        return None

    cleaned = normalize_space(value)

    if not cleaned or cleaned in {"-", "--"}:
        return None

    try:
        return float(cleaned)
    except ValueError:
        return None


def classify_ab_sample(
    at_bats: int | None,
) -> str:
    if at_bats is None or at_bats == 0:
        return "NONE"

    if 1 <= at_bats <= 2:
        return "TINY"

    if 3 <= at_bats <= 7:
        return "LIMITED"

    if at_bats >= 8:
        return "ESTABLISHED"

    raise ValueError(
        f"Invalid AB opportunity count: {at_bats}"
    )


@dataclass
class Cell:
    text: str
    hrefs: list[str]


@dataclass
class Row:
    cells: list[Cell]

    @property
    def texts(self) -> list[str]:
        return [
            normalize_space(cell.text)
            for cell in self.cells
        ]

    @property
    def joined_text(self) -> str:
        return normalize_space(
            " ".join(self.texts)
        )


class TeamTableParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()

        self.rows: list[Row] = []

        self._row_cells: list[Cell] | None = None
        self._cell_text: list[str] | None = None
        self._cell_hrefs: list[str] | None = None

        self.title_parts: list[str] = []
        self._inside_title = False

    def handle_starttag(
        self,
        tag: str,
        attrs: list[tuple[str, str | None]],
    ) -> None:
        attrs_dict = dict(attrs)

        if tag.lower() == "title":
            self._inside_title = True

        elif tag.lower() == "tr":
            self._row_cells = []

        elif (
            tag.lower() in {"td", "th"}
            and self._row_cells is not None
        ):
            self._cell_text = []
            self._cell_hrefs = []

        elif (
            tag.lower() == "a"
            and self._cell_hrefs is not None
        ):
            href = attrs_dict.get("href")

            if href:
                self._cell_hrefs.append(href)

    def handle_data(self, data: str) -> None:
        if self._inside_title:
            self.title_parts.append(data)

        if self._cell_text is not None:
            self._cell_text.append(data)

    def handle_endtag(self, tag: str) -> None:
        lowered = tag.lower()

        if lowered == "title":
            self._inside_title = False

        elif (
            lowered in {"td", "th"}
            and self._row_cells is not None
            and self._cell_text is not None
        ):
            self._row_cells.append(
                Cell(
                    text=normalize_space(
                        "".join(self._cell_text)
                    ),
                    hrefs=list(
                        self._cell_hrefs or []
                    ),
                )
            )

            self._cell_text = None
            self._cell_hrefs = None

        elif (
            lowered == "tr"
            and self._row_cells is not None
        ):
            if self._row_cells:
                self.rows.append(
                    Row(
                        cells=list(
                            self._row_cells
                        )
                    )
                )

            self._row_cells = None
            self._cell_text = None
            self._cell_hrefs = None

    @property
    def title(self) -> str | None:
        value = normalize_space(
            "".join(self.title_parts)
        )

        return value or None


def player_id_from_row(
    row: Row,
) -> int | None:
    for cell in row.cells:
        for href in cell.hrefs:
            match = PLAYER_ID_RE.search(href)

            if match:
                return int(
                    match.group("player_id")
                )

    return None


def player_name_from_row(
    row: Row,
) -> str | None:
    for cell in row.cells:
        if any(
            PLAYER_ID_RE.search(href)
            for href in cell.hrefs
        ):
            value = normalize_space(cell.text)

            if value:
                return value

    return None


def locate_pitcher_section(
    rows: list[Row],
) -> int:
    for index, row in enumerate(rows):
        text = row.joined_text.lower()

        if any(
            marker in text
            for marker in PITCHER_SECTION_PATTERNS
        ):
            return index

    raise ValueError(
        "Pitcher hitting section marker not found."
    )


def locate_header_row(
    rows: list[Row],
    marker_index: int,
) -> tuple[int, list[str]]:
    for index in range(
        marker_index - 1,
        -1,
        -1,
    ):
        texts = rows[index].texts
        field_set = set(texts)

        if all(
            field in field_set
            for field in REQUIRED_HEADER_FIELDS
        ):
            return index, texts

    raise ValueError(
        "Batting header row not found before "
        "pitcher hitting section."
    )


def row_to_stat_map(
    headers: list[str],
    row: Row,
) -> dict[str, str]:
    values = row.texts

    if len(values) != len(headers):
        raise ValueError(
            "Pitcher batting row width does not "
            "match batting header width: "
            f"{len(values)} vs {len(headers)}."
        )

    return {
        header: value
        for header, value in zip(
            headers,
            values,
        )
    }


def parse_pitcher_offense_html(
    *,
    html_bytes: bytes,
    team_id: int,
    source_path: str,
    league_id: int,
    observed_context: str,
) -> dict[str, Any]:
    text = html_bytes.decode(
        "utf-8",
        errors="replace",
    )

    parser = TeamTableParser()
    parser.feed(text)

    marker_index = locate_pitcher_section(
        parser.rows
    )

    (
        header_index,
        headers,
    ) = locate_header_row(
        parser.rows,
        marker_index,
    )

    pitchers: list[dict[str, Any]] = []

    for row in parser.rows[
        marker_index + 1:
    ]:
        texts = row.texts

        if not texts:
            continue

        first = texts[0].upper()

        if first == "TOTALS":
            break

        player_id = player_id_from_row(row)

        if player_id is None:
            continue

        player_name = player_name_from_row(row)

        if not player_name:
            continue

        stat_map = row_to_stat_map(
            headers,
            row,
        )

        observed_stats: dict[str, Any] = {}

        for field in NUMERIC_INTEGER_FIELDS:
            if field in stat_map:
                observed_stats[field] = integer(
                    stat_map[field]
                )

        for field in NUMERIC_DECIMAL_FIELDS:
            if field in stat_map:
                observed_stats[field] = decimal(
                    stat_map[field]
                )

        for field in (
            "B",
            "P",
            "Def.",
            "Stl",
            "Run",
            "Inj",
            "BAL",
            "Salary",
        ):
            if field in stat_map:
                observed_stats[field] = (
                    stat_map[field]
                    or None
                )

        at_bats = observed_stats.get("AB")

        pitchers.append(
            {
                "leagueId": league_id,
                "teamId": team_id,
                "playerId": player_id,
                "playerName": player_name,
                "observedContext": (
                    observed_context
                ),
                "observedStats": (
                    observed_stats
                ),
                "sampleGovernance": {
                    "opportunityField": "AB",
                    "opportunityCount": at_bats,
                    "sampleClass": (
                        classify_ab_sample(
                            at_bats
                        )
                    ),
                },
                "source": {
                    "sourceType": (
                        "strat365TeamPage"
                    ),
                    "sourcePath": source_path,
                    "sha256": sha256_bytes(
                        html_bytes
                    ),
                },
            }
        )

    if not pitchers:
        raise ValueError(
            "Pitcher hitting section contained "
            "no linked pitcher rows."
        )

    return {
        "teamId": team_id,
        "teamPageTitle": parser.title,
        "headerIndex": header_index,
        "headers": headers,
        "pitchers": pitchers,
    }


def discover_team_pages(
    capture_root: Path,
) -> list[tuple[int, Path]]:
    root = (
        capture_root
        / "responses"
        / "league-intelligence"
        / "team-offense"
    )

    if not root.exists():
        raise ValueError(
            "Team offense response root missing: "
            f"{root}"
        )

    pages: list[tuple[int, Path]] = []

    for team_dir in sorted(root.iterdir()):
        if not team_dir.is_dir():
            continue

        if not team_dir.name.isdigit():
            continue

        page = (
            team_dir
            / "page-00000.html"
        )

        if not page.exists():
            continue

        pages.append(
            (
                int(team_dir.name),
                page,
            )
        )

    return pages


def build_league_artifact(
    *,
    league_id: int,
    capture_root: Path,
    observed_context: str,
    expected_team_count: int,
) -> dict[str, Any]:
    team_pages = discover_team_pages(
        capture_root
    )

    if len(team_pages) != expected_team_count:
        raise ValueError(
            "Expected "
            f"{expected_team_count} team offense pages; "
            f"found {len(team_pages)}."
        )

    teams: list[dict[str, Any]] = []
    pitchers: list[dict[str, Any]] = []

    for team_id, page in team_pages:
        parsed = parse_pitcher_offense_html(
            html_bytes=page.read_bytes(),
            team_id=team_id,
            source_path=str(page),
            league_id=league_id,
            observed_context=observed_context,
        )

        team_pitchers = parsed["pitchers"]

        teams.append(
            {
                "teamId": team_id,
                "teamPageTitle": (
                    parsed["teamPageTitle"]
                ),
                "pitcherCount": len(
                    team_pitchers
                ),
                "sourcePath": str(page),
            }
        )

        pitchers.extend(
            team_pitchers
        )

    player_ids = [
        pitcher["playerId"]
        for pitcher in pitchers
    ]

    return {
        "schemaVersion": SCHEMA_VERSION,
        "generatedAtUtc": utc_now(),
        "leagueId": league_id,
        "observedContext": observed_context,
        "teamCount": len(teams),
        "pitcherObservationCount": len(
            pitchers
        ),
        "uniquePlayerCount": len(
            set(player_ids)
        ),
        "sampleGovernance": {
            "status": (
                "CALIBRATED"
            ),
            "opportunityField": "AB",
        },
        "teams": teams,
        "pitchers": pitchers,
    }


def write_json(
    path: Path,
    payload: dict[str, Any],
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporary = path.with_suffix(
        path.suffix + ".tmp"
    )

    temporary.write_text(
        json.dumps(
            payload,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    temporary.replace(path)


def main() -> int:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--league-id",
        type=int,
        required=True,
    )

    parser.add_argument(
        "--capture-root",
        type=Path,
    )

    parser.add_argument(
        "--single-html",
        type=Path,
    )

    parser.add_argument(
        "--team-id",
        type=int,
    )

    parser.add_argument(
        "--observed-context",
        default="CURRENT_LEAGUE",
        choices=(
            "CURRENT_LEAGUE",
            "CROSS_LEAGUE_1968",
        ),
    )

    parser.add_argument(
        "--expected-team-count",
        type=int,
        default=12,
    )

    parser.add_argument(
        "--output",
        type=Path,
        required=True,
    )

    args = parser.parse_args()

    if (
        args.single_html is not None
        and args.capture_root is not None
    ):
        parser.error(
            "Use --single-html or --capture-root, "
            "not both."
        )

    if args.single_html is not None:
        if args.team_id is None:
            parser.error(
                "--team-id is required with "
                "--single-html."
            )

        parsed = parse_pitcher_offense_html(
            html_bytes=args.single_html.read_bytes(),
            team_id=args.team_id,
            source_path=str(
                args.single_html
            ),
            league_id=args.league_id,
            observed_context=(
                args.observed_context
            ),
        )

        payload = {
            "schemaVersion": SCHEMA_VERSION,
            "generatedAtUtc": utc_now(),
            "leagueId": args.league_id,
            "observedContext": (
                args.observed_context
            ),
            "teamCount": 1,
            "pitcherObservationCount": len(
                parsed["pitchers"]
            ),
            "uniquePlayerCount": len(
                {
                    row["playerId"]
                    for row in parsed[
                        "pitchers"
                    ]
                }
            ),
            "sampleGovernance": {
                "status": (
                    "PENDING_CALIBRATION"
                ),
                "opportunityField": "AB",
            },
            "teams": [
                {
                    "teamId": args.team_id,
                    "teamPageTitle": (
                        parsed[
                            "teamPageTitle"
                        ]
                    ),
                    "pitcherCount": len(
                        parsed["pitchers"]
                    ),
                    "sourcePath": str(
                        args.single_html
                    ),
                }
            ],
            "pitchers": parsed[
                "pitchers"
            ],
        }

    elif args.capture_root is not None:
        payload = build_league_artifact(
            league_id=args.league_id,
            capture_root=args.capture_root,
            observed_context=(
                args.observed_context
            ),
            expected_team_count=(
                args.expected_team_count
            ),
        )

    else:
        parser.error(
            "One of --single-html or "
            "--capture-root is required."
        )

    write_json(
        args.output,
        payload,
    )

    print("# RESULT SUMMARY")
    print(
        "LEAGUE_PITCHER_OFFENSE_NORMALIZER: PASS"
    )
    print(
        "TEAM_COUNT: "
        + str(payload["teamCount"])
    )
    print(
        "PITCHER_OBSERVATION_COUNT: "
        + str(
            payload[
                "pitcherObservationCount"
            ]
        )
    )
    print(
        "UNIQUE_PLAYER_COUNT: "
        + str(
            payload[
                "uniquePlayerCount"
            ]
        )
    )
    print(
        "SAMPLE_GOVERNANCE: "
        + payload[
            "sampleGovernance"
        ]["status"]
    )
    print(
        "OUTPUT: "
        + str(args.output)
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())