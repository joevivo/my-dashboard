from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]

DEFAULT_INPUT = ROOT / "data" / "baseball" / "parsed" / "strat365" / "1968" / "playerset" / "1968.playerset.json"
DEFAULT_OUT_BASE = ROOT / "data" / "baseball" / "parsed" / "strat365" / "1968"

PLAYER_URL_TEMPLATE = "https://365.strat-o-matic.com/player/{player_id}/{season}/5/{season}"


def as_int(value: Any) -> int | None:
    if value is None or value == "":
        return None
    return int(value)


def money(raw: str, millions: float) -> dict[str, Any]:
    cents = int(round(float(millions) * 100))
    frac = Fraction(cents, 100)

    return {
        "raw": raw,
        "millions": {
            "numerator": frac.numerator,
            "denominator": frac.denominator,
            "decimal": round(float(millions), 2),
        },
        "dollars": int(round(float(millions) * 1_000_000)),
    }


def row_text_for_hitter(player: dict[str, Any]) -> str:
    fields = [
        player["playerName"],
        player["team"],
        player["bats"],
        player["primaryPosition"],
        player["defense"],
        player["ab"],
        player["runs"],
        player["hits"],
        player["doubles"],
        player["triples"],
        player["homeRuns"],
        player["rbi"],
        player["walks"],
        player["strikeouts"],
        player["stolenBases"],
        player["caughtStealing"],
        player["steal"],
        player["runRating"],
        player["battingAverage"],
        player["onBasePercentage"],
        player["sluggingPercentage"],
        player["injury"],
        player["balance"],
        player["salary"]["raw"],
    ]
    return " ".join(str(item) for item in fields)


def row_text_for_pitcher(player: dict[str, Any]) -> str:
    fields = [
        player["playerName"],
        player["team"],
        player["throws"],
        player["endurance"],
        player["wins"],
        player["losses"],
        player["saves"],
        player["inningsPitched"],
        player["hitsAllowed"],
        player["earnedRuns"],
        player["walks"],
        player["strikeouts"],
        player["homeRunsAllowed"],
        player["hold"],
        player["balkRating"],
        player["wildPitchRating"],
        player["batting"],
        player["era"],
        player["whip"],
        player["balance"],
        player["salary"]["raw"],
    ]
    return " ".join(str(item) for item in fields)


def normalize_position(position: str) -> str:
    return position.strip().upper()


def parse_browser_defense(position: str, defense: str) -> dict[str, Any]:
    pos = normalize_position(position)
    raw = defense.strip()

    # Browser defense examples:
    # OF/C: 1(-3)e3, 4(+4)e15
    # IF/1B: 3e25, 1e15
    match = re.fullmatch(r"(?P<range>\d+)(?:\((?P<arm>[+-]?\d+)\))?e(?P<error>\d+)", raw)

    if not match:
        return {
            "raw": f"{pos.lower()}-{raw}",
            "defenseRaw": raw,
            "defenseUnavailable": True,
            "running": None,
            "positions": [],
            "warnings": [f"Could not parse browser defense: {raw}"],
        }

    arm = match.group("arm")

    parsed = {
        "position": pos,
        "range": int(match.group("range")),
        "arm": int(arm) if arm is not None else None,
        "error": int(match.group("error")),
        "raw": f"{pos.lower()}-{raw}",
    }

    return {
        "raw": f"Defense: {parsed['raw']}",
        "defenseRaw": parsed["raw"],
        "defenseUnavailable": False,
        "running": None,
        "positions": [parsed],
        "warnings": [],
    }


def adapt_roster_player(player: dict[str, Any], season: int) -> dict[str, Any]:
    player_id = as_int(player["playerId"])
    salary = money(player["salary"]["raw"], player["salary"]["millions"])

    base = {
        "playerId": player_id,
        "playerName": player["playerName"],
        "season": season,
        "team": player["team"],
        "teamId": as_int(player["teamId"]),
        "role": player["role"],
        "positionId": player.get("sourcePositionId"),
        "sourceUrl": PLAYER_URL_TEMPLATE.format(player_id=player_id, season=season),
        "salary": salary,
    }

    if player["role"] == "hitter":
        base["raw"] = {"rowText": row_text_for_hitter(player)}
        base["hitter"] = {
            "bats": player["bats"],
            "primaryPosition": player["primaryPosition"],
            "defense": player["defense"],
            "balance": player["balance"],
            "injury": player["injury"],
            "runRating": player["runRating"],
            "steal": player["steal"],
        }
        base["hitterStats"] = {
            "ab": player["ab"],
            "runs": player["runs"],
            "hits": player["hits"],
            "doubles": player["doubles"],
            "triples": player["triples"],
            "homeRuns": player["homeRuns"],
            "rbi": player["rbi"],
            "walks": player["walks"],
            "strikeouts": player["strikeouts"],
            "stolenBases": player["stolenBases"],
            "caughtStealing": player["caughtStealing"],
            "battingAverage": player["battingAverage"],
            "onBasePercentage": player["onBasePercentage"],
            "sluggingPercentage": player["sluggingPercentage"],
        }
    else:
        base["raw"] = {"rowText": row_text_for_pitcher(player)}
        base["pitcher"] = {
            "throws": player["throws"],
            "endurance": player["endurance"],
            "balance": player["balance"],
            "batting": player["batting"],
        }
        base["pitcherStats"] = {
            "wins": player["wins"],
            "losses": player["losses"],
            "saves": player["saves"],
            "inningsPitched": player["inningsPitched"],
            "hitsAllowed": player["hitsAllowed"],
            "earnedRuns": player["earnedRuns"],
            "walks": player["walks"],
            "strikeouts": player["strikeouts"],
            "homeRunsAllowed": player["homeRunsAllowed"],
            "hold": player["hold"],
            "balkRating": player["balkRating"],
            "wildPitchRating": player["wildPitchRating"],
            "era": player["era"],
            "whip": player["whip"],
        }

    return base


def adapt_defense_player(player: dict[str, Any], season: int) -> dict[str, Any]:
    player_id = as_int(player["playerId"])

    base = {
        "playerId": player_id,
        "playerName": player["playerName"],
        "season": season,
        "team": player["team"],
        "teamId": as_int(player["teamId"]),
        "role": player["role"],
        "rowText": row_text_for_hitter(player) if player["role"] == "hitter" else row_text_for_pitcher(player),
        "sourceCardPath": None,
        "source": "strat365-playerset-browser",
        "warnings": [],
    }

    if player["role"] == "hitter":
        defense = parse_browser_defense(player["primaryPosition"], player["defense"])
        base["hitterDefense"] = defense
        base["warnings"].extend(defense.get("warnings", []))
    else:
        base["pitcherDefense"] = {
            "defenseUnavailable": True,
            "reason": "Pitcher fielding defense is not exposed in the player-set browser import.",
            "throws": player["throws"],
            "endurance": player["endurance"],
        }

    return base


def main() -> int:
    parser = argparse.ArgumentParser(description="Adapt Strat365 1968 playerset browser data into BIE metadata shapes.")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--out-base", type=Path, default=DEFAULT_OUT_BASE)
    args = parser.parse_args()

    data = json.loads(args.input.read_text(encoding="utf-8"))
    season = int(data["season"])

    source_players = data["hitters"] + data["pitchers"]

    roster_players = [adapt_roster_player(player, season) for player in source_players]
    defense_players = [adapt_defense_player(player, season) for player in source_players]

    roster_dir = args.out_base / "player-roster-metadata"
    defense_dir = args.out_base / "player-defense-metadata"
    roster_dir.mkdir(parents=True, exist_ok=True)
    defense_dir.mkdir(parents=True, exist_ok=True)

    roster_path = roster_dir / f"{season}.player-roster-metadata.json"
    defense_path = defense_dir / f"{season}.player-defense-metadata.json"

    role_counts = {
        "hitters": sum(1 for player in roster_players if player["role"] == "hitter"),
        "pitchers": sum(1 for player in roster_players if player["role"] == "pitcher"),
    }

    roster_payload = {
        "schemaVersion": "strat365.player-roster-metadata.browser-adapter.v0",
        "parserVersion": "adapt_strat365_playerset_to_bie_metadata_v0",
        "season": season,
        "sourceFile": str(args.input.relative_to(ROOT)).replace("\\", "/"),
        "counts": {
            "players": len(roster_players),
            "hitters": role_counts["hitters"],
            "pitchers": role_counts["pitchers"],
            "salaryParsed": sum(1 for player in roster_players if player.get("salary")),
            "salaryMissing": 0,
        },
        "players": roster_players,
        "warnings": [
            "Adapter is browser-derived. It does not include full authenticated card probabilities.",
            "Hitter defense is primary-position-only from the player browser.",
        ],
    }

    defense_payload = {
        "schemaVersion": "strat365.player-defense-metadata.browser-adapter.v0",
        "parserVersion": "adapt_strat365_playerset_to_bie_metadata_v0",
        "season": season,
        "sourceFiles": {
            "playerset": str(args.input.relative_to(ROOT)).replace("\\", "/"),
            "cardDirs": [],
        },
        "counts": {
            "players": len(defense_players),
            "roleCounts": {
                "hitter": role_counts["hitters"],
                "pitcher": role_counts["pitchers"],
            },
            "warnings": sum(len(player.get("warnings", [])) for player in defense_players),
        },
        "players": defense_players,
        "warnings": [
            "Browser-derived defense only. Multi-position card defense still requires authenticated card capture.",
            "Pitcher fielding defense is unavailable from the player-set browser.",
        ],
    }

    roster_path.write_text(json.dumps(roster_payload, indent=2), encoding="utf-8")
    defense_path.write_text(json.dumps(defense_payload, indent=2), encoding="utf-8")

    print("Wrote:", roster_path)
    print("Wrote:", defense_path)
    print("Players:", len(roster_players))
    print("Hitters:", role_counts["hitters"])
    print("Pitchers:", role_counts["pitchers"])
    print("Defense warnings:", defense_payload["counts"]["warnings"])

    sample_hitter = next(player for player in defense_players if player["role"] == "hitter")
    print()
    print("Sample hitter defense:")
    print(json.dumps(sample_hitter["hitterDefense"], indent=2))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
