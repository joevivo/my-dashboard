from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from typing import Iterable
from urllib.request import Request, urlopen


DEFAULT_OUT_DIR = Path("data/baseball/parsed/strat365/1980/draft-reports")


BLOCK_TAGS = {
    "br",
    "p",
    "div",
    "section",
    "article",
    "header",
    "footer",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "li",
    "tr",
    "table",
    "thead",
    "tbody",
    "tfoot",
}

CELL_TAGS = {"td", "th"}
SKIP_TAGS = {"script", "style", "noscript"}


class VisibleTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []
        self.skip_depth = 0

    def handle_starttag(self, tag: str, attrs) -> None:
        tag = tag.lower()
        if tag in SKIP_TAGS:
            self.skip_depth += 1
            return
        if self.skip_depth:
            return
        if tag in CELL_TAGS:
            self.parts.append("\t")
        elif tag in BLOCK_TAGS:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in SKIP_TAGS and self.skip_depth:
            self.skip_depth -= 1
            return
        if self.skip_depth:
            return
        if tag in CELL_TAGS:
            self.parts.append("\t")
        elif tag in BLOCK_TAGS:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if self.skip_depth:
            return
        self.parts.append(data)

    def text(self) -> str:
        return "".join(self.parts)


@dataclass
class ImportedPlayer:
    player_name: str
    slot: str
    section: str
    salary: str
    raw_line: str


def normalize_space(value: str) -> str:
    return re.sub(r"\s+", " ", value.replace("\xa0", " ")).strip()


def slugify(value: str) -> str:
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-") or "team"


def fetch_html(url: str) -> str:
    request = Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 BIE-Strat365-Team-Importer/0.1",
            "Accept": "text/html,application/xhtml+xml",
        },
    )
    with urlopen(request, timeout=30) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        return response.read().decode(charset, errors="replace")


def visible_lines(html: str) -> list[str]:
    parser = VisibleTextParser()
    parser.feed(html)
    lines = []
    for raw in parser.text().splitlines():
        line = normalize_space(raw)
        if line:
            lines.append(line)
    return lines


def extract_metadata(lines: list[str], url: str) -> dict:
    joined = "\n".join(lines)

    def find_one(pattern: str) -> str | None:
        match = re.search(pattern, joined, flags=re.I)
        return normalize_space(match.group(1)) if match else None

    metadata = {
        "sourceUrl": url,
        "team": find_one(r"TEAM:\s*(.+)"),
        "result": None,
        "owner": find_one(r"Owner:\s*(.+)"),
        "manager": find_one(r"Manager:\s*(.+)"),
        "record": find_one(r"Record:\s*([0-9]+-[0-9]+)"),
        "ballpark": find_one(r"Home Ballpark:\s*(.+)"),
        "initialSalaryCap": find_one(r"Initial Salary Cap:\s*([$0-9,]+)"),
        "totalCurrentValue": find_one(r"Total Current Value:\s*([$0-9,]+)"),
        "rosterValue": find_one(r"Roster Value:\s*([$0-9,]+)"),
        "cashAvailable": find_one(r"Cash Available:\s*([$0-9,]+)"),
    }

    for line in lines:
        if "Won the Championship" in line or "Lost the Finals" in line or "Lost in Semi-Finals" in line:
            metadata["result"] = line
            break

    return metadata


def find_section_lines(lines: list[str], start_label: str, next_label: str | None) -> list[str]:
    start_idx = None
    for i, line in enumerate(lines):
        if line.startswith(start_label):
            start_idx = i
            break

    if start_idx is None:
        return []

    end_idx = len(lines)
    if next_label:
        for i in range(start_idx + 1, len(lines)):
            if lines[i].startswith(next_label):
                end_idx = i
                break

    return lines[start_idx:end_idx]


def candidate_stat_lines(section_lines: Iterable[str]) -> list[str]:
    result = []
    for line in section_lines:
        if not line:
            continue
        if line.startswith(("Pitchers", "Hitters", "Name ", "TOTALS")):
            continue
        if re.search(r"\s\.?\d+(?:\.\d+)?M$", line):
            result.append(line)
    return result


PITCHER_RE = re.compile(
    r"^(?P<name>.+?,\s+[A-Z]\.)(?:\s+I(?:-\d+)?)?\s+"
    r"(?P<throws>[LRS])\s+(?P<endurance>\S+)\s+.*?\s+"
    r"(?P<salary>\.?\d+(?:\.\d+)?M)$"
)

HITTER_RE = re.compile(
    r"^(?P<name>.+?,\s+[A-Z]\.)(?:\s+I(?:-\d+)?)?\s+"
    r"(?P<bats>[LRS])\s+(?P<position>C|1B|2B|3B|SS|LF|CF|RF|DH)\s+.*?\s+"
    r"(?P<salary>\.?\d+(?:\.\d+)?M)$"
)


PITCHER_COLUMNS = [
    "Name",
    "T",
    "End.",
    "W",
    "L",
    "S",
    "BS",
    "IP",
    "H",
    "R",
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

HITTER_COLUMNS = [
    "Name",
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
    "HBP",
    "SB",
    "CS",
    "E",
    "Stl",
    "Run",
    "BA",
    "OBP",
    "SLG",
    "Inj",
    "BAL",
    "Salary",
]


def clean_player_name(value: str) -> str:
    return normalize_space(re.sub(r"\s+I(?:-\d+)?\s*$", "", value))


def table_rows_from_cell_lines(section_lines: list[str], columns: list[str]) -> list[list[str]]:
    try:
        header_start = next(
            idx
            for idx in range(0, len(section_lines) - len(columns) + 1)
            if section_lines[idx : idx + len(columns)] == columns
        )
    except StopIteration:
        return []

    width = len(columns)
    rows: list[list[str]] = []
    idx = header_start + width

    while idx + width <= len(section_lines):
        if section_lines[idx] == "TOTALS":
            break

        row = section_lines[idx : idx + width]
        if row[0].startswith(("Pitchers", "Hitters")):
            idx += 1
            continue

        if re.search(r"\.?\d+(?:\.\d+)?M$", row[-1]):
            rows.append(row)
            idx += width
        else:
            idx += 1

    return rows


def pitcher_slot(endurance: str) -> str:
    endurance = endurance.upper()
    if endurance.startswith("R") and not endurance.startswith("S"):
        return "relief"
    return "starter"


def parse_players(lines: list[str]) -> list[ImportedPlayer]:
    players: list[ImportedPlayer] = []

    pitcher_section = find_section_lines(lines, "Pitchers", "Hitters")
    hitter_section = find_section_lines(lines, "Hitters", None)

    pitcher_lines = candidate_stat_lines(pitcher_section)
    hitter_lines = candidate_stat_lines(hitter_section)

    if pitcher_lines or hitter_lines:
        for line in pitcher_lines:
            match = PITCHER_RE.match(line)
            if not match:
                raise ValueError(f"Could not parse pitcher row: {line}")
            players.append(
                ImportedPlayer(
                    player_name=clean_player_name(match.group("name")),
                    slot=pitcher_slot(match.group("endurance")),
                    section="pitcher",
                    salary=match.group("salary"),
                    raw_line=line,
                )
            )

        for line in hitter_lines:
            match = HITTER_RE.match(line)
            if not match:
                raise ValueError(f"Could not parse hitter row: {line}")
            players.append(
                ImportedPlayer(
                    player_name=clean_player_name(match.group("name")),
                    slot=match.group("position"),
                    section="hitter",
                    salary=match.group("salary"),
                    raw_line=line,
                )
            )

        return players

    for row in table_rows_from_cell_lines(pitcher_section, PITCHER_COLUMNS):
        players.append(
            ImportedPlayer(
                player_name=clean_player_name(row[0]),
                slot=pitcher_slot(row[2]),
                section="pitcher",
                salary=row[-1],
                raw_line=" | ".join(row),
            )
        )

    for row in table_rows_from_cell_lines(hitter_section, HITTER_COLUMNS):
        players.append(
            ImportedPlayer(
                player_name=clean_player_name(row[0]),
                slot=row[2],
                section="hitter",
                salary=row[-1],
                raw_line=" | ".join(row),
            )
        )

    return players


def default_output_path(metadata: dict, url: str) -> Path:
    team = metadata.get("team") or url.rstrip("/").split("/")[-1]
    ballpark = metadata.get("ballpark") or "unknown-park"
    season_match = re.search(r"\b(19\d{2}|20\d{2})\b", ballpark)
    season = season_match.group(1) if season_match else "1980"

    filename = (
        f"{season}."
        f"{slugify(ballpark.replace(season, ''))}-"
        f"{slugify(team)}-roster-template-v0.csv"
    )
    return DEFAULT_OUT_DIR / filename


def write_roster_csv(path: Path, players: list[ImportedPlayer]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["playerName", "slot"])
        writer.writeheader()
        for player in players:
            writer.writerow({"playerName": player.player_name, "slot": player.slot})


def write_metadata(path: Path, metadata: dict, players: list[ImportedPlayer]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        **metadata,
        "playerCount": len(players),
        "pitcherCount": sum(1 for player in players if player.section == "pitcher"),
        "hitterCount": sum(1 for player in players if player.section == "hitter"),
        "players": [player.__dict__ for player in players],
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Import a public Strat365 team page into a BIE roster-template CSV."
    )
    parser.add_argument("url", help="Public Strat365 team URL, e.g. https://365.strat-o-matic.com/team/1820660")
    parser.add_argument("--out", type=Path, help="Output roster-template CSV path.")
    parser.add_argument("--metadata-out", type=Path, help="Optional metadata JSON output path.")
    args = parser.parse_args()

    html = fetch_html(args.url)
    lines = visible_lines(html)
    metadata = extract_metadata(lines, args.url)
    players = parse_players(lines)

    if not players:
        raise SystemExit("No active roster players parsed from the team page.")

    out_path = args.out or default_output_path(metadata, args.url)
    write_roster_csv(out_path, players)

    if args.metadata_out:
        write_metadata(args.metadata_out, metadata, players)

    print(f"Wrote roster CSV: {out_path}")
    if args.metadata_out:
        print(f"Wrote metadata JSON: {args.metadata_out}")
    print(f"Team: {metadata.get('team') or 'unknown'}")
    print(f"Result: {metadata.get('result') or 'unknown'}")
    print(f"Record: {metadata.get('record') or 'unknown'}")
    print(f"Ballpark: {metadata.get('ballpark') or 'unknown'}")
    print(
        "Players parsed: "
        f"{len(players)} total, "
        f"{sum(1 for player in players if player.section == 'pitcher')} pitchers, "
        f"{sum(1 for player in players if player.section == 'hitter')} hitters"
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
