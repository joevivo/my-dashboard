from __future__ import annotations

import hashlib
import json
import re
from html.parser import HTMLParser
from pathlib import Path
from typing import Any


TRANSACTION_SCHEMA = (
    "bie.strat365.league-transaction-events.v0"
)

INJURY_SCHEMA = (
    "bie.strat365.league-injury-snapshot.v0"
)


def normalize_text(
    value: Any,
) -> str:
    return " ".join(
        str(value or "").split()
    )


def parse_money_dollars(
    value: str | None,
) -> int | None:
    if value is None:
        return None

    text = normalize_text(value)

    if not text:
        return None

    cleaned = (
        text.replace("$", "")
        .replace(",", "")
        .strip()
    )

    if not cleaned:
        return None

    if cleaned.upper().endswith("M"):
        numeric = cleaned[:-1].strip()

        if numeric.startswith("."):
            numeric = "0" + numeric

        try:
            return int(
                round(
                    float(numeric)
                    * 1_000_000
                )
            )
        except ValueError:
            return None

    try:
        return int(cleaned)
    except ValueError:
        return None


def stable_hash(
    payload: dict[str, Any],
) -> str:
    canonical = json.dumps(
        payload,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    )

    return hashlib.sha256(
        canonical.encode("utf-8")
    ).hexdigest()


class LinkTableParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()

        self.tables: list[
            list[
                list[
                    dict[str, Any]
                ]
            ]
        ] = []

        self.table_depth = 0
        self.current_table = None
        self.current_row = None
        self.current_cell_text = None
        self.current_cell_links = None

        self.anchor_href = None
        self.anchor_text = None

    def handle_starttag(
        self,
        tag: str,
        attrs: list[
            tuple[str, str | None]
        ],
    ) -> None:
        tag = tag.lower()
        attributes = dict(attrs)

        if tag == "table":
            self.table_depth += 1

            if self.table_depth == 1:
                self.current_table = []

        elif (
            tag == "tr"
            and self.table_depth == 1
        ):
            self.current_row = []

        elif (
            tag in {"th", "td"}
            and self.table_depth == 1
            and self.current_row is not None
        ):
            self.current_cell_text = []
            self.current_cell_links = []

        elif (
            tag == "a"
            and self.current_cell_text is not None
        ):
            self.anchor_href = (
                attributes.get("href")
                or attributes.get("url")
                or ""
            )

            self.anchor_text = []

    def handle_data(
        self,
        data: str,
    ) -> None:
        if self.current_cell_text is not None:
            self.current_cell_text.append(data)

        if self.anchor_text is not None:
            self.anchor_text.append(data)

    def handle_endtag(
        self,
        tag: str,
    ) -> None:
        tag = tag.lower()

        if (
            tag == "a"
            and self.anchor_text is not None
        ):
            if self.current_cell_links is not None:
                self.current_cell_links.append(
                    {
                        "text": normalize_text(
                            "".join(
                                self.anchor_text
                            )
                        ),
                        "href": (
                            self.anchor_href
                            or ""
                        ),
                    }
                )

            self.anchor_href = None
            self.anchor_text = None

        elif (
            tag in {"th", "td"}
            and self.current_cell_text is not None
            and self.current_row is not None
        ):
            self.current_row.append(
                {
                    "text": normalize_text(
                        "".join(
                            self.current_cell_text
                        )
                    ),
                    "links": list(
                        self.current_cell_links
                        or []
                    ),
                }
            )

            self.current_cell_text = None
            self.current_cell_links = None

        elif (
            tag == "tr"
            and self.table_depth == 1
            and self.current_row is not None
        ):
            if any(
                cell["text"]
                for cell in self.current_row
            ):
                assert self.current_table is not None

                self.current_table.append(
                    self.current_row
                )

            self.current_row = None

        elif tag == "table":
            if (
                self.table_depth == 1
                and self.current_table is not None
            ):
                self.tables.append(
                    self.current_table
                )

            self.current_table = None
            self.table_depth -= 1


def cell_texts(
    row: list[dict[str, Any]],
) -> list[str]:
    return [
        normalize_text(
            cell.get("text")
        )
        for cell in row
    ]


def cell_links(
    cell: dict[str, Any],
) -> list[dict[str, Any]]:
    value = cell.get(
        "links",
        [],
    )

    if not isinstance(value, list):
        return []

    return [
        item
        for item in value
        if isinstance(item, dict)
    ]


def row_links(
    row: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    output = []

    for cell in row:
        output.extend(
            cell_links(cell)
        )

    return output


def extract_team_identity(
    cell: dict[str, Any],
) -> tuple[str | None, str | None]:
    for link in cell_links(cell):
        href = str(
            link.get("href", "")
        )

        match = re.search(
            r"/team/(\d+)",
            href,
        )

        if match:
            return (
                match.group(1),
                normalize_text(
                    link.get("text")
                )
                or None,
            )

    return None, None


def extract_player_identity(
    cell: dict[str, Any],
) -> tuple[
    str | None,
    str | None,
    str | None,
]:
    for link in cell_links(cell):
        href = str(
            link.get("href", "")
        )

        match = re.search(
            r"/player/"
            r"(\d+)/"
            r"[^/'\",\)\s]+/"
            r"[^/'\",\)\s]+/"
            r"[^/'\",\)\s]+/"
            r"(\d+)",
            href,
        )

        if match:
            return (
                match.group(1),
                match.group(2),
                normalize_text(
                    link.get("text")
                )
                or None,
            )

    return None, None, None


def extract_trade_id(
    row: list[dict[str, Any]],
) -> str | None:
    for link in row_links(row):
        match = re.search(
            r"/league/transaction/(\d+)",
            str(
                link.get(
                    "href",
                    "",
                )
            ),
        )

        if match:
            return match.group(1)

    return None


def extract_counterparty_team(
    row: list[dict[str, Any]],
    primary_team_id: str | None,
) -> tuple[str | None, str | None]:
    found = []

    for link in row_links(row):
        href = str(
            link.get("href", "")
        )

        match = re.search(
            r"/team/(\d+)",
            href,
        )

        if not match:
            continue

        found.append(
            (
                match.group(1),
                normalize_text(
                    link.get("text")
                )
                or None,
            )
        )

    for team_id, team_name in found:
        if (
            primary_team_id is None
            or team_id != primary_team_id
        ):
            return (
                team_id,
                team_name,
            )

    return None, None


def parse_player_subject(
    value: str,
) -> tuple[
    str,
    str | None,
    int | None,
]:
    text = normalize_text(value)

    match = re.match(
        r"^(.*?)\s+-\s+([.$0-9,]+M)$",
        text,
        flags=re.I,
    )

    if not match:
        return (
            text,
            None,
            None,
        )

    name = normalize_text(
        match.group(1)
    )

    salary_text = normalize_text(
        match.group(2)
    )

    return (
        name,
        salary_text,
        parse_money_dollars(
            salary_text
        ),
    )


def classify_transaction_action(
    action: str,
) -> tuple[str, str]:
    raw = normalize_text(action)
    lowered = raw.lower()

    if lowered == "added":
        return (
            "TRANSACTION",
            "ADD",
        )

    if lowered == "dropped":
        return (
            "TRANSACTION",
            "DROP",
        )

    if "waiver" in lowered:
        return (
            "WAIVER",
            "WAIVER_CLAIM",
        )

    if lowered == "traded with":
        return (
            "TRADE",
            "TRADE",
        )

    slug = re.sub(
        r"[^A-Za-z0-9]+",
        "_",
        raw,
    ).strip("_").upper()

    return (
        "TRANSACTION",
        slug or "OTHER",
    )


def transaction_rows_from_html(
    html_text: str,
) -> list[list[dict[str, Any]]]:
    parser = LinkTableParser()
    parser.feed(html_text)

    rows = []

    for table in parser.tables:
        header_index = None

        for index, row in enumerate(
            table
        ):
            cells = cell_texts(row)

            if (
                len(cells) >= 3
                and cells[0].lower() == "date"
                and cells[1].lower() == "team"
                and cells[2].lower() == "action"
            ):
                header_index = index
                break

        if header_index is None:
            continue

        for row in table[
            header_index + 1:
        ]:
            cells = cell_texts(row)

            if (
                len(cells) == 1
                and cells[0].startswith(
                    "Pages:"
                )
            ):
                continue

            if len(cells) < 4:
                continue

            if not cells[0]:
                continue

            rows.append(row)

    return rows


def normalize_transaction_pages(
    *,
    league_id: str,
    pages: list[Path],
) -> dict[str, Any]:
    events = []

    seen_event_keys: set[str] = set()

    raw_row_count = 0
    duplicate_count = 0

    for page in sorted(
        pages,
        key=lambda item: item.name,
    ):
        offset_match = re.search(
            r"page-(\d+)\.html$",
            page.name,
        )

        page_offset = (
            int(
                offset_match.group(1)
            )
            if offset_match
            else None
        )

        rows = transaction_rows_from_html(
            page.read_text(
                encoding="utf-8",
                errors="replace",
            )
        )

        for source_row_index, row in enumerate(
            rows,
            start=1,
        ):
            raw_row_count += 1

            cells = cell_texts(row)

            while len(cells) < 6:
                cells.append("")

            (
                date_text,
                team_text,
                action_text,
                subject_text,
                before_text,
                after_text,
            ) = cells[:6]

            (
                team_id,
                linked_team_name,
            ) = extract_team_identity(
                row[1]
            )

            (
                player_id,
                player_league_id,
                linked_player_name,
            ) = extract_player_identity(
                row[3]
            )

            (
                subject_name,
                salary_text,
                salary_dollars,
            ) = parse_player_subject(
                subject_text
            )

            trade_id = extract_trade_id(
                row
            )

            (
                counterparty_team_id,
                counterparty_team_name,
            ) = extract_counterparty_team(
                row,
                team_id,
            )

            domain, action_code = (
                classify_transaction_action(
                    action_text
                )
            )

            identity_payload = {
                "leagueId": str(
                    league_id
                ),
                "sourceDateText": (
                    date_text
                ),
                "teamId": team_id,
                "teamName": (
                    linked_team_name
                    or team_text
                ),
                "rawAction": (
                    action_text
                ),
                "subjectText": (
                    subject_text
                ),
                "playerId": player_id,
                "tradeId": trade_id,
                "counterpartyTeamId": (
                    counterparty_team_id
                ),
                "balanceBeforeText": (
                    before_text
                ),
                "balanceAfterText": (
                    after_text
                ),
            }

            event_key = stable_hash(
                identity_payload
            )

            if event_key in seen_event_keys:
                duplicate_count += 1
                continue

            seen_event_keys.add(
                event_key
            )

            events.append(
                {
                    "eventKey": event_key,
                    "domain": domain,
                    "actionCode": action_code,
                    "rawAction": (
                        action_text
                    ),
                    "sourceDateText": (
                        date_text
                    ),
                    "teamId": team_id,
                    "teamName": (
                        linked_team_name
                        or team_text
                    ),
                    "playerId": player_id,
                    "playerLeagueId": (
                        player_league_id
                    ),
                    "playerName": (
                        linked_player_name
                        or (
                            subject_name
                            if player_id
                            else None
                        )
                    ),
                    "playerSalaryText": (
                        salary_text
                    ),
                    "playerSalaryDollars": (
                        salary_dollars
                    ),
                    "tradeId": trade_id,
                    "counterpartyTeamId": (
                        counterparty_team_id
                    ),
                    "counterpartyTeamName": (
                        counterparty_team_name
                    ),
                    "subjectText": (
                        subject_text
                    ),
                    "balanceBeforeText": (
                        before_text
                        or None
                    ),
                    "balanceBeforeDollars": (
                        parse_money_dollars(
                            before_text
                        )
                    ),
                    "balanceAfterText": (
                        after_text
                        or None
                    ),
                    "balanceAfterDollars": (
                        parse_money_dollars(
                            after_text
                        )
                    ),
                    "sourcePageOffset": (
                        page_offset
                    ),
                    "sourceRowIndex": (
                        source_row_index
                    ),
                }
            )

    return {
        "schemaVersion": (
            TRANSACTION_SCHEMA
        ),
        "leagueId": str(
            league_id
        ),
        "capturePageCount": len(
            pages
        ),
        "rawTransactionRowCount": (
            raw_row_count
        ),
        "deduplicatedEventCount": (
            len(events)
        ),
        "duplicateEventCount": (
            duplicate_count
        ),
        "events": events,
    }


class InjurySnapshotParser(
    HTMLParser
):
    def __init__(
        self,
        league_id: str,
    ) -> None:
        super().__init__()

        self.league_id = str(
            league_id
        )

        self.current_team_id = None
        self.current_team_name = None

        self.anchor_href = None
        self.anchor_text = None

        self.pending_player = None
        self.pending_tail = []

        self.injuries = []

        self.saw_injuries_heading = False
        self.saw_current_source_link = False

    def finalize_pending(
        self,
    ) -> None:
        if self.pending_player is None:
            self.pending_tail = []
            return

        tail = normalize_text(
            "".join(
                self.pending_tail
            )
        )

        match = re.search(
            r"\(([^)]+)\)\s*-\s*"
            r"injured\s+through\s+Game\s+(\d+)",
            tail,
            flags=re.I,
        )

        if match:
            salary_text = normalize_text(
                match.group(1)
            )

            self.injuries.append(
                {
                    "identityKey": (
                        f"{self.league_id}:"
                        f"{self.pending_player['teamId']}:"
                        f"{self.pending_player['playerId']}"
                    ),
                    "teamId": (
                        self.pending_player[
                            "teamId"
                        ]
                    ),
                    "teamName": (
                        self.pending_player[
                            "teamName"
                        ]
                    ),
                    "playerId": (
                        self.pending_player[
                            "playerId"
                        ]
                    ),
                    "playerName": (
                        self.pending_player[
                            "playerName"
                        ]
                    ),
                    "salaryText": (
                        salary_text
                    ),
                    "salaryDollars": (
                        parse_money_dollars(
                            salary_text
                        )
                    ),
                    "injuredThroughGame": int(
                        match.group(2)
                    ),
                }
            )

        self.pending_player = None
        self.pending_tail = []

    def handle_starttag(
        self,
        tag: str,
        attrs: list[
            tuple[str, str | None]
        ],
    ) -> None:
        tag = tag.lower()

        if tag == "br":
            self.finalize_pending()
            return

        if tag != "a":
            return

        attributes = dict(attrs)

        self.anchor_href = (
            attributes.get("href")
            or attributes.get("url")
            or ""
        )

        self.anchor_text = []

    def handle_data(
        self,
        data: str,
    ) -> None:
        normalized = normalize_text(
            data
        )

        if normalized == "Injuries":
            self.saw_injuries_heading = True

        if self.anchor_text is not None:
            self.anchor_text.append(
                data
            )

        elif self.pending_player is not None:
            self.pending_tail.append(
                data
            )

    def handle_endtag(
        self,
        tag: str,
    ) -> None:
        if tag.lower() != "a":
            return

        if self.anchor_text is None:
            return

        text = normalize_text(
            "".join(
                self.anchor_text
            )
        )

        href = self.anchor_href or ""

        if (
            f"/league/injuries/{self.league_id}"
            in href
        ):
            self.saw_current_source_link = True

        team_match = re.search(
            r"/team/(\d+)",
            href,
        )

        if team_match:
            self.finalize_pending()

            self.current_team_id = (
                team_match.group(1)
            )

            self.current_team_name = (
                text or None
            )

        player_match = re.search(
            r"/player/"
            r"(\d+)/"
            r"[^/'\",\)\s]+/"
            r"[^/'\",\)\s]+/"
            r"[^/'\",\)\s]+/"
            r"(\d+)",
            href,
        )

        if player_match:
            self.finalize_pending()

            player_league_id = (
                player_match.group(2)
            )

            if (
                player_league_id
                == self.league_id
                and self.current_team_id
            ):
                self.pending_player = {
                    "teamId": (
                        self.current_team_id
                    ),
                    "teamName": (
                        self.current_team_name
                    ),
                    "playerId": (
                        player_match.group(1)
                    ),
                    "playerName": (
                        text or None
                    ),
                }

                self.pending_tail = []

        self.anchor_href = None
        self.anchor_text = None

    def close(self) -> None:
        super().close()
        self.finalize_pending()


def normalize_injury_snapshot(
    *,
    league_id: str,
    page: Path,
    capture_valid: bool = True,
) -> dict[str, Any]:
    if not capture_valid:
        return {
            "schemaVersion": (
                INJURY_SCHEMA
            ),
            "leagueId": str(
                league_id
            ),
            "snapshotValid": False,
            "snapshotValidityReason": (
                "SOURCE_CAPTURE_NOT_VALID"
            ),
            "activeInjuryCount": 0,
            "injuries": [],
        }

    if not page.exists():
        return {
            "schemaVersion": (
                INJURY_SCHEMA
            ),
            "leagueId": str(
                league_id
            ),
            "snapshotValid": False,
            "snapshotValidityReason": (
                "SOURCE_PAGE_MISSING"
            ),
            "activeInjuryCount": 0,
            "injuries": [],
        }

    parser = InjurySnapshotParser(
        str(league_id)
    )

    parser.feed(
        page.read_text(
            encoding="utf-8",
            errors="replace",
        )
    )

    parser.close()

    injuries = sorted(
        parser.injuries,
        key=lambda item: (
            item["teamId"],
            item["playerId"],
        ),
    )

    identities = [
        item["identityKey"]
        for item in injuries
    ]

    contract_valid = (
        parser.saw_injuries_heading
        and parser.saw_current_source_link
    )

    if (
        len(identities)
        != len(set(identities))
    ):
        snapshot_valid = False
        validity_reason = (
            "DUPLICATE_ACTIVE_INJURY_IDENTITY"
        )

    elif not contract_valid:
        snapshot_valid = False
        validity_reason = (
            "SOURCE_PAGE_CONTRACT_NOT_CONFIRMED"
        )

    else:
        snapshot_valid = True
        validity_reason = (
            "VALID_COMPLETE_CURRENT_SNAPSHOT"
        )

    return {
        "schemaVersion": (
            INJURY_SCHEMA
        ),
        "leagueId": str(
            league_id
        ),
        "snapshotValid": (
            snapshot_valid
        ),
        "snapshotValidityReason": (
            validity_reason
        ),
        "activeInjuryCount": (
            len(injuries)
        ),
        "injuries": injuries,
    }
