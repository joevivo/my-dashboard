from __future__ import annotations

from fractions import Fraction
from pathlib import Path
import json
import re
from typing import Any


UNIVERSE_PATH = Path("data/baseball/raw/strat365/1980/players/1980_players_universe.json")
OUTPUT_DIR = Path("data/baseball/parsed/strat365/1980/player-roster-metadata")
OUTPUT_PATH = OUTPUT_DIR / "1980.player-roster-metadata.json"

SCHEMA_VERSION = "bie.player-roster-metadata.v0"
PARSER_VERSION = "bie-player-roster-metadata-parser-v0.1"

SALARY_RE = re.compile(r"(?P<salary>(?:\d+|\d*\.\d+)M)\s*$")


def parse_salary(row_text: str) -> dict[str, Any] | None:
    match = SALARY_RE.search(row_text or "")

    if not match:
        return None

    salary_text = match.group("salary")
    numeric_text = salary_text[:-1]

    if numeric_text.startswith("."):
        numeric_text = "0" + numeric_text

    salary_millions = Fraction(numeric_text)

    return {
        "raw": salary_text,
        "millions": {
            "numerator": salary_millions.numerator,
            "denominator": salary_millions.denominator,
            "decimal": round(float(salary_millions), 4),
        },
        "dollars": int(salary_millions * 1_000_000),
    }


def render_player(player: dict[str, Any]) -> dict[str, Any]:
    salary = parse_salary(player.get("rowText", ""))

    output = {
        "playerId": player.get("playerId"),
        "playerName": player.get("playerName"),
        "season": player.get("season"),
        "team": player.get("team"),
        "role": player.get("role"),
        "positionId": player.get("positionId"),
        "sourceUrl": player.get("sourceUrl"),
        "salary": salary,
        "raw": {
            "rowText": player.get("rowText"),
        },
    }

    if player.get("role") == "hitter":
        output["hitter"] = {
            "bats": player.get("bats"),
            "primaryPosition": player.get("position"),
        }

    if player.get("role") == "pitcher":
        output["pitcher"] = {
            "throws": player.get("throws"),
            "pitchingRole": player.get("pitchingRole"),
        }

    return output


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    universe = json.loads(UNIVERSE_PATH.read_text(encoding="utf-8-sig", errors="replace"))
    players = universe.get("players", [])

    rendered = [render_player(player) for player in players]

    salary_count = sum(1 for player in rendered if player.get("salary"))
    missing_salary = [player for player in rendered if not player.get("salary")]

    hitters = [player for player in rendered if player.get("role") == "hitter"]
    pitchers = [player for player in rendered if player.get("role") == "pitcher"]

    output = {
        "schemaVersion": SCHEMA_VERSION,
        "parserVersion": PARSER_VERSION,
        "season": 1980,
        "sourceFile": str(UNIVERSE_PATH).replace("\\", "/"),
        "counts": {
            "players": len(rendered),
            "hitters": len(hitters),
            "pitchers": len(pitchers),
            "salaryParsed": salary_count,
            "salaryMissing": len(missing_salary),
        },
        "players": rendered,
        "warnings": [
            {
                "type": "missing_salary",
                "playerId": player.get("playerId"),
                "playerName": player.get("playerName"),
                "rowText": player.get("raw", {}).get("rowText"),
            }
            for player in missing_salary
        ],
    }

    OUTPUT_PATH.write_text(json.dumps(output, indent=2), encoding="utf-8")

    print("BIE Player Roster Metadata Parser v0")
    print("=" * 72)
    print(f"Players: {len(rendered)}")
    print(f"Hitters: {len(hitters)}")
    print(f"Pitchers: {len(pitchers)}")
    print(f"Salary parsed: {salary_count}")
    print(f"Salary missing: {len(missing_salary)}")
    print(f"Output: {OUTPUT_PATH}")
    print("=" * 72)

    if len(rendered) != 721 or len(hitters) != 442 or len(pitchers) != 279 or salary_count != 721:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
