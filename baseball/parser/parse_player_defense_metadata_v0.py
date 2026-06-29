from __future__ import annotations

from pathlib import Path
import json
import re
from typing import Any

from bs4 import BeautifulSoup


UNIVERSE_PATH = Path("data/baseball/raw/strat365/1980/players/1980_players_universe.json")
OUTPUT_DIR = Path("data/baseball/parsed/strat365/1980/player-defense-metadata")
OUTPUT_PATH = OUTPUT_DIR / "1980.player-defense-metadata.json"

CARD_DIRS = [
    Path("data/baseball/raw/strat365/authenticated/1980/cards"),
    Path("data/baseball/raw/strat365/1980/cards"),
]

SCHEMA_VERSION = "bie.player-defense-metadata.v0"
PARSER_VERSION = "bie-player-defense-metadata-parser-v0.1"

DEFENSE_RE = re.compile(
    r"(?P<position>1b|2b|3b|ss|lf|cf|rf|c)-"
    r"(?P<range>\d+)"
    r"(?:\((?P<arm>[+-]?\d+)\))?"
    r"e(?P<error>\d+)",
    re.IGNORECASE,
)


def load_players(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [row for row in payload if isinstance(row, dict)]

    if isinstance(payload, dict):
        for key in ("players", "items", "rows", "data"):
            value = payload.get(key)
            if isinstance(value, list):
                return [row for row in value if isinstance(row, dict)]

    raise ValueError(f"Could not locate player list in {UNIVERSE_PATH}")


def card_path(player_id: str) -> Path | None:
    for directory in CARD_DIRS:
        path = directory / f"{player_id}.html"
        if path.exists():
            return path
    return None


def table_texts(path: Path) -> list[str]:
    html = path.read_text(encoding="utf-8-sig", errors="replace")
    soup = BeautifulSoup(html, "html.parser")
    return [table.get_text(" ", strip=True) for table in soup.find_all("table")]


def find_hitter_defense_table(tables: list[str]) -> str | None:
    for text in tables:
        if "Defense:" in text:
            return text
    return None


def find_pitcher_metadata_table(tables: list[str]) -> str | None:
    for text in tables:
        lowered = text.casefold()
        if "pitcher-" in lowered and "hold" in lowered:
            return text
    return None


def int_match(pattern: str, text: str) -> int | None:
    match = re.search(pattern, text, re.IGNORECASE)
    if not match:
        return None
    return int(match.group(1))


def str_match(pattern: str, text: str) -> str | None:
    match = re.search(pattern, text, re.IGNORECASE)
    if not match:
        return None
    return match.group(1)


def parse_hitter_defense(raw: str) -> dict[str, Any]:
    defense_part = raw

    if "Defense:" in defense_part:
        defense_part = defense_part.split("Defense:", 1)[1].strip()

    running = str_match(r"\brunning\s+([0-9]+-[0-9]+)", defense_part)

    if " running " in defense_part:
        defense_only = defense_part.split(" running ", 1)[0].strip()
    else:
        defense_only = defense_part.strip()

    positions: list[dict[str, Any]] = []

    for match in DEFENSE_RE.finditer(defense_only):
        positions.append(
            {
                "position": match.group("position").upper(),
                "range": int(match.group("range")),
                "arm": int(match.group("arm")) if match.group("arm") is not None else None,
                "error": int(match.group("error")),
                "raw": match.group(0),
            }
        )

    return {
        "raw": raw,
        "defenseRaw": defense_only,
        "defenseUnavailable": defense_only == "-",
        "running": running,
        "positions": positions,
    }


def parse_pitcher_metadata(raw: str) -> dict[str, Any]:
    relief_match = re.search(r"\brelief\((\d+)\)/(\d+)", raw, re.IGNORECASE)

    return {
        "raw": raw,
        "balk": int_match(r"\bbk-\s*(\d+)", raw),
        "wildPitch": int_match(r"\bwp-\s*(\d+)", raw),
        "error": int_match(r"\be(\d+)\b", raw),
        "pitcherDefense": int_match(r"\bpitcher-(\d+)", raw),
        "hold": int_match(r"\bhold\s*([+-]?\d+)", raw),
        "bunting": str_match(r"\bbunting-([A-E])", raw),
        "starterEndurance": int_match(r"\bstarter\((\d+)\)", raw),
        "reliefEndurance": int(relief_match.group(1)) if relief_match else None,
        "reliefFatigue": int(relief_match.group(2)) if relief_match else None,
        "weaknessRaw": str_match(r"#([0-9A-Z]+)", raw),
    }


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    raw = json.loads(UNIVERSE_PATH.read_text(encoding="utf-8-sig", errors="replace"))
    players = load_players(raw)

    output_players: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []

    for player in players:
        player_id = str(player["playerId"])
        path = card_path(player_id)

        row: dict[str, Any] = {
            "playerId": int(player_id),
            "playerName": player.get("playerName"),
            "team": player.get("team"),
            "role": player.get("role"),
            "rowText": player.get("rowText"),
            "sourceCardPath": str(path).replace("\\", "/") if path else None,
            "warnings": [],
        }

        if path is None:
            row["warnings"].append("missing_card_html")
            output_players.append(row)
            warnings.append({"playerId": int(player_id), "warning": "missing_card_html"})
            continue

        tables = table_texts(path)

        if player.get("role") == "hitter":
            defense_table = find_hitter_defense_table(tables)
            if defense_table:
                row["hitterDefense"] = parse_hitter_defense(defense_table)
                if not row["hitterDefense"]["positions"] and not row["hitterDefense"].get("defenseUnavailable"):
                    row["warnings"].append("no_hitter_defense_positions_parsed")
            else:
                row["warnings"].append("missing_hitter_defense_table")

        elif player.get("role") == "pitcher":
            metadata_table = find_pitcher_metadata_table(tables)
            if metadata_table:
                row["pitcherDefense"] = parse_pitcher_metadata(metadata_table)
            else:
                row["warnings"].append("missing_pitcher_metadata_table")

        else:
            row["warnings"].append("unknown_role")

        for warning in row["warnings"]:
            warnings.append({"playerId": int(player_id), "warning": warning})

        output_players.append(row)

    role_counts: dict[str, int] = {}
    for player in output_players:
        role = str(player.get("role"))
        role_counts[role] = role_counts.get(role, 0) + 1

    output = {
        "schemaVersion": SCHEMA_VERSION,
        "parserVersion": PARSER_VERSION,
        "season": 1980,
        "sourceFiles": {
            "universe": str(UNIVERSE_PATH).replace("\\", "/"),
            "cardDirs": [str(path).replace("\\", "/") for path in CARD_DIRS],
        },
        "counts": {
            "players": len(output_players),
            "roleCounts": role_counts,
            "warnings": len(warnings),
        },
        "players": output_players,
        "warnings": warnings,
    }

    OUTPUT_PATH.write_text(json.dumps(output, indent=2), encoding="utf-8")

    hitter_position_rows = sum(
        len(player.get("hitterDefense", {}).get("positions", []))
        for player in output_players
        if player.get("role") == "hitter"
    )

    pitcher_rows = sum(
        1
        for player in output_players
        if player.get("role") == "pitcher" and "pitcherDefense" in player
    )

    print("BIE Player Defense Metadata Parser v0")
    print("=" * 80)
    print(f"Players: {len(output_players)}")
    print(f"Role counts: {role_counts}")
    print(f"Hitter defensive position rows: {hitter_position_rows}")
    print(f"Pitcher metadata rows: {pitcher_rows}")
    print(f"Warnings: {len(warnings)}")
    print(f"Output: {OUTPUT_PATH}")

    if warnings:
        print()
        print("Warning examples:")
        for warning in warnings[:20]:
            print(warning)


if __name__ == "__main__":
    main()

