#!/usr/bin/env python3

from __future__ import annotations

import argparse
import html
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PRE_RE = re.compile(
    r"<pre\b[^>]*>(.*?)</pre>",
    flags=re.IGNORECASE | re.DOTALL,
)

TAG_RE = re.compile(
    r"<[^>]+>",
    flags=re.DOTALL,
)

HEADER_RE = re.compile(
    r"-{2,}\s*"
    r"(?P<name>[A-Z][A-Z0-9 /%&().'+-]*?)"
    r"\s*-{2,}",
    flags=re.IGNORECASE,
)

CELL_RE = re.compile(
    r"^\s*"
    r"(?P<player>.+?)"
    r"\s{2,}"
    r"(?P<team>[A-Z0-9]{3})"
    r"\s+"
    r"(?P<value>.+?)"
    r"\s*$"
)

OTHERS_TIED_RE = re.compile(
    r"^\s*OTHERS\s+TIED\s+WITH",
    flags=re.IGNORECASE,
)

NUMERIC_RE = re.compile(
    r"[-+]?(?:\d+(?:\.\d+)?|\.\d+)"
)


def extract_leaders_pre(raw_html: str) -> str:
    candidates: list[str] = []

    for match in PRE_RE.finditer(raw_html):
        block = html.unescape(
            TAG_RE.sub(
                "",
                match.group(1),
            )
        )

        if re.search(
            r"BATTING\s+AVERAGE",
            block,
            re.IGNORECASE,
        ) and re.search(
            r"\bWINS\b",
            block,
            re.IGNORECASE,
        ):
            candidates.append(block)

    if len(candidates) != 1:
        raise ValueError(
            "Expected exactly one League Leaders PRE block; "
            f"found {len(candidates)}"
        )

    return candidates[0]


def category_slug(name: str) -> str:
    normalized = name.lower()

    normalized = normalized.replace(
        "'",
        "",
    )

    normalized = re.sub(
        r"[^a-z0-9]+",
        "_",
        normalized,
    )

    return normalized.strip("_")


def parse_numeric_value(
    raw_value: str,
) -> float | int | None:
    cleaned = raw_value.replace(
        ",",
        "",
    )

    cleaned = cleaned.replace(
        "*",
        "",
    ).strip()

    match = NUMERIC_RE.search(cleaned)

    if match is None:
        return None

    token = match.group(0)

    try:
        if "." in token:
            return float(token)

        return int(token)
    except ValueError:
        return None


def parse_cell(
    cell: str,
) -> dict[str, Any] | None:
    stripped = cell.strip()

    if not stripped:
        return None

    if OTHERS_TIED_RE.match(stripped):
        return None

    match = CELL_RE.match(cell)

    if match is None:
        return None

    player_name = (
        match.group("player").strip()
    )

    team_abbreviation = (
        match.group("team").strip()
    )

    raw_value = (
        match.group("value").strip()
    )

    current_marker = (
        "*"
        if raw_value.startswith("*")
        else None
    )

    clean_value = (
        raw_value[1:].strip()
        if current_marker
        else raw_value
    )

    return {
        "playerName": player_name,
        "teamAbbreviation": team_abbreviation,
        "valueRaw": clean_value,
        "valueNumeric": parse_numeric_value(
            clean_value
        ),
        "isCurrent": current_marker == "*",
        "rawCurrentMarker": current_marker,
        "rawText": stripped,
    }


def values_tied(
    left: dict[str, Any],
    right: dict[str, Any],
) -> bool:
    left_numeric = left.get(
        "valueNumeric"
    )

    right_numeric = right.get(
        "valueNumeric"
    )

    if (
        left_numeric is not None
        and right_numeric is not None
    ):
        return left_numeric == right_numeric

    return (
        str(
            left.get(
                "valueRaw",
                "",
            )
        ).strip()
        ==
        str(
            right.get(
                "valueRaw",
                "",
            )
        ).strip()
    )


def apply_competition_ranks(
    rows: list[dict[str, Any]],
) -> None:
    prior: dict[str, Any] | None = None
    prior_rank: int | None = None

    for index, row in enumerate(
        rows,
        start=1,
    ):
        if (
            prior is not None
            and values_tied(
                prior,
                row,
            )
        ):
            rank = prior_rank
        else:
            rank = index

        row["rank"] = rank
        row["displayOrder"] = index

        prior = row
        prior_rank = rank


def parse_leader_categories(
    raw_html: str,
) -> list[dict[str, Any]]:
    text = extract_leaders_pre(
        raw_html
    )

    lines = text.splitlines()

    header_rows: list[
        dict[str, Any]
    ] = []

    pitching_started = False
    category_order = 0

    for line_index, line in enumerate(
        lines
    ):
        matches = list(
            HEADER_RE.finditer(line)
        )

        if not matches:
            continue

        names = [
            re.sub(
                r"\s+",
                " ",
                match.group(
                    "name"
                ),
            ).strip()
            for match in matches
        ]

        if any(
            name.upper() == "WINS"
            for name in names
        ):
            pitching_started = True

        section = (
            "pitchers"
            if pitching_started
            else "hitters"
        )

        columns: list[
            dict[str, Any]
        ] = []

        for column_index, match in enumerate(
            matches
        ):
            category_order += 1

            category_name = names[
                column_index
            ]

            next_start = (
                matches[
                    column_index + 1
                ].start()
                if (
                    column_index + 1
                    < len(matches)
                )
                else None
            )

            columns.append(
                {
                    "categoryName":
                        category_name,
                    "categoryKey":
                        (
                            f"{section}_"
                            f"{category_slug(category_name)}"
                        ),
                    "section":
                        section,
                    "categoryOrder":
                        category_order,
                    "columnStart":
                        match.start(),
                    "columnEnd":
                        next_start,
                }
            )

        header_rows.append(
            {
                "lineIndex":
                    line_index,
                "columns":
                    columns,
            }
        )

    if not header_rows:
        raise ValueError(
            "No League Leaders category headers parsed"
        )

    categories: list[
        dict[str, Any]
    ] = []

    for header_index, header in enumerate(
        header_rows
    ):
        data_start = (
            header["lineIndex"] + 1
        )

        data_end = (
            header_rows[
                header_index + 1
            ]["lineIndex"]
            if (
                header_index + 1
                < len(header_rows)
            )
            else len(lines)
        )

        for column in header["columns"]:
            leaders: list[
                dict[str, Any]
            ] = []

            start = column[
                "columnStart"
            ]

            end = column[
                "columnEnd"
            ]

            for row_line in lines[
                data_start:data_end
            ]:
                if end is None:
                    cell = row_line[
                        start:
                    ]
                else:
                    cell = row_line[
                        start:end
                    ]

                parsed = parse_cell(
                    cell
                )

                if parsed is None:
                    continue

                leaders.append(
                    parsed
                )

            apply_competition_ranks(
                leaders
            )

            categories.append(
                {
                    "categoryKey":
                        column[
                            "categoryKey"
                        ],
                    "categoryName":
                        column[
                            "categoryName"
                        ],
                    "section":
                        column[
                            "section"
                        ],
                    "displayOrder":
                        column[
                            "categoryOrder"
                        ],
                    "leaderCount":
                        len(leaders),
                    "leaders":
                        leaders,
                }
            )

    return categories


def build_output(
    input_path: Path,
) -> dict[str, Any]:
    raw_html = input_path.read_text(
        encoding="utf-8",
        errors="replace",
    )

    categories = parse_leader_categories(
        raw_html
    )

    flat_leaders: list[
        dict[str, Any]
    ] = []

    for category in categories:
        for row in category[
            "leaders"
        ]:
            flat_leaders.append(
                {
                    "categoryKey":
                        category[
                            "categoryKey"
                        ],
                    "categoryName":
                        category[
                            "categoryName"
                        ],
                    "section":
                        category[
                            "section"
                        ],
                    **row,
                }
            )

    hitter_categories = [
        category
        for category in categories
        if (
            category["section"]
            == "hitters"
        )
    ]

    pitcher_categories = [
        category
        for category in categories
        if (
            category["section"]
            == "pitchers"
        )
    ]

    return {
        "schemaVersion":
            "strat365-league-leaders-v0",
        "artifactType":
            "league-leader-evidence",
        "generatedAtUtc":
            datetime.now(
                timezone.utc
            ).isoformat(),
        "source": {
            "path":
                str(
                    input_path
                ).replace(
                    "\\",
                    "/",
                ),
            "sourceFamily":
                "leagueLeaders",
        },
        "semanticRules": {
            "sourceOrderPreserved":
                True,
            "competitionRanksCalculated":
                True,
            "equalDisplayedValuesShareRank":
                True,
            "asteriskPreservedAsCurrentMarker":
                True,
            "othersTiedSummaryRowsExcluded":
                True,
            "sectionBoundary":
                "WINS_STARTS_PITCHERS",
        },
        "counts": {
            "categoryCount":
                len(categories),
            "hitterCategoryCount":
                len(
                    hitter_categories
                ),
            "pitcherCategoryCount":
                len(
                    pitcher_categories
                ),
            "leaderRowCount":
                len(
                    flat_leaders
                ),
        },
        "categories":
            categories,
        "leaders":
            flat_leaders,
    }


def main() -> int:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--input",
        required=True,
    )

    parser.add_argument(
        "--output",
        required=True,
    )

    args = parser.parse_args()

    input_path = Path(
        args.input
    )

    output_path = Path(
        args.output
    )

    result = build_output(
        input_path
    )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path.write_text(
        json.dumps(
            result,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())