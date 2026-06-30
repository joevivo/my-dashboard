from __future__ import annotations

import argparse
import csv
import json
import re
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen


DEFAULT_SEASON = "1968"
DEFAULT_URL_TEMPLATE = "https://365.strat-o-matic.com/playerset/browse/{season}"
DEFAULT_OUT_DIR = Path("data/baseball/parsed/strat365")
PAGE_SIZE = 50

HITTER_POSITION_ID = "10"
PITCHER_POSITION_ID = "1"

HITTER_COLUMNS = [
    "Name",
    "Team",
    "B",
    "P",
    "Def.",
    "AB",
    "R",
    "H",
    "2B",
    "3B",
    "HR",
    "RBI",
    "BB",
    "SO",
    "SB",
    "CS",
    "Stl",
    "Run",
    "BA",
    "OBP",
    "SLG",
    "Inj",
    "BAL",
    "Salary",
]

PITCHER_COLUMNS = [
    "Name",
    "Team",
    "T",
    "End.",
    "W",
    "L",
    "S",
    "IP",
    "H",
    "ER",
    "BB",
    "SO",
    "HR",
    "Hold",
    "BkR",
    "WpR",
    "Bat",
    "ERA",
    "WHIP",
    "BAL",
    "Salary",
]


@dataclass
class ParsedCell:
    text: str
    links: list[str]


class PlayerTableParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.rows: list[list[ParsedCell]] = []
        self.current_row: list[ParsedCell] | None = None
        self.current_cell_text: list[str] | None = None
        self.current_cell_links: list[str] | None = None
        self.in_cell = False
        self.skip_depth = 0

    def handle_starttag(self, tag: str, attrs) -> None:
        tag = tag.lower()
        attrs = dict(attrs)

        if tag in {"script", "style", "noscript"}:
            self.skip_depth += 1
            return

        if self.skip_depth:
            return

        if tag == "tr":
            self.current_row = []

        if tag in {"td", "th"} and self.current_row is not None:
            self.current_cell_text = []
            self.current_cell_links = []
            self.in_cell = True

        if tag == "a" and self.in_cell and self.current_cell_links is not None:
            href = attrs.get("href")
            if href:
                self.current_cell_links.append(href)

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()

        if tag in {"script", "style", "noscript"} and self.skip_depth:
            self.skip_depth -= 1
            return

        if self.skip_depth:
            return

        if tag in {"td", "th"} and self.current_row is not None and self.current_cell_text is not None:
            self.current_row.append(
                ParsedCell(
                    text=normalize_space("".join(self.current_cell_text)),
                    links=list(self.current_cell_links or []),
                )
            )
            self.current_cell_text = None
            self.current_cell_links = None
            self.in_cell = False

        if tag == "tr" and self.current_row is not None:
            if any(cell.text for cell in self.current_row):
                self.rows.append(self.current_row)
            self.current_row = None

    def handle_data(self, data: str) -> None:
        if self.skip_depth:
            return

        if self.in_cell and self.current_cell_text is not None:
            self.current_cell_text.append(data)


def normalize_space(value: str) -> str:
    return re.sub(r"\s+", " ", value.replace("\xa0", " ")).strip()


def salary_millions(value: str) -> float:
    text = normalize_space(value).replace("$", "").replace(",", "").replace("M", "").replace("m", "")
    if text.startswith("."):
        text = "0" + text
    return float(text)


def parse_int(value: str) -> int | None:
    text = normalize_space(value).replace(",", "")
    if text in {"", "--"}:
        return None
    try:
        return int(text)
    except ValueError:
        return None


def parse_float(value: str) -> float | None:
    text = normalize_space(value).replace(",", "")
    if text in {"", "--"}:
        return None
    if text.startswith("."):
        text = "0" + text
    try:
        return float(text)
    except ValueError:
        return None


def parse_player_id(links: list[str]) -> str | None:
    for href in links:
        match = re.search(r"/player/(\d+)/", href)
        if match:
            return match.group(1)
    return None


def parse_team_id(links: list[str], season: str) -> str | None:
    pattern = rf"/playerset/browse/team/{re.escape(season)}/(\d+)"
    for href in links:
        match = re.search(pattern, href)
        if match:
            return match.group(1)
    return None


def fetch_page(url: str, position_id: str, start_row: int) -> str:
    payload = urlencode(
        {
            "name": "",
            "start_row": str(start_row),
            "position_id": position_id,
            "order_by": "salary",
            "sort_dir": "desc",
        }
    ).encode("utf-8")

    request = Request(
        url,
        data=payload,
        headers={
            "User-Agent": "Mozilla/5.0 BIE-Strat365-PlayerSet-Importer/0.1",
            "Accept": "text/html,application/xhtml+xml",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        method="POST",
    )

    with urlopen(request, timeout=30) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        return response.read().decode(charset, errors="replace")


def parse_rows_from_html(html: str, expected_columns: list[str]) -> list[list[ParsedCell]]:
    parser = PlayerTableParser()
    parser.feed(html)

    rows = parser.rows
    output: list[list[ParsedCell]] = []
    in_player_table = False

    for row in rows:
        texts = [cell.text for cell in row]

        if texts == expected_columns:
            in_player_table = True
            continue

        if not in_player_table:
            continue

        if len(texts) != len(expected_columns):
            continue

        if not texts[-1].endswith("M"):
            continue

        output.append(row)

    return output


def parse_hitter_row(row: list[ParsedCell], season: str, source_position_id: str) -> dict[str, Any]:
    values = [cell.text for cell in row]
    data = dict(zip(HITTER_COLUMNS, values))

    return {
        "role": "hitter",
        "season": season,
        "sourcePositionId": source_position_id,
        "playerId": parse_player_id(row[0].links),
        "playerName": data["Name"],
        "team": data["Team"],
        "teamId": parse_team_id(row[1].links, season),
        "bats": data["B"],
        "primaryPosition": data["P"],
        "defense": data["Def."],
        "ab": parse_int(data["AB"]),
        "runs": parse_int(data["R"]),
        "hits": parse_int(data["H"]),
        "doubles": parse_int(data["2B"]),
        "triples": parse_int(data["3B"]),
        "homeRuns": parse_int(data["HR"]),
        "rbi": parse_int(data["RBI"]),
        "walks": parse_int(data["BB"]),
        "strikeouts": parse_int(data["SO"]),
        "stolenBases": parse_int(data["SB"]),
        "caughtStealing": parse_int(data["CS"]),
        "steal": data["Stl"],
        "runRating": data["Run"],
        "battingAverage": parse_float(data["BA"]),
        "onBasePercentage": parse_float(data["OBP"]),
        "sluggingPercentage": parse_float(data["SLG"]),
        "injury": data["Inj"],
        "balance": data["BAL"],
        "salary": {
            "raw": data["Salary"],
            "millions": salary_millions(data["Salary"]),
        },
    }


def parse_pitcher_row(row: list[ParsedCell], season: str, source_position_id: str) -> dict[str, Any]:
    values = [cell.text for cell in row]
    data = dict(zip(PITCHER_COLUMNS, values))

    return {
        "role": "pitcher",
        "season": season,
        "sourcePositionId": source_position_id,
        "playerId": parse_player_id(row[0].links),
        "playerName": data["Name"],
        "team": data["Team"],
        "teamId": parse_team_id(row[1].links, season),
        "throws": data["T"],
        "endurance": data["End."],
        "wins": parse_int(data["W"]),
        "losses": parse_int(data["L"]),
        "saves": parse_int(data["S"]),
        "inningsPitched": data["IP"],
        "hitsAllowed": parse_int(data["H"]),
        "earnedRuns": parse_int(data["ER"]),
        "walks": parse_int(data["BB"]),
        "strikeouts": parse_int(data["SO"]),
        "homeRunsAllowed": parse_int(data["HR"]),
        "hold": data["Hold"],
        "balkRating": data["BkR"],
        "wildPitchRating": data["WpR"],
        "batting": data["Bat"],
        "era": parse_float(data["ERA"]),
        "whip": parse_float(data["WHIP"]),
        "balance": data["BAL"],
        "salary": {
            "raw": data["Salary"],
            "millions": salary_millions(data["Salary"]),
        },
    }


def crawl_role(url: str, season: str, role: str, position_id: str) -> list[dict[str, Any]]:
    players: list[dict[str, Any]] = []
    seen_keys: set[tuple[str, str, str]] = set()

    columns = HITTER_COLUMNS if role == "hitter" else PITCHER_COLUMNS
    parser = parse_hitter_row if role == "hitter" else parse_pitcher_row

    start_row = 0
    while True:
        html = fetch_page(url, position_id, start_row)
        page_rows = parse_rows_from_html(html, columns)

        print(f"{role} start_row={start_row}: {len(page_rows)} rows")

        if not page_rows:
            break

        for row in page_rows:
            player = parser(row, season, position_id)
            key = (
                str(player.get("playerId") or ""),
                player["playerName"],
                player["team"],
            )
            if key in seen_keys:
                continue
            seen_keys.add(key)
            players.append(player)

        if len(page_rows) < PAGE_SIZE:
            break

        start_row += PAGE_SIZE

    return players


def write_outputs(season: str, url: str, hitters: list[dict[str, Any]], pitchers: list[dict[str, Any]], out_dir: Path) -> tuple[Path, Path]:
    season_dir = out_dir / season / "playerset"
    season_dir.mkdir(parents=True, exist_ok=True)

    json_path = season_dir / f"{season}.playerset.json"
    md_path = season_dir / f"{season}.playerset-summary.md"
    csv_path = season_dir / f"{season}.playerset.csv"

    payload = {
        "schemaVersion": "bie-strat365-playerset-v0",
        "season": season,
        "sourceUrl": url,
        "counts": {
            "hitters": len(hitters),
            "pitchers": len(pitchers),
            "total": len(hitters) + len(pitchers),
        },
        "hitters": hitters,
        "pitchers": pitchers,
    }

    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    flat_rows = []
    for player in hitters + pitchers:
        flat_rows.append(
            {
                "role": player["role"],
                "playerId": player.get("playerId") or "",
                "playerName": player["playerName"],
                "team": player["team"],
                "teamId": player.get("teamId") or "",
                "positionOrEndurance": player.get("primaryPosition") or player.get("endurance") or "",
                "throwsOrBats": player.get("throws") or player.get("bats") or "",
                "balance": player.get("balance") or "",
                "salary": player["salary"]["raw"],
                "salaryMillions": player["salary"]["millions"],
            }
        )

    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "role",
                "playerId",
                "playerName",
                "team",
                "teamId",
                "positionOrEndurance",
                "throwsOrBats",
                "balance",
                "salary",
                "salaryMillions",
            ],
        )
        writer.writeheader()
        writer.writerows(flat_rows)

    lines = [
        f"# Strat365 {season} Player Set Summary",
        "",
        f"Source: {url}",
        "",
        "## Counts",
        "",
        f"- Hitters: {len(hitters)}",
        f"- Pitchers: {len(pitchers)}",
        f"- Total: {len(hitters) + len(pitchers)}",
        "",
        "## Top Hitter Salaries",
        "",
    ]

    for player in sorted(hitters, key=lambda item: item["salary"]["millions"], reverse=True)[:20]:
        lines.append(
            f"- {player['playerName']} | {player['team']} | {player['primaryPosition']} | "
            f"{player['salary']['raw']} | OBP {player.get('onBasePercentage')} | SLG {player.get('sluggingPercentage')}"
        )

    lines.extend(["", "## Top Pitcher Salaries", ""])

    for player in sorted(pitchers, key=lambda item: item["salary"]["millions"], reverse=True)[:20]:
        lines.append(
            f"- {player['playerName']} | {player['team']} | {player['endurance']} | "
            f"{player['salary']['raw']} | ERA {player.get('era')} | WHIP {player.get('whip')}"
        )

    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    return json_path, md_path, csv_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Import Strat365 player-set browser rows for a season.")
    parser.add_argument("--season", default=DEFAULT_SEASON)
    parser.add_argument("--url")
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    args = parser.parse_args()

    url = args.url or DEFAULT_URL_TEMPLATE.format(season=args.season)

    hitters = crawl_role(url, args.season, "hitter", HITTER_POSITION_ID)
    pitchers = crawl_role(url, args.season, "pitcher", PITCHER_POSITION_ID)

    if not hitters:
        raise SystemExit("No hitters parsed.")
    if not pitchers:
        raise SystemExit("No pitchers parsed.")

    json_path, md_path, csv_path = write_outputs(args.season, url, hitters, pitchers, args.out_dir)

    print()
    print(f"Wrote JSON: {json_path}")
    print(f"Wrote Markdown: {md_path}")
    print(f"Wrote CSV: {csv_path}")
    print(f"Season: {args.season}")
    print(f"Hitters: {len(hitters)}")
    print(f"Pitchers: {len(pitchers)}")
    print(f"Total: {len(hitters) + len(pitchers)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
