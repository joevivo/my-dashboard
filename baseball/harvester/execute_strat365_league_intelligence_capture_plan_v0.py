from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen


SCHEMA_VERSION = (
    "strat365-league-intelligence-capture-manifest-v0"
)

EXPECTED_PLAN_SCHEMA = (
    "strat365-league-intelligence-capture-plan-v0"
)

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/151 Safari/537.36"
)

MAX_PAGINATED_PAGES = 20


class LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.hrefs: list[str] = []

    def handle_starttag(
        self,
        tag: str,
        attrs: list[tuple[str, str | None]],
    ) -> None:
        if tag.lower() != "a":
            return

        values = dict(attrs)
        href = values.get("href")

        if href:
            self.hrefs.append(href)


class TableParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()

        self.tables: list[list[list[str]]] = []

        self._table_depth = 0
        self._current_table: list[list[str]] | None = None
        self._current_row: list[str] | None = None
        self._current_cell: list[str] | None = None
        self._cell_tag: str | None = None

    def handle_starttag(
        self,
        tag: str,
        attrs: list[tuple[str, str | None]],
    ) -> None:
        lowered = tag.lower()

        if lowered == "table":
            self._table_depth += 1

            if self._table_depth == 1:
                self._current_table = []

        elif (
            lowered == "tr"
            and self._table_depth == 1
        ):
            self._current_row = []

        elif (
            lowered in {"th", "td"}
            and self._table_depth == 1
            and self._current_row is not None
        ):
            self._current_cell = []
            self._cell_tag = lowered

    def handle_data(self, data: str) -> None:
        if self._current_cell is not None:
            self._current_cell.append(data)

    def handle_endtag(self, tag: str) -> None:
        lowered = tag.lower()

        if (
            lowered in {"th", "td"}
            and self._current_cell is not None
            and self._current_row is not None
        ):
            text = " ".join(
                " ".join(
                    self._current_cell
                ).split()
            )

            self._current_row.append(text)

            self._current_cell = None
            self._cell_tag = None

        elif (
            lowered == "tr"
            and self._table_depth == 1
            and self._current_row is not None
        ):
            if any(
                cell.strip()
                for cell in self._current_row
            ):
                assert self._current_table is not None
                self._current_table.append(
                    self._current_row
                )

            self._current_row = None

        elif lowered == "table":
            if (
                self._table_depth == 1
                and self._current_table is not None
            ):
                self.tables.append(
                    self._current_table
                )

                self._current_table = None

            self._table_depth -= 1


def load_json(path: Path) -> Any:
    return json.loads(
        path.read_text(encoding="utf-8")
    )


def write_json(
    path: Path,
    payload: Any,
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    path.write_text(
        json.dumps(
            payload,
            indent=2,
            ensure_ascii=False,
        ) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(
        path.read_bytes()
    ).hexdigest().upper()


def utc_now() -> str:
    return datetime.now(
        timezone.utc
    ).isoformat()


def safe_slug(value: str) -> str:
    value = re.sub(
        r"([a-z0-9])([A-Z])",
        r"\1-\2",
        value,
    )

    value = re.sub(
        r"[^A-Za-z0-9]+",
        "-",
        value,
    )

    return value.strip("-").lower()


def fetch(
    url: str,
) -> tuple[int, str, dict[str, str], bytes]:
    request = Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": (
                "text/html,application/xhtml+xml,"
                "application/xml;q=0.9,*/*;q=0.8"
            ),
            "Accept-Language": "en-US,en;q=0.9",
        },
        method="GET",
    )

    with urlopen(
        request,
        timeout=45,
    ) as response:
        body = response.read()

        headers = {
            str(key): str(value)
            for key, value in response.headers.items()
        }

        return (
            int(response.status),
            str(response.geturl()),
            headers,
            body,
        )


def write_headers(
    path: Path,
    *,
    status: int,
    effective_url: str,
    headers: dict[str, str],
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    lines = [
        f"HTTP-Status: {status}",
        f"Effective-URL: {effective_url}",
    ]

    lines.extend(
        f"{key}: {value}"
        for key, value in sorted(
            headers.items(),
            key=lambda item: item[0].lower(),
        )
    )

    path.write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def discover_offsets(
    html_text: str,
    *,
    initial_url: str,
    current_url: str,
    page_size: int,
) -> dict[int, str]:
    parser = LinkParser()
    parser.feed(html_text)

    initial = urlparse(initial_url)
    base_path = initial.path.rstrip("/")

    found: dict[int, str] = {
        0: initial_url,
    }

    for href in parser.hrefs:
        absolute = urljoin(
            current_url,
            href,
        )

        parsed = urlparse(absolute)

        if (
            parsed.scheme != initial.scheme
            or parsed.netloc != initial.netloc
        ):
            continue

        path = parsed.path.rstrip("/")

        if path == base_path:
            found[0] = absolute
            continue

        prefix = base_path + "/"

        if not path.startswith(prefix):
            continue

        suffix = path[len(prefix):]

        if not suffix.isdigit():
            continue

        offset = int(suffix)

        if offset < 0:
            continue

        if (
            offset != 0
            and offset % page_size != 0
        ):
            continue

        found[offset] = absolute

    return found


def find_player_table(
    html_text: str,
) -> tuple[list[str], list[list[str]]] | None:
    parser = TableParser()
    parser.feed(html_text)

    candidates: list[
        tuple[list[str], list[list[str]]]
    ] = []

    for table in parser.tables:
        if not table:
            continue

        header = table[0]

        if not header:
            continue

        if (
            header[0].strip().lower() != "name"
            or len(header) < 10
        ):
            continue

        rows = [
            row
            for row in table[1:]
            if len(row) == len(header)
        ]

        candidates.append(
            (header, rows)
        )

    if not candidates:
        return None

    candidates.sort(
        key=lambda item: len(item[1]),
        reverse=True,
    )

    return candidates[0]


def capture_single_page(
    *,
    request: dict[str, Any],
    output_root: Path,
) -> dict[str, Any]:
    family = str(
        request["sourceFamily"]
    )

    slug = safe_slug(family)

    artifact_root = (
        output_root
        / "responses"
        / "league-intelligence"
        / slug
    )

    metadata_root = (
        output_root
        / "metadata"
        / "league-intelligence"
        / slug
    )

    requested_url = str(
        request["requestedUrl"]
    )

    try:
        (
            status,
            effective_url,
            headers,
            body,
        ) = fetch(requested_url)

        body_path = (
            artifact_root
            / "page-00000.html"
        )

        headers_path = (
            artifact_root
            / "page-00000.headers.txt"
        )

        metadata_path = (
            metadata_root
            / "page-00000.json"
        )

        body_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        body_path.write_bytes(body)

        write_headers(
            headers_path,
            status=status,
            effective_url=effective_url,
            headers=headers,
        )

        metadata = {
            "schemaVersion": (
                "strat365-league-intelligence-"
                "raw-response-metadata-v0"
            ),
            "requestId": request[
                "requestId"
            ],
            "sourceFamily": family,
            "requestedUrl": requested_url,
            "effectiveUrl": effective_url,
            "httpStatus": status,
            "capturedAtUtc": utc_now(),
            "byteCount": len(body),
            "sha256": sha256_bytes(body),
            "pageOffset": 0,
            "captureMode": "singlePage",
            "transportResult": "PASS",
        }

        write_json(
            metadata_path,
            metadata,
        )

        return {
            "requestId": request[
                "requestId"
            ],
            "sourceFamily": family,
            "required": bool(
                request["required"]
            ),
            "captureMode": "singlePage",
            "requestStatus": "captured",
            "physicalRequestCount": 1,
            "capturedPageCount": 1,
            "rowCount": None,
            "columns": None,
            "error": None,
        }

    except (
        HTTPError,
        URLError,
        TimeoutError,
        OSError,
    ) as exc:
        return {
            "requestId": request[
                "requestId"
            ],
            "sourceFamily": family,
            "required": bool(
                request["required"]
            ),
            "captureMode": "singlePage",
            "requestStatus": "failed",
            "physicalRequestCount": 1,
            "capturedPageCount": 0,
            "rowCount": None,
            "columns": None,
            "error": str(exc),
        }


def capture_paginated_table(
    *,
    request: dict[str, Any],
    output_root: Path,
) -> dict[str, Any]:
    family = str(
        request["sourceFamily"]
    )

    slug = safe_slug(family)

    artifact_root = (
        output_root
        / "responses"
        / "league-intelligence"
        / slug
    )

    metadata_root = (
        output_root
        / "metadata"
        / "league-intelligence"
        / slug
    )

    requested_url = str(
        request["requestedUrl"]
    )

    policy = request[
        "paginationPolicy"
    ]

    page_size = int(
        policy["pageSize"]
    )

    queue: list[tuple[int, str]] = [
        (0, requested_url)
    ]

    queued: set[int] = {0}
    captured: set[int] = set()

    expected_header: list[str] | None = None

    physical_count = 0
    all_rows: list[list[str]] = []
    row_signatures: set[str] = set()

    try:
        while queue:
            queue.sort(
                key=lambda item: item[0]
            )

            offset, url = queue.pop(0)

            if offset in captured:
                continue

            if len(captured) >= MAX_PAGINATED_PAGES:
                raise ValueError(
                    "Pagination exceeded safety limit "
                    f"of {MAX_PAGINATED_PAGES} pages."
                )

            (
                status,
                effective_url,
                headers,
                body,
            ) = fetch(url)

            physical_count += 1

            html_text = body.decode(
                "utf-8",
                errors="replace",
            )

            table = find_player_table(
                html_text
            )

            if table is None:
                raise ValueError(
                    f"{family} player-stat table "
                    f"not found at offset {offset}."
                )

            header, rows = table

            if expected_header is None:
                expected_header = header

            elif header != expected_header:
                raise ValueError(
                    f"{family} column schema changed "
                    f"at offset {offset}."
                )

            for row in rows:
                signature = "\x1f".join(
                    cell.strip()
                    for cell in row
                )

                if signature in row_signatures:
                    continue

                row_signatures.add(
                    signature
                )

                all_rows.append(row)

            body_path = (
                artifact_root
                / f"page-{offset:05d}.html"
            )

            headers_path = (
                artifact_root
                / f"page-{offset:05d}.headers.txt"
            )

            metadata_path = (
                metadata_root
                / f"page-{offset:05d}.json"
            )

            body_path.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            body_path.write_bytes(body)

            write_headers(
                headers_path,
                status=status,
                effective_url=effective_url,
                headers=headers,
            )

            discovered = discover_offsets(
                html_text,
                initial_url=requested_url,
                current_url=effective_url,
                page_size=page_size,
            )

            metadata = {
                "schemaVersion": (
                    "strat365-league-intelligence-"
                    "raw-response-metadata-v0"
                ),
                "requestId": request[
                    "requestId"
                ],
                "sourceFamily": family,
                "requestedUrl": url,
                "effectiveUrl": effective_url,
                "httpStatus": status,
                "capturedAtUtc": utc_now(),
                "byteCount": len(body),
                "sha256": sha256_bytes(body),
                "pageOffset": offset,
                "tableColumns": header,
                "tableRowCount": len(rows),
                "discoveredOffsets": sorted(
                    discovered
                ),
                "captureMode": (
                    "completePaginatedTable"
                ),
                "transportResult": "PASS",
            }

            write_json(
                metadata_path,
                metadata,
            )

            captured.add(offset)

            for (
                discovered_offset,
                discovered_url,
            ) in discovered.items():
                if (
                    discovered_offset not in captured
                    and discovered_offset not in queued
                ):
                    queue.append(
                        (
                            discovered_offset,
                            discovered_url,
                        )
                    )

                    queued.add(
                        discovered_offset
                    )

        if expected_header is None:
            raise ValueError(
                f"{family} captured no table schema."
            )

        dataset = {
            "schemaVersion": (
                "strat365-league-player-table-v0"
            ),
            "sourceFamily": family,
            "leagueId": str(
                request["leagueId"]
            ),
            "leagueDate": str(
                request["leagueDate"]
            ),
            "acquisitionSort": policy[
                "acquisitionSort"
            ],
            "acquisitionSortSemanticMeaning": (
                "NONE"
            ),
            "completePagination": True,
            "pageOffsets": sorted(
                captured
            ),
            "pageCount": len(
                captured
            ),
            "columns": expected_header,
            "rowCount": len(
                all_rows
            ),
            "rows": all_rows,
        }

        write_json(
            artifact_root / "dataset.json",
            dataset,
        )

        return {
            "requestId": request[
                "requestId"
            ],
            "sourceFamily": family,
            "required": bool(
                request["required"]
            ),
            "captureMode": (
                "completePaginatedTable"
            ),
            "requestStatus": "captured",
            "physicalRequestCount": (
                physical_count
            ),
            "capturedPageCount": len(
                captured
            ),
            "pageOffsets": sorted(
                captured
            ),
            "rowCount": len(
                all_rows
            ),
            "columns": expected_header,
            "error": None,
        }

    except (
        HTTPError,
        URLError,
        TimeoutError,
        OSError,
        ValueError,
    ) as exc:
        return {
            "requestId": request[
                "requestId"
            ],
            "sourceFamily": family,
            "required": bool(
                request["required"]
            ),
            "captureMode": (
                "completePaginatedTable"
            ),
            "requestStatus": "failed",
            "physicalRequestCount": (
                physical_count
            ),
            "capturedPageCount": len(
                captured
            ),
            "pageOffsets": sorted(
                captured
            ),
            "rowCount": len(
                all_rows
            ),
            "columns": expected_header,
            "error": str(exc),
        }



def capture_paginated_pages(
    *,
    request: dict[str, Any],
    output_root: Path,
) -> dict[str, Any]:
    family = str(
        request["sourceFamily"]
    )

    slug = safe_slug(family)

    artifact_root = (
        output_root
        / "responses"
        / "league-intelligence"
        / slug
    )

    metadata_root = (
        output_root
        / "metadata"
        / "league-intelligence"
        / slug
    )

    requested_url = str(
        request["requestedUrl"]
    )

    policy = request[
        "paginationPolicy"
    ]

    page_size = int(
        policy["pageSize"]
    )

    queue: list[tuple[int, str]] = [
        (0, requested_url)
    ]

    queued: set[int] = {0}
    captured: set[int] = set()

    physical_count = 0

    try:
        while queue:
            queue.sort(
                key=lambda item: item[0]
            )

            offset, url = queue.pop(0)

            if offset in captured:
                continue

            if len(captured) >= MAX_PAGINATED_PAGES:
                raise ValueError(
                    "Pagination exceeded safety limit "
                    f"of {MAX_PAGINATED_PAGES} pages."
                )

            (
                status,
                effective_url,
                headers,
                body,
            ) = fetch(url)

            physical_count += 1

            html_text = body.decode(
                "utf-8",
                errors="replace",
            )

            body_path = (
                artifact_root
                / f"page-{offset:05d}.html"
            )

            headers_path = (
                artifact_root
                / f"page-{offset:05d}.headers.txt"
            )

            metadata_path = (
                metadata_root
                / f"page-{offset:05d}.json"
            )

            body_path.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            body_path.write_bytes(body)

            write_headers(
                headers_path,
                status=status,
                effective_url=effective_url,
                headers=headers,
            )

            discovered = discover_offsets(
                html_text,
                initial_url=requested_url,
                current_url=effective_url,
                page_size=page_size,
            )

            metadata = {
                "schemaVersion": (
                    "strat365-league-intelligence-"
                    "raw-response-metadata-v0"
                ),
                "requestId": request[
                    "requestId"
                ],
                "sourceFamily": family,
                "requestedUrl": url,
                "effectiveUrl": effective_url,
                "httpStatus": status,
                "capturedAtUtc": utc_now(),
                "byteCount": len(body),
                "sha256": sha256_bytes(body),
                "pageOffset": offset,
                "discoveredOffsets": sorted(
                    discovered
                ),
                "captureMode": (
                    "completePaginatedPages"
                ),
                "transportResult": "PASS",
            }

            write_json(
                metadata_path,
                metadata,
            )

            captured.add(offset)

            for (
                discovered_offset,
                discovered_url,
            ) in discovered.items():
                if (
                    discovered_offset
                    not in captured
                    and discovered_offset
                    not in queued
                ):
                    queue.append(
                        (
                            discovered_offset,
                            discovered_url,
                        )
                    )

                    queued.add(
                        discovered_offset
                    )

        if not captured:
            raise ValueError(
                f"{family} captured no pages."
            )

        return {
            "requestId": request[
                "requestId"
            ],
            "sourceFamily": family,
            "required": bool(
                request["required"]
            ),
            "captureMode": (
                "completePaginatedPages"
            ),
            "requestStatus": "captured",
            "physicalRequestCount": (
                physical_count
            ),
            "capturedPageCount": len(
                captured
            ),
            "pageOffsets": sorted(
                captured
            ),
            "rowCount": None,
            "columns": None,
            "error": None,
        }

    except (
        HTTPError,
        URLError,
        TimeoutError,
        OSError,
        ValueError,
    ) as exc:
        return {
            "requestId": request[
                "requestId"
            ],
            "sourceFamily": family,
            "required": bool(
                request["required"]
            ),
            "captureMode": (
                "completePaginatedPages"
            ),
            "requestStatus": "failed",
            "physicalRequestCount": (
                physical_count
            ),
            "capturedPageCount": len(
                captured
            ),
            "pageOffsets": sorted(
                captured
            ),
            "rowCount": None,
            "columns": None,
            "error": str(exc),
        }

def execute(
    *,
    plan_path: Path,
    output_root: Path,
) -> dict[str, Any]:
    plan = load_json(
        plan_path
    )

    if (
        plan.get("schemaVersion")
        != EXPECTED_PLAN_SCHEMA
    ):
        raise ValueError(
            "Unexpected capture-plan schema."
        )

    requests = plan.get(
        "requests"
    )

    if not isinstance(
        requests,
        list,
    ):
        raise ValueError(
            "Plan requests collection is missing."
        )

    if len(requests) != int(
        plan.get(
            "plannedSourceCount",
            -1,
        )
    ):
        raise ValueError(
            "Plan source count does not match "
            "plannedSourceCount."
        )

    output_root.mkdir(
        parents=True,
        exist_ok=True,
    )

    results: list[
        dict[str, Any]
    ] = []

    for request in requests:
        mode = str(
            request.get(
                "captureMode"
            )
        )

        if mode == "singlePage":
            result = capture_single_page(
                request=request,
                output_root=output_root,
            )

        elif mode == "completePaginatedTable":
            result = capture_paginated_table(
                request=request,
                output_root=output_root,
            )

        elif mode == "completePaginatedPages":
            result = capture_paginated_pages(
                request=request,
                output_root=output_root,
            )

        else:
            result = {
                "requestId": request.get(
                    "requestId"
                ),
                "sourceFamily": request.get(
                    "sourceFamily"
                ),
                "required": bool(
                    request.get(
                        "required"
                    )
                ),
                "captureMode": mode,
                "requestStatus": "failed",
                "physicalRequestCount": 0,
                "capturedPageCount": 0,
                "rowCount": None,
                "columns": None,
                "error": (
                    "Unsupported captureMode: "
                    f"{mode}"
                ),
            }

        results.append(
            result
        )

    required_failures = [
        result
        for result in results
        if (
            result["required"]
            and result[
                "requestStatus"
            ]
            != "captured"
        )
    ]

    optional_failures = [
        result
        for result in results
        if (
            not result["required"]
            and result[
                "requestStatus"
            ]
            != "captured"
        )
    ]

    physical_request_count = sum(
        int(
            result[
                "physicalRequestCount"
            ]
        )
        for result in results
    )

    manifest = {
        "schemaVersion": SCHEMA_VERSION,
        "captureStatus": (
            "PASS"
            if not required_failures
            else "FAIL"
        ),
        "capturedAtUtc": utc_now(),
        "planPath": str(
            plan_path
        ),
        "planSha256": sha256_file(
            plan_path
        ),
        "leagueId": str(
            plan["leagueId"]
        ),
        "teamId": str(
            plan["teamId"]
        ),
        "leagueDate": str(
            plan["leagueDate"]
        ),
        "phase": str(
            plan["phase"]
        ),
        "logicalSourceCount": len(
            requests
        ),
        "requiredSourceCount": int(
            plan["requiredSourceCount"]
        ),
        "capturedLogicalSourceCount": sum(
            result[
                "requestStatus"
            ]
            == "captured"
            for result in results
        ),
        "requiredFailureCount": len(
            required_failures
        ),
        "optionalFailureCount": len(
            optional_failures
        ),
        "physicalHttpRequestCount": (
            physical_request_count
        ),
        "canonicalDataChanged": False,
        "gameCaptureContractChanged": False,
        "bieOwnsSortingAndAnalysis": True,
        "requests": results,
    }

    write_json(
        output_root
        / "league-intelligence-capture-manifest.json",
        manifest,
    )

    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--plan",
        required=True,
    )

    parser.add_argument(
        "--output-root",
        required=True,
    )

    args = parser.parse_args()

    try:
        manifest = execute(
            plan_path=Path(
                args.plan
            ).resolve(),
            output_root=Path(
                args.output_root
            ).resolve(),
        )

    except Exception as exc:
        print(
            json.dumps(
                {
                    "status": "FAIL",
                    "error": str(exc),
                },
                separators=(",", ":"),
            )
        )

        return 1

    summary = {
        "status": manifest[
            "captureStatus"
        ],
        "leagueId": manifest[
            "leagueId"
        ],
        "logicalSourceCount": (
            manifest[
                "logicalSourceCount"
            ]
        ),
        "capturedLogicalSourceCount": (
            manifest[
                "capturedLogicalSourceCount"
            ]
        ),
        "requiredFailureCount": (
            manifest[
                "requiredFailureCount"
            ]
        ),
        "optionalFailureCount": (
            manifest[
                "optionalFailureCount"
            ]
        ),
        "physicalHttpRequestCount": (
            manifest[
                "physicalHttpRequestCount"
            ]
        ),
    }

    print(
        json.dumps(
            summary,
            separators=(",", ":"),
        )
    )

    return (
        0
        if manifest[
            "captureStatus"
        ]
        == "PASS"
        else 1
    )


if __name__ == "__main__":
    raise SystemExit(main())