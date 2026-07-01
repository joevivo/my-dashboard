from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]

DEFAULT_INPUT = ROOT / "data" / "baseball" / "parsed" / "strat365" / "1968" / "playerset" / "1968.playerset.json"
DEFAULT_OUTPUT = ROOT / "data" / "baseball" / "raw" / "strat365" / "1968" / "players" / "1968_players_universe.json"


def money(raw: Any) -> str:
    if isinstance(raw, dict):
        return str(raw.get("raw", ""))
    return str(raw or "")


def hitter_row_text(row: dict[str, Any]) -> str:
    fields = [
        row.get("playerName"),
        row.get("team"),
        row.get("bats"),
        row.get("primaryPosition"),
        row.get("defense"),
        row.get("ab"),
        row.get("runs"),
        row.get("hits"),
        row.get("doubles"),
        row.get("triples"),
        row.get("homeRuns"),
        row.get("rbi"),
        row.get("walks"),
        row.get("strikeouts"),
        row.get("stolenBases"),
        row.get("caughtStealing"),
        row.get("steal"),
        row.get("runRating"),
        row.get("battingAverage"),
        row.get("onBasePercentage"),
        row.get("sluggingPercentage"),
        row.get("injury"),
        row.get("balance"),
        money(row.get("salary")),
    ]
    return " ".join(str(value) for value in fields if value is not None and value != "")


def pitcher_row_text(row: dict[str, Any]) -> str:
    fields = [
        row.get("playerName"),
        row.get("team"),
        row.get("throws"),
        row.get("endurance"),
        row.get("wins"),
        row.get("losses"),
        row.get("saves"),
        row.get("inningsPitched"),
        row.get("hitsAllowed"),
        row.get("earnedRuns"),
        row.get("walks"),
        row.get("strikeouts"),
        row.get("homeRunsAllowed"),
        row.get("hold"),
        row.get("balkRating"),
        row.get("wildPitchRating"),
        row.get("batting"),
        row.get("era"),
        row.get("whip"),
        row.get("balance"),
        money(row.get("salary")),
    ]
    return " ".join(str(value) for value in fields if value is not None and value != "")


def player_url(player_id: str, season: str) -> str:
    # Mirrors the existing 1980 universe URL shape closely enough for provenance.
    # Authenticated card capture will validate the exact URL shape before batch use.
    return f"https://365.strat-o-matic.com/player/{player_id}/{season}/4/{season}"


def adapt_hitter(row: dict[str, Any], season: str) -> dict[str, Any]:
    player_id = str(row["playerId"])
    return {
        "provider": "strat365",
        "season": int(season),
        "playerId": int(player_id),
        "playerName": row["playerName"],
        "sourceUrl": player_url(player_id, season),
        "rowText": hitter_row_text(row),
        "role": "hitter",
        "positionId": str(row.get("sourcePositionId") or "10"),
        "status": "discovered",
        "team": row.get("team"),
        "bats": row.get("bats"),
        "position": row.get("primaryPosition"),
    }


def adapt_pitcher(row: dict[str, Any], season: str) -> dict[str, Any]:
    player_id = str(row["playerId"])
    return {
        "provider": "strat365",
        "season": int(season),
        "playerId": int(player_id),
        "playerName": row["playerName"],
        "sourceUrl": player_url(player_id, season),
        "rowText": pitcher_row_text(row),
        "role": "pitcher",
        "positionId": str(row.get("sourcePositionId") or "1"),
        "status": "discovered",
        "team": row.get("team"),
        "throws": row.get("throws"),
        "pitchingRole": row.get("endurance"),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Adapt a Strat365 browser playerset into the BIE player universe contract.")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    source = json.loads(args.input.read_text(encoding="utf-8-sig"))
    season = str(source["season"])

    hitters = [adapt_hitter(row, season) for row in source.get("hitters", [])]
    pitchers = [adapt_pitcher(row, season) for row in source.get("pitchers", [])]
    players = hitters + pitchers

    duplicate_ids = sorted(
        player_id for player_id in {row["playerId"] for row in players}
        if sum(1 for row in players if row["playerId"] == player_id) > 1
    )

    payload = {
        "provider": "strat365",
        "season": int(season),
        "discoveryVersion": "strat365_browser_playerset_universe_adapter_v0",
        "discoveredAt": "derived-from-1968-playerset",
        "playerCount": len(players),
        "roleCounts": {
            "hitter": len(hitters),
            "pitcher": len(pitchers),
        },
        "duplicatePlayerIdsAcrossRoles": duplicate_ids,
        "sourceFiles": {
            "playerset": str(args.input.relative_to(ROOT)).replace("\\", "/"),
        },
        "notes": [
            "Adapted from public Strat365 player browser data.",
            "Authenticated card capture is still required before full card-probability parsing.",
            "sourceUrl is provisional and must be validated against authenticated card access before batch capture.",
        ],
        "players": players,
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print("Wrote:", args.output)
    print("Players:", payload["playerCount"])
    print("Hitters:", payload["roleCounts"]["hitter"])
    print("Pitchers:", payload["roleCounts"]["pitcher"])
    print("Duplicate player IDs:", len(duplicate_ids))
    print()
    print("Sample hitter:")
    print(json.dumps(hitters[0], indent=2))
    print()
    print("Sample pitcher:")
    print(json.dumps(pitchers[0], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
