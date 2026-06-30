from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from urllib.request import Request, urlopen


DEFAULT_SEASON = "1968"
DEFAULT_URL_TEMPLATE = "https://365.strat-o-matic.com/playerset/browse/ballparks/{season}"
DEFAULT_OUT_DIR = Path("data/baseball/parsed/strat365")


@dataclass
class BallparkRow:
    name: str
    capacity: int
    si_left: int
    si_right: int
    hr_left: int
    hr_right: int


class TableParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.rows: list[list[str]] = []
        self.current_row: list[str] | None = None
        self.current_cell: list[str] | None = None
        self.in_cell = False
        self.skip_depth = 0

    def handle_starttag(self, tag: str, attrs) -> None:
        tag = tag.lower()
        if tag in {"script", "style", "noscript"}:
            self.skip_depth += 1
            return
        if self.skip_depth:
            return
        if tag == "tr":
            self.current_row = []
        elif tag in {"td", "th"} and self.current_row is not None:
            self.current_cell = []
            self.in_cell = True

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in {"script", "style", "noscript"} and self.skip_depth:
            self.skip_depth -= 1
            return
        if self.skip_depth:
            return
        if tag in {"td", "th"} and self.current_row is not None and self.current_cell is not None:
            value = normalize_space("".join(self.current_cell))
            self.current_row.append(value)
            self.current_cell = None
            self.in_cell = False
        elif tag == "tr" and self.current_row is not None:
            if any(cell.strip() for cell in self.current_row):
                self.rows.append(self.current_row)
            self.current_row = None

    def handle_data(self, data: str) -> None:
        if self.skip_depth:
            return
        if self.in_cell and self.current_cell is not None:
            self.current_cell.append(data)


def normalize_space(value: str) -> str:
    return re.sub(r"\s+", " ", value.replace("\xa0", " ")).strip()


def parse_int(value: str) -> int:
    text = normalize_space(value).replace(",", "")
    match = re.search(r"-?\d+", text)
    if not match:
        raise ValueError(f"Could not parse integer from {value!r}")
    return int(match.group(0))


def fetch_html(url: str) -> str:
    request = Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 BIE-Strat365-Ballpark-Importer/0.1",
            "Accept": "text/html,application/xhtml+xml",
        },
    )
    with urlopen(request, timeout=30) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        return response.read().decode(charset, errors="replace")


def parse_ballparks(html: str) -> list[BallparkRow]:
    parser = TableParser()
    parser.feed(html)

    ballparks: list[BallparkRow] = []

    for row in parser.rows:
        cells = [normalize_space(cell) for cell in row if normalize_space(cell)]

        if len(cells) < 6:
            continue

        header_text = " ".join(cells).lower()
        if "ballpark" in header_text and "capacity" in header_text:
            continue

        # Expected row shape:
        # Name | Capacity | SI L | SI R | HR L | HR R
        try:
            candidate = BallparkRow(
                name=cells[0],
                capacity=parse_int(cells[1]),
                si_left=parse_int(cells[2]),
                si_right=parse_int(cells[3]),
                hr_left=parse_int(cells[4]),
                hr_right=parse_int(cells[5]),
            )
        except ValueError:
            continue

        if not candidate.name or candidate.name.lower() in {"name", "ballpark"}:
            continue

        ballparks.append(candidate)

    # Deduplicate while preserving order.
    seen = set()
    unique: list[BallparkRow] = []
    for item in ballparks:
        key = item.name.lower()
        if key in seen:
            continue
        seen.add(key)
        unique.append(item)

    return unique


def classify_park(row: BallparkRow) -> dict:
    single_avg = (row.si_left + row.si_right) / 2
    homer_avg = (row.hr_left + row.hr_right) / 2

    if homer_avg >= 16:
        homer_shape = "power-amplifying"
    elif homer_avg <= 5:
        homer_shape = "power-suppressing"
    else:
        homer_shape = "neutral-to-moderate-power"

    if single_avg >= 14:
        single_shape = "hit-amplifying"
    elif single_avg <= 6:
        single_shape = "hit-suppressing"
    else:
        single_shape = "neutral-to-moderate-hits"

    return {
        "singleAverage": round(single_avg, 2),
        "homerAverage": round(homer_avg, 2),
        "singleShape": single_shape,
        "homerShape": homer_shape,
    }


def write_outputs(season: str, url: str, ballparks: list[BallparkRow], out_dir: Path) -> tuple[Path, Path]:
    season_dir = out_dir / season / "ballparks"
    season_dir.mkdir(parents=True, exist_ok=True)

    json_path = season_dir / f"{season}.ballparks.json"
    md_path = season_dir / f"{season}.ballparks.md"

    payload = {
        "schemaVersion": "bie-strat365-ballparks-v0",
        "season": season,
        "sourceUrl": url,
        "count": len(ballparks),
        "ballparks": [
            {
                "name": row.name,
                "capacity": row.capacity,
                "singleLeft": row.si_left,
                "singleRight": row.si_right,
                "homeRunLeft": row.hr_left,
                "homeRunRight": row.hr_right,
                **classify_park(row),
            }
            for row in ballparks
        ],
    }

    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    lines = [
        f"# Strat365 {season} Ballparks",
        "",
        f"Source: {url}",
        "",
        f"Ballparks parsed: {len(ballparks)}",
        "",
        "| Ballpark | Capacity | SI L | SI R | HR L | HR R | Shape |",
        "|---|---:|---:|---:|---:|---:|---|",
    ]

    for row in ballparks:
        shape = classify_park(row)
        lines.append(
            f"| {row.name} | {row.capacity:,} | {row.si_left} | {row.si_right} | "
            f"{row.hr_left} | {row.hr_right} | {shape['singleShape']} / {shape['homerShape']} |"
        )

    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    return json_path, md_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Import Strat365 ballparks for a player-set season.")
    parser.add_argument("--season", default=DEFAULT_SEASON)
    parser.add_argument("--url", help="Optional explicit ballpark URL.")
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    args = parser.parse_args()

    url = args.url or DEFAULT_URL_TEMPLATE.format(season=args.season)
    html = fetch_html(url)
    ballparks = parse_ballparks(html)

    if not ballparks:
        raise SystemExit(f"No ballparks parsed from {url}")

    json_path, md_path = write_outputs(args.season, url, ballparks, args.out_dir)

    print(f"Wrote JSON: {json_path}")
    print(f"Wrote Markdown: {md_path}")
    print(f"Season: {args.season}")
    print(f"Ballparks parsed: {len(ballparks)}")

    for row in ballparks:
        shape = classify_park(row)
        print(
            f"- {row.name}: SI {row.si_left}/{row.si_right}, "
            f"HR {row.hr_left}/{row.hr_right}, "
            f"{shape['singleShape']} / {shape['homerShape']}"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
