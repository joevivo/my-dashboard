from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ADAPTER = ROOT / "baseball" / "parser" / "adapt_strat365_playerset_to_player_universe_v0.py"
OUTPUT = ROOT / "data" / "baseball" / "raw" / "strat365" / "1968" / "players" / "1968_players_universe.json"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    subprocess.run([sys.executable, str(ADAPTER)], check=True)

    require(OUTPUT.exists(), f"Missing output: {OUTPUT}")

    data = json.loads(OUTPUT.read_text(encoding="utf-8-sig"))
    players = data.get("players", [])

    require(data.get("provider") == "strat365", "provider mismatch")
    require(data.get("season") == 1968, "season mismatch")
    require(data.get("discoveryVersion") == "strat365_browser_playerset_universe_adapter_v0", "discovery version mismatch")
    require(data.get("discoveredAt") == "derived-from-1968-playerset", "discoveredAt must be deterministic")
    require(data.get("playerCount") == 537, "player count mismatch")
    require(data.get("roleCounts", {}).get("hitter") == 325, "hitter count mismatch")
    require(data.get("roleCounts", {}).get("pitcher") == 212, "pitcher count mismatch")
    require(data.get("duplicatePlayerIdsAcrossRoles") == [], "duplicate player IDs found")
    require(len(players) == 537, "players array length mismatch")

    ids = [int(player["playerId"]) for player in players]
    require(len(ids) == len(set(ids)), "player IDs are not unique")

    hitters = [player for player in players if player.get("role") == "hitter"]
    pitchers = [player for player in players if player.get("role") == "pitcher"]

    require(len(hitters) == 325, "hitter array count mismatch")
    require(len(pitchers) == 212, "pitcher array count mismatch")

    for player in players:
        require(player.get("provider") == "strat365", f"provider mismatch for {player.get('playerId')}")
        require(player.get("season") == 1968, f"season mismatch for {player.get('playerId')}")
        require(isinstance(player.get("playerId"), int), f"playerId must be int for {player.get('playerName')}")
        require(player.get("playerName"), f"missing playerName for {player.get('playerId')}")
        require(player.get("team"), f"missing team for {player.get('playerId')}")
        require(player.get("rowText"), f"missing rowText for {player.get('playerId')}")
        require(player.get("sourceUrl"), f"missing sourceUrl for {player.get('playerId')}")
        require(player.get("status") == "discovered", f"status mismatch for {player.get('playerId')}")

        if player.get("role") == "hitter":
            require(player.get("positionId") == "10", f"hitter positionId mismatch for {player.get('playerId')}")
            require(player.get("bats"), f"missing bats for hitter {player.get('playerId')}")
            require(player.get("position"), f"missing position for hitter {player.get('playerId')}")

        elif player.get("role") == "pitcher":
            require(player.get("positionId") == "1", f"pitcher positionId mismatch for {player.get('playerId')}")
            require(player.get("throws"), f"missing throws for pitcher {player.get('playerId')}")
            require(player.get("pitchingRole"), f"missing pitchingRole for pitcher {player.get('playerId')}")

        else:
            raise AssertionError(f"unknown role for {player.get('playerId')}: {player.get('role')}")

    by_name = {player["playerName"]: player for player in players}

    aaron = by_name.get("Aaron, Hank")
    require(aaron is not None, "Aaron missing")
    require(aaron["playerId"] == 30000, "Aaron playerId mismatch")
    require(aaron["role"] == "hitter", "Aaron role mismatch")
    require(aaron["bats"] == "R", "Aaron bats mismatch")
    require(aaron["position"] == "RF", "Aaron position mismatch")
    require("10.92M" in aaron["rowText"], "Aaron salary missing from rowText")

    abernathy = by_name.get("Abernathy, Ted")
    require(abernathy is not None, "Abernathy missing")
    require(abernathy["playerId"] == 30015, "Abernathy playerId mismatch")
    require(abernathy["role"] == "pitcher", "Abernathy role mismatch")
    require(abernathy["throws"] == "R", "Abernathy throws mismatch")
    require(abernathy["pitchingRole"] == "R3", "Abernathy pitchingRole mismatch")
    require(".50M" in abernathy["rowText"], "Abernathy salary missing from rowText")

    print("PASS: Strat365 1968 playerset-to-player-universe adapter verification")
    print(f"Players: {len(players)}")
    print(f"Hitters: {len(hitters)}")
    print(f"Pitchers: {len(pitchers)}")
    print(f"Output: {OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
